#!/usr/bin/env python3
"""
Create a small test simulation for integration testing.

This creates a real simulation with minimal patients/duration that can be
used for testing the selection and loading functionality.
"""

import sys
from pathlib import Path

# Add parent directories to path

from simulation_v2.protocols.protocol_spec import ProtocolSpecification
from ape.core.simulation_runner import SimulationRunner
import shutil


def create_test_simulation(output_dir: Path = None, n_patients: int = 10, duration_years: float = 0.1):
    """Create a small test simulation and save it.
    
    Args:
        output_dir: Directory to save simulation (optional)
        n_patients: Number of patients (default: 10)
        duration_years: Duration in years (default: 0.1)
    """
    
    # Use the eylea protocol - check v2 directory first, then fallback
    protocol_path = Path(__file__).parent.parent.parent / "protocols" / "v2" / "eylea.yaml"
    if not protocol_path.exists():
        # Try old location as fallback
        protocol_path = Path(__file__).parent.parent.parent / "protocols" / "eylea.yaml"
        if not protocol_path.exists():
            raise FileNotFoundError(f"Protocol not found in either protocols/v2/ or protocols/")
    
    # Load protocol
    spec = ProtocolSpecification.from_yaml(protocol_path)
    
    # Create runner
    runner = SimulationRunner(spec)
    
    # If output_dir is specified, temporarily change the results directory
    original_results_dir = None
    if output_dir:
        from ape.core.results.factory import ResultsFactory
        original_results_dir = ResultsFactory.DEFAULT_RESULTS_DIR
        ResultsFactory.DEFAULT_RESULTS_DIR = Path(output_dir)
    
    try:
        # Run small simulation
        print(f"Creating test simulation: {n_patients} patients × {duration_years} years")
        results = runner.run(
            engine_type="abs",
            n_patients=n_patients,
            duration_years=duration_years,
            seed=12345
        )
        
        print(f"Created simulation: {results.metadata.sim_id}")
        print(f"Saved to: {results.data_path}")
        
        # Return the appropriate value
        if output_dir:
            return str(results.data_path)
        else:
            return results.metadata.sim_id
            
    finally:
        # Restore original results directory
        if original_results_dir:
            ResultsFactory.DEFAULT_RESULTS_DIR = original_results_dir


if __name__ == "__main__":
    # Create in default location
    sim_id = create_test_simulation()
    print(f"\nTest simulation created: {sim_id}")
    print("\nYou can use this simulation ID in tests.")