#!/usr/bin/env python3
"""
Test the new parameter-driven time-based engine.
"""

import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from simulation_v2.protocols.time_based_protocol_spec import TimeBasedProtocolSpecification
from simulation_v2.core.time_based_simulation_runner import TimeBasedSimulationRunner

def main():
    """Run a test simulation with the parameter-driven engine."""
    
    # Load time-based protocol
    protocol_path = Path("protocols/v2_time_based/eylea_time_based.yaml")
    protocol_spec = TimeBasedProtocolSpecification.from_yaml(protocol_path)
    
    print(f"Loaded protocol: {protocol_spec.name} v{protocol_spec.version}")
    print(f"Model type: {protocol_spec.model_type}")
    print(f"Vision parameters file: {protocol_spec.vision_parameters_file}")
    
    # Create runner
    runner = TimeBasedSimulationRunner(protocol_spec)
    
    # Run small test simulation
    print("\nRunning test simulation...")
    results = runner.run(
        engine_type='abs',
        n_patients=50,
        duration_years=2,
        seed=42
    )
    
    print(f"\nSimulation complete:")
    print(f"- Total injections: {results.total_injections}")
    print(f"- Final vision mean: {results.final_vision_mean:.1f}")
    print(f"- Final vision std: {results.final_vision_std:.1f}")
    print(f"- Discontinuation rate: {results.discontinuation_rate:.2%}")
    
    # Check for hardcoded values by inspecting a few patients
    print("\nChecking patient vision states...")
    patient_count = 0
    for patient_id, patient in results.patient_histories.items():
        if patient_count < 3:
            print(f"\nPatient {patient_id}:")
            print(f"  Baseline vision: {patient.baseline_vision}")
            if hasattr(patient, 'visit_history') and patient.visit_history:
                print(f"  Number of visits: {len(patient.visit_history)}")
                last_visit = patient.visit_history[-1]
                print(f"  Final measured vision: {last_visit['vision']}")
                if 'actual_vision' in last_visit:
                    print(f"  Final actual vision: {last_visit['actual_vision']:.1f}")
                if 'is_improving' in last_visit:
                    print(f"  Is improving: {last_visit['is_improving']}")
            patient_count += 1
    
    print("\nParameter-driven engine test complete!")

if __name__ == "__main__":
    main()