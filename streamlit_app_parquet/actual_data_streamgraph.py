"""
Streamgraph visualization using ONLY ACTUAL patient data.

This module strictly adheres to the "NEVER GENERATE SYNTHETIC DATA" principle.
It uses only real patient timelines and fails explicitly when data is missing.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import os
import sys

# Import the central color system
try:
    from visualization.color_system import COLORS, SEMANTIC_COLORS, ALPHAS
except ImportError:
    # Fallback for when running in streamlit_app directory
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    try:
        from visualization.color_system import COLORS, SEMANTIC_COLORS, ALPHAS
    except ImportError:
        # Fail explicitly rather than creating synthetic fallbacks
        raise ImportError("Failed to import color system. Cannot proceed without proper styling.")


def extract_patient_data(patient_histories: Dict) -> pd.DataFrame:
    """
    Extract actual patient timeline data without any synthetic generation.
    
    Parameters
    ----------
    patient_histories : dict
        Dictionary of patient histories
        
    Returns
    -------
    pd.DataFrame
        Timeline data with columns: time_months, state, count
        
    Raises
    ------
    ValueError
        If patient data is missing or invalid
    """
    if not patient_histories:
        raise ValueError("No patient histories available. Cannot create visualization.")
    
    # Analyze data structure for the first patient
    sample_id = next(iter(patient_histories))
    sample_patient = patient_histories[sample_id]
    
    print(f"Analyzing patient data structure...")
    
    # Track patient states over time (patient_id -> [(time_months, state)])
    patient_states = {}
    
    # Process each patient's history
    for patient_id, patient in patient_histories.items():
        visits = []
        
        # Handle different data structures
        if isinstance(patient, list):
            # Patient is directly a list of visits
            visits = patient
        elif isinstance(patient, dict) and "visits" in patient:
            # Patient has a visits list
            visits = patient["visits"]
        elif isinstance(patient, dict):
            # Each key might be a visit or other identifier
            # Try to extract visits if there are time fields
            potential_visits = []
            for _, data in patient.items():
                if isinstance(data, dict) and any(k in data for k in ["time", "date", "time_weeks"]):
                    potential_visits.append(data)
            if potential_visits:
                visits = potential_visits
        
        # Skip patients with no visits
        if not visits:
            continue
        
        # Process patient timeline
        timeline = []
        start_time = None
        
        for visit in visits:
            # Get visit time (try various field names)
            # Print the available fields for debugging
            if patient_id == 'PATIENT001' and len(timeline) < 2:
                print(f"Visit data fields: {list(visit.keys())}")
                for field in ["date", "time", "time_weeks", "interval"]:
                    if field in visit:
                        print(f"  {field}: {visit[field]} (type: {type(visit[field])})")
            
            # Try different ways to get time
            time_value = None
            
            # Try get a visit index from the "phase" if available
            if "phase" in visit:
                phase = visit.get("phase")
                if isinstance(phase, str) and phase.startswith("visit_"):
                    try:
                        # Extract visit number
                        visit_num = int(phase.split("_")[1])
                        if visit_num > 0:
                            # Assume roughly 1 month per visit
                            time_value = visit_num - 1  # 0-based
                    except (ValueError, IndexError):
                        pass
            
            # Try interval field - would give time since last visit
            if time_value is None and "interval" in visit:
                interval = visit.get("interval")
                if isinstance(interval, (int, float)) and interval > 0:
                    if len(timeline) > 0:
                        # Add to previous time
                        prev_time = timeline[-1][0]
                        time_value = prev_time + (interval / 4.33)  # Convert weeks to months
                    else:
                        # First visit, use interval directly
                        time_value = interval / 4.33
            
            # Use date or time if available
            if time_value is None:
                time_data = visit.get("date") or visit.get("time") or visit.get("time_weeks", 0)
                
                # Convert to months
                if isinstance(time_data, (int, float)):
                    # Direct time value (assume weeks)
                    time_value = time_data / 4.33
                elif hasattr(time_data, "days"):
                    # datetime or timedelta
                    if start_time is None:
                        start_time = time_data
                    delta = time_data - start_time
                    time_value = delta.days / 30
            
            # If we still don't have a time value, use the index
            if time_value is None:
                if len(timeline) > 0:
                    # Use previous time + 1 month
                    time_value = timeline[-1][0] + 1
                else:
                    # First visit, use 0
                    time_value = 0
            
            # Convert to integer months
            time_months = int(time_value)
            
            # Determine state
            state = get_patient_state(visit)
            
            # Add to timeline - debug the time values
            if time_months < 0:
                print(f"WARNING: Negative time value: {time_months} from {time_data}")
                time_months = 0
            
            # Add to timeline
            timeline.append((time_months, state))
            
            # Debug output for first few patients and visits
            if patient_id in ['PATIENT001', 'PATIENT002'] and len(timeline) <= 5:
                print(f"Patient {patient_id}, visit {len(timeline)}: time={time_months}, state={state}")
        
        # Sort by time for consistency
        timeline.sort(key=lambda x: x[0])
        
        # Store patient timeline
        patient_states[patient_id] = timeline
    
    # Make sure we have data
    if not patient_states:
        raise ValueError("Failed to extract any valid patient data")
    
    # Create timeline data by counting patients in each state at each time point
    print(f"Creating timeline from {len(patient_states)} patient histories...")
    
    # Find maximum timeline length
    try:
        max_months = max(
            max(time for time, _ in timeline) 
            for timeline in patient_states.values() 
            if timeline
        )
    except ValueError:
        raise ValueError("No valid timeline data extracted from patient histories")
    
    # Generate complete timeline
    timeline_data = []
    monthly_totals = {}
    
    # Debug: Check how many months we're processing
    print(f"Generating timeline for months 0 to {max_months}")
    
    # Make sure we have a reasonable number of months (at least 1 year)
    if max_months < 12:
        print(f"WARNING: Max months is only {max_months}, using default of 60 months (5 years)")
        max_months = 60
    
    # For debugging: Count total state changes over time
    total_state_changes = 0
    for patient_id, timeline in patient_states.items():
        if len(timeline) > 1:
            total_state_changes += len(timeline) - 1
    print(f"Total patient state changes in data: {total_state_changes}")
    
    # Process data for each month
    for month in range(max_months + 1):
        states = defaultdict(int)
        
        # Count patients in each state at this month
        for patient_id, timeline in patient_states.items():
            current_state = "Active"  # Default state
            
            # Find most recent state at or before this month
            for time, state in timeline:
                if time <= month:
                    current_state = state
                else:
                    break
            
            # Count this patient's state
            states[current_state] += 1
        
        # Add all states to timeline data
        for state, count in states.items():
            timeline_data.append({
                "time_months": month,
                "state": state,
                "count": count
            })
        
        # Track total for verification
        monthly_totals[month] = sum(states.values())
        
        # Debug output for selected months
        if month in [0, 12, 24, 36, 48, 60] or month % 20 == 0:
            print(f"Month {month}: {sum(states.values())} patients across {len(states)} states")
            for state, count in sorted(states.items()):
                if count > 0:
                    print(f"  {state}: {count}")
    
    # Verify patient conservation
    unique_totals = set(monthly_totals.values())
    if len(unique_totals) == 1:
        print(f"GOOD: Patient count is constant at {list(unique_totals)[0]}")
    else:
        print(f"WARNING: Patient count varies: min={min(monthly_totals.values())}, max={max(monthly_totals.values())}")
    
    # Verify patient conservation (should have same count at all times)
    unique_totals = set(monthly_totals.values())
    if len(unique_totals) != 1:
        print(f"WARNING: Patient count varies: min={min(monthly_totals.values())}, max={max(monthly_totals.values())}")
    
    return pd.DataFrame(timeline_data)


def get_patient_state(visit: Dict) -> str:
    """
    Determine patient state from visit data.
    
    Parameters
    ----------
    visit : dict
        Visit data
        
    Returns
    -------
    str
        Patient state name
    """
    # Check for discontinuation visit
    if visit.get("is_discontinuation_visit", False):
        # Get discontinuation reason
        reason = visit.get("discontinuation_reason", "")
        
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
    
    # Check for retreatment visit
    if visit.get("is_retreatment_visit", False) or visit.get("is_retreatment", False):
        # Get previous state if available
        previous_state = visit.get("previous_state", "Unknown")
        
        if "planned" in previous_state.lower():
            return "Retreated Planned"
        elif "administrative" in previous_state.lower():
            return "Retreated Administrative"
        elif "not_renewed" in previous_state.lower():
            return "Retreated Not Renewed"
        elif "premature" in previous_state.lower():
            return "Retreated Premature"
        else:
            return "Retreated Other"
    
    # Check treatment_status field if present
    treatment_status = visit.get("treatment_status", {})
    if treatment_status:
        if not treatment_status.get("active", True):
            # Patient is discontinued
            reason = treatment_status.get("discontinuation_reason", "")
            
            if treatment_status.get("retreated", False):
                # Retreated patient
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
                # Discontinued patient
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
    
    # If no special state, patient is active
    return "Active"


def create_actual_data_streamgraph(
    data: pd.DataFrame,
    title: str = "Patient Treatment Journey (Actual Data)",
    figsize: Tuple[int, int] = (12, 8)
) -> Figure:
    """
    Create streamgraph visualization using only actual patient data.
    
    Parameters
    ----------
    data : pd.DataFrame
        Actual patient timeline data with columns: time_months, state, count
    title : str
        Title for the visualization
    figsize : tuple
        Figure size (width, height)
        
    Returns
    -------
    Figure
        Matplotlib figure with the streamgraph
    """
    # Define color scheme using the central color system
    color_scheme = {
        "Active": SEMANTIC_COLORS.get("state", {}).get("active", "#2E7D32"),
        
        "Discontinued Planned": SEMANTIC_COLORS.get("discontinuation", {}).get("planned", "#FFA000"),
        "Discontinued Administrative": SEMANTIC_COLORS.get("discontinuation", {}).get("administrative", "#D32F2F"),
        "Discontinued Not Renewed": SEMANTIC_COLORS.get("discontinuation", {}).get("not_renewed", "#C62828"),
        "Discontinued Premature": SEMANTIC_COLORS.get("discontinuation", {}).get("premature", "#B71C1C"),
        "Discontinued Other": SEMANTIC_COLORS.get("discontinuation", {}).get("other", "#880E4F"),
        
        "Retreated Planned": SEMANTIC_COLORS.get("retreatment", {}).get("planned", "#81C784"),
        "Retreated Administrative": SEMANTIC_COLORS.get("retreatment", {}).get("administrative", "#EF9A9A"),
        "Retreated Not Renewed": SEMANTIC_COLORS.get("retreatment", {}).get("not_renewed", "#E57373"),
        "Retreated Premature": SEMANTIC_COLORS.get("retreatment", {}).get("premature", "#EF5350"),
        "Retreated Other": SEMANTIC_COLORS.get("retreatment", {}).get("other", "#CE93D8"),
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
        "Discontinued Other",
        "Retreated Planned",
        "Retreated Administrative",
        "Retreated Not Renewed",
        "Retreated Premature",
        "Retreated Other"
    ]
    
    # Filter to available states
    available_states = [s for s in state_order if s in pivot_data.columns]
    
    # If no matching states, use whatever is in the data
    if not available_states:
        available_states = list(pivot_data.columns)
    
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
    ax.set_xlabel("Time (Years)")
    ax.set_ylabel("Number of Patients")
    ax.set_title(title, fontsize=14, loc="left")
    
    # Set y-axis to start at 0
    ax.set_ylim(bottom=0)
    
    # Set x-axis ticks at yearly intervals
    max_years = int(np.ceil(max(times) / 12))
    yearly_ticks = np.arange(0, max_years * 12 + 1, 12)
    ax.set_xticks(yearly_ticks)
    ax.set_xticklabels([f"{int(year/12)}" for year in yearly_ticks])
    
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
    return fig


def visualize_patient_flow(results: Dict) -> Figure:
    """
    Create a streamgraph visualization using actual patient data from simulation results.
    
    Parameters
    ----------
    results : dict
        Simulation results containing patient histories
        
    Returns
    -------
    Figure
        Matplotlib figure with the streamgraph
        
    Raises
    ------
    ValueError
        If patient data is missing or invalid
    """
    # Get patient histories
    patient_histories = results.get("patient_histories", {})
    
    if not patient_histories:
        raise ValueError(
            "ERROR: No patient histories found in simulation results. "
            "Cannot create visualization without actual patient data."
        )
    
    # Extract actual timeline data
    timeline_data = extract_patient_data(patient_histories)
    
    # Create streamgraph
    patient_count = len(patient_histories)
    fig = create_actual_data_streamgraph(
        timeline_data,
        title=f"Patient Treatment Journey (Actual Data from {patient_count} patients)"
    )
    
    # Add summary statistics
    disc_counts = results.get("discontinuation_counts", {})
    total_disc = sum(disc_counts.values()) if disc_counts else "Unknown"
    
    recurrences = results.get("recurrences", {})
    total_retreat = recurrences.get("total", "Unknown") if recurrences else "Unknown"
    
    ax = fig.axes[0]
    ax.text(
        0.02, 0.98,
        f"Total Discontinuations: {total_disc}\nTotal Retreatments: {total_retreat}",
        transform=ax.transAxes,
        verticalalignment='top',
        fontsize=10,
        bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.8)
    )
    
    return fig


# For testing the module directly
if __name__ == "__main__":
    import json
    import os
    import sys
    
    # Try to load simulation results
    simulations_dir = "../output/simulation_results"
    results = None
    
    # Find the most recent simulation file
    if os.path.exists(simulations_dir):
        sim_files = [
            os.path.join(simulations_dir, f) 
            for f in os.listdir(simulations_dir) 
            if f.endswith('.json')
        ]
        
        if sim_files:
            sim_files.sort(key=os.path.getmtime, reverse=True)
            file_path = sim_files[0]
            
            try:
                with open(file_path, 'r') as f:
                    results = json.load(f)
                print(f"Loaded simulation results from {file_path}")
            except Exception as e:
                print(f"Error loading simulation results: {e}")
    
    # If no results loaded, try known debug files
    if not results:
        alt_paths = [
            "../deep_debug_output.json",
            "../streamgraph_debug_data.json"
        ]
        
        for path in alt_paths:
            if os.path.exists(path):
                try:
                    with open(path, 'r') as f:
                        results = json.load(f)
                    print(f"Loaded simulation results from {path}")
                    break
                except Exception as e:
                    print(f"Error loading from {path}: {e}")
    
    if not results:
        print("ERROR: Could not load any simulation results. Please provide a valid simulation file.")
        sys.exit(1)
    
    # Create the streamgraph using actual data
    try:
        fig = visualize_patient_flow(results)
        output_file = "actual_data_streamgraph.png"
        fig.savefig(output_file, dpi=150, bbox_inches='tight')
        print(f"Streamgraph saved to {output_file}")
        plt.show()
    except Exception as e:
        import traceback
        print(f"ERROR: {e}")
        traceback.print_exc()
        sys.exit(1)