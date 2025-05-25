"""
Streamgraph visualization for patient cohort lifecycle.

This module creates a streamgraph showing the flow of patients through various 
treatment states, including discontinuation and retreatment over time.
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


def prepare_cohort_timeline_data(results: Dict) -> pd.DataFrame:
    """
    Extract timeline data from simulation results showing patient states over time.
    
    Parameters
    ----------
    results : dict
        Simulation results containing patient histories
        
    Returns
    -------
    pd.DataFrame
        Timeline data with columns: time_weeks, state, count, newly_transitioned
        
    Raises
    ------
    ValueError
        If required patient history data is not available
    """
    # Initialize data storage
    timeline_data = defaultdict(lambda: defaultdict(int))
    transitions = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    
    # Extract patient histories - FAIL FAST if not available
    # The simulation stores patient data as "patient_histories"
    patient_data = results.get("patient_histories", results.get("patients", []))
    
    if not patient_data:
        raise ValueError(
            "Cannot create streamgraph: No patient history data available in simulation results. "
            "Streamgraph requires detailed patient timelines from the simulation."
        )
    
    # Process each patient's history
    patients_with_history = 0
    
    # Handle both dict (patient_id -> history) and list formats
    if isinstance(patient_data, dict):
        # patient_histories format: {patient_id: visit_list}
        for patient_id, visit_list in patient_data.items():
            if visit_list:
                patients_with_history += 1
                prev_state = "active"
                
                for i, visit in enumerate(visit_list):
                    # Convert date to weeks since start if needed
                    if 'date' in visit:
                        from datetime import datetime
                        visit_date = pd.to_datetime(visit['date'])
                        start_date = pd.to_datetime('2023-01-01')  # Default start
                        week = int((visit_date - start_date).days / 7)
                    else:
                        week = i * 4  # Default to 4-week intervals if no date
                    
                    # Check for treatment status in visit
                    treatment_status = visit.get("treatment_status", {})
                    if not treatment_status and 'phase' in visit:
                        # If no treatment status but has phase, assume active
                        treatment_status = {"active": True}
                    
                    # Determine current state
                    current_state = determine_patient_state(treatment_status, visit)
                    
                    # Track state counts
                    timeline_data[week][current_state] += 1
                    
                    # Track transitions
                    if current_state != prev_state:
                        transitions[week][prev_state][current_state] += 1
                    
                    prev_state = current_state
    else:
        # Original format: list of patient objects
        for patient in patient_data:
            if "visit_history" not in patient:
                continue
                
            patients_with_history += 1
            history = patient["visit_history"]
            prev_state = "active"
            
            for i, visit in enumerate(history):
                week = int(visit.get("time_weeks", i * 4))
                treatment_status = visit.get("treatment_status", {})
                
                # Determine current state
                current_state = determine_patient_state(treatment_status, visit)
                
                # Track state counts
                timeline_data[week][current_state] += 1
                
                # Track transitions
                if current_state != prev_state:
                    transitions[week][prev_state][current_state] += 1
                
                prev_state = current_state
    
    # Fail if no patients had history data
    if patients_with_history == 0:
        raise ValueError(
            "Cannot create streamgraph: No patients with visit history found. "
            "Streamgraph requires detailed patient timeline data."
        )
    
    # Convert to DataFrame
    rows = []
    for week in sorted(timeline_data.keys()):
        for state, count in timeline_data[week].items():
            # Calculate newly transitioned patients
            newly_transitioned = 0
            for from_state, to_states in transitions[week].items():
                if state in to_states:
                    newly_transitioned += to_states[state]
            
            rows.append({
                "time_weeks": week,
                "state": state,
                "count": count,
                "newly_transitioned": newly_transitioned
            })
    
    return pd.DataFrame(rows)


def determine_patient_state(treatment_status: Dict, visit: Dict) -> str:
    """
    Determine patient state based on treatment status and visit data.
    
    Parameters
    ----------
    treatment_status : dict
        Treatment status from visit
    visit : dict
        Visit data
        
    Returns
    -------
    str
        Patient state category
    """
    if not treatment_status.get("active", True):
        reason = treatment_status.get("discontinuation_reason", "")
        
        if treatment_status.get("retreated", False):
            return f"retreated_{reason.lower()}"
        else:
            return f"discontinued_{reason.lower()}"
    
    # For simplified data where we only have phase, not detailed status
    if not treatment_status and 'phase' in visit:
        phase = visit.get('phase', '')
        if 'loading' in phase:
            return "active_loading"
        elif 'maintenance' in phase:
            return "active_maintenance"
        else:
            return "active_standard"
    
    # Active treatment states
    if visit.get("disease_state") == "HIGHLY_ACTIVE":
        return "active_highly_active"
    elif visit.get("disease_state") == "STABLE":
        return "active_stable"
    else:
        return "active_standard"




def create_patient_streamgraph(
    data: pd.DataFrame,
    title: str = "Patient Cohort Flow Over Time",
    figsize: Tuple[int, int] = (12, 8),
    color_scheme: Optional[Dict[str, str]] = None,
    show_transitions: bool = True
) -> Tuple[plt.Figure, plt.Axes]:
    """
    Create a streamgraph showing patient flow through treatment states.
    
    Parameters
    ----------
    data : pd.DataFrame
        Timeline data with columns: time_weeks, state, count, newly_transitioned
    title : str
        Chart title
    figsize : tuple
        Figure size
    color_scheme : dict, optional
        Custom color mapping for states
    show_transitions : bool
        Whether to highlight newly transitioned patients
        
    Returns
    -------
    tuple
        (fig, ax) matplotlib objects
    """
    # Default color scheme
    if color_scheme is None:
        color_scheme = {
            "active": COLORS['primary'],
            "active_stable": SEMANTIC_COLORS['patient_counts'], 
            "active_standard": COLORS['primary'],
            "active_highly_active": SEMANTIC_COLORS['critical_info'],
            
            "discontinued_planned": "#B3A386",  # Muted yellow
            "discontinued_administrative": "#B39086",  # Muted orange
            "discontinued_not_renewed": "#B38690",  # Muted pink
            "discontinued_premature": "#B38686",  # Muted red
            
            "retreated_planned": "#869EB3",  # Muted blue
            "retreated_administrative": "#8690B3",  # Muted purple
            "retreated_not_renewed": "#9086B3",  # Muted violet
            "retreated_premature": "#8686B3",  # Muted indigo
        }
    
    # Pivot data for streamgraph
    pivot_data = data.pivot_table(
        index="time_weeks",
        columns="state", 
        values="count",
        fill_value=0
    )
    
    # Ensure all time points are present
    full_time_range = range(0, int(pivot_data.index.max()) + 1, 4)
    pivot_data = pivot_data.reindex(full_time_range, fill_value=0)
    
    # Order states for visual flow
    state_order = [
        "active_stable",
        "active_standard", 
        "active_highly_active",
        "active",
        
        "discontinued_planned",
        "discontinued_administrative",
        "discontinued_not_renewed",
        "discontinued_premature",
        
        "retreated_planned",
        "retreated_administrative", 
        "retreated_not_renewed",
        "retreated_premature"
    ]
    
    # Filter to only states present in data
    available_states = [s for s in state_order if s in pivot_data.columns]
    pivot_data = pivot_data[available_states]
    
    # Create figure
    fig, ax = plt.subplots(figsize=figsize)
    
    # Convert to numpy array for streamgraph calculation
    data_array = pivot_data.values.T
    times = pivot_data.index.values
    
    # Calculate streamgraph baseline
    streamgraph_data = calculate_streamgraph_baseline(data_array)
    
    # Plot each stream
    for i, (state, stream) in enumerate(zip(available_states, streamgraph_data)):
        color = color_scheme.get(state, COLORS['text_secondary'])
        
        # Main stream
        ax.fill_between(
            times,
            stream[0],  # bottom
            stream[1],  # top
            color=color,
            alpha=0.8,
            label=state.replace("_", " ").title()
        )
        
        # Add transition highlights if requested
        if show_transitions and state in data["state"].values:
            transition_data = data[data["state"] == state]
            for _, row in transition_data.iterrows():
                if row["newly_transitioned"] > 0:
                    week = row["time_weeks"]
                    if week in times:
                        idx = np.where(times == week)[0][0]
                        # Highlight with brighter color
                        highlight_height = row["newly_transitioned"]
                        bottom = stream[0][idx]
                        ax.fill_between(
                            [week - 2, week + 2],
                            [bottom, bottom],
                            [bottom + highlight_height, bottom + highlight_height],
                            color=color,
                            alpha=1.0,
                            edgecolor='white',
                            linewidth=1
                        )
    
    # Styling
    ax.set_xlabel("Time (Months)")
    ax.set_ylabel("Number of Patients")
    ax.set_title(title, fontsize=14, loc="left")
    
    # X-axis formatting (convert weeks to months)
    month_ticks = range(0, int(times.max()) + 1, 13)  # Every 3 months
    month_labels = [f"{int(w/4.33)}" for w in month_ticks]
    ax.set_xticks(month_ticks)
    ax.set_xticklabels(month_labels)
    
    # Remove spines for cleaner look
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    
    # Grid
    ax.grid(axis='y', linestyle=':', alpha=0.3)
    ax.set_axisbelow(True)
    
    # Legend
    handles, labels = ax.get_legend_handles_labels()
    # Group legend items
    legend_groups = {
        "Active": [],
        "Discontinued": [],
        "Retreated": []
    }
    
    for handle, label in zip(handles, labels):
        if label.startswith("Active"):
            legend_groups["Active"].append((handle, label))
        elif label.startswith("Discontinued"):
            legend_groups["Discontinued"].append((handle, label))
        elif label.startswith("Retreated"):
            legend_groups["Retreated"].append((handle, label))
    
    # Create grouped legend
    legend_handles = []
    legend_labels = []
    
    for group_name, items in legend_groups.items():
        if items:
            # Add group header
            legend_handles.append(plt.Line2D([0], [0], color='none'))
            legend_labels.append(f"__{group_name}__")
            # Add items
            for handle, label in items:
                legend_handles.append(handle)
                legend_labels.append(f"  {label}")
    
    ax.legend(
        legend_handles,
        legend_labels,
        loc='center left',
        bbox_to_anchor=(1, 0.5),
        frameon=False
    )
    
    plt.tight_layout()
    return fig, ax


def calculate_streamgraph_baseline(data: np.ndarray) -> List[Tuple[np.ndarray, np.ndarray]]:
    """
    Calculate streamgraph baselines for patient cohort data.
    
    For patient cohort data, we want the baseline to start at 0 since
    we're showing the full cohort size declining over time.
    
    Parameters
    ----------
    data : np.ndarray
        2D array where rows are categories and columns are time points
        
    Returns
    -------
    list
        List of (bottom, top) arrays for each stream
    """
    n_series, n_points = data.shape
    
    # Initialize baselines - start at 0 for patient cohort
    baselines = np.zeros((n_series + 1, n_points))
    
    # Simple stacking - appropriate for cohort data that starts at full size
    streams = []
    for i in range(n_series):
        baselines[i + 1] = baselines[i] + data[i]
        streams.append((baselines[i], baselines[i + 1]))
    
    return streams


def generate_enhanced_discontinuation_streamgraph(results: Dict) -> plt.Figure:
    """
    Generate enhanced streamgraph visualization for simulation results.
    
    Parameters
    ----------
    results : dict
        Simulation results
        
    Returns
    -------
    plt.Figure
        The created figure
        
    Raises
    ------
    ValueError
        If required patient history data is not available
    """
    try:
        # Prepare timeline data - will raise ValueError if data missing
        timeline_data = prepare_cohort_timeline_data(results)
    except ValueError as e:
        # Create an error figure
        fig, ax = plt.subplots(figsize=(12, 8))
        ax.text(0.5, 0.5, str(e), 
                ha='center', va='center', fontsize=12, 
                transform=ax.transAxes, wrap=True)
        ax.set_title("Streamgraph Error", fontsize=14, loc="left")
        ax.axis('off')
        return fig
    
    # Create streamgraph
    fig, ax = create_patient_streamgraph(
        timeline_data,
        title="Patient Cohort Lifecycle: Treatment, Discontinuation, and Retreatment",
        figsize=(12, 8),
        show_transitions=True
    )
    
    # Add annotations for key metrics
    if "discontinuation_counts" in results:
        total_disc = sum(results["discontinuation_counts"].values())
        total_retreat = results.get("recurrences", {}).get("total", 0)
        
        # Add summary text
        summary_text = f"Total Discontinuations: {total_disc}\\nTotal Retreatments: {total_retreat}"
        ax.text(
            0.02, 0.98,
            summary_text,
            transform=ax.transAxes,
            verticalalignment='top',
            fontsize=10,
            bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.8)
        )
    
    return fig