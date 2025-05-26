"""
Example of using the memory-aware simulation architecture.

This shows how to run simulations that automatically select
appropriate storage based on size.
"""

import sys
from pathlib import Path

# Add imports
sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent.parent.parent))

from simulation_v2.protocols.protocol_spec import ProtocolSpecification
from core.simulation_adapter import MemoryAwareSimulationRunner
from core.monitoring.memory import MemoryMonitor


def run_small_simulation():
    """Run a small simulation that uses in-memory storage."""
    print("\n=== Small Simulation (In-Memory) ===")
    
    # Load protocol
    protocol_path = Path(__file__).parent.parent / "protocols" / "eylea.yaml"
    spec = ProtocolSpecification.from_yaml(protocol_path)
    
    # Create memory-aware runner
    runner = MemoryAwareSimulationRunner(spec)
    
    # Run small simulation
    results = runner.run(
        engine_type="abs",
        n_patients=100,
        duration_years=2.0,
        seed=42
    )
    
    # Show results info
    print(f"Storage type: {results.metadata.storage_type}")
    print(f"Memory usage: {results.get_memory_usage_mb():.1f} MB")
    print(f"Patient count: {results.get_patient_count()}")
    print(f"Total injections: {results.get_total_injections()}")
    
    # Access data
    stats = results.get_summary_statistics()
    print(f"Mean final vision: {stats['mean_final_vision']:.1f}")
    
    return results


def run_large_simulation():
    """Run a large simulation that uses Parquet storage."""
    print("\n=== Large Simulation (Parquet) ===")
    
    # Load protocol
    protocol_path = Path(__file__).parent.parent / "protocols" / "eylea.yaml"
    spec = ProtocolSpecification.from_yaml(protocol_path)
    
    # Create memory-aware runner
    runner = MemoryAwareSimulationRunner(spec)
    
    # Run large simulation
    results = runner.run(
        engine_type="abs",
        n_patients=5000,
        duration_years=5.0,
        seed=42
    )
    
    # Show results info
    print(f"Storage type: {results.metadata.storage_type}")
    print(f"Memory usage: {results.get_memory_usage_mb():.1f} MB")
    print(f"Patient count: {results.get_patient_count()}")
    print(f"Total injections: {results.get_total_injections()}")
    
    # Access data efficiently
    print("\nProcessing patients in batches...")
    patient_count = 0
    for batch in results.iterate_patients(batch_size=500):
        patient_count += len(batch)
        if patient_count <= 1000:  # Show first few batches
            print(f"  Processed batch: {len(batch)} patients (total: {patient_count})")
    
    return results


def demonstrate_memory_monitoring():
    """Show memory monitoring in action."""
    print("\n=== Memory Monitoring ===")
    
    monitor = MemoryMonitor()
    
    # Check current memory
    info = monitor.get_memory_info()
    print(f"Current memory usage: {info['used_mb']:.1f} MB")
    print(f"Available memory: {info['available_mb']:.1f} MB")
    
    # Check status
    status, message = monitor.check_memory_status()
    print(f"Status: {message}")
    
    # Get optimization suggestions
    suggestion = monitor.suggest_memory_optimization(10000, 5.0)
    if suggestion:
        print("\nOptimization suggestion:")
        print(suggestion)


def main():
    """Run examples."""
    print("Memory-Aware Simulation Examples")
    print("=" * 50)
    
    # Show memory monitoring
    demonstrate_memory_monitoring()
    
    # Run small simulation
    small_results = run_small_simulation()
    
    # Run large simulation
    large_results = run_large_simulation()
    
    # Clean up
    print("\n=== Cleanup ===")
    monitor = MemoryMonitor()
    before = monitor.get_memory_info()['used_mb']
    monitor.cleanup_memory()
    after = monitor.get_memory_info()['used_mb']
    print(f"Memory freed: {before - after:.1f} MB")


if __name__ == "__main__":
    main()