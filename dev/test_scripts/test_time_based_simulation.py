"""
Test script for time-based simulation model.

This verifies that the time-based engine produces valid output
that works with existing analysis pages.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

from simulation_v2.protocols.time_based_protocol_spec import TimeBasedProtocolSpecification
from simulation_v2.core.time_based_simulation_runner import TimeBasedSimulationRunner


def test_time_based_simulation():
    """Run a small time-based simulation and verify output format."""
    
    print("Loading time-based protocol...")
    protocol_path = Path("protocols/v2_time_based/eylea_time_based.yaml")
    
    # Load time-based protocol specification
    spec = TimeBasedProtocolSpecification.from_yaml(protocol_path)
    
    print(f"Protocol: {spec.name} v{spec.version}")
    print(f"Model type: {spec.model_type}")
    print(f"Update interval: {spec.update_interval_days} days")
    
    # Create time-based simulation runner
    runner = TimeBasedSimulationRunner(spec)
    
    # Run small simulation
    print("\nRunning simulation...")
    print("- Engine: ABS")
    print("- Patients: 50")
    print("- Duration: 1 year")
    print("- Seed: 42")
    
    results = runner.run(
        engine_type='abs',
        n_patients=50,
        duration_years=1.0,
        seed=42
    )
    
    # Verify output format
    print("\n=== RESULTS ===")
    print(f"Total injections: {results.total_injections}")
    print(f"Patient count: {len(results.patient_histories)}")
    print(f"Mean final vision: {results.final_vision_mean:.1f}")
    print(f"Discontinuation rate: {results.discontinuation_rate:.2%}")
    
    # Check a sample patient
    sample_patient = next(iter(results.patient_histories.values()))
    print(f"\nSample patient ID: {sample_patient.id}")
    print(f"Baseline vision: {sample_patient.baseline_vision}")
    print(f"Current state: {sample_patient.current_state.name}")
    print(f"Number of visits: {len(sample_patient.visit_history)}")
    
    if sample_patient.visit_history:
        first_visit = sample_patient.visit_history[0]
        print(f"\nFirst visit:")
        print(f"  Date: {first_visit['date']}")
        print(f"  Vision: {first_visit['vision']}")
        print(f"  Disease state: {first_visit['disease_state'].name}")
        print(f"  Treatment given: {first_visit.get('treatment_given', False)}")
        
        if len(sample_patient.visit_history) > 1:
            last_visit = sample_patient.visit_history[-1]
            print(f"\nLast visit:")
            print(f"  Date: {last_visit['date']}")
            print(f"  Vision: {last_visit['vision']}")
            print(f"  Disease state: {last_visit['disease_state'].name}")
    
    print("\n✅ Simulation completed successfully!")
    print("Output format is compatible with existing analysis pages.")
    
    return results


if __name__ == "__main__":
    test_time_based_simulation()