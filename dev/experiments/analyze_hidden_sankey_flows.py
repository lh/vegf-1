#!/usr/bin/env python3
"""
Analyze hidden flows in Sankey visualizations.

This script investigates what patient transitions are being filtered out
of the Sankey diagram, particularly focusing on the Maximum Extension node.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys
from collections import defaultdict

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from core.results.factory import ResultsFactory
from components.treatment_patterns import extract_treatment_patterns_vectorized


def analyze_transition_flows(transitions_df, min_flow_threshold=0.001):
    """
    Analyze all transition flows and identify which ones are filtered.
    
    Args:
        transitions_df: DataFrame with columns ['patient_id', 'from_state', 'to_state', ...]
        min_flow_threshold: Minimum proportion of flows to display (default 0.001 = 0.1%)
    """
    print("=" * 80)
    print("TRANSITION FLOW ANALYSIS")
    print("=" * 80)
    
    # Get total number of transitions
    total_transitions = len(transitions_df)
    print(f"\nTotal transitions in dataset: {total_transitions:,}")
    
    # Calculate minimum flow size for filtering
    min_flow_size = max(1, int(total_transitions * min_flow_threshold))
    print(f"Minimum flow size for display (>{min_flow_threshold:.1%}): {min_flow_size:,} transitions")
    
    # Group by transition type and count
    flow_counts = transitions_df.groupby(['from_state', 'to_state']).size().reset_index(name='count')
    flow_counts = flow_counts.sort_values('count', ascending=False)
    
    # Split into visible and hidden flows
    visible_flows = flow_counts[flow_counts['count'] >= min_flow_size]
    hidden_flows = flow_counts[flow_counts['count'] < min_flow_size]
    
    print(f"\nVisible flows: {len(visible_flows)}")
    print(f"Hidden flows: {len(hidden_flows)}")
    print(f"Hidden transitions: {hidden_flows['count'].sum():,} ({hidden_flows['count'].sum() / total_transitions:.1%})")
    
    return flow_counts, visible_flows, hidden_flows


def calculate_visual_gap(transitions_df, node_name):
    """
    Calculate the size of the visual gap in the Sankey diagram.
    
    The gap represents the difference between:
    - Height of the node (total transitions through it)
    - Sum of visible outgoing flows
    """
    # Get incoming and outgoing flows
    incoming = transitions_df[transitions_df['to_state'] == node_name]
    outgoing = transitions_df[transitions_df['from_state'] == node_name]
    
    # The node height should be the maximum of incoming or outgoing
    node_height = max(len(incoming), len(outgoing))
    
    return node_height, len(incoming), len(outgoing)


def analyze_specific_node(transitions_df, node_name, min_flow_threshold=0.001):
    """
    Deep dive into flows for a specific node.
    
    Args:
        transitions_df: DataFrame with transition data
        node_name: Name of the node to analyze (e.g., 'Maximum Extension (16 weeks)')
        min_flow_threshold: Minimum proportion for display
    """
    print(f"\n{'=' * 80}")
    print(f"DETAILED ANALYSIS: {node_name}")
    print(f"{'=' * 80}")
    
    # Get all transitions FROM this node
    from_node = transitions_df[transitions_df['from_state'] == node_name]
    
    if len(from_node) == 0:
        print(f"No transitions found FROM '{node_name}'")
        return
    
    # Get all transitions TO this node
    to_node = transitions_df[transitions_df['to_state'] == node_name]
    
    print(f"\nTransitions INTO {node_name}: {len(to_node):,}")
    print(f"Transitions FROM {node_name}: {len(from_node):,}")
    
    # Analyze outgoing flows
    total_transitions = len(transitions_df)
    min_flow_size = max(1, int(total_transitions * min_flow_threshold))
    
    outgoing = from_node.groupby('to_state').size().reset_index(name='count')
    outgoing = outgoing.sort_values('count', ascending=False)
    outgoing['percentage'] = (outgoing['count'] / len(from_node) * 100).round(2)
    outgoing['of_total'] = (outgoing['count'] / total_transitions * 100).round(3)
    
    print(f"\n--- Outgoing flows from {node_name} ---")
    print(f"{'Destination':<40} {'Count':>8} {'% of Node':>10} {'% of Total':>10} {'Status':>10}")
    print("-" * 80)
    
    total_shown = 0
    total_hidden = 0
    hidden_destinations = []
    
    for _, row in outgoing.iterrows():
        status = "SHOWN" if row['count'] >= min_flow_size else "HIDDEN"
        print(f"{row['to_state']:<40} {row['count']:>8,} {row['percentage']:>9.1f}% {row['of_total']:>9.3f}% {status:>10}")
        
        if status == "SHOWN":
            total_shown += row['count']
        else:
            total_hidden += row['count']
            hidden_destinations.append(row['to_state'])
    
    print("-" * 80)
    print(f"{'TOTAL SHOWN':<40} {total_shown:>8,} {(total_shown/len(from_node)*100):>9.1f}%")
    print(f"{'TOTAL HIDDEN':<40} {total_hidden:>8,} {(total_hidden/len(from_node)*100):>9.1f}%")
    
    if hidden_destinations:
        print(f"\nHidden destinations: {', '.join(hidden_destinations)}")
    
    # Calculate the "gap" - difference between input and output
    print(f"\n--- Flow Balance ---")
    print(f"Total IN:  {len(to_node):>8,}")
    print(f"Total OUT: {len(from_node):>8,}")
    difference = len(to_node) - len(from_node)
    print(f"Difference: {difference:>8,}")
    
    if difference > 0:
        pct_of_incoming = (difference / len(to_node) * 100)
        print(f"\n🔍 {difference:,} patients ({pct_of_incoming:.1f}% of incoming) remain in {node_name}")
        print("   These patients create the visual 'gap' in the Sankey diagram")
    
    return outgoing


def analyze_all_nodes(transitions_df, min_flow_threshold=0.001):
    """
    Analyze hidden flows for all nodes.
    """
    print(f"\n{'=' * 80}")
    print("SUMMARY: HIDDEN FLOWS BY NODE")
    print(f"{'=' * 80}")
    
    total_transitions = len(transitions_df)
    min_flow_size = max(1, int(total_transitions * min_flow_threshold))
    
    # Get unique states
    all_states = set(transitions_df['from_state'].unique()) | set(transitions_df['to_state'].unique())
    
    node_stats = []
    
    for state in sorted(all_states):
        from_state = transitions_df[transitions_df['from_state'] == state]
        if len(from_state) == 0:
            continue
            
        # Count outgoing flows
        outgoing = from_state.groupby('to_state').size().reset_index(name='count')
        
        total_out = len(from_state)
        hidden_flows = outgoing[outgoing['count'] < min_flow_size]
        hidden_count = hidden_flows['count'].sum()
        
        if hidden_count > 0:  # Only show nodes with hidden flows
            node_stats.append({
                'node': state,
                'total_out': total_out,
                'hidden_transitions': hidden_count,
                'hidden_percentage': (hidden_count / total_out * 100),
                'hidden_destinations': len(hidden_flows)
            })
    
    # Sort by hidden percentage
    node_stats = sorted(node_stats, key=lambda x: x['hidden_percentage'], reverse=True)
    
    print(f"\n{'Node':<40} {'Hidden Trans':>12} {'Hidden %':>10} {'# Hidden Dest':>15}")
    print("-" * 80)
    
    for stat in node_stats:
        print(f"{stat['node']:<40} {stat['hidden_transitions']:>12,} {stat['hidden_percentage']:>9.1f}% {stat['hidden_destinations']:>15}")


def main():
    """Main analysis function."""
    # Find the most recent simulation
    sim_dir = Path("simulation_results")
    if not sim_dir.exists():
        print("No simulation results directory found!")
        return
    
    # Get most recent simulation
    sim_dirs = sorted([d for d in sim_dir.iterdir() if d.is_dir() and d.name.startswith("sim_")])
    if not sim_dirs:
        print("No simulations found!")
        return
    
    latest_sim = sim_dirs[-1]
    print(f"Analyzing simulation: {latest_sim.name}")
    
    # Load the simulation
    try:
        results = ResultsFactory.load_results(latest_sim)
        print(f"Loaded simulation with {results.metadata.n_patients} patients over {results.metadata.duration_years} years")
    except Exception as e:
        print(f"Error loading simulation: {e}")
        return
    
    # Extract treatment patterns
    print("\nExtracting treatment patterns...")
    transitions_df, visits_df = extract_treatment_patterns_vectorized(results)
    
    # Overall flow analysis
    flow_counts, visible_flows, hidden_flows = analyze_transition_flows(transitions_df)
    
    # Specific analysis of Maximum Extension
    analyze_specific_node(transitions_df, 'Maximum Extension (16 weeks)')
    
    # Also analyze other nodes that might have gaps
    analyze_specific_node(transitions_df, 'Extended (12+ weeks)')
    
    # Summary of all nodes
    analyze_all_nodes(transitions_df)
    
    # Save detailed hidden flows for inspection
    if len(hidden_flows) > 0:
        output_file = f"hidden_flows_{latest_sim.name}.csv"
        hidden_flows.to_csv(output_file, index=False)
        print(f"\n💾 Detailed hidden flows saved to: {output_file}")


if __name__ == "__main__":
    main()