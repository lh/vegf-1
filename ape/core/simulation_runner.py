"""
Streamlit simulation runner for APE V2.

Provides a clean interface between Streamlit UI and the V2 simulation engine,
handling progress reporting, timing, and result conversion to Parquet format.
"""

import time
from pathlib import Path
from typing import Dict, Any, List, Optional

from simulation_v2.core.simulation_runner import SimulationRunner as V2SimulationRunner
from simulation_v2.protocols.protocol_spec import ProtocolSpecification

from .results.factory import ResultsFactory
from .results.base import SimulationResults


class SimulationRunner:
    """
    Simulation runner that bridges Streamlit UI with V2 engine.
    
    Handles:
    - Running simulations with progress feedback
    - Converting results to Parquet format
    - Tracking runtime and audit logs
    """
    
    def __init__(self, protocol_spec: ProtocolSpecification):
        """
        Initialize with protocol specification.
        
        Args:
            protocol_spec: Protocol specification to use
        """
        self.v2_runner = V2SimulationRunner(protocol_spec)
        self.protocol_spec = protocol_spec
        
    def run(
        self,
        engine_type: str,
        n_patients: int,
        duration_years: float,
        seed: int,
        show_progress: bool = True,
        recruitment_mode: str = "Fixed Total",
        patient_arrival_rate: Optional[float] = None
    ) -> SimulationResults:
        """
        Run simulation and return results in Parquet format.
        
        Args:
            engine_type: 'abs' or 'des'
            n_patients: Number of patients to simulate (Fixed Total Mode)
            duration_years: Duration in years
            seed: Random seed
            show_progress: Show progress indicators
            recruitment_mode: "Fixed Total" or "Constant Rate"
            patient_arrival_rate: Patients per week (Constant Rate Mode only)
            
        Returns:
            ParquetResults instance with simulation data
        """
        # Show start message
        if show_progress:
            print(f"🚀 Starting {engine_type.upper()} simulation: "
                  f"{n_patients:,} patients × {duration_years} years")
            
        # Track runtime
        start_time = time.time()
        
        # Run V2 simulation
        raw_results = self.v2_runner.run(
            engine_type=engine_type,
            n_patients=n_patients,
            duration_years=duration_years,
            seed=seed
        )
        
        runtime_seconds = time.time() - start_time
        
        if show_progress:
            print(f"✅ Simulation completed in {runtime_seconds:.1f} seconds")
            
        # Convert to Parquet results
        results = ResultsFactory.create_results(
            raw_results=raw_results,
            protocol_name=self.protocol_spec.name,
            protocol_version=self.protocol_spec.version,
            engine_type=engine_type,
            n_patients=n_patients,
            duration_years=duration_years,
            seed=seed,
            runtime_seconds=runtime_seconds
        )
        
        # Save the full protocol specification with the results
        protocol_path = results.data_path / "protocol.yaml"
        try:
            import yaml
            
            # Use the built-in to_yaml_dict method
            protocol_dict = self.protocol_spec.to_yaml_dict()
            
            with open(protocol_path, 'w') as f:
                yaml.dump(protocol_dict, f, default_flow_style=False, sort_keys=False)
                    
            print(f"✅ Saved full protocol specification to {protocol_path}")
        except Exception as e:
            print(f"Warning: Could not save full protocol spec: {e}")
            
        # Save audit log if available
        if hasattr(self, 'v2_runner') and hasattr(self.v2_runner, 'audit_log'):
            audit_log_path = results.data_path / "audit_log.json"
            try:
                import json
                with open(audit_log_path, 'w') as f:
                    json.dump(self.v2_runner.audit_log, f, indent=2)
                print(f"✅ Saved audit log with {len(self.v2_runner.audit_log)} events")
            except Exception as e:
                print(f"Warning: Could not save audit log: {e}")
        
        return results
        
    @property
    def audit_log(self) -> List[Dict[str, Any]]:
        """Get audit log from V2 runner."""
        return self.v2_runner.audit_log
        

def upgrade_existing_results(
    existing_results: Dict[str, Any],
    protocol_info: Dict[str, Any]
) -> SimulationResults:
    """
    Upgrade existing session state results to Parquet format.
    
    This is used for backward compatibility with results already
    in Streamlit session state.
    
    Args:
        existing_results: Dictionary with 'results' and other fields
        protocol_info: Protocol information dictionary
        
    Returns:
        ParquetResults instance
    """
    raw_results = existing_results['results']
    params = existing_results['parameters']
    
    return ResultsFactory.create_results(
        raw_results=raw_results,
        protocol_name=protocol_info['name'],
        protocol_version=protocol_info['version'],
        engine_type=params['engine'],
        n_patients=params['n_patients'],
        duration_years=params['duration_years'],
        seed=params['seed'],
        runtime_seconds=existing_results.get('runtime', 0.0)
    )