"""
Run a standard simulation with full data export for comparison.
"""

import sys
from pathlib import Path
from datetime import datetime

sys.path.append(str(Path(__file__).parent))

from simulation_v2.protocols.protocol_spec import ProtocolSpecification
from simulation_v2.core.simulation_runner import SimulationRunner
from ape.core.results.factory import ResultsFactory


def run_standard_simulation():
    """Run standard simulation and save with ResultsFactory."""
    
    print("🚀 Running standard (visit-based) simulation...")
    
    # Load protocol
    protocol_path = Path("protocols/v2/eylea_treat_and_extend_v1.0.yaml")
    spec = ProtocolSpecification.from_yaml(protocol_path)
    
    print(f"Protocol: {spec.name} v{spec.version}")
    
    # Create runner
    runner = SimulationRunner(spec)
    
    # Same parameters as time-based for comparison
    n_patients = 200
    duration_years = 2.0
    seed = 42
    
    print(f"\nRunning simulation:")
    print(f"- Patients: {n_patients}")
    print(f"- Duration: {duration_years} years")
    print(f"- Seed: {seed}")
    
    # Run simulation
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
    
    # Use ResultsFactory to save properly
    print("\n📦 Saving simulation results...")
    
    # Create proper results object
    factory = ResultsFactory()
    saved_results = factory.create_results(
        raw_results=results,
        protocol_name=spec.name,
        protocol_version=spec.version,
        engine_type='abs',
        n_patients=n_patients,
        duration_years=duration_years,
        seed=seed,
        runtime_seconds=0.1  # Placeholder
    )
    
    print(f"\n💾 Saved as: {saved_results.metadata.sim_id}")
    print(f"   Memorable name: {saved_results.metadata.memorable_name}")
    
    return saved_results.metadata.sim_id


if __name__ == "__main__":
    sim_id = run_standard_simulation()
    print(f"\n🎯 Now you can compare:")
    print(f"   - Time-based: sim_20250616_124007_02-00_broken-brook")
    print(f"   - Standard: {sim_id}")
    print(f"\n📊 Run: streamlit run Home.py")