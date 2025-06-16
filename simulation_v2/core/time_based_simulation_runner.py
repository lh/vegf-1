"""
Simulation runner for time-based disease progression model.

Separate from standard SimulationRunner as the models are fundamentally different.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

from simulation_v2.protocols.time_based_protocol_spec import TimeBasedProtocolSpecification
from simulation_v2.core.disease_model_time_based import DiseaseModelTimeBased
from simulation_v2.core.protocol import StandardProtocol
from simulation_v2.core.loading_dose_protocol import LoadingDoseProtocol
from simulation_v2.engines.abs_engine_time_based_with_specs import ABSEngineTimeBasedWithSpecs
from simulation_v2.engines.abs_engine_time_based_with_params import ABSEngineTimeBasedWithParams
from simulation_v2.engines.abs_engine import SimulationResults


class TimeBasedSimulationRunner:
    """Run time-based simulations with full parameter tracking."""
    
    def __init__(self, protocol_spec: TimeBasedProtocolSpecification):
        """
        Initialize with time-based protocol specification.
        
        Args:
            protocol_spec: Time-based protocol specification
        """
        self.spec = protocol_spec
        self.audit_log: List[Dict[str, Any]] = []
        
        # Log specification load
        self.audit_log.append({
            'event': 'protocol_loaded',
            'timestamp': datetime.now().isoformat(),
            'protocol': self.spec.to_audit_log()
        })
    
    def run(
        self,
        engine_type: str,
        n_patients: int,
        duration_years: float,
        seed: int
    ) -> SimulationResults:
        """
        Run time-based simulation.
        
        Args:
            engine_type: 'abs' only (DES not yet implemented)
            n_patients: Number of patients to simulate
            duration_years: Simulation duration in years
            seed: Random seed for reproducibility
            
        Returns:
            SimulationResults with patient histories
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
            'event': 'simulation_start',
            'timestamp': datetime.now().isoformat(),
            'engine_type': engine_type,
            'n_patients': n_patients,
            'duration_years': duration_years,
            'seed': seed,
            'protocol_name': self.spec.name,
            'protocol_version': self.spec.version,
            'protocol_checksum': self.spec.checksum,
            'model_type': self.spec.model_type
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
        
        # Create time-based ABS engine with full parameter support
        # Use ABSEngineTimeBasedWithParams which removes all hardcoded values
        engine = ABSEngineTimeBasedWithParams(
            disease_model=disease_model,
            protocol=protocol,
            protocol_spec=self.spec,
            n_patients=n_patients,
            seed=seed
        )
        
        # Run simulation
        results = engine.run(duration_years)
        
        # Log completion
        self.audit_log.append({
            'event': 'simulation_complete',
            'timestamp': datetime.now().isoformat(),
            'total_injections': results.total_injections,
            'final_vision_mean': results.final_vision_mean,
            'final_vision_std': results.final_vision_std,
            'discontinuation_rate': results.discontinuation_rate,
            'patient_count': results.patient_count
        })
        
        return results
    
    def save_audit_trail(self, filepath: Path) -> None:
        """
        Save complete audit trail to JSON file.
        
        Args:
            filepath: Path to save audit trail
        """
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w') as f:
            json.dump(self.audit_log, f, indent=2)
        
        # Log save event
        self.audit_log.append({
            'event': 'audit_trail_saved',
            'timestamp': datetime.now().isoformat(),
            'filepath': str(filepath)
        })