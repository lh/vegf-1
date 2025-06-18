#!/usr/bin/env python3
"""
Verify patient conservation in terminal states.
Tests that the number of unique patients is conserved throughout the simulation.
"""

import pandas as pd
from pathlib import Path
from ape.core.results.factory import ResultsFactory
from ape.components.treatment_patterns.pattern_analyzer_enhanced import extract_treatment_patterns_with_terminals

def verify_patient_conservation(results_path):
    """Verify that patient counts are conserved in the simulation results."""
    print(f"\nVerifying patient conservation for: {results_path.name}")
    print("=" * 60)
    
    # Load results
    results = ResultsFactory.load_results(results_path)
    # Handle different result types
    if hasattr(results, 'patient_histories'):
        patient_histories = results.patient_histories
    else:
        patient_histories = results.get('patient_histories', {})
    
    # Total number of patients
    total_patients = len(patient_histories)
    print(f"Total patients in simulation: {total_patients}")
    
    # Extract transitions with terminal states
    transitions_df, visits_df = extract_treatment_patterns_with_terminals(results)
    
    # Count unique patients in initial state
    initial_patients = transitions_df[transitions_df['from_state'] == 'Pre-Treatment']['patient_id'].nunique()
    print(f"Patients starting treatment: {initial_patients}")
    
    # Count unique patients in terminal states
    terminal_states = transitions_df[
        (transitions_df['to_state'].str.contains('Still in')) | 
        (transitions_df['to_state'].str.contains('No Further Visits'))
    ]
    
    print("\nTerminal state patient counts:")
    terminal_counts = {}
    for state in sorted(terminal_states['to_state'].unique()):
        count = terminal_states[terminal_states['to_state'] == state]['patient_id'].nunique()
        terminal_counts[state] = count
        print(f"  {state}: {count} patients")
    
    total_terminal = sum(terminal_counts.values())
    print(f"\nTotal patients in terminal states: {total_terminal}")
    
    # Verify conservation
    print("\nConservation check:")
    print(f"  Total patients: {total_patients}")
    print(f"  Terminal state total: {total_terminal}")
    print(f"  Difference: {total_patients - total_terminal}")
    
    if total_patients == total_terminal:
        print("✓ PASS: Patient conservation verified!")
    else:
        print("✗ FAIL: Patient counts do not match!")
        
        # Debug: Find patients not in terminal states
        terminal_patient_ids = set(terminal_states['patient_id'].unique())
        all_patient_ids = set(patient_histories.keys())
        missing_patients = all_patient_ids - terminal_patient_ids
        
        if missing_patients:
            print(f"\nMissing {len(missing_patients)} patients from terminal states")
            # Show a few examples
            for pid in list(missing_patients)[:5]:
                last_visit = patient_histories[pid]['visits'][-1]
                print(f"  Patient {pid}: Last visit at month {last_visit['month']:.1f}, state: {last_visit.get('treatment_state', 'Unknown')}")
    
    return total_patients == total_terminal

# Test on recent simulations
if __name__ == "__main__":
    results_dir = Path("simulation_results")
    
    # Get recent simulations
    recent_sims = sorted(
        [d for d in results_dir.iterdir() if d.is_dir() and not d.name.startswith('.')],
        key=lambda x: x.stat().st_mtime,
        reverse=True
    )[:3]  # Test last 3 simulations
    
    if not recent_sims:
        print("No simulations found to test")
    else:
        all_passed = True
        for sim_path in recent_sims:
            passed = verify_patient_conservation(sim_path)
            all_passed = all_passed and passed
        
        print("\n" + "=" * 60)
        if all_passed:
            print("✓ All simulations passed conservation check!")
        else:
            print("✗ Some simulations failed conservation check!")