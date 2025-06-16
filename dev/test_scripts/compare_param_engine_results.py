#!/usr/bin/env python3
"""
Compare results from parameter-driven engine with standard engine.
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from simulation_v2.protocols.time_based_protocol_spec import TimeBasedProtocolSpecification
from simulation_v2.core.time_based_simulation_runner import TimeBasedSimulationRunner
from simulation_v2.protocols.protocol_spec import ProtocolSpecification
from simulation_v2.core.simulation_runner import SimulationRunner

def run_time_based_simulation(n_patients, duration_years, seed):
    """Run time-based simulation with parameter-driven engine."""
    protocol_path = Path("protocols/v2_time_based/eylea_time_based.yaml")
    protocol_spec = TimeBasedProtocolSpecification.from_yaml(protocol_path)
    
    runner = TimeBasedSimulationRunner(protocol_spec)
    results = runner.run(
        engine_type='abs',
        n_patients=n_patients,
        duration_years=duration_years,
        seed=seed
    )
    
    return results, runner.audit_log

def run_standard_simulation(n_patients, duration_years, seed):
    """Run standard simulation for comparison."""
    # Skip standard comparison for now - focus on time-based results
    return None, None

def analyze_results(results, model_type):
    """Analyze simulation results."""
    vision_changes = []
    treatment_counts = []
    
    for patient in results.patient_histories.values():
        if patient.visit_history:
            initial_vision = patient.baseline_vision
            final_vision = patient.visit_history[-1]['vision']
            vision_change = final_vision - initial_vision
            vision_changes.append(vision_change)
            treatment_counts.append(patient.injection_count)
    
    avg_vision_change = sum(vision_changes) / len(vision_changes) if vision_changes else 0
    avg_treatments = sum(treatment_counts) / len(treatment_counts) if treatment_counts else 0
    
    print(f"\n{model_type} Model Results:")
    print(f"- Average vision change: {avg_vision_change:.1f} letters")
    print(f"- Average treatments per patient: {avg_treatments:.1f}")
    print(f"- Total injections: {results.total_injections}")
    print(f"- Final vision mean: {results.final_vision_mean:.1f}")
    print(f"- Final vision std: {results.final_vision_std:.1f}")
    print(f"- Discontinuation rate: {results.discontinuation_rate:.2%}")
    
    # Check for vision improvements
    improvements = sum(1 for vc in vision_changes if vc > 0)
    print(f"- Patients with vision improvement: {improvements}/{len(vision_changes)} ({improvements/len(vision_changes)*100:.1f}%)")

def main():
    """Compare simulation results."""
    n_patients = 200
    duration_years = 3
    seed = 42
    
    print(f"Running comparison with {n_patients} patients over {duration_years} years...")
    
    # Run time-based simulation
    print("\n1. Running TIME-BASED simulation with parameter-driven engine...")
    time_based_results, time_based_audit = run_time_based_simulation(n_patients, duration_years, seed)
    analyze_results(time_based_results, "Time-Based")
    
    # Skip standard comparison for now
    print("\n2. Standard simulation comparison skipped (focus on time-based results)")
    
    # Check for parameter usage
    print("\n3. Verifying parameter usage in time-based model...")
    
    # Sample a few patients to check vision mechanics
    print("\nSampling patient vision trajectories from time-based model:")
    sample_count = 0
    for patient_id, patient in time_based_results.patient_histories.items():
        if sample_count < 3 and len(patient.visit_history) > 5:
            print(f"\nPatient {patient_id}:")
            print(f"  Baseline: {patient.baseline_vision}")
            
            # Show vision progression
            for i, visit in enumerate(patient.visit_history):
                if i % 3 == 0 or i == len(patient.visit_history) - 1:  # Show every 3rd visit and last
                    measured = visit['vision']
                    actual = visit.get('actual_vision', measured)
                    improving = visit.get('is_improving', False)
                    print(f"  Visit {i+1}: Measured={measured}, Actual={actual:.1f}, Improving={improving}")
            
            sample_count += 1
    
    print("\nComparison complete! The parameter-driven engine should show:")
    print("- Vision improvements in early treatments")
    print("- Bimodal vision loss (gradual + occasional hemorrhages)")
    print("- Treatment effect decay over time")
    print("- All values driven by parameter files")

if __name__ == "__main__":
    main()