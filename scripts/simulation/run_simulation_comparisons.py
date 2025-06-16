"""
Run multiple simulations for comparison.

Creates both time-based and standard simulations with different parameters.
"""

import sys
from pathlib import Path
from datetime import datetime
import time

sys.path.append(str(Path(__file__).parent))

from simulation_v2.protocols.protocol_spec import ProtocolSpecification
from simulation_v2.protocols.time_based_protocol_spec import TimeBasedProtocolSpecification
from simulation_v2.core.simulation_runner import SimulationRunner
from simulation_v2.core.time_based_simulation_runner import TimeBasedSimulationRunner
from ape.core.results.factory import ResultsFactory


def run_time_based_simulation(n_patients: int, duration_years: float, seed: int):
    """Run time-based simulation with loading dose."""
    print(f"\n{'='*60}")
    print(f"🚀 Running TIME-BASED simulation")
    print(f"   Patients: {n_patients}, Duration: {duration_years}y, Seed: {seed}")
    print(f"{'='*60}")
    
    # Load time-based protocol
    protocol_path = Path("protocols/v2_time_based/eylea_time_based.yaml")
    spec = TimeBasedProtocolSpecification.from_yaml(protocol_path)
    
    # Create runner
    runner = TimeBasedSimulationRunner(spec)
    
    # Run simulation
    start_time = time.time()
    results = runner.run(
        engine_type='abs',
        n_patients=n_patients,
        duration_years=duration_years,
        seed=seed
    )
    runtime = time.time() - start_time
    
    print(f"\n✅ Completed in {runtime:.1f} seconds")
    print(f"   Total injections: {results.total_injections}")
    print(f"   Mean final vision: {results.final_vision_mean:.1f}")
    print(f"   Discontinuation rate: {results.discontinuation_rate:.2%}")
    
    # Save with ResultsFactory for proper format
    factory = ResultsFactory()
    saved_results = factory.create_results(
        raw_results=results,
        protocol_name=f"{spec.name} (Time-Based)",
        protocol_version=spec.version,
        engine_type='abs',
        n_patients=n_patients,
        duration_years=duration_years,
        seed=seed,
        runtime_seconds=runtime
    )
    
    print(f"   Saved as: {saved_results.metadata.sim_id}")
    return saved_results.metadata.sim_id


def run_standard_simulation(n_patients: int, duration_years: float, seed: int):
    """Run standard visit-based simulation."""
    print(f"\n{'='*60}")
    print(f"🚀 Running STANDARD simulation")
    print(f"   Patients: {n_patients}, Duration: {duration_years}y, Seed: {seed}")
    print(f"{'='*60}")
    
    # Load standard protocol
    protocol_path = Path("protocols/v2/eylea_treat_and_extend_v1.0.yaml")
    spec = ProtocolSpecification.from_yaml(protocol_path)
    
    # Create runner
    runner = SimulationRunner(spec)
    
    # Run simulation
    start_time = time.time()
    results = runner.run(
        engine_type='abs',
        n_patients=n_patients,
        duration_years=duration_years,
        seed=seed
    )
    runtime = time.time() - start_time
    
    print(f"\n✅ Completed in {runtime:.1f} seconds")
    print(f"   Total injections: {results.total_injections}")
    print(f"   Mean final vision: {results.final_vision_mean:.1f}")
    print(f"   Discontinuation rate: {results.discontinuation_rate:.2%}")
    
    # Save with ResultsFactory
    factory = ResultsFactory()
    saved_results = factory.create_results(
        raw_results=results,
        protocol_name=f"{spec.name} (Standard)",
        protocol_version=spec.version,
        engine_type='abs',
        n_patients=n_patients,
        duration_years=duration_years,
        seed=seed,
        runtime_seconds=runtime
    )
    
    print(f"   Saved as: {saved_results.metadata.sim_id}")
    return saved_results.metadata.sim_id


def main():
    """Run multiple simulation scenarios."""
    print("🔬 SIMULATION COMPARISON SUITE")
    print("=" * 60)
    
    scenarios = [
        # Small, short duration (good for quick testing)
        {"n_patients": 100, "duration_years": 1, "seed": 123},
        
        # Medium size, standard duration
        {"n_patients": 500, "duration_years": 2, "seed": 456},
        
        # Large, long duration (closer to clinical trials)
        {"n_patients": 1000, "duration_years": 3, "seed": 789},
    ]
    
    results_summary = []
    
    for scenario in scenarios:
        print(f"\n\n{'#'*60}")
        print(f"# SCENARIO: {scenario['n_patients']} patients, {scenario['duration_years']} years")
        print(f"{'#'*60}")
        
        # Run time-based
        time_based_id = run_time_based_simulation(**scenario)
        
        # Run standard
        standard_id = run_standard_simulation(**scenario)
        
        results_summary.append({
            "scenario": scenario,
            "time_based": time_based_id,
            "standard": standard_id
        })
    
    # Print summary
    print(f"\n\n{'='*60}")
    print("📊 SIMULATION SUMMARY")
    print(f"{'='*60}")
    
    for i, result in enumerate(results_summary):
        scenario = result['scenario']
        print(f"\nScenario {i+1}: {scenario['n_patients']}p / {scenario['duration_years']}y")
        print(f"  Time-based: {result['time_based']}")
        print(f"  Standard:   {result['standard']}")
    
    print(f"\n\n✨ All simulations complete!")
    print(f"📊 Run 'streamlit run Home.py' to visualize and compare")


if __name__ == "__main__":
    main()