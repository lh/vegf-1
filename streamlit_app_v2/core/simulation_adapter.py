"""
Adapter to integrate memory-aware results with existing simulation infrastructure.

This module provides a bridge between the V2 simulation engine and the new
memory-aware results architecture.
"""

import sys
from pathlib import Path
from typing import Dict, Any, Optional, List

# Add parent to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from simulation_v2.core.simulation_runner import SimulationRunner as V2SimulationRunner
from simulation_v2.protocols.protocol_spec import ProtocolSpecification

from .results.factory import ResultsFactory
from .results.base import SimulationResults
from .monitoring.memory import MemoryMonitor, monitor_function


class MemoryAwareSimulationRunner:
    """
    Simulation runner with memory-aware results handling.
    
    This wraps the V2 simulation runner and automatically selects
    appropriate storage based on simulation size.
    """
    
    def __init__(self, protocol_spec: ProtocolSpecification):
        """
        Initialize with protocol specification.
        
        Args:
            protocol_spec: Protocol specification to use
        """
        self.v2_runner = V2SimulationRunner(protocol_spec)
        self.protocol_spec = protocol_spec
        self.memory_monitor = MemoryMonitor()
        
    @monitor_function
    def run(
        self,
        engine_type: str,
        n_patients: int,
        duration_years: float,
        seed: int,
        force_parquet: bool = False,
        show_progress: bool = True
    ) -> SimulationResults:
        """
        Run simulation with memory-aware results handling.
        
        Args:
            engine_type: 'abs' or 'des'
            n_patients: Number of patients to simulate
            duration_years: Duration in years
            seed: Random seed
            force_parquet: Force Parquet storage even for small simulations
            show_progress: Show progress indicators
            
        Returns:
            Memory-aware SimulationResults instance
        """
        # Check memory before starting
        suggestion = self.memory_monitor.suggest_memory_optimization(
            n_patients, duration_years
        )
        if suggestion and show_progress:
            print(suggestion)
            
        # Run V2 simulation
        if show_progress:
            print(f"🚀 Starting {engine_type.upper()} simulation: "
                  f"{n_patients} patients × {duration_years} years")
            
        import time
        start_time = time.time()
        
        raw_results = self.v2_runner.run(
            engine_type=engine_type,
            n_patients=n_patients,
            duration_years=duration_years,
            seed=seed
        )
        
        runtime_seconds = time.time() - start_time
        
        if show_progress:
            print(f"✅ Simulation completed in {runtime_seconds:.1f} seconds")
            
        # Create memory-aware results
        results = ResultsFactory.create_results(
            raw_results=raw_results,
            protocol_name=self.protocol_spec.name,
            protocol_version=self.protocol_spec.version,
            engine_type=engine_type,
            n_patients=n_patients,
            duration_years=duration_years,
            seed=seed,
            runtime_seconds=runtime_seconds,
            force_parquet=force_parquet
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
        
        # Cleanup memory after simulation
        self.memory_monitor.cleanup_memory()
        
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
    Upgrade existing session state results to memory-aware format.
    
    This is used for backward compatibility with results already
    in Streamlit session state.
    
    Args:
        existing_results: Dictionary with 'results' and other fields
        protocol_info: Protocol information dictionary
        
    Returns:
        Memory-aware SimulationResults instance
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
        runtime_seconds=existing_results.get('runtime', 0.0),
        force_parquet=False  # Keep in memory for existing results
    )