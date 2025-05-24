"""
Fixed streamgraph implementation for patient state visualization.

This module provides a robust implementation of patient state tracking over time,
ensuring proper data handling, time conversion, and population conservation.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List, Tuple, Any, Optional, Union
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Define all possible patient states
PATIENT_STATES = [
    # Active states
    "active",  # Never discontinued
    "active_retreated_from_stable_max_interval",
    "active_retreated_from_random_administrative", 
    "active_retreated_from_course_complete",
    "active_retreated_from_premature",
    
    # Discontinued states
    "discontinued_stable_max_interval",
    "discontinued_random_administrative",
    "discontinued_course_complete_but_not_renewed",
    "discontinued_premature"
]

# Color scheme for visualization
STATE_COLORS = {
    # Active states - shades of green
    "active": "#2E7D32",  # Dark green for never discontinued
    "active_retreated_from_stable_max_interval": "#66BB6A",  # Medium green
    "active_retreated_from_random_administrative": "#81C784",  # Light green
    "active_retreated_from_course_complete": "#A5D6A7",  # Lighter green
    "active_retreated_from_premature": "#C8E6C9",  # Lightest green
    
    # Discontinued states - traffic light colors
    "discontinued_stable_max_interval": "#FFA500",  # Amber (planned)
    "discontinued_random_administrative": "#DC143C",  # Red
    "discontinued_course_complete_but_not_renewed": "#B22222",  # Dark red
    "discontinued_premature": "#8B0000"  # Darkest red
}

# Display names for legend
STATE_DISPLAY_NAMES = {
    "active": "Active (Never Discontinued)",
    "active_retreated_from_stable_max_interval": "Active (Retreated from Planned)",
    "active_retreated_from_random_administrative": "Active (Retreated from Admin)",
    "active_retreated_from_course_complete": "Active (Retreated from Course Complete)",
    "active_retreated_from_premature": "Active (Retreated from Premature)",
    "discontinued_stable_max_interval": "Discontinued (Planned)",
    "discontinued_random_administrative": "Discontinued (Administrative)",
    "discontinued_course_complete_but_not_renewed": "Discontinued (Course Complete)",
    "discontinued_premature": "Discontinued (Premature)"
}


def normalize_time(time_value) -> int:
    """Normalize time values to months regardless of input format.
    
    Args:
        time_value: Time value which could be int, float, datetime, or timedelta
        
    Returns:
        int: Time in months (rounded down)
    """
    if isinstance(time_value, (datetime, pd.Timestamp)):
        # Can't convert directly - this needs reference date at aggregation
        return time_value
    elif isinstance(time_value, timedelta):
        return int(time_value.days / 30)
    elif isinstance(time_value, (int, float)):
        return int(time_value / 30)
    else:
        # Fallback
        logger.warning(f"Unknown time format: {type(time_value)} - defaulting to 0")
        return 0


def extract_patient_states(patient_histories: Dict) -> pd.DataFrame:
    """Extract patient states at each time point from simulation results.
    
    Args:
        patient_histories: Dict mapping patient_id to list of visits
        
    Returns:
        DataFrame with columns: patient_id, time_months, state
    """
    logger.info("Extracting patient states from visit histories")
    
    # Validate input
    if not patient_histories:
        logger.error("Empty patient histories provided")
        return pd.DataFrame(columns=["patient_id", "time_months", "state", "visit_time"])
    
    patient_states = []
    patients_processed = 0
    
    # Track statistics for verification
    discontinuation_counter = defaultdict(int)
    retreatment_counter = defaultdict(int)
    
    for patient_id, visits in patient_histories.items():
        # Skip empty visit lists
        if not visits:
            logger.warning(f"Patient {patient_id} has no visits")
            continue
        
        # Track patient's discontinuation history
        current_state = "active"
        last_discontinuation_type = None
        
        # Sort visits by time for consistent processing
        sorted_visits = sorted(visits, key=lambda v: v.get("time", v.get("date", 0)))
        
        for visit in sorted_visits:
            # Get visit time in months (keeping original for datetime handling)
            visit_time = visit.get("time", visit.get("date", 0))
            months = normalize_time(visit_time)
            
            # Check for discontinuation
            if visit.get("is_discontinuation_visit", False):
                # Get discontinuation type
                disc_type = visit.get("discontinuation_reason", "")
                discontinuation_counter[disc_type] += 1
                
                # Map to our state names
                if disc_type == "stable_max_interval":
                    current_state = "discontinued_stable_max_interval"
                    last_discontinuation_type = "stable_max_interval"
                elif disc_type == "random_administrative":
                    current_state = "discontinued_random_administrative"
                    last_discontinuation_type = "random_administrative"
                elif disc_type == "course_complete_but_not_renewed":
                    current_state = "discontinued_course_complete_but_not_renewed"
                    last_discontinuation_type = "course_complete"
                elif disc_type == "premature":
                    current_state = "discontinued_premature"
                    last_discontinuation_type = "premature"
                else:
                    # Default fallback - log for investigation
                    logger.warning(f"Unknown discontinuation reason: {disc_type} for patient {patient_id}")
                    current_state = "discontinued_premature"  # Default fallback
                    last_discontinuation_type = "premature"
            
            # Check for retreatment
            elif visit.get("is_retreatment_visit", False):
                retreatment_counter[last_discontinuation_type or "unknown"] += 1
                
                # Set state based on what they're returning FROM
                if last_discontinuation_type == "stable_max_interval":
                    current_state = "active_retreated_from_stable_max_interval"
                elif last_discontinuation_type == "random_administrative":
                    current_state = "active_retreated_from_random_administrative"
                elif last_discontinuation_type == "course_complete":
                    current_state = "active_retreated_from_course_complete"
                elif last_discontinuation_type == "premature":
                    current_state = "active_retreated_from_premature"
                else:
                    # Shouldn't happen, but fallback
                    logger.warning(f"Retreatment without prior discontinuation for patient {patient_id}")
                    current_state = "active"
            
            # Record state at this time
            patient_states.append({
                "patient_id": patient_id,
                "time_months": months,
                "state": current_state,
                "visit_time": visit_time  # Keep original for datetime handling
            })
        
        patients_processed += 1
    
    logger.info(f"Processed {patients_processed} patients")
    logger.info(f"Discontinuations by type: {dict(discontinuation_counter)}")
    logger.info(f"Retreatments by prior discontinuation: {dict(retreatment_counter)}")
    
    return pd.DataFrame(patient_states)


def aggregate_states_by_month(patient_states_df: pd.DataFrame, 
                            duration_months: int) -> pd.DataFrame:
    """Aggregate patient states by month for streamgraph.
    
    Args:
        patient_states_df: DataFrame with patient states
        duration_months: Total simulation duration in months
        
    Returns:
        DataFrame with columns: time_months, state, count
    """
    logger.info(f"Aggregating patient states by month over {duration_months} months")
    
    # Handle empty input
    if patient_states_df.empty:
        logger.warning("Empty patient states dataframe provided")
        empty_result = []
        for month in range(duration_months + 1):
            for state in PATIENT_STATES:
                empty_result.append({
                    "time_months": month,
                    "state": state,
                    "count": 0
                })
        return pd.DataFrame(empty_result)
    
    # Normalize time to ensure consistent months
    if 'time_months' not in patient_states_df.columns or patient_states_df['time_months'].dtype == 'object':
        logger.info("Converting time values to months")
        # Check if we have datetime objects in visit_time
        if 'visit_time' in patient_states_df.columns:
            sample = patient_states_df['visit_time'].iloc[0]
            if isinstance(sample, (datetime, pd.Timestamp)):
                logger.info("Converting datetime values to months")
                # Find earliest date as reference
                min_date = patient_states_df['visit_time'].min()
                # Convert to months from start
                patient_states_df['time_months'] = patient_states_df['visit_time'].apply(
                    lambda x: int((x - min_date).days / 30)
                )
            else:
                # Use visit_time directly if it's already numeric
                logger.info("Using numeric time values")
                patient_states_df['time_months'] = pd.to_numeric(
                    patient_states_df['visit_time'], errors='coerce'
                ).fillna(0).astype(int)
    
    # Ensure time_months is integer type for comparison
    patient_states_df['time_months'] = patient_states_df['time_months'].astype(int)
    
    # Get unique patient IDs for tracking
    unique_patients = patient_states_df['patient_id'].unique()
    total_patients = len(unique_patients)
    logger.info(f"Found {total_patients} unique patients for aggregation")
    
    # For each month, determine each patient's state
    monthly_counts = []
    
    for month in range(duration_months + 1):
        # Track each patient's state at this month
        patient_states_at_month = {}
        
        for patient_id in unique_patients:
            patient_data = patient_states_df[patient_states_df['patient_id'] == patient_id]
            
            # Get all states up to this month
            states_before_month = patient_data[patient_data['time_months'] <= month]
            
            if not states_before_month.empty:
                # Take the most recent state
                latest_state = states_before_month.iloc[-1]['state']
                patient_states_at_month[patient_id] = latest_state
            else:
                # Patient hasn't started yet or no data
                patient_states_at_month[patient_id] = "active"
        
        # Count states with validation
        state_counts = defaultdict(int)
        for state in patient_states_at_month.values():
            state_counts[state] += 1
        
        # Ensure all states are represented (even with zero counts)
        for state in PATIENT_STATES:
            monthly_counts.append({
                "time_months": month,
                "state": state,
                "count": state_counts[state]
            })
        
        # Conservation check for this month
        month_total = sum(state_counts.values())
        if month_total != total_patients:
            logger.warning(f"Population not conserved at month {month}: "
                          f"Expected {total_patients}, got {month_total}")
    
    # Create output DataFrame
    result_df = pd.DataFrame(monthly_counts)
    
    # Verify overall conservation
    conservation_check = result_df.groupby('time_months')['count'].sum().nunique() == 1
    if conservation_check:
        logger.info("Population conservation verified across all time points")
    else:
        logger.warning("Population conservation violated - check aggregation logic")
    
    return result_df


def create_streamgraph(results: Dict) -> plt.Figure:
    """Create streamgraph visualization of patient states over time.
    
    Args:
        results: Simulation results dictionary
        
    Returns:
        Matplotlib figure
    """
    logger.info("Creating patient state streamgraph")
    
    # Extract patient histories with validation
    patient_histories = results.get("patient_histories", {})
    if not patient_histories:
        logger.error("No patient history data in results")
        # Create an empty visualization
        fig, ax = plt.subplots(figsize=(14, 8))
        ax.text(0.5, 0.5, "No patient data available", 
               ha='center', va='center', fontsize=14)
        return fig
    
    # Get simulation duration with validation
    duration_years = results.get("duration_years", 5)
    duration_months = int(duration_years * 12)
    
    # Extract patient states
    patient_states_df = extract_patient_states(patient_histories)
    
    # Aggregate by month
    monthly_counts = aggregate_states_by_month(patient_states_df, duration_months)
    
    # Create the visualization
    fig = plot_streamgraph(monthly_counts)
    
    logger.info("Streamgraph visualization created successfully")
    return fig


def plot_streamgraph(monthly_counts: pd.DataFrame) -> plt.Figure:
    """Plot the streamgraph using the monthly counts data.
    
    Args:
        monthly_counts: DataFrame with time_months, state, count columns
        
    Returns:
        Matplotlib figure
    """
    # Pivot data for stacking
    pivot_data = monthly_counts.pivot(
        index='time_months',
        columns='state',
        values='count'
    ).fillna(0)
    
    # Create figure
    fig, ax = plt.subplots(figsize=(14, 8))
    
    # Create stacked area plot
    x = pivot_data.index
    bottom = np.zeros(len(x))
    
    # Track which states are actually present (for legend)
    used_states = []
    
    # Plot in the order we defined (ensures consistent stack order)
    for state in PATIENT_STATES:
        if state in pivot_data.columns:
            values = pivot_data[state].values
            # Only include in plot if this state has non-zero values
            if np.any(values > 0):
                color = STATE_COLORS.get(state, "#808080")
                label = STATE_DISPLAY_NAMES.get(state, state)
                
                ax.fill_between(x, bottom, bottom + values, 
                              label=label,
                              color=color, 
                              alpha=0.8)
                bottom += values
                used_states.append(state)
    
    # Add total line to emphasize population conservation
    ax.plot(x, bottom, color='black', linewidth=2, 
            label='Total Population', linestyle='--', alpha=0.7)
    
    # Customize plot
    ax.set_xlabel('Time (months)', fontsize=12)
    ax.set_ylabel('Number of Patients', fontsize=12)
    ax.set_title('Patient Treatment Status Over Time', fontsize=16, fontweight='bold')
    
    # Set x-axis ticks at yearly intervals
    max_months = int(max(x))
    ax.set_xticks(range(0, max_months + 1, 12))
    ax.set_xticklabels([f'{y}' for y in range(0, (max_months // 12) + 1)])
    ax.set_xlabel('Time (years)', fontsize=12)
    
    # Grid and styling
    ax.grid(True, axis='y', alpha=0.3)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    # Only include states that are actually present in the legend
    handles, labels = ax.get_legend_handles_labels()
    filtered_handles = []
    filtered_labels = []
    
    for handle, label in zip(handles, labels):
        if label in [STATE_DISPLAY_NAMES.get(state, state) for state in used_states] or label == 'Total Population':
            filtered_handles.append(handle)
            filtered_labels.append(label)
    
    # Legend with filtered states
    ax.legend(
        filtered_handles, filtered_labels,
        bbox_to_anchor=(1.05, 1), 
        loc='upper left',
        frameon=False, 
        fontsize=10
    )
    
    plt.tight_layout()
    return fig


def test_with_sample_data():
    """Test the streamgraph with sample data."""
    # Generate simple test data
    patient_histories = {}
    
    # Create 10 test patients with different pathways
    for i in range(10):
        patient_id = f"P{i+1:03d}"
        
        # Create different patient pathways
        if i % 5 == 0:
            # No discontinuation
            visits = [
                {"time": j*30, "is_discontinuation_visit": False} 
                for j in range(60)
            ]
        elif i % 5 == 1:
            # Planned discontinuation, no retreatment
            visits = [
                {"time": j*30, "is_discontinuation_visit": False} 
                for j in range(20)
            ]
            visits.append({
                "time": 600, 
                "is_discontinuation_visit": True,
                "discontinuation_reason": "stable_max_interval"
            })
            visits.extend([
                {"time": 600 + j*30, "is_discontinuation_visit": False} 
                for j in range(1, 40)
            ])
        elif i % 5 == 2:
            # Planned discontinuation with retreatment
            visits = [
                {"time": j*30, "is_discontinuation_visit": False} 
                for j in range(15)
            ]
            visits.append({
                "time": 450, 
                "is_discontinuation_visit": True,
                "discontinuation_reason": "stable_max_interval"
            })
            visits.extend([
                {"time": 450 + j*30, "is_discontinuation_visit": False} 
                for j in range(1, 10)
            ])
            visits.append({
                "time": 750,
                "is_retreatment_visit": True
            })
            visits.extend([
                {"time": 750 + j*30, "is_discontinuation_visit": False} 
                for j in range(1, 30)
            ])
        elif i % 5 == 3:
            # Random administrative discontinuation
            visits = [
                {"time": j*30, "is_discontinuation_visit": False} 
                for j in range(10)
            ]
            visits.append({
                "time": 300, 
                "is_discontinuation_visit": True,
                "discontinuation_reason": "random_administrative"
            })
            # No visits after administrative discontinuation
        else:
            # Premature discontinuation with retreatment
            visits = [
                {"time": j*30, "is_discontinuation_visit": False} 
                for j in range(5)
            ]
            visits.append({
                "time": 150, 
                "is_discontinuation_visit": True,
                "discontinuation_reason": "premature"
            })
            visits.extend([
                {"time": 150 + j*30, "is_discontinuation_visit": False} 
                for j in range(1, 5)
            ])
            visits.append({
                "time": 300,
                "is_retreatment_visit": True
            })
            visits.extend([
                {"time": 300 + j*30, "is_discontinuation_visit": False} 
                for j in range(1, 50)
            ])
        
        patient_histories[patient_id] = visits
    
    # Create test results
    results = {
        "patient_histories": patient_histories,
        "duration_years": 5
    }
    
    # Generate visualization
    fig = create_streamgraph(results)
    return fig


if __name__ == "__main__":
    # Test the implementation with sample data
    fig = test_with_sample_data()
    
    # Show or save the figure
    plt.savefig("streamgraph_test.png", dpi=100, bbox_inches="tight")
    plt.show()
    
    print("Streamgraph test complete. Check streamgraph_test.png for the result.")