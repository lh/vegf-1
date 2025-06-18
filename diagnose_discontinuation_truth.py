#!/usr/bin/env python3
"""
Diagnose the TRUE discontinuation rate for a simulation.
Find ground truth by examining raw patient data.
"""

import pandas as pd
from pathlib import Path
from ape.core.results.factory import ResultsFactory
import json

def find_discontinuation_truth(sim_path):
    """Find the ground truth about discontinuations in a simulation."""
    print(f"\n{'='*80}")
    print(f"DISCONTINUATION TRUTH ANALYSIS: {sim_path.name}")
    print(f"{'='*80}\n")
    
    # Load results
    results = ResultsFactory.load_results(sim_path)
    
    # Method 1: Check discontinuation summary if available
    print("1. CHECKING DISCONTINUATION SUMMARY")
    print("-" * 40)
    if hasattr(results, 'discontinuation_summary'):
        disc_summary = results.discontinuation_summary
        print(f"Discontinuation summary: {disc_summary}")
    else:
        # Try to load from JSON
        summary_file = sim_path / "summary_stats.json"
        if summary_file.exists():
            with open(summary_file) as f:
                summary = json.load(f)
                if 'discontinuation_summary' in summary:
                    disc_summary = summary['discontinuation_summary']
                    print(f"Total discontinued: {disc_summary.get('total_discontinued', 'N/A')}")
                    print(f"By reason: {disc_summary.get('by_reason', {})}")
    
    # Method 2: Count from patient histories
    print("\n2. ANALYZING PATIENT HISTORIES")
    print("-" * 40)
    
    # Get patient data
    if hasattr(results, 'iterate_patients'):
        # ParquetResults
        total_patients = 0
        discontinued_patients = 0
        active_patients = 0
        final_states = {}
        
        for batch in results.iterate_patients(batch_size=500):
            for patient in batch:
                total_patients += 1
                
                # Check if patient is discontinued
                if patient.get('discontinued', False):
                    discontinued_patients += 1
                    
                # Get final visit state
                visits = patient.get('visits', [])
                if visits:
                    last_visit = visits[-1]
                    final_state = last_visit.get('treatment_state', 'Unknown')
                    
                    # Check if this is a discontinuation visit
                    if last_visit.get('is_discontinuation_visit', False):
                        final_state = f"Discontinued ({last_visit.get('reason', 'unknown reason')})"
                    
                    final_states[final_state] = final_states.get(final_state, 0) + 1
                    
                    # Count as active if last visit was recent (not discontinued)
                    if not patient.get('discontinued', False):
                        active_patients += 1
    else:
        # In-memory results
        patient_histories = results.patient_histories if hasattr(results, 'patient_histories') else {}
        total_patients = len(patient_histories)
        discontinued_patients = 0
        active_patients = 0
        final_states = {}
        
        for patient_id, history in patient_histories.items():
            # Check discontinued flag
            if history.get('discontinued', False):
                discontinued_patients += 1
                
            # Check final visit
            visits = history.get('visits', [])
            if visits:
                last_visit = visits[-1]
                final_state = last_visit.get('treatment_state', 'Unknown')
                
                if last_visit.get('is_discontinuation_visit', False):
                    final_state = f"Discontinued ({last_visit.get('reason', 'unknown reason')})"
                    
                final_states[final_state] = final_states.get(final_state, 0) + 1
                
                if not history.get('discontinued', False):
                    active_patients += 1
    
    print(f"Total patients: {total_patients}")
    print(f"Discontinued (by flag): {discontinued_patients} ({discontinued_patients/total_patients*100:.1f}%)")
    print(f"Active (not discontinued): {active_patients} ({active_patients/total_patients*100:.1f}%)")
    
    print("\n3. FINAL STATES DISTRIBUTION")
    print("-" * 40)
    for state, count in sorted(final_states.items(), key=lambda x: x[1], reverse=True):
        pct = count / total_patients * 100
        print(f"{state:40s}: {count:4d} patients ({pct:5.1f}%)")
    
    # Method 3: Check what the pattern analyzer sees
    print("\n4. PATTERN ANALYZER TERMINAL STATES")
    print("-" * 40)
    try:
        from ape.components.treatment_patterns.pattern_analyzer_enhanced import extract_treatment_patterns_with_terminals
        transitions_df, visits_df = extract_treatment_patterns_with_terminals(results)
        
        # Count terminal transitions
        terminal_transitions = transitions_df[
            (transitions_df['to_state'].str.contains('Still in')) | 
            (transitions_df['to_state'].str.contains('No Further Visits'))
        ]
        
        print("Terminal state transitions:")
        for state in sorted(terminal_transitions['to_state'].unique()):
            count = len(terminal_transitions[terminal_transitions['to_state'] == state])
            pct = count / total_patients * 100
            print(f"{state:40s}: {count:4d} transitions ({pct:5.1f}%)")
            
        # Check for "No Further Visits" specifically
        no_further = len(terminal_transitions[terminal_transitions['to_state'] == 'No Further Visits'])
        print(f"\nSpecific 'No Further Visits' count: {no_further} ({no_further/total_patients*100:.1f}%)")
        
    except Exception as e:
        print(f"Error analyzing patterns: {e}")
    
    print("\n" + "="*80)
    
    return {
        'total_patients': total_patients,
        'discontinued': discontinued_patients,
        'active': active_patients,
        'final_states': final_states
    }


if __name__ == "__main__":
    # Analyze the super-pine simulation
    results_dir = Path("simulation_results")
    
    # Find super-pine simulation
    super_pine = None
    for sim_dir in results_dir.iterdir():
        if sim_dir.is_dir() and 'super-pine' in sim_dir.name:
            super_pine = sim_dir
            break
    
    if super_pine:
        truth = find_discontinuation_truth(super_pine)
    else:
        print("Could not find super-pine simulation!")
        print("Available simulations:")
        for sim_dir in sorted(results_dir.iterdir()):
            if sim_dir.is_dir() and not sim_dir.name.startswith('.'):
                print(f"  - {sim_dir.name}")