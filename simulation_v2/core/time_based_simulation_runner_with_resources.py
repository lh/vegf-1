"""
Time-based simulation runner with integrated resource tracking.

Extends the standard runner to use the resource-aware engine.
"""

from pathlib import Path
from typing import Optional, Dict, Any

from simulation_v2.core.time_based_simulation_runner import TimeBasedSimulationRunner
from simulation_v2.engines.abs_engine_time_based_with_resources import ABSEngineTimeBasedWithResources
from simulation_v2.core.disease_model_time_based import DiseaseModelTimeBased
from simulation_v2.core.loading_dose_protocol import LoadingDoseProtocol
from simulation_v2.core.protocol import StandardProtocol
from simulation_v2.models.baseline_vision_distributions import DistributionFactory


class TimeBasedSimulationRunnerWithResources(TimeBasedSimulationRunner):
    """Run time-based simulations with resource tracking."""
    
    def __init__(self, protocol_spec, resource_config: Optional[Dict[str, Any]] = None,
                 resource_config_path: Optional[str] = None):
        """
        Initialize with resource configuration.
        
        Args:
            protocol_spec: Time-based protocol specification
            resource_config: Resource configuration dictionary
            resource_config_path: Path to resource configuration YAML
        """
        super().__init__(protocol_spec)
        self.resource_config = resource_config
        self.resource_config_path = resource_config_path
    
    def run(self, engine_type: str, n_patients: int, duration_years: float, seed: int):
        """
        Run simulation with resource tracking.
        
        Args:
            engine_type: 'abs' only (DES not yet implemented)
            n_patients: Number of patients to simulate
            duration_years: Simulation duration in years
            seed: Random seed for reproducibility
            
        Returns:
            SimulationResults with resource tracking data
        """
        # Validate parameters
        if engine_type.lower() != 'abs':
            raise NotImplementedError(f"Only ABS engine implemented for time-based model, not {engine_type}")
        
        if n_patients <= 0:
            raise ValueError(f"Number of patients must be positive, got {n_patients}")
        
        if duration_years <= 0:
            raise ValueError(f"Duration must be positive, got {duration_years}")
        
        # Log simulation start
        self.audit_log.append({
            'event': 'simulation_start_with_resources',
            'timestamp': self._get_timestamp(),
            'engine_type': engine_type,
            'n_patients': n_patients,
            'duration_years': duration_years,
            'seed': seed,
            'protocol_name': self.spec.name,
            'protocol_version': self.spec.version,
            'resource_tracking': bool(self.resource_config or self.resource_config_path)
        })
        
        # Create disease model from parameter files
        params_dir = Path(self.spec.source_file).parent / 'parameters'
        disease_model = DiseaseModelTimeBased.from_parameter_files(
            params_dir=params_dir,
            seed=seed
        )
        
        # Create protocol with loading dose if specified
        if self.spec.loading_dose_injections:
            protocol = LoadingDoseProtocol(
                loading_dose_injections=self.spec.loading_dose_injections,
                loading_dose_interval_days=self.spec.loading_dose_interval_days,
                min_interval_days=self.spec.min_interval_days,
                max_interval_days=self.spec.max_interval_days,
                extension_days=self.spec.extension_days,
                shortening_days=self.spec.shortening_days
            )
        else:
            protocol = StandardProtocol(
                min_interval_days=self.spec.min_interval_days,
                max_interval_days=self.spec.max_interval_days,
                extension_days=self.spec.extension_days,
                shortening_days=self.spec.shortening_days
            )
        
        # Create baseline vision distribution from spec
        baseline_vision_distribution = DistributionFactory.create_from_protocol_spec(self.spec)
        
        # Create resource-aware engine
        engine = ABSEngineTimeBasedWithResources(
            resource_config=self.resource_config,
            resource_config_path=self.resource_config_path,
            disease_model=disease_model,
            protocol=protocol,
            protocol_spec=self.spec,
            n_patients=n_patients,
            seed=seed,
            baseline_vision_distribution=baseline_vision_distribution
        )
        
        # Run simulation
        results = engine.run(duration_years)
        
        # Log completion with resource summary
        completion_log = {
            'event': 'simulation_complete_with_resources',
            'timestamp': self._get_timestamp(),
            'total_injections': results.total_injections,
            'final_vision_mean': results.final_vision_mean,
            'final_vision_std': results.final_vision_std,
            'discontinuation_rate': results.discontinuation_rate,
            'patient_count': results.patient_count
        }
        
        # Add resource tracking summary if available
        if hasattr(results, 'total_costs'):
            completion_log['total_costs'] = results.total_costs
            completion_log['average_cost_per_patient_year'] = getattr(
                results, 'average_cost_per_patient_year', None
            )
        
        if hasattr(results, 'workload_summary'):
            completion_log['total_visits'] = results.workload_summary.get('total_visits', 0)
            completion_log['bottleneck_count'] = len(getattr(results, 'bottlenecks', []))
        
        self.audit_log.append(completion_log)
        
        return results
    
    def _get_timestamp(self):
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()