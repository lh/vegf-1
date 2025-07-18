"""
Final streamgraph implementation with correct patient counting.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from typing import Dict

# Fix the import path
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# TODO: Add these traffic light colors to SEMANTIC_COLORS in the future
TRAFFIC_LIGHT_COLORS = {
    # Green - Currently being treated
    "active_never_discontinued": "#006400",  # Strong green - never discontinued
    "retreated_planned": "#228B22",         # Medium green - resumed after planned discontinuation
    "retreated_administrative": "#32CD32",  # Weaker green - resumed after admin discontinuation
    "retreated_not_renewed": "#90EE90",     # Weaker green - resumed after not renewed
    "retreated_premature": "#98FB98",       # Weaker green - resumed after premature discontinuation
    
    # Amber - Discontinued planned (stable)
    "discontinued_planned": "#FFA500",       # Amber - planned discontinuation
    
    # Red - Other discontinuations (problems)
    "discontinued_administrative": "#DC143C", # Red - administrative issues
    "discontinued_not_renewed": "#B22222",    # Red - renewal issues
    "discontinued_premature": "#8B0000"       # Dark red - premature discontinuation
}


def sigmoid(x, steepness=10, midpoint=0.5):
    """Sigmoid function for smooth transitions."""
    return 1 / (1 + np.exp(-steepness * (x - midpoint)))


def stepped_curve(x, steps=4):
    """Create a stepped curve for certain events."""
    return np.floor(x * steps) / steps + (x * steps % 1) * 0.2


def extract_retreatment_data(results: Dict) -> Dict:
    """Extract retreatment data from the actual Streamlit data structure."""
    # Try to get from raw_discontinuation_stats first
    raw_stats = results.get("raw_discontinuation_stats", {})
    retreatments_by_type = raw_stats.get("retreatments_by_type", {})
    
    if retreatments_by_type:
        return {
            "stable_max_interval": retreatments_by_type.get("stable_max_interval", 0),
            "random_administrative": retreatments_by_type.get("random_administrative", 0),
            "course_complete_but_not_renewed": retreatments_by_type.get("course_complete_but_not_renewed", 0),
            "premature": retreatments_by_type.get("premature", 0)
        }
    
    # Return empty dict if no data found
    return {
        "stable_max_interval": 0,
        "random_administrative": 0, 
        "course_complete_but_not_renewed": 0,
        "premature": 0
    }


def create_streamgraph_data(results: Dict) -> pd.DataFrame:
    """Create timeline data with correct patient counting."""
    duration_years = results.get("duration_years", 5)
    duration_months = int(duration_years * 12)
    population_size = results.get("population_size", 250)
    
    # Get final counts
    disc_counts = results.get("discontinuation_counts", {})
    retreatments_by_type = extract_retreatment_data(results)
    
    timeline_data = []
    
    # Create curves for each month
    for month in range(duration_months + 1):
        t = month / duration_months
        
        # Calculate cumulative discontinuations at this time point
        cumulative_disc = {}
        for disc_type, total_count in disc_counts.items():
            if disc_type == "Planned":
                curve = sigmoid(t, steepness=8, midpoint=0.7)
            elif disc_type == "Administrative":
                curve = t  # Linear
            elif disc_type == "Not Renewed":
                curve = stepped_curve(t, steps=4)
            elif disc_type == "Premature":
                curve = sigmoid(t, steepness=8, midpoint=0.3)
            else:
                curve = t
            
            cumulative_disc[disc_type] = total_count * curve
        
        # Calculate retreatments with delay
        cumulative_retreat = {}
        retreat_key_mapping = {
            "Planned": "stable_max_interval",
            "Administrative": "random_administrative",
            "Not Renewed": "course_complete_but_not_renewed",
            "Premature": "premature"
        }
        
        for disc_type, retreat_key in retreat_key_mapping.items():
            treat_count = retreatments_by_type.get(retreat_key, 0)
            # Add delay for retreatments
            retreat_curve = sigmoid(t - 0.1, steepness=10, midpoint=0.5)
            retreat_curve = max(0, retreat_curve)
            cumulative_retreat[disc_type] = treat_count * retreat_curve
        
        # CORRECT COUNTING LOGIC:
        # Total discontinued = sum of all discontinuations
        total_discontinued = sum(cumulative_disc.values())
        
        # Currently discontinued = discontinued - retreated
        # (because retreated patients are no longer in discontinued state)
        currently_discontinued = {}
        for disc_type in cumulative_disc:
            retreated_from_this_type = cumulative_retreat.get(disc_type, 0)
            currently_disc = cumulative_disc[disc_type] - retreated_from_this_type
            currently_discontinued[disc_type] = max(0, currently_disc)  # Can't be negative
        
        # Active = population - currently discontinued - retreated
        total_currently_disc = sum(currently_discontinued.values())
        total_retreated = sum(cumulative_retreat.values())
        active_never_disc = population_size - total_currently_disc - total_retreated
        
        # Store data
        # Active (never discontinued)
        timeline_data.append({
            'time_months': month,
            'state': 'Active (Never Discontinued)',
            'count': max(0, active_never_disc)  # Can't be negative
        })
        
        # Currently discontinued states
        for disc_type, count in currently_discontinued.items():
            if count > 0:
                timeline_data.append({
                    'time_months': month,
                    'state': f'Discontinued {disc_type}',
                    'count': count
                })
        
        # Retreated states
        for disc_type, count in cumulative_retreat.items():
            if count > 0:
                timeline_data.append({
                    'time_months': month,
                    'state': f'Retreated {disc_type}',
                    'count': count
                })
    
    return pd.DataFrame(timeline_data)


def generate_final_streamgraph(results: Dict) -> plt.Figure:
    """Generate the final corrected streamgraph."""
    
    # Fail fast if no data
    if not results:
        raise ValueError("No simulation results provided")
    
    # Create timeline data
    timeline_data = create_streamgraph_data(results)
    
    # Pivot data for stacking
    pivot_data = timeline_data.pivot(
        index='time_months', 
        columns='state', 
        values='count'
    ).fillna(0)
    
    # Create figure
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # State ordering (bottom to top)
    state_order = [
        'Active (Never Discontinued)',
        'Retreated Planned',
        'Retreated Administrative',
        'Retreated Not Renewed', 
        'Retreated Premature',
        'Discontinued Planned',
        'Discontinued Administrative',
        'Discontinued Not Renewed',
        'Discontinued Premature'
    ]
    
    # Color mapping
    state_color_map = {
        'Active (Never Discontinued)': ('active_never_discontinued', 0.9),
        'Discontinued Planned': ('discontinued_planned', 0.8),
        'Discontinued Administrative': ('discontinued_administrative', 0.8),
        'Discontinued Not Renewed': ('discontinued_not_renewed', 0.8),
        'Discontinued Premature': ('discontinued_premature', 0.8),
        'Retreated Planned': ('retreated_planned', 0.7),
        'Retreated Administrative': ('retreated_administrative', 0.7),
        'Retreated Not Renewed': ('retreated_not_renewed', 0.7),
        'Retreated Premature': ('retreated_premature', 0.7)
    }
    
    # Create stacked area plot
    x = pivot_data.index
    bottom = np.zeros(len(x))
    
    # Plot in the specified order
    for state in state_order:
        if state in pivot_data.columns:
            values = pivot_data[state].values
            color_key, alpha = state_color_map[state]
            color = TRAFFIC_LIGHT_COLORS[color_key]
            
            ax.fill_between(
                x, bottom, bottom + values,
                color=color,
                alpha=alpha,
                label=state
            )
            bottom += values
    
    # Styling
    ax.set_xlabel("Time (Months)")
    ax.set_ylabel("Number of Patients")
    ax.set_title("Patient Cohort Flow Through Treatment States", fontsize=14, loc="left")
    
    # Set axis limits
    ax.set_xlim(0, max(x))
    ax.set_ylim(0, results.get("population_size", 1000) * 1.05)
    
    # Clean style
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    
    ax.grid(axis='y', linestyle=':', alpha=0.3)
    ax.set_axisbelow(True)
    
    # Legend outside plot area
    available_states = [state for state in state_order if state in pivot_data.columns]
    if available_states:
        ax.legend(
            loc='center left',
            bbox_to_anchor=(1.02, 0.5),
            frameon=False,
            fontsize=9
        )
    
    plt.tight_layout()
    
    # Add summary annotation
    disc_counts = results.get("discontinuation_counts", {})
    total_disc = sum(disc_counts.values())
    
    # Get actual retreatment count
    raw_stats = results.get("raw_discontinuation_stats", {})
    total_retreat = raw_stats.get("retreatments", results.get("recurrences", {}).get("total", 0))
    
    annotation_text = f"Total Discontinuations: {total_disc}\\nTotal Retreatments: {total_retreat}"
    ax.text(
        0.02, 0.98,
        annotation_text,
        transform=ax.transAxes,
        verticalalignment='top',
        fontsize=10,
        bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.8)
    )
    
    return fig