"""
Verify the DES adapter functionality with standalone visualizations.

This script runs the DES simulation with the enhanced discontinuation model
and creates various visualizations to verify the results, without requiring
Streamlit.
"""

import os
import sys
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from collections import defaultdict
import matplotlib.dates as mdates

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from simulation.config import SimulationConfig
from treat_and_extend_des import TreatAndExtendDES, run_treat_and_extend_des
from simulation.des_streamlit_adapter import adapt_des_for_streamlit

def run_small_simulation():
    """Run a small DES simulation for testing."""
    print("Running small DES simulation...")
    
    # Create a test config with shorter duration and fewer patients
    config = SimulationConfig.from_yaml("eylea_literature_based")
    config.duration_days = 365  # 1 year
    config.num_patients = 100   # Small number of patients
    
    # Enable enhanced discontinuation
    config.parameters["discontinuation"] = {
        "enabled": True,
        "criteria": {
            "stable_max_interval": {
                "consecutive_visits": 3,
                "probability": 0.5,  # Higher probability for testing
                "interval_weeks": 16
            },
            "random_administrative": {
                "annual_probability": 0.1  # Higher probability for testing
            },
            "treatment_duration": {
                "threshold_weeks": 26,
                "probability": 0.2  # Higher probability for testing
            },
            "premature": {
                "min_interval_weeks": 8,
                "probability_factor": 2.0
            }
        }
    }
    
    # Run the simulation with Streamlit-compatible output
    results = run_treat_and_extend_des(
        config=config,
        verbose=False,
        streamlit_compatible=True
    )
    
    return results

def plot_discontinuation_counts(results):
    """Plot discontinuation counts by type."""
    print("Creating discontinuation counts plot...")
    
    # Extract discontinuation counts
    disc_counts = results.get("discontinuation_counts", {})
    
    # Set up colors
    colors = {
        "Planned": "#FFA500",  # Amber
        "Administrative": "#DC143C",  # Red
        "Not Renewed": "#B22222",  # Dark red
        "Premature": "#8B0000"  # Darker red
    }
    
    # Create the plot
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Plot as horizontal bars
    types = list(disc_counts.keys())
    counts = [disc_counts[t] for t in types]
    y_pos = np.arange(len(types))
    
    bars = ax.barh(y_pos, counts, align='center', alpha=0.8)
    
    # Color the bars
    for i, bar in enumerate(bars):
        bar.set_color(colors.get(types[i], "#808080"))
    
    # Add labels
    ax.set_yticks(y_pos)
    ax.set_yticklabels(types)
    ax.invert_yaxis()  # Labels read top-to-bottom
    ax.set_xlabel('Number of Patients')
    ax.set_title('Discontinuations by Type')
    
    # Add count labels on the bars
    for i, v in enumerate(counts):
        if v > 0:
            ax.text(v + 0.5, i, str(v), va='center')
    
    # Add total as text annotation
    total_disc = sum(counts)
    ax.text(0.9, 0.05, f"Total: {total_disc}", transform=ax.transAxes, 
            bbox=dict(facecolor='white', alpha=0.5))
    
    # Clean styling
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    # Save the figure
    plt.tight_layout()
    plt.savefig("des_discontinuation_counts.png", dpi=150)
    plt.close()
    
    print(f"Discontinuation counts plot saved to des_discontinuation_counts.png")

def plot_patient_pathways(results):
    """Plot example patient pathways showing discontinuations and retreatments."""
    print("Creating patient pathways plot...")
    
    patient_histories = results.get("patient_histories", {})
    
    # Find patients with interesting pathways (discontinuation, monitoring, retreatment)
    candidates = []
    
    for patient_id, visits in patient_histories.items():
        has_discontinuation = any(visit.get("is_discontinuation_visit", False) for visit in visits)
        has_retreatment = any(visit.get("is_retreatment", False) for visit in visits)
        
        if has_discontinuation and has_retreatment:
            candidates.append((patient_id, len(visits)))
    
    # Select up to 3 patients with most visits (or fewer if not enough found)
    selected_patients = [p[0] for p in sorted(candidates, key=lambda x: x[1], reverse=True)[:3]]
    
    # If no patients with both discontinuation and retreatment, just get patients with discontinuation
    if not selected_patients:
        for patient_id, visits in patient_histories.items():
            if any(visit.get("is_discontinuation_visit", False) for visit in visits):
                selected_patients.append(patient_id)
                if len(selected_patients) >= 3:
                    break
    
    # If still no patients, just pick the first 3
    if not selected_patients and patient_histories:
        selected_patients = list(patient_histories.keys())[:3]
    
    if not selected_patients:
        print("No patients found for pathway visualization")
        return
    
    # Create plot with multiple subplots, one for each patient
    fig, axes = plt.subplots(len(selected_patients), 1, figsize=(12, 4*len(selected_patients)))
    if len(selected_patients) == 1:
        axes = [axes]
    
    markers = {
        "regular_visit": "o",
        "monitoring_visit": "s",
        "is_discontinuation_visit": "X",
        "is_retreatment": "^"
    }
    
    colors = {
        "regular_visit": "#2E7D32",  # Dark green
        "monitoring_visit": "#9E9E9E",  # Gray
        "is_discontinuation_visit": "#DC143C",  # Red
        "is_retreatment": "#1E88E5"   # Blue
    }
    
    # Process each selected patient
    for i, patient_id in enumerate(selected_patients):
        ax = axes[i]
        visits = patient_histories[patient_id]
        
        # Sort visits chronologically
        visits = sorted(visits, key=lambda v: v.get("time", v.get("date", 0)))
        
        # Extract dates and vision values
        dates = [visit.get("time", visit.get("date", 0)) for visit in visits]
        vision = [visit.get("vision", None) for visit in visits]
        
        # Plot vision over time
        ax.plot(dates, vision, '-', color='gray', alpha=0.6, linewidth=1)
        
        # Plot specific visit types with different markers
        for j, visit in enumerate(visits):
            visit_type = visit.get("type", "regular_visit")
            marker = markers.get(visit_type, "o")
            color = colors.get(visit_type, "#2E7D32")
            
            # Special markers for discontinuation and retreatment
            if visit.get("is_discontinuation_visit", False):
                marker = markers["is_discontinuation_visit"]
                color = colors["is_discontinuation_visit"]
                
                # Add label for discontinuation type
                if "discontinuation_reason" in visit:
                    disc_reason = visit["discontinuation_reason"]
                    ax.annotate(disc_reason, (dates[j], vision[j]), 
                                xytext=(5, 5), textcoords='offset points',
                                fontsize=8, alpha=0.7)
            
            elif visit.get("is_retreatment", False):
                marker = markers["is_retreatment"]
                color = colors["is_retreatment"]
            
            # Plot the marker
            ax.plot(dates[j], vision[j], marker, color=color, markersize=8, alpha=0.8)
        
        # Format x-axis to show dates
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        # Set labels and title
        ax.set_ylabel('Vision (ETDRS letters)')
        if i == len(selected_patients) - 1:
            ax.set_xlabel('Date')
        ax.set_title(f'Patient {patient_id} Treatment Pathway')
        
        # Set y-axis range
        ax.set_ylim(0, 85)
        
        # Clean styling
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.grid(axis='y', linestyle=':', alpha=0.3)
        
        # Add legend
        legend_elements = [
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor=colors["regular_visit"], 
                       label='Regular Visit', markersize=8),
            plt.Line2D([0], [0], marker='s', color='w', markerfacecolor=colors["monitoring_visit"], 
                       label='Monitoring Visit', markersize=8),
            plt.Line2D([0], [0], marker='X', color='w', markerfacecolor=colors["is_discontinuation_visit"], 
                       label='Discontinuation', markersize=8),
            plt.Line2D([0], [0], marker='^', color='w', markerfacecolor=colors["is_retreatment"], 
                       label='Retreatment', markersize=8)
        ]
        ax.legend(handles=legend_elements, loc='upper right')
    
    # Adjust layout
    plt.tight_layout()
    plt.savefig("des_patient_pathways.png", dpi=150)
    plt.close()
    
    print(f"Patient pathways plot saved to des_patient_pathways.png")

def plot_patient_states_over_time(results):
    """Plot how patients move through different states over time."""
    print("Creating patient states over time plot...")
    
    patient_histories = results.get("patient_histories", {})
    duration_years = results.get("duration_years", 5)
    duration_months = int(duration_years * 12)
    
    # Define states
    states = [
        "active",              # Active treatment, never discontinued
        "active_retreated",    # Active treatment after retreatment
        "discontinued",        # Discontinued (all types)
        "monitoring"           # In monitoring phase
    ]
    
    # Initialize count arrays
    months = list(range(duration_months + 1))
    state_counts = {state: [0] * len(months) for state in states}
    
    # Process each patient's state at each month
    for patient_id, visits in patient_histories.items():
        # Sort visits chronologically
        sorted_visits = sorted(visits, key=lambda v: v.get("time", v.get("date", 0)))
        
        # For each month, determine patient's state
        for month in months:
            # Find the most recent visit before or at this month
            current_state = "active"  # Default state
            is_discontinued = False
            is_monitoring = False
            is_retreated = False
            
            for visit in sorted_visits:
                visit_time = visit.get("time", visit.get("date", 0))
                
                # Convert to month number
                if hasattr(visit_time, 'month'):
                    visit_month = (visit_time.year - sorted_visits[0].get("time").year) * 12 + visit_time.month - sorted_visits[0].get("time").month
                else:
                    # Use a default conversion if timestamp is not a datetime
                    visit_month = 0
                
                if visit_month <= month:
                    if visit.get("is_discontinuation_visit", False):
                        is_discontinued = True
                        is_monitoring = False
                        is_retreated = False
                    elif visit.get("type") == "monitoring_visit":
                        is_monitoring = True
                    elif visit.get("is_retreatment", False):
                        is_retreated = True
                        is_discontinued = False
                        is_monitoring = False
            
            # Determine final state for this month
            if is_discontinued:
                current_state = "discontinued"
            elif is_monitoring:
                current_state = "monitoring"
            elif is_retreated:
                current_state = "active_retreated"
            else:
                current_state = "active"
            
            # Increment count for this state
            state_counts[current_state][month] += 1
    
    # Create stacked area plot
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Define colors
    colors = {
        "active": "#2E7D32",           # Dark green
        "active_retreated": "#66BB6A",  # Light green
        "discontinued": "#DC143C",      # Red
        "monitoring": "#FFA500"         # Amber
    }
    
    # Create stacked area plot
    stack_data = []
    stack_colors = []
    stack_labels = []
    
    # Only include states that actually occur
    for state in states:
        if sum(state_counts[state]) > 0:
            stack_data.append(state_counts[state])
            stack_colors.append(colors[state])
            stack_labels.append(state)
    
    # Create the plot
    ax.stackplot(months, stack_data, labels=stack_labels, colors=stack_colors, alpha=0.8)
    
    # Add labels and title
    ax.set_xlabel('Month')
    ax.set_ylabel('Number of Patients')
    ax.set_title('Patient States Over Time')
    
    # Set x-axis ticks at yearly intervals
    ax.set_xticks(range(0, duration_months + 1, 12))
    ax.set_xticklabels([f'Year {i}' for i in range(len(ax.get_xticks()))])
    
    # Clean styling
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.grid(axis='y', linestyle=':', alpha=0.3)
    
    # Add legend
    ax.legend(loc='upper right')
    
    # Save the figure
    plt.tight_layout()
    plt.savefig("des_patient_states_over_time.png", dpi=150)
    plt.close()
    
    print(f"Patient states over time plot saved to des_patient_states_over_time.png")

def plot_transition_diagram(results):
    """Create a simple transition diagram showing treatment phases."""
    print("Creating treatment phases transition diagram...")
    
    # Define treatments phases and transitions
    phases = [
        "Loading Phase\n(3 monthly injections)",
        "Maintenance Phase\n(T&E intervals)",
        "Discontinued\n(stable/administrative)",
        "Monitoring\n(follow-up visits)",
        "Retreatment\n(restart therapy)"
    ]
    
    # Define relationships as adjacency list
    # Each tuple is (source_index, target_index, transition_label)
    transitions = [
        (0, 1, "Complete loading"),
        (1, 2, "Discontinue"),
        (2, 3, "Monitor"),
        (3, 4, "Recurrence detected"),
        (4, 0, "Restart treatment")
    ]
    
    # Extract actual transition counts from results
    transition_counts = {
        "Complete loading": results.get("statistics", {}).get("discontinuation_stats", {}).get("protocol_completions", 0),
        "Discontinue": results.get("statistics", {}).get("discontinuation_stats", {}).get("total_discontinuations", 0),
        "Monitor": results.get("statistics", {}).get("monitoring_visits", 0),
        "Recurrence detected": results.get("statistics", {}).get("retreatment_stats", {}).get("total_retreatments", 0),
        "Restart treatment": results.get("statistics", {}).get("retreatment_stats", {}).get("total_retreatments", 0)
    }
    
    # Create transition diagram using NetworkX and matplotlib
    try:
        import networkx as nx
        
        # Create directed graph
        G = nx.DiGraph()
        
        # Add nodes
        for i, phase in enumerate(phases):
            G.add_node(i, label=phase)
        
        # Add edges with counts
        for source, target, label in transitions:
            count = transition_counts.get(label, 0)
            G.add_edge(source, target, label=f"{label}\n(n={count})")
        
        # Create figure
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Draw the graph
        pos = {
            0: (0, 0.5),
            1: (2, 0.5),
            2: (4, 0.5),
            3: (4, -0.5),
            4: (2, -0.5)
        }
        
        # Node styling
        node_colors = [
            "#66BB6A",  # Green for loading
            "#2E7D32",  # Dark green for maintenance
            "#DC143C",  # Red for discontinued
            "#FFA500",  # Amber for monitoring
            "#1E88E5"   # Blue for retreatment
        ]
        
        # Draw nodes
        nx.draw_networkx_nodes(G, pos, node_size=5000, 
                             node_color=node_colors, alpha=0.8, 
                             node_shape="o", ax=ax)
        
        # Draw edges
        nx.draw_networkx_edges(G, pos, edgelist=G.edges(), 
                             width=2, alpha=0.7, 
                             edge_color="gray",
                             connectionstyle="arc3,rad=0.1",
                             arrows=True, arrowsize=20, ax=ax)
        
        # Draw node labels
        nx.draw_networkx_labels(G, pos, labels=nx.get_node_attributes(G, 'label'),
                              font_size=12, ax=ax)
        
        # Draw edge labels
        edge_labels = {(source, target): G.edges[source, target]['label'] 
                     for source, target in G.edges()}
        nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, 
                                   font_size=10, ax=ax)
        
        # Remove axis
        ax.axis('off')
        
        # Add title
        ax.set_title('Treatment Phase Transitions')
        
        # Save figure
        plt.tight_layout()
        plt.savefig("des_transition_diagram.png", dpi=150)
        plt.close()
        
        print(f"Transition diagram saved to des_transition_diagram.png")
        
    except ImportError:
        print("NetworkX not available for transition diagram. Skipping...")

def main():
    """Run the verification process."""
    print("=== DES Adapter Verification ===")
    
    # Run simulation
    results = run_small_simulation()
    
    # Print basic statistics
    print("\nSimulation Results:")
    print(f"Population Size: {results['population_size']}")
    print(f"Duration (years): {results['duration_years']}")
    
    # Create visualizations
    plot_discontinuation_counts(results)
    plot_patient_pathways(results)
    plot_patient_states_over_time(results)
    plot_transition_diagram(results)
    
    print("\n=== Verification Complete ===")

if __name__ == "__main__":
    main()