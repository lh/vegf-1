"""
Example of running simulations with the Streamlit simulation runner.

This shows how to run simulations with automatic Parquet storage
and optional memory limit checking.
"""

import sys
from pathlib import Path

# Add imports
sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent.parent.parent))

from simulation_v2.protocols.protocol_spec import ProtocolSpecification
from core.simulation_runner import SimulationRunner
from core.monitoring.memory import MemoryMonitor


def run_simulation_with_memory_check():
    """Run a simulation with optional memory checking."""
    print("\n=== Simulation with Memory Check ===")
    
    # Load protocol
    protocol_path = Path(__file__).parent.parent / "protocols" / "eylea.yaml"
    spec = ProtocolSpecification.from_yaml(protocol_path)
    
    # Check memory before starting
    monitor = MemoryMonitor()
    n_patients = 5000
    duration_years = 3.0
    
    is_feasible, warning = monitor.check_simulation_feasibility(n_patients, duration_years)
    if warning:
        print(f"\nMemory check result:\n{warning}")
        if not is_feasible:
            print("\nSimulation may exceed memory limits!")
            # In a real app, you might stop here or reduce parameters
    
    # Create runner
    runner = SimulationRunner(spec)
    
    # Run simulation (always saves to Parquet)
    results = runner.run(
        engine_type="abs",
        n_patients=n_patients,
        duration_years=duration_years,
        seed=42
    )
    
    # Show results info
    print(f"\nSimulation ID: {results.metadata.sim_id}")
    print(f"Storage: Parquet at {results.data_path}")
    print(f"Memory usage: {results.get_memory_usage_mb():.1f} MB")
    print(f"Patient count: {results.get_patient_count()}")
    print(f"Total injections: {results.get_total_injections()}")
    
    # Access summary statistics
    stats = results.get_summary_statistics()
    print(f"Mean final vision: {stats['mean_final_vision']:.1f}")
    print(f"Mean visits per patient: {stats['mean_visits_per_patient']:.1f}")
    
    return results


def run_large_simulation():
    """Run a large simulation to demonstrate Parquet efficiency."""
    print("\n=== Large Simulation (Parquet Storage) ===")
    
    # Load protocol
    protocol_path = Path(__file__).parent.parent / "protocols" / "eylea.yaml"
    spec = ProtocolSpecification.from_yaml(protocol_path)
    
    # Create runner
    runner = SimulationRunner(spec)
    
    # Run large simulation
    results = runner.run(
        engine_type="des",  # Use DES for variety
        n_patients=10000,
        duration_years=5.0,
        seed=12345
    )
    
    print(f"\nSimulation complete!")
    print(f"Storage: {results.data_path}")
    print(f"Memory usage: {results.get_memory_usage_mb():.1f} MB (should be ~1-2MB)")
    
    # Demonstrate efficient data access
    print("\nAccessing data efficiently:")
    
    # Get first 10 patients
    patient_count = 0
    for batch in results.iterate_patients(batch_size=10):
        print(f"  Batch of {len(batch)} patients")
        for patient in batch:
            patient_count += 1
            if patient_count == 1:
                print(f"    First patient: {patient['patient_id']}, "
                      f"{len(patient['visits'])} visits")
        break  # Just show first batch
    
    # Get discontinuation summary
    if hasattr(results, 'get_discontinuation_summary'):
        disc_summary = results.get_discontinuation_summary()
        print("\nDiscontinuation summary:")
        for disc_type, count in disc_summary.items():
            if count > 0:
                print(f"  {disc_type}: {count}")
    
    return results


def demonstrate_memory_monitoring():
    """Show how memory monitoring works independently."""
    print("\n=== Memory Monitoring Demo ===")
    
    monitor = MemoryMonitor()
    info = monitor.get_memory_info()
    
    print(f"Current memory usage: {info['used_mb']:.1f} MB")
    print(f"Available memory: {info['available_mb']:.1f} MB")
    print(f"System memory: {info['percent']:.1f}% used")
    
    status, message = monitor.check_memory_status()
    print(f"\nStatus: {status}")
    print(f"Message: {message}")


if __name__ == "__main__":
    # Show memory monitoring
    demonstrate_memory_monitoring()
    
    # Run simulation with memory check
    small_results = run_simulation_with_memory_check()
    
    # Run large simulation
    large_results = run_large_simulation()
    
    print("\n✅ All examples completed successfully!")