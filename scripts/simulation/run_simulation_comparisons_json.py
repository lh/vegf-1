"""
Run multiple simulations for comparison using JSON format.
"""

import sys
import json
from pathlib import Path
from datetime import datetime
import time

sys.path.append(str(Path(__file__).parent))

from simulation_v2.protocols.protocol_spec import ProtocolSpecification
from simulation_v2.protocols.time_based_protocol_spec import TimeBasedProtocolSpecification
from simulation_v2.core.simulation_runner import SimulationRunner
from simulation_v2.core.time_based_simulation_runner import TimeBasedSimulationRunner
# Remove unused import


def save_simulation_json(results, spec, n_patients, duration_years, seed, model_type, runtime):
    """Save simulation in JSON format like run_time_based_simulation.py does."""
    
    # Generate simulation name
    timestamp = datetime.now()
    sim_name = f"{timestamp.strftime('%Y%m%d-%H%M%S')}-sim-{n_patients}p-{int(duration_years)}y-{model_type}"
    
    # Create simulation info
    sim_info = {
        'timestamp': timestamp.isoformat(),
        'engine_type': 'ABS',
        'n_patients': n_patients,
        'duration_years': duration_years,
        'seed': seed,
        'protocol_name': spec.name,
        'protocol_version': spec.version,
        'model_type': model_type,
        'total_injections': results.total_injections,
        'mean_final_vision': results.final_vision_mean,
        'discontinuation_rate': results.discontinuation_rate,
        'runtime_seconds': runtime
    }
    
    # Add time-based specific info
    if hasattr(spec, 'update_interval_days'):
        sim_info['update_interval_days'] = spec.update_interval_days
    
    # Convert patient histories to serializable format
    patient_data = {}
    for patient_id, patient in results.patient_histories.items():
        patient_data[patient_id] = {
            'baseline_vision': patient.baseline_vision,
            'current_vision': patient.current_vision,
            'current_state': patient.current_state.name,
            'injection_count': patient.injection_count,
            'is_discontinued': patient.is_discontinued,
            'visit_history': [
                {
                    'date': visit['date'].isoformat(),
                    'disease_state': visit['disease_state'].name,
                    'vision': visit['vision'],
                    'treatment_given': visit.get('treatment_given', False),
                    'actual_vision': visit.get('actual_vision', visit['vision'])
                }
                for visit in patient.visit_history
            ]
        }
    
    # Create package
    package_data = {
        'simulation_info': sim_info,
        'patient_histories': patient_data,
        'protocol_spec': {
            'name': spec.name,
            'version': spec.version,
            'model_type': model_type,
            'source_file': spec.source_file
        }
    }
    
    # Save to standard location
    output_dir = Path("simulation_results") / sim_name
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save simulation data
    with open(output_dir / "simulation_data.json", 'w') as f:
        json.dump(package_data, f, indent=2)
    
    # Save metadata
    metadata = {
        'name': sim_name,
        'timestamp': sim_info['timestamp'],
        'engine_type': 'ABS',
        'n_patients': n_patients,
        'duration_years': duration_years,
        'protocol': spec.name,
        'model_type': model_type,
        'total_injections': results.total_injections,
        'mean_final_vision': results.final_vision_mean
    }
    
    with open(output_dir / "metadata.json", 'w') as f:
        json.dump(metadata, f, indent=2)
    
    return sim_name


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
    
    # Save in JSON format
    sim_name = save_simulation_json(results, spec, n_patients, duration_years, seed, "time_based", runtime)
    
    # Save audit log
    audit_path = Path("simulation_results") / sim_name / "audit_log.json"
    runner.save_audit_trail(audit_path)
    
    print(f"   Saved as: {sim_name}")
    print(f"   (Convert with convert_to_parquet_format.py for visualization)")
    
    return sim_name


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
    
    # Save in JSON format
    sim_name = save_simulation_json(results, spec, n_patients, duration_years, seed, "standard", runtime)
    
    # Save audit log
    audit_path = Path("simulation_results") / sim_name / "audit_log.json"
    runner.save_audit_trail(audit_path)
    
    print(f"   Saved as: {sim_name}")
    
    return sim_name


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
        time_based_name = run_time_based_simulation(**scenario)
        
        # Run standard
        standard_name = run_standard_simulation(**scenario)
        
        results_summary.append({
            "scenario": scenario,
            "time_based": time_based_name,
            "standard": standard_name
        })
    
    # Print summary
    print(f"\n\n{'='*60}")
    print("📊 SIMULATION SUMMARY")
    print(f"{'='*60}")
    
    for i, result in enumerate(results_summary):
        scenario = result['scenario']
        print(f"\nScenario {i+1}: {scenario['n_patients']}p / {scenario['duration_years']}y / seed={scenario['seed']}")
        print(f"  Time-based: {result['time_based']}")
        print(f"  Standard:   {result['standard']}")
    
    print(f"\n\n✨ All simulations complete!")
    print(f"\n📊 To visualize:")
    print(f"1. Convert each with: python convert_to_parquet_format.py")
    print(f"2. Run: streamlit run Home.py")


if __name__ == "__main__":
    main()