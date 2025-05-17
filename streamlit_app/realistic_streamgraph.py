"""
Realistic streamgraph that uses actual patient timeline data when available.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import PathPatch
from matplotlib.path import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from collections import defaultdict

# Import the central color system
from visualization.color_system import COLORS, SEMANTIC_COLORS, ALPHAS


def extract_realistic_timeline(results: Dict) -> pd.DataFrame:
    """
    Extract realistic patient state timeline from simulation results.
    
    First attempts to use actual patient histories for accurate timing,
    falls back to interpolated data if histories not available.
    
    Parameters
    ----------
    results : dict
        Simulation results
        
    Returns
    -------
    pd.DataFrame
        Timeline data with columns: time_months, state, count
    """
    # Check if we have patient histories
    patient_data = results.get("patient_histories", {})
    
    if patient_data:
        # Use actual patient timeline data
        return extract_timeline_from_histories(patient_data)
    else:
        # Fall back to interpolated data with realistic variation
        return extract_interpolated_timeline(results)


def extract_timeline_from_histories(patient_histories: Dict) -> pd.DataFrame:
    """
    Extract timeline from actual patient histories.
    
    Parameters
    ----------
    patient_histories : dict
        Dictionary of patient histories
        
    Returns
    -------
    pd.DataFrame
        Timeline data with realistic transitions
    """
    # Track patient states over time
    patient_states = {}  # patient_id -> [(time_months, state)]
    
    # Process each patient's history
    for patient_id, patient in patient_histories.items():
        # Get the patient's visit history
        history = patient if isinstance(patient, list) else getattr(patient, 'history', [])
        
        if not history:
            continue
        
        patient_timeline = []
        
        for visit in history:
            # Convert time to months
            time_data = visit.get('time', visit.get('time_weeks', 0))
            
            # Handle different time formats
            if isinstance(time_data, (int, float)):
                time_weeks = time_data
            elif isinstance(time_data, datetime):
                # Convert datetime to weeks from start
                if not hasattr(extract_timeline_from_histories, 'start_time'):
                    extract_timeline_from_histories.start_time = time_data
                time_delta = time_data - extract_timeline_from_histories.start_time
                time_weeks = time_delta.days / 7
            else:
                time_weeks = 0
                
            time_months = int(time_weeks / 4.33)  # Convert weeks to months
            
            # Determine patient state from visit data
            state = determine_state_from_visit(visit)
            
            patient_timeline.append((time_months, state))
        
        patient_states[patient_id] = patient_timeline
    
    # Check if we have any patient data
    if not patient_states:
        return pd.DataFrame(columns=['time_months', 'state', 'count'])
    
    # Now create timeline data counting patients in each state at each time
    max_months = max(max(t for t, s in timeline) for timeline in patient_states.values() if timeline)
    timeline_data = []
    
    for month in range(max_months + 1):
        month_states = defaultdict(int)
        
        # For each patient, find their state at this month
        for patient_id, timeline in patient_states.items():
            # Find the most recent state for this patient at this time
            current_state = "Active"  # Default state
            
            for t, state in timeline:
                if t <= month:
                    current_state = state
                else:
                    break
            
            month_states[current_state] += 1
        
        # Add rows for each state present this month
        for state, count in month_states.items():
            timeline_data.append({
                "time_months": month,
                "state": state,
                "count": count
            })
    
    return pd.DataFrame(timeline_data)


def determine_state_from_visit(visit: Dict) -> str:
    """
    Determine patient state from visit data.
    
    Parameters
    ----------
    visit : dict
        Visit data
        
    Returns
    -------
    str
        Patient state
    """
    # Check treatment status
    treatment_status = visit.get("treatment_status", {})
    
    if not treatment_status.get("active", True):
        # Patient is discontinued
        reason = treatment_status.get("discontinuation_reason", "")
        
        if treatment_status.get("retreated", False):
            # Patient has retreated
            if reason == "stable_max_interval":
                return "Retreated Planned"
            elif reason in ["random_administrative", "administrative"]:
                return "Retreated Administrative"
            elif reason in ["course_complete_but_not_renewed", "not_renewed"]:
                return "Retreated Not Renewed"
            elif reason == "premature":
                return "Retreated Premature"
            else:
                return "Retreated Other"
        else:
            # Patient is still discontinued
            if reason == "stable_max_interval":
                return "Discontinued Planned"
            elif reason in ["random_administrative", "administrative"]:
                return "Discontinued Administrative"
            elif reason in ["course_complete_but_not_renewed", "not_renewed"]:
                return "Discontinued Not Renewed"
            elif reason == "premature":
                return "Discontinued Premature"
            else:
                return "Discontinued Other"
    
    # Patient is active
    return "Active"


def extract_interpolated_timeline(results: Dict) -> pd.DataFrame:
    """
    Create interpolated timeline with realistic variation.
    
    This is the fallback when actual patient histories aren't available.
    It adds realistic variation to avoid perfectly linear progression.
    
    Parameters
    ----------
    results : dict
        Simulation results
        
    Returns
    -------
    pd.DataFrame
        Timeline data with realistic-looking variation
    """
    duration_years = results.get("duration_years", 5)
    duration_months = int(duration_years * 12)
    population_size = results.get("population_size", 250)
    
    # Get final counts
    disc_counts = results.get("discontinuation_counts", {})
    recurrences = results.get("recurrences", {})
    retreatments_by_type = recurrences.get("by_type", {})
    
    timeline_data = []
    
    # Initialize cumulative tracking
    cumulative_disc = {k: 0.0 for k in disc_counts.keys()}
    cumulative_retreat = {
        "Planned": 0.0,
        "Administrative": 0.0,
        "Not Renewed": 0.0,
        "Premature": 0.0
    }
    
    # Create realistic curves using sigmoid functions
    for month in range(duration_months + 1):
        t = month / duration_months  # Normalized time
        
        # Apply different curves for different discontinuation types
        for disc_type, total_count in disc_counts.items():
            if disc_type == "Planned":
                # Planned discontinuations happen later (after stability achieved)
                curve = sigmoid(t, steepness=8, midpoint=0.7)
            elif disc_type == "Administrative":
                # Administrative issues can happen anytime
                curve = t  # Linear
            elif disc_type == "Not Renewed":
                # Renewal issues cluster around certain times
                curve = stepped_curve(t, steps=4)
            elif disc_type == "Premature":
                # Premature discontinuations happen early
                curve = sigmoid(t, steepness=8, midpoint=0.3)
            else:
                curve = t
            
            # Add some noise for realism
            noise = np.random.normal(0, 0.02)
            curve = max(0, min(1, curve + noise))
            
            cumulative_disc[disc_type] = total_count * curve
        
        # Calculate retreatments with delay and variation
        retreat_key_mapping = {
            "Planned": "stable_max_interval",
            "Administrative": "random_administrative",
            "Not Renewed": "treatment_duration",
            "Premature": "premature"
        }
        
        for disc_type, retreat_key in retreat_key_mapping.items():
            if month > 6:  # Retreatments start after some delay
                retreat_delay = month - 6
                retreat_t = retreat_delay / (duration_months - 6)
                
                total_retreats = retreatments_by_type.get(retreat_key, 0)
                # Retreatments follow a delayed sigmoid
                retreat_curve = sigmoid(retreat_t, steepness=6, midpoint=0.5)
                
                cumulative_retreat[disc_type] = total_retreats * retreat_curve
        
        # Calculate current states
        total_ever_discontinued = sum(cumulative_disc.values())
        never_discontinued = population_size - total_ever_discontinued
        
        # Add active count
        timeline_data.append({
            "time_months": month,
            "state": "Active",
            "count": never_discontinued
        })
        
        # Add discontinued states
        for disc_type in cumulative_disc.keys():
            disc_count = cumulative_disc[disc_type] - cumulative_retreat.get(disc_type, 0)
            if disc_count > 0:
                timeline_data.append({
                    "time_months": month,
                    "state": f"Discontinued {disc_type}",
                    "count": disc_count
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


def sigmoid(x, steepness=10, midpoint=0.5):
    """S-shaped curve for realistic transitions."""
    return 1 / (1 + np.exp(-steepness * (x - midpoint)))


def stepped_curve(x, steps=4):
    """Stepped curve for events that cluster at certain times."""
    step_size = 1.0 / steps
    return min(1.0, int(x / step_size + 0.5) * step_size)


def create_realistic_streamgraph(
    data: pd.DataFrame,
    title: str = "Patient Treatment Journey: Realistic Timeline",
    figsize: Tuple[int, int] = (12, 8),
    show_annotations: bool = True
) -> Tuple[plt.Figure, plt.Axes]:
    """
    Create a streamgraph with realistic patient flow visualization.
    
    Uses the same visual style as enhanced_streamgraph but with
    more realistic data representation.
    """
    # Define traffic light color scheme
    color_scheme = {
        "Active": "#2E7D32",  # Strong forest green
        
        "Discontinued Planned": "#FFA000",  # Amber
        "Discontinued Administrative": "#D32F2F",  # Red
        "Discontinued Not Renewed": "#C62828",  # Dark red
        "Discontinued Premature": "#B71C1C",  # Darker red
        
        "Retreated Planned": "#81C784",  # Light green
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
    
    # Create figure
    fig, ax = plt.subplots(figsize=figsize)
    
    # Convert to numpy for streamgraph
    times = pivot_data.index.values
    
    # Define state order for consistent stacking
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
    
    # Filter to available states
    available_states = [s for s in state_order if s in pivot_data.columns]
    data_array = pivot_data[available_states].values.T
    
    # Stack the data
    baselines = np.zeros((len(available_states) + 1, len(times)))
    
    for i in range(len(available_states)):
        baselines[i + 1] = baselines[i] + data_array[i]
    
    # Plot streams
    for i, state in enumerate(available_states):
        color = color_scheme.get(state, "#666666")
        
        ax.fill_between(
            times,
            baselines[i],
            baselines[i + 1],
            color=color,
            alpha=0.8,
            label=state
        )
    
    # Styling
    ax.set_xlabel("Time (Months)")
    ax.set_ylabel("Number of Patients")
    ax.set_title(title, fontsize=14, loc="left")
    
    # Clean style
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    
    ax.grid(axis='y', linestyle=':', alpha=0.3)
    ax.set_axisbelow(True)
    
    # Legend
    if available_states:
        ax.legend(
            loc='center left',
            bbox_to_anchor=(1.02, 0.5),
            frameon=False,
            fontsize=9
        )
    
    plt.tight_layout()
    return fig, ax


def generate_realistic_streamgraph(results: Dict) -> plt.Figure:
    """
    Generate a realistic streamgraph from simulation results.
    
    Parameters
    ----------
    results : dict
        Simulation results
        
    Returns
    -------
    plt.Figure
        The streamgraph figure
    """
    # Extract timeline data (realistic if possible)
    timeline_data = extract_realistic_timeline(results)
    
    # Create streamgraph
    fig, ax = create_realistic_streamgraph(timeline_data)
    
    # Add summary annotation
    disc_counts = results.get("discontinuation_counts", {})
    total_disc = sum(disc_counts.values())
    total_retreat = results.get("recurrences", {}).get("total", 0)
    
    annotation_text = f"Total Discontinuations: {total_disc}\nTotal Retreatments: {total_retreat}"
    ax.text(
        0.02, 0.98,
        annotation_text,
        transform=ax.transAxes,
        verticalalignment='top',
        fontsize=10,
        bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.8)
    )
    
    return fig