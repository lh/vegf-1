"""
Enhanced streamgraph visualization for patient cohort lifecycle.

This version properly tracks discontinuation and retreatment states.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import PathPatch
from matplotlib.path import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from collections import defaultdict

# Import the central color system - no fallbacks
from visualization.color_system import COLORS, SEMANTIC_COLORS, ALPHAS


def extract_patient_states_timeline(results: Dict) -> pd.DataFrame:
    """
    Extract patient states over time from simulation results.
    
    This version handles the actual data structure where discontinuation
    counts are provided at the simulation level.
    
    Parameters
    ----------
    results : dict
        Simulation results containing patient histories and discontinuation data
        
    Returns
    -------
    pd.DataFrame
        Timeline data with columns: time_months, state, count
    """
    # Get simulation duration and patient count
    duration_years = results.get("duration_years", 5)
    duration_months = int(duration_years * 12)
    population_size = results.get("population_size", 250)
    
    # Get discontinuation counts
    disc_counts = results.get("discontinuation_counts", {})
    
    # Get retreatment data
    recurrences = results.get("recurrences", {})
    retreatments_by_type = recurrences.get("by_type", {})
    
    # Initialize timeline data
    timeline_data = []
    
    # Track cumulative states over time
    cumulative_disc = {
        "Planned": 0,
        "Administrative": 0,
        "Not Renewed": 0,
        "Premature": 0
    }
    
    cumulative_retreat = {
        "Planned": 0,
        "Administrative": 0,
        "Not Renewed": 0,
        "Premature": 0
    }
    
    # Map discontinuation types to retreatment keys
    retreat_key_mapping = {
        "Planned": "stable_max_interval",
        "Administrative": "random_administrative",
        "Not Renewed": "treatment_duration",
        "Premature": "premature"
    }
    
    # Calculate monthly discontinuation rates
    monthly_disc_rate = {}
    for disc_type, count in disc_counts.items():
        monthly_disc_rate[disc_type] = count / duration_months if duration_months > 0 else 0
    
    # Calculate retreatment rates by type
    retreat_rates = {}
    for disc_type, retreat_key in retreat_key_mapping.items():
        if disc_type in disc_counts and disc_counts[disc_type] > 0:
            retreated = retreatments_by_type.get(retreat_key, 0)
            retreat_rates[disc_type] = retreated / disc_counts[disc_type]
        else:
            retreat_rates[disc_type] = 0
    
    # Generate timeline month by month
    for month in range(duration_months + 1):
        # Update discontinuations for this month
        for disc_type, monthly_rate in monthly_disc_rate.items():
            new_disc = monthly_rate
            cumulative_disc[disc_type] += new_disc
            
            # Calculate retreatments (with some delay)
            # Retreatments happen after discontinuation, so apply with a lag
            if month > 6:  # Start retreatments after 6 months
                retreat_from_earlier = cumulative_disc[disc_type] * retreat_rates.get(disc_type, 0)
                cumulative_retreat[disc_type] = min(retreat_from_earlier, cumulative_disc[disc_type])
        
        # Calculate patient states
        # 1. Never discontinued (active from start)
        total_ever_discontinued = sum(cumulative_disc.values())
        never_discontinued = population_size - total_ever_discontinued
        
        # 2. Currently discontinued (discontinued but not retreated)
        currently_discontinued = {}
        for disc_type in cumulative_disc.keys():
            currently_discontinued[disc_type] = cumulative_disc[disc_type] - cumulative_retreat[disc_type]
        
        # 3. Retreated (back on treatment)
        # These are already tracked in cumulative_retreat
        
        # Add never discontinued count
        timeline_data.append({
            "time_months": month,
            "state": "Active",
            "count": never_discontinued
        })
        
        # Add currently discontinued states
        for disc_type, count in currently_discontinued.items():
            if count > 0:
                timeline_data.append({
                    "time_months": month,
                    "state": f"Discontinued {disc_type}",
                    "count": count
                })
        
        # Add retreated states
        for disc_type, count in cumulative_retreat.items():
            if count > 0:
                timeline_data.append({
                    "time_months": month,
                    "state": f"Retreated {disc_type}",
                    "count": count
                })
    
    return pd.DataFrame(timeline_data)


def create_enhanced_streamgraph(
    data: pd.DataFrame,
    title: str = "Patient Treatment Journey: Active, Discontinued, and Retreated States",
    figsize: Tuple[int, int] = (12, 8),
    show_annotations: bool = True
) -> Tuple[plt.Figure, plt.Axes]:
    """
    Create an enhanced streamgraph showing patient cohort flow.
    
    Parameters
    ----------
    data : pd.DataFrame
        Timeline data with columns: time_months, state, count
    title : str
        Chart title
    figsize : tuple
        Figure size
    show_annotations : bool
        Whether to show summary annotations
        
    Returns
    -------
    tuple
        (fig, ax) matplotlib objects
    """
    # Define color scheme with traffic light analogy
    color_scheme = {
        # Strong green - patients who never discontinue
        "Active": "#2E7D32",  # Strong forest green
        
        # Amber - stable discontinuations (good outcome)
        "Discontinued Planned": "#FFA000",  # Amber
        
        # Red shades - error discontinuations (problematic outcomes)
        "Discontinued Administrative": "#D32F2F",  # Red
        "Discontinued Not Renewed": "#C62828",  # Dark red
        "Discontinued Premature": "#B71C1C",  # Darker red
        
        # Pale green - retreated patients (restarted treatment)
        "Retreated Planned": "#81C784",  # Light green
        
        # Pale red/pink - retreated after error discontinuation
        "Retreated Administrative": "#EF9A9A",  # Light red/pink
        "Retreated Not Renewed": "#E57373",  # Medium pink-red
        "Retreated Premature": "#EF5350",  # Slightly stronger pink-red
    }
    
    # Pivot data for streamgraph
    pivot_data = data.pivot_table(
        index="time_months",
        columns="state", 
        values="count",
        fill_value=0
    )
    
    # Order states for visual flow
    state_order = [
        "Active",
        "Discontinued Planned",
        "Discontinued Administrative",
        "Discontinued Not Renewed",
        "Discontinued Premature",
        "Retreated Planned",
        "Retreated Administrative",
        "Retreated Not Renewed",
        "Retreated Premature"
    ]
    
    # Filter to only states present in data
    available_states = [s for s in state_order if s in pivot_data.columns]
    pivot_data = pivot_data[available_states]
    
    # Create figure
    fig, ax = plt.subplots(figsize=figsize)
    
    # Convert to numpy array for streamgraph calculation
    data_array = pivot_data.values.T
    times = pivot_data.index.values
    
    # Simple stacking for cohort data
    baselines = np.zeros((len(available_states) + 1, len(times)))
    streams = []
    
    for i in range(len(available_states)):
        baselines[i + 1] = baselines[i] + data_array[i]
        streams.append((baselines[i], baselines[i + 1]))
    
    # Plot each stream
    for i, (state, stream) in enumerate(zip(available_states, streams)):
        color = color_scheme.get(state, COLORS['primary'])
        
        ax.fill_between(
            times,
            stream[0],  # bottom
            stream[1],  # top
            color=color,
            alpha=0.8,
            label=state
        )
    
    # Styling
    ax.set_xlabel("Time (Months)")
    ax.set_ylabel("Number of Patients")
    ax.set_title(title, fontsize=14, loc="left")
    
    # Remove spines for cleaner look
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    
    # Grid
    ax.grid(axis='y', linestyle=':', alpha=0.3)
    ax.set_axisbelow(True)
    
    # Create custom legend with semantic grouping
    from matplotlib.patches import Patch
    legend_elements = []
    
    # Group 1: Active (Strong Green)
    legend_elements.append(Patch(facecolor=color_scheme["Active"], label='Active (Never Discontinued)'))
    
    # Group 2: Good outcomes (Amber)
    if "Discontinued Planned" in available_states:
        legend_elements.append(Patch(facecolor=color_scheme["Discontinued Planned"], 
                                   label='Discontinued - Stable Disease'))
    
    # Group 3: Problematic outcomes (Red shades)
    error_types = ["Administrative", "Not Renewed", "Premature"]
    for error_type in error_types:
        disc_key = f"Discontinued {error_type}"
        if disc_key in available_states:
            legend_elements.append(Patch(facecolor=color_scheme[disc_key], 
                                       label=f'Discontinued - {error_type}'))
    
    # Group 4: Retreated - Good restart (Pale Green)
    if "Retreated Planned" in available_states:
        legend_elements.append(Patch(facecolor=color_scheme["Retreated Planned"], 
                                   label='Retreated - After Stable'))
    
    # Group 5: Retreated - After problems (Pale Red/Pink)
    for error_type in error_types:
        retreat_key = f"Retreated {error_type}"
        if retreat_key in available_states:
            legend_elements.append(Patch(facecolor=color_scheme[retreat_key], 
                                       label=f'Retreated - After {error_type}'))
    
    # Add legend with better positioning
    if legend_elements:
        ax.legend(handles=legend_elements, 
                 loc='center left', 
                 bbox_to_anchor=(1.02, 0.5),
                 frameon=False,
                 fontsize=9)
    
    # Add annotations if requested
    if show_annotations and 'discontinuation_counts' in pivot_data.columns.get_level_values(0):
        total_disc = data[data['state'].str.contains('Discontinued')]['count'].max()
        total_retreat = data[data['state'].str.contains('Retreated')]['count'].max()
        
        annotation_text = f"Total Discontinuations: {int(total_disc)}\\nTotal Retreatments: {int(total_retreat)}"
        ax.text(
            0.02, 0.98,
            annotation_text,
            transform=ax.transAxes,
            verticalalignment='top',
            bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.8)
        )
    
    plt.tight_layout()
    return fig, ax


def generate_cohort_flow_streamgraph(results: Dict) -> plt.Figure:
    """
    Generate streamgraph visualization from simulation results.
    
    Parameters
    ----------
    results : dict
        Simulation results
        
    Returns
    -------
    plt.Figure
        The created figure
    """
    # Extract timeline data
    timeline_data = extract_patient_states_timeline(results)
    
    # Create streamgraph
    fig, ax = create_enhanced_streamgraph(timeline_data)
    
    # Add summary annotation
    disc_counts = results.get("discontinuation_counts", {})
    total_disc = sum(disc_counts.values())
    total_retreat = results.get("recurrences", {}).get("total", 0)
    
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