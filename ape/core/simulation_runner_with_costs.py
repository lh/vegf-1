"""
Enhanced Streamlit simulation runner with cost tracking support.

Extends the base simulation runner to include economic analysis capabilities.
"""

import time
from pathlib import Path
from typing import Dict, Any, List, Optional

from simulation_v2.core.simulation_runner import SimulationRunner as V2SimulationRunner
from simulation_v2.protocols.protocol_spec import ProtocolSpecification
from simulation_v2.protocols.time_based_protocol_spec import TimeBasedProtocolSpecification
from simulation_v2.core.time_based_simulation_runner import TimeBasedSimulationRunner
from simulation_v2.economics.cost_config import CostConfig
from simulation_v2.economics.enhanced_cost_tracker import EnhancedCostTracker

from .results.factory import ResultsFactory
from .results.base import SimulationResults
from .simulation_runner import SimulationRunner


class SimulationRunnerWithCosts(SimulationRunner):
    """
    Enhanced simulation runner that supports cost tracking.
    
    Extends the base runner to:
    - Accept cost configuration parameters
    - Use cost-aware simulation engines
    - Include economic analysis in results
    """
    
    def __init__(self, protocol_spec, cost_config: Optional[CostConfig] = None):
        """
        Initialize with protocol specification and optional cost configuration.
        
        Args:
            protocol_spec: Protocol specification to use (standard or time-based)
            cost_config: Optional cost configuration for economic analysis
        """
        # Initialize base runner
        super().__init__(protocol_spec)
        
        # Store cost configuration
        self.cost_config = cost_config
        
    def run(
        self,
        engine_type: str,
        n_patients: int,
        duration_years: float,
        seed: int,
        show_progress: bool = True,
        recruitment_mode: str = "Fixed Total",
        patient_arrival_rate: Optional[float] = None,
        drug_type: Optional[str] = None
    ) -> SimulationResults:
        """
        Run simulation with optional cost tracking.
        
        Args:
            engine_type: 'abs' or 'des'
            n_patients: Number of patients to simulate (Fixed Total Mode)
            duration_years: Duration in years
            seed: Random seed
            show_progress: Show progress indicators
            recruitment_mode: "Fixed Total" or "Constant Rate"
            patient_arrival_rate: Patients per week (Constant Rate Mode only)
            drug_type: Active drug for cost calculations
            
        Returns:
            SimulationResults instance with simulation data and cost tracking
        """
        # Show start message
        if show_progress:
            cost_msg = " with cost tracking" if self.cost_config else ""
            print(f"🚀 Starting {engine_type.upper()} simulation{cost_msg}: "
                  f"{n_patients:,} patients × {duration_years} years")
            
        # Track runtime
        start_time = time.time()
        
        # Check if we need to use cost-aware engine
        if self.cost_config and engine_type == 'abs':
            # Use enhanced ABS engine with cost tracking
            raw_results = self._run_with_cost_tracking(
                n_patients=n_patients,
                duration_years=duration_years,
                seed=seed,
                drug_type=drug_type
            )
        else:
            # Run standard V2 simulation
            raw_results = self.v2_runner.run(
                engine_type=engine_type,
                n_patients=n_patients,
                duration_years=duration_years,
                seed=seed
            )
        
        runtime_seconds = time.time() - start_time
        
        if show_progress:
            print(f"✅ Simulation completed in {runtime_seconds:.1f} seconds")
            
        # Convert to results with cost data if available
        results = self._create_results_with_costs(
            raw_results=raw_results,
            engine_type=engine_type,
            n_patients=n_patients,
            duration_years=duration_years,
            seed=seed,
            runtime_seconds=runtime_seconds,
            drug_type=drug_type
        )
        
        # Save additional cost tracking data if available
        if hasattr(raw_results, 'cost_tracker') and raw_results.cost_tracker:
            self._save_cost_tracking_data(results, raw_results.cost_tracker)
            
        return results
        
    def _run_with_cost_tracking(
        self,
        n_patients: int,
        duration_years: float,
        seed: int,
        drug_type: Optional[str] = None
    ) -> Any:
        """
        Run simulation using cost-aware engine.
        
        Args:
            n_patients: Number of patients
            duration_years: Duration in years
            seed: Random seed
            drug_type: Active drug for costs
            
        Returns:
            Raw simulation results with cost tracking
        """
        # Import the enhanced engine
        from simulation_v2.engines.abs_engine_with_enhanced_costs import ABSEngineWithEnhancedCosts
        
        # Create disease model and protocol
        disease_model = self.v2_runner._create_disease_model()
        protocol = self.v2_runner._create_protocol()
        
        # Determine protocol type for cost tracker
        protocol_type = "fixed" if "treat_and_treat" in self.protocol_spec.name.lower() else "treat_and_extend"
        
        # Create enhanced engine with cost tracking
        engine = ABSEngineWithEnhancedCosts(
            disease_model=disease_model,
            protocol=protocol,
            protocol_spec=self.protocol_spec,
            n_patients=n_patients,
            seed=seed,
            clinical_improvements=self.v2_runner.clinical_improvements,
            cost_config=self.cost_config,
            drug_type=drug_type or "eylea_2mg_biosimilar"
        )
        
        # Run simulation
        results = engine.run(
            duration_years=duration_years,
            recruitment_period_months=0.0  # TODO: Support recruitment period
        )
        
        return results
        
    def _create_results_with_costs(
        self,
        raw_results: Any,
        engine_type: str,
        n_patients: int,
        duration_years: float,
        seed: int,
        runtime_seconds: float,
        drug_type: Optional[str] = None
    ) -> SimulationResults:
        """
        Create results object including cost tracking data.
        
        Args:
            raw_results: Raw simulation results
            engine_type: Engine type used
            n_patients: Number of patients
            duration_years: Duration in years
            seed: Random seed
            runtime_seconds: Runtime in seconds
            drug_type: Active drug used
            
        Returns:
            SimulationResults with cost data
        """
        # Create base results
        results = ResultsFactory.create_results(
            raw_results=raw_results,
            protocol_name=self.protocol_spec.name,
            protocol_version=self.protocol_spec.version,
            engine_type=engine_type,
            n_patients=n_patients,
            duration_years=duration_years,
            seed=seed,
            runtime_seconds=runtime_seconds,
            model_type="time_based" if self.is_time_based else "visit_based"
        )
        
        # Add cost tracking metadata if available
        if hasattr(raw_results, 'cost_tracker') and raw_results.cost_tracker:
            results.metadata.has_cost_tracking = True
            results.metadata.drug_type = drug_type or "eylea_2mg_biosimilar"
            
            # Store cost effectiveness summary in metadata
            ce_metrics = raw_results.cost_effectiveness
            results.metadata.cost_effectiveness = {
                'total_cost': ce_metrics['total_cost'],
                'cost_per_patient': ce_metrics['cost_per_patient'],
                'cost_per_injection': ce_metrics['cost_per_injection'],
                'cost_per_vision_maintained': ce_metrics['cost_per_vision_maintained']
            }
        else:
            results.metadata.has_cost_tracking = False
            
        # Save protocol and audit log as before
        self._save_protocol_and_audit(results)
        
        return results
        
    def _save_protocol_and_audit(self, results: SimulationResults) -> None:
        """Save protocol specification and audit log."""
        # Save the full protocol specification
        protocol_path = results.data_path / "protocol.yaml"
        try:
            import yaml
            protocol_dict = self.protocol_spec.to_yaml_dict()
            with open(protocol_path, 'w') as f:
                yaml.dump(protocol_dict, f, default_flow_style=False, sort_keys=False)
        except Exception as e:
            print(f"Warning: Could not save full protocol spec: {e}")
            
        # Save audit log if available
        if hasattr(self.v2_runner, 'audit_log'):
            audit_log_path = results.data_path / "audit_log.json"
            try:
                import json
                with open(audit_log_path, 'w') as f:
                    json.dump(self.v2_runner.audit_log, f, indent=2)
            except Exception as e:
                print(f"Warning: Could not save audit log: {e}")
                
    def _save_cost_tracking_data(
        self, 
        results: SimulationResults, 
        cost_tracker: EnhancedCostTracker
    ) -> None:
        """
        Save detailed cost tracking data to results directory.
        
        Args:
            results: Simulation results object
            cost_tracker: Enhanced cost tracker with data
        """
        try:
            # Save workload summary
            workload_df = cost_tracker.get_workload_summary()
            if not workload_df.empty:
                workload_path = results.data_path / "workload_summary.parquet"
                workload_df.to_parquet(workload_path, index=False)
                
            # Save cost breakdown
            import json
            cost_breakdown = cost_tracker.get_cost_breakdown()
            breakdown_path = results.data_path / "cost_breakdown.json"
            with open(breakdown_path, 'w') as f:
                json.dump(cost_breakdown, f, indent=2)
                
            # Save patient cost data
            patient_path = results.data_path / "patient_costs.csv"
            cost_tracker.export_patient_data(str(patient_path))
            
        except Exception as e:
            print(f"Warning: Could not save cost tracking data: {e}")