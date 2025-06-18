#!/usr/bin/env python3
"""Debug why Sankey is showing wrong patient counts."""
from pathlib import Path
from ape.core.results.factory import ResultsFactory
from ape.components.treatment_patterns.pattern_analyzer_enhanced import extract_treatment_patterns_with_terminals
from ape.components.treatment_patterns.sankey_builder_enhanced import create_enhanced_sankey_with_terminals
from ape.components.treatment_patterns.sankey_patient_counts import adjust_terminal_node_counts
import pandas as pd

# Load super-pine simulation
results_dir = Path("simulation_results")
super_pine = None
for sim in results_dir.glob("*super-pine*"):
    if sim.is_dir():
        super_pine = sim
        break

if super_pine:
    print(f"Loading {super_pine.name}")
    results = ResultsFactory.load_results(super_pine)
    
    # Extract patterns
    transitions_df, visits_df = extract_treatment_patterns_with_terminals(results)
    
    print(f"\nTotal transitions: {len(transitions_df)}")
    print(f"Unique patients: {transitions_df['patient_id'].nunique()}")
    
    # Check terminal transitions
    terminal_transitions = transitions_df[transitions_df['to_state'].str.contains('Still in|Discontinued')]
    print(f"\nTerminal transitions:")
    for state, group in terminal_transitions.groupby('to_state'):
        print(f"  {state}: {len(group)} transitions, {group['patient_id'].nunique()} unique patients")
    
    # Test the adjustment function
    print("\n\nTesting adjust_terminal_node_counts:")
    
    # Create flow counts
    flow_counts = transitions_df.groupby(['from_state', 'to_state']).size().reset_index(name='count')
    print(f"\nBefore adjustment:")
    terminal_flows = flow_counts[flow_counts['to_state'].str.contains('Still in|Discontinued')]
    for _, row in terminal_flows.iterrows():
        print(f"  {row['from_state']} -> {row['to_state']}: {row['count']}")
    
    # Apply adjustment
    adjusted_counts = adjust_terminal_node_counts(flow_counts, transitions_df)
    print(f"\nAfter adjustment:")
    terminal_flows = adjusted_counts[adjusted_counts['to_state'].str.contains('Still in|Discontinued')]
    for _, row in terminal_flows.iterrows():
        print(f"  {row['from_state']} -> {row['to_state']}: {row['count']}")
    
    # Check what the Sankey shows
    print("\n\nCreating Sankey diagram...")
    fig = create_enhanced_sankey_with_terminals(transitions_df, results)
    
    # Extract node values from the Sankey
    print("\nSankey node values:")
    sankey_data = fig.data[0]
    for i, label in enumerate(sankey_data.node.label):
        if 'Discontinued' in label or 'Still' in label:
            # Sum all incoming flows to this node
            incoming_value = sum(sankey_data.link.value[j] for j in range(len(sankey_data.link.value)) 
                               if sankey_data.link.target[j] == i)
            print(f"  {label}: {incoming_value}")