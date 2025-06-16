"""
Run a standard (visit-based) simulation for comparison with time-based model.
"""

import sys
from pathlib import Path
from datetime import datetime

sys.path.append(str(Path(__file__).parent))

from simulation_v2.protocols.protocol_spec import ProtocolSpecification
from simulation_v2.core.simulation_runner import SimulationRunner
from ape.utils.simulation_package import create_simulation_package


def run_standard_simulation():
    """Run standard simulation with similar parameters for comparison."""
    
    print("🚀 Running standard (visit-based) simulation for comparison...")
    
    # Load a standard protocol
    protocol_path = Path("protocols/v2/eylea_treat_and_extend_v1.0.yaml")
    spec = ProtocolSpecification.from_yaml(protocol_path)
    
    print(f"Protocol: {spec.name} v{spec.version}")
    
    # Create runner
    runner = SimulationRunner(spec)
    
    # Same parameters as time-based
    n_patients = 200
    duration_years = 2.0
    seed = 42
    
    print(f"\nRunning simulation:")
    print(f"- Patients: {n_patients}")
    print(f"- Duration: {duration_years} years")
    print(f"- Seed: {seed}")
    
    results = runner.run(
        engine_type='abs',
        n_patients=n_patients,
        duration_years=duration_years,
        seed=seed
    )
    
    print(f"\n✅ Simulation complete!")
    print(f"- Total injections: {results.total_injections}")
    print(f"- Mean final vision: {results.final_vision_mean:.1f}")
    print(f"- Discontinuation rate: {results.discontinuation_rate:.2%}")
    
    # Save results in standard format
    print("\n📦 Saving simulation results...")
    
    timestamp = datetime.now()
    sim_name = f"{timestamp.strftime('%Y%m%d-%H%M%S')}-sim-{n_patients}p-{int(duration_years)}y-standard"
    
    # Save to standard simulation_results directory
    output_dir = Path("simulation_results") / sim_name
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save metadata
    metadata = {
        'name': sim_name,
        'timestamp': timestamp.isoformat(),
        'engine_type': 'ABS',
        'n_patients': n_patients,
        'duration_years': duration_years,
        'protocol': spec.name,
        'model_type': 'standard',
        'total_injections': results.total_injections,
        'mean_final_vision': results.final_vision_mean,
        'discontinuation_rate': results.discontinuation_rate
    }
    
    with open(output_dir / "metadata.json", 'w') as f:
        import json
        json.dump(metadata, f, indent=2)
    
    # Save audit log
    with open(output_dir / "audit_log.json", 'w') as f:
        json.dump(runner.audit_log, f, indent=2)
    
    # Save protocol spec copy
    import shutil
    shutil.copy(protocol_path, output_dir / "protocol.yaml")
    
    package_path = str(output_dir)
    
    print(f"\n💾 Saved to: {package_path}")
    
    return package_path


if __name__ == "__main__":
    run_standard_simulation()
    print("\n🎯 Now you can compare:")
    print("   - Time-based model: 20250616-124007-sim-200p-2y-time_based")
    print("   - Standard model: (check latest sim_* folder)")
    print("\n📊 Run: streamlit run Home.py")