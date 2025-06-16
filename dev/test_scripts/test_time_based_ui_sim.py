#!/usr/bin/env python3
"""
Test running a time-based simulation through the UI wrapper.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from simulation_v2.protocols.time_based_protocol_spec import TimeBasedProtocolSpecification
from ape.core.simulation_runner import SimulationRunner

def main():
    """Test the UI wrapper with a time-based protocol."""
    
    # Load time-based protocol
    protocol_path = Path("protocols/v2_time_based/eylea_time_based.yaml")
    spec = TimeBasedProtocolSpecification.from_yaml(protocol_path)
    
    print(f"Loaded protocol: {spec.name}")
    print(f"Model type: {spec.model_type}")
    
    # Create UI wrapper
    runner = SimulationRunner(spec)
    print(f"Runner created, time-based: {runner.is_time_based}")
    
    # Run a small simulation
    print("\nRunning time-based simulation through UI wrapper...")
    results = runner.run(
        engine_type='abs',
        n_patients=100,
        duration_years=2,
        seed=42,
        show_progress=True
    )
    
    print(f"\nResults:")
    print(f"- Storage type: {results.metadata.storage_type}")
    print(f"- Total injections: {results.get_total_injections()}")
    mean_vision, std_vision = results.get_final_vision_stats()
    print(f"- Final vision mean: {mean_vision:.1f} (std: {std_vision:.1f})")
    print(f"- Discontinuation rate: {results.get_discontinuation_rate():.2%}")
    print(f"- Memory usage: {results.get_memory_usage_mb():.1f} MB")
    
    print("\nTime-based model integration successful!")

if __name__ == "__main__":
    main()