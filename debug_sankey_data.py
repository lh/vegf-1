#!/usr/bin/env python3
"""Debug what data is being passed to Sankey."""
from pathlib import Path
from ape.core.results.factory import ResultsFactory
from ape.components.treatment_patterns.pattern_analyzer_enhanced import extract_treatment_patterns_with_terminals

# Load super-pine simulation
results_dir = Path("simulation_results")
super_pine = next(results_dir.glob("*super-pine*"))
results = ResultsFactory.load_results(super_pine)

# Extract patterns with terminals (what enhanced tab should use)
print("Extracting patterns with terminals...")
transitions_df, visits_df = extract_treatment_patterns_with_terminals(results)

print(f"\nTotal transitions: {len(transitions_df)}")
print(f"Unique 'to_state' values:")
unique_to_states = transitions_df['to_state'].unique()
for state in sorted(unique_to_states):
    count = len(transitions_df[transitions_df['to_state'] == state])
    print(f"  - {state}: {count} transitions")

# Check if we have both "Discontinued" and "No Further Visits"
has_discontinued = 'Discontinued' in unique_to_states
has_no_further = 'No Further Visits' in unique_to_states

print(f"\nHas 'Discontinued': {has_discontinued}")
print(f"Has 'No Further Visits': {has_no_further}")

if has_discontinued and has_no_further:
    print("\nERROR: We have BOTH discontinued states!")
    
# Check what memorable name we have
print(f"\nMemorable name: {results.metadata.memorable_name}")