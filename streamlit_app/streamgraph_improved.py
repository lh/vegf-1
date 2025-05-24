"""
Improved streamgraph implementation for Streamlit integration.

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
import streamlit as st
import json
import os

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


def parse_time_format(time_value):
    """Parse different time formats into a standard format."""
    if isinstance(time_value, (int, float)):
        return time_value
    
    if isinstance(time_value, str):
        # Try different datetime formats
        formats = [
            "%Y-%m-%d",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%S.%f",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%dT%H:%M:%S.%fZ"
        ]
        
        for fmt in formats:
            try:
                dt = datetime.strptime(time_value, fmt)
                # Return timestamp in days
                return dt.timestamp() / (24 * 3600)
            except ValueError:
                continue
    
    # If we can't parse it, return the original value
    return time_value


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
    elif isinstance(time_value, str):
        # Try to parse string time
        parsed = parse_time_format(time_value)
        if isinstance(parsed, (int, float)):
            return int(parsed / 30)
        return 0
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
        try:
            # First ensure time values are parseable
            for visit in visits:
                if "time" in visit and isinstance(visit["time"], str):
                    parsed_time = parse_time_format(visit["time"])
                    if isinstance(parsed_time, (int, float)):
                        visit["time"] = parsed_time
                elif "date" in visit and isinstance(visit["date"], str):
                    parsed_time = parse_time_format(visit["date"])
                    if isinstance(parsed_time, (int, float)):
                        visit["date"] = parsed_time
            
            # Now sort by time
            sorted_visits = sorted(visits, key=lambda v: v.get("time", v.get("date", 0)))
        except Exception as e:
            # If sorting fails, just use the original order
            logger.warning(f"Failed to sort visits for patient {patient_id}: {e}")
            sorted_visits = visits
        
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


def fix_time_values(patient_histories):
    """Fix time values in the patient histories."""
    fixed_histories = {}
    
    for patient_id, visits in patient_histories.items():
        fixed_visits = []
        
        for visit in visits:
            # Create a copy of the visit
            fixed_visit = visit.copy()
            
            # Fix time value
            time_value = visit.get("time", visit.get("date"))
            if time_value is not None and isinstance(time_value, str):
                parsed_time = parse_time_format(time_value)
                if parsed_time is not None:
                    fixed_visit["time"] = parsed_time
            
            fixed_visits.append(fixed_visit)
        
        fixed_histories[patient_id] = fixed_visits
    
    return fixed_histories


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
    
    # Fix time values if needed
    fixed_histories = fix_time_values(patient_histories)
    results["patient_histories"] = fixed_histories
    
    # Get simulation duration with validation
    duration_years = results.get("duration_years", 5)
    duration_months = int(duration_years * 12)
    
    # Extract patient states
    patient_states_df = extract_patient_states(fixed_histories)
    
    # Aggregate by month
    monthly_counts = aggregate_states_by_month(patient_states_df, duration_months)
    
    # Create the visualization
    fig = plot_streamgraph(monthly_counts)
    
    logger.info("Streamgraph visualization created successfully")
    return fig


def create_streamlit_visualization(results, show_data=False):
    """Create visualization for Streamlit with optional data debugging.
    
    Args:
        results: Simulation results dictionary
        show_data: Whether to show data tables for debugging
        
    Returns:
        None - directly renders to Streamlit
    """
    # Add a spinner during processing
    with st.spinner("Generating patient state visualization..."):
        try:
            # Extract patient histories
            patient_histories = results.get("patient_histories", {})
            if not patient_histories:
                st.error("No patient history data found in results. Cannot create visualization.")
                return
            
            # Fix time values if needed
            fixed_histories = fix_time_values(patient_histories)
            results["patient_histories"] = fixed_histories
            
            # Get simulation duration
            duration_years = results.get("duration_years", 5)
            duration_months = int(duration_years * 12)
            
            # Extract and aggregate data
            patient_states_df = extract_patient_states(fixed_histories)
            monthly_counts = aggregate_states_by_month(patient_states_df, duration_months)
            
            # Create the visualization
            fig = plot_streamgraph(monthly_counts)
            
            # Display the figure
            st.pyplot(fig)
            
            # Show data tables if requested (for debugging)
            if show_data:
                with st.expander("View State Data"):
                    # Create pivot table for easy viewing
                    pivot = monthly_counts.pivot(
                        index='time_months',
                        columns='state',
                        values='count'
                    ).fillna(0)
                    
                    # Add total column to verify conservation
                    pivot['Total'] = pivot.sum(axis=1)
                    
                    # Show the data
                    st.dataframe(pivot)
                    
                    # Check conservation
                    conservation_ok = pivot['Total'].nunique() == 1
                    if conservation_ok:
                        st.success(f"Population conservation verified: {pivot['Total'].iloc[0]} patients tracked consistently")
                    else:
                        st.error(f"Population conservation issue: Patient counts vary from {pivot['Total'].min()} to {pivot['Total'].max()}")
                    
                    # Show discontinuation statistics
                    st.subheader("Discontinuation Statistics")
                    disc_stats = {}
                    for state in PATIENT_STATES:
                        if state.startswith("discontinued"):
                            # Get max count for this state
                            max_count = pivot[state].max()
                            disc_stats[STATE_DISPLAY_NAMES.get(state, state)] = max_count
                    
                    stats_df = pd.DataFrame([disc_stats]).T.reset_index()
                    stats_df.columns = ["Discontinuation Type", "Count"]
                    st.dataframe(stats_df.sort_values("Count", ascending=False))
        
        except Exception as e:
            st.error(f"Error creating visualization: {str(e)}")
            import traceback
            st.exception(e)


# Function to debug time parsing issues
def analyze_time_formats(results):
    """Analyze and fix time formats in simulation results."""
    st.subheader("Time Format Analysis")
    
    patient_histories = results.get("patient_histories", {})
    if not patient_histories:
        st.error("No patient histories found in the data.")
        return
    
    # Analyze time formats
    time_formats = {}
    datetime_formats = {}
    
    # Sample patients
    sample_size = min(5, len(patient_histories))
    sample_patients = list(patient_histories.keys())[:sample_size]
    
    for patient_id in sample_patients:
        visits = patient_histories[patient_id]
        if not visits:
            continue
        
        # Look at first few visits
        sample_visits = visits[:min(5, len(visits))]
        for visit in sample_visits:
            time_value = visit.get("time", visit.get("date"))
            if time_value is not None:
                time_type = type(time_value).__name__
                if time_type not in time_formats:
                    time_formats[time_type] = []
                
                if time_type == 'str' and time_value not in time_formats[time_type]:
                    time_formats[time_type].append(time_value)
                    
                    # Try to figure out the format
                    for fmt in [
                        "%Y-%m-%d",
                        "%Y-%m-%dT%H:%M:%S",
                        "%Y-%m-%dT%H:%M:%S.%f",
                        "%Y-%m-%dT%H:%M:%SZ",
                        "%Y-%m-%dT%H:%M:%S.%fZ"
                    ]:
                        try:
                            datetime.strptime(time_value, fmt)
                            datetime_formats[time_value] = fmt
                            break
                        except ValueError:
                            continue
    
    # Display findings
    st.write("Time format types found:")
    for fmt, examples in time_formats.items():
        st.write(f"- {fmt}: {examples[:3]}")
    
    if datetime_formats:
        st.write("Detected datetime formats:")
        for example, fmt in datetime_formats.items():
            st.write(f"- {example}: {fmt}")
    
    # Test parsing a few values
    if 'str' in time_formats and time_formats['str']:
        st.subheader("Time Parsing Test")
        for example in time_formats['str'][:3]:
            parsed = parse_time_format(example)
            st.write(f"{example} → {parsed}")


# Entry point for standalone testing
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Test streamgraph visualization')
    parser.add_argument('--file', help='Input simulation results file')
    parser.add_argument('--output', help='Output visualization file')
    args = parser.parse_args()
    
    # Load data
    if args.file and os.path.exists(args.file):
        try:
            with open(args.file, 'r') as f:
                data = json.load(f)
            logger.info(f"Loaded data from {args.file}")
        except Exception as e:
            logger.error(f"Error loading file: {e}")
            data = {"patient_histories": {}, "duration_years": 5}
    else:
        # Generate test data
        logger.info("No input file. Generating test data...")
        data = {
            "patient_histories": {},
            "duration_years": 5
        }
        
        # Create 10 test patients
        for i in range(10):
            patient_id = f"P{i+1:03d}"
            
            if i % 3 == 0:
                # Never discontinued
                visits = [
                    {"time": j*30, "is_discontinuation_visit": False} 
                    for j in range(60)
                ]
            elif i % 3 == 1:
                # Planned discontinuation
                visits = [
                    {"time": j*30, "is_discontinuation_visit": False} 
                    for j in range(20)
                ]
                visits.append({
                    "time": 600, 
                    "is_discontinuation_visit": True,
                    "discontinuation_reason": "stable_max_interval"
                })
            else:
                # Premature discontinuation with retreatment
                visits = [
                    {"time": j*30, "is_discontinuation_visit": False} 
                    for j in range(10)
                ]
                visits.append({
                    "time": 300, 
                    "is_discontinuation_visit": True,
                    "discontinuation_reason": "premature"
                })
                visits.append({
                    "time": 450,
                    "is_retreatment_visit": True
                })
            
            data["patient_histories"][patient_id] = visits
    
    # Create visualization
    fig = create_streamgraph(data)
    
    # Save or show
    if args.output:
        fig.savefig(args.output, dpi=100, bbox_inches="tight")
        logger.info(f"Saved visualization to {args.output}")
    else:
        plt.show()