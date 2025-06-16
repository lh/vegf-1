"""
Run a time-based simulation and save results for visualization.

This creates simulation output that can be viewed in the existing
Analysis pages (Calendar-Time Analysis, Patient Explorer, etc.)
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

from simulation_v2.protocols.time_based_protocol_spec import TimeBasedProtocolSpecification
from simulation_v2.core.time_based_simulation_runner import TimeBasedSimulationRunner
from ape.utils.simulation_package import create_simulation_package


def run_and_save_time_based_simulation():
    """Run time-based simulation and save for visualization."""
    
    print("🚀 Starting time-based simulation...")
    
    # Load time-based protocol
    protocol_path = Path("protocols/v2_time_based/eylea_time_based.yaml")
    spec = TimeBasedProtocolSpecification.from_yaml(protocol_path)
    
    print(f"Protocol: {spec.name} v{spec.version}")
    print(f"Model type: {spec.model_type}")
    
    # Create runner
    runner = TimeBasedSimulationRunner(spec)
    
    # Run larger simulation for better visualization
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
    
    # Print summary
    print(f"\n✅ Simulation complete!")
    print(f"- Total injections: {results.total_injections}")
    print(f"- Mean final vision: {results.final_vision_mean:.1f}")
    print(f"- Discontinuation rate: {results.discontinuation_rate:.2%}")
    
    # Create simulation package for visualization
    print("\n📦 Creating simulation package...")
    
    # Create simulation info
    sim_info = {
        'timestamp': datetime.now().isoformat(),
        'engine_type': 'ABS',
        'n_patients': n_patients,
        'duration_years': duration_years,
        'seed': seed,
        'protocol_name': spec.name,
        'protocol_version': spec.version,
        'model_type': spec.model_type,
        'update_interval_days': spec.update_interval_days,
        'total_injections': results.total_injections,
        'mean_final_vision': results.final_vision_mean,
        'discontinuation_rate': results.discontinuation_rate
    }
    
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
            'model_type': spec.model_type,
            'source_file': spec.source_file
        },
        'audit_log': runner.audit_log
    }
    
    # Save to standard location
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    sim_name = f"{timestamp}-sim-{n_patients}p-{int(duration_years)}y-time_based"
    
    output_dir = Path("simulation_results") / sim_name
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save simulation data
    with open(output_dir / "simulation_data.json", 'w') as f:
        json.dump(package_data, f, indent=2)
    
    # Save audit log
    with open(output_dir / "audit_log.json", 'w') as f:
        json.dump(runner.audit_log, f, indent=2)
    
    # Save metadata
    metadata = {
        'name': sim_name,
        'timestamp': sim_info['timestamp'],
        'engine_type': 'ABS',
        'n_patients': n_patients,
        'duration_years': duration_years,
        'protocol': spec.name,
        'model_type': spec.model_type,
        'total_injections': results.total_injections,
        'mean_final_vision': results.final_vision_mean
    }
    
    with open(output_dir / "metadata.json", 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"\n💾 Saved to: {output_dir}")
    print("\n🎉 You can now view this simulation in:")
    print("   - Calendar-Time Analysis page")
    print("   - Patient Explorer page")
    print("   - Other analysis pages")
    
    return str(output_dir)


if __name__ == "__main__":
    output_path = run_and_save_time_based_simulation()
    print(f"\n📊 To visualize: streamlit run Home.py")
    print(f"   Then navigate to an Analysis page and select: {Path(output_path).name}")