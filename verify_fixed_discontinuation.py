#!/usr/bin/env python3
"""
Verify that the discontinuation fix is working correctly.
Tests both streamgraph and Sankey to ensure they show consistent data.
"""
import pandas as pd
from pathlib import Path
from ape.core.results.factory import ResultsFactory
from ape.components.treatment_patterns.pattern_analyzer_enhanced import extract_treatment_patterns_with_terminals
from ape.components.treatment_patterns.time_series_generator import generate_patient_state_time_series
from ape.components.treatment_patterns.discontinued_utils import get_discontinued_patients, add_discontinued_info_to_visits
import sys

def verify_discontinuation_consistency(sim_path):
    """Verify discontinuation counts are consistent across visualizations."""
    print(f"\n{'='*80}")
    print(f"VERIFYING DISCONTINUATION CONSISTENCY: {sim_path.name}")
    print(f"{'='*80}\n")
    
    # Load results
    results = ResultsFactory.load_results(sim_path)
    
    # Get ground truth
    discontinued_info = get_discontinued_patients(results)
    true_discontinued_count = sum(1 for info in discontinued_info.values() if info['discontinued'])
    total_patients = results.metadata.n_patients
    
    print(f"GROUND TRUTH:")
    print(f"- Total patients: {total_patients}")
    print(f"- Discontinued patients: {true_discontinued_count} ({true_discontinued_count/total_patients*100:.1f}%)")
    print(f"- Active patients: {total_patients - true_discontinued_count} ({(total_patients - true_discontinued_count)/total_patients*100:.1f}%)")
    
    # Test 1: Time Series Generator (Streamgraph data)
    print(f"\n{'='*40}")
    print("TEST 1: TIME SERIES GENERATOR (Streamgraph)")
    print(f"{'='*40}")
    
    # Extract visits
    visits_df = results.get_visits_df()
    
    # Convert time_days to time_months for compatibility
    visits_df['time_months'] = visits_df['time_days'] / 30.44
    
    # Add treatment state from disease_state
    visits_df['treatment_state'] = visits_df['disease_state']
    
    # Add visit number for each patient
    visits_df = visits_df.sort_values(['patient_id', 'time_days'])
    visits_df['visit_num'] = visits_df.groupby('patient_id').cumcount()
    
    visits_df = add_discontinued_info_to_visits(visits_df, results)
    
    # Generate time series at final time point
    time_series = generate_patient_state_time_series(
        visits_df,
        time_resolution='month',
        results=results
    )
    
    # Get final time point data
    final_time = time_series['time_point'].max()
    final_states = time_series[time_series['time_point'] == final_time].copy()
    
    print(f"\nFinal states at month {final_time}:")
    for _, row in final_states.iterrows():
        if row['patient_count'] > 0:
            print(f"- {row['state']}: {row['patient_count']} patients ({row['percentage']:.1f}%)")
    
    # Check discontinued count
    discontinued_in_ts = final_states[final_states['state'] == 'Discontinued']['patient_count'].sum()
    print(f"\nDiscontinued in time series: {discontinued_in_ts}")
    print(f"Matches ground truth: {'✓' if discontinued_in_ts == true_discontinued_count else '✗'}")
    
    # Test 2: Pattern Analyzer (Sankey data)
    print(f"\n{'='*40}")
    print("TEST 2: PATTERN ANALYZER (Sankey)")
    print(f"{'='*40}")
    
    # Extract patterns with terminals
    transitions_df, visits_df_patterns = extract_treatment_patterns_with_terminals(
        results
    )
    
    # Count terminal states
    terminal_states = transitions_df[transitions_df['to_state'].str.contains('Still in|Discontinued')]
    terminal_counts = terminal_states.groupby('to_state')['patient_id'].nunique()
    
    print(f"\nTerminal states (unique patients):")
    for state, count in terminal_counts.items():
        percentage = count / total_patients * 100
        print(f"- {state}: {count} patients ({percentage:.1f}%)")
    
    # Check discontinued count
    discontinued_in_sankey = terminal_counts.get('Discontinued', 0)
    print(f"\nDiscontinued in Sankey: {discontinued_in_sankey}")
    print(f"Matches ground truth: {'✓' if discontinued_in_sankey == true_discontinued_count else '✗'}")
    
    # Summary
    print(f"\n{'='*40}")
    print("SUMMARY")
    print(f"{'='*40}")
    
    all_match = (discontinued_in_ts == true_discontinued_count == discontinued_in_sankey)
    
    if all_match:
        print("\n✓ SUCCESS: All visualizations show consistent discontinuation counts!")
    else:
        print("\n✗ FAILURE: Discontinuation counts do not match!")
        print(f"  - Ground truth: {true_discontinued_count}")
        print(f"  - Streamgraph: {discontinued_in_ts}")
        print(f"  - Sankey: {discontinued_in_sankey}")
    
    return all_match

if __name__ == "__main__":
    results_dir = Path("simulation_results")
    
    # Find super-pine simulation
    super_pine = None
    for sim in results_dir.glob("*super-pine*"):
        if sim.is_dir() and (sim / "metadata.json").exists():
            super_pine = sim
            break
    
    if super_pine:
        success = verify_discontinuation_consistency(super_pine)
        sys.exit(0 if success else 1)
    else:
        print("ERROR: Could not find super-pine simulation")
        sys.exit(1)