"""
Standalone script to debug and fix streamgraph visualization.

This script loads saved simulation results and tests the visualization
without requiring Streamlit or running a new simulation.
"""

import json
import os
import sys
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List, Tuple

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

def load_simulation_results(file_path):
    """Load simulation results from JSON file."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading simulation results: {e}")
        return None


def extract_patient_states(patient_histories: Dict) -> pd.DataFrame:
    """
    Extract patient states at each time point from simulation results.
    
    Args:
        patient_histories: Dict mapping patient_id to list of visits
        
    Returns:
        DataFrame with columns: patient_id, time_months, state
    """
    patient_states = []
    print(f"Processing {len(patient_histories)} patient histories...")
    
    # Use a counter for progress tracking
    count = 0
    
    for patient_id, visits in patient_histories.items():
        # Track patient's discontinuation history
        current_state = "active"
        last_discontinuation_type = None
        has_been_retreated = False
        
        for visit in visits:
            # Get visit time in months
            visit_time = visit.get("time", visit.get("date", 0))
            
            # Convert to months
            if isinstance(visit_time, (datetime, pd.Timestamp)):
                # This is handled later in aggregation
                months = visit_time
            elif isinstance(visit_time, timedelta):
                months = int(visit_time.days / 30)
            elif isinstance(visit_time, (int, float)):
                months = int(visit_time / 30)
            else:
                months = 0
            
            # Check for discontinuation
            if visit.get("is_discontinuation_visit", False):
                # Get discontinuation type
                disc_type = visit.get("discontinuation_reason", "")
                
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
                    # Default fallback - but we should log this
                    print(f"Unknown discontinuation reason: {disc_type}")
                    current_state = "discontinued_premature"
                    last_discontinuation_type = "premature"
            
            # Check for retreatment
            elif visit.get("is_retreatment_visit", False):
                has_been_retreated = True
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
                    current_state = "active"
            
            # Record state at this time
            patient_states.append({
                "patient_id": patient_id,
                "time_months": months,
                "state": current_state,
                "visit_time": visit_time  # Keep original for datetime handling
            })
        
        # Show progress every 100 patients
        count += 1
        if count % 100 == 0:
            print(f"Processed {count} patients...")
    
    print(f"Extracted {len(patient_states)} patient state records")
    return pd.DataFrame(patient_states)


def aggregate_states_by_month(patient_states_df: pd.DataFrame, 
                            duration_months: int,
                            population_size: int) -> pd.DataFrame:
    """
    Aggregate patient states by month for streamgraph.
    
    Args:
        patient_states_df: DataFrame with patient states
        duration_months: Total simulation duration in months
        population_size: Total number of patients in simulation
        
    Returns:
        DataFrame with columns: time_months, state, count
    """
    print("Aggregating patient states by month...")
    
    # First, ensure time_months column is numeric
    if 'time_months' not in patient_states_df.columns or patient_states_df['time_months'].dtype == 'object':
        # Check if we have datetime objects in visit_time
        if 'visit_time' in patient_states_df.columns:
            sample = patient_states_df['visit_time'].iloc[0]
            if isinstance(sample, (datetime, pd.Timestamp)):
                # Find earliest date as reference
                min_date = patient_states_df['visit_time'].min()
                # Convert to months from start
                patient_states_df['time_months'] = patient_states_df['visit_time'].apply(
                    lambda x: int((x - min_date).days / 30)
                )
            else:
                # Use visit_time directly if it's already numeric
                patient_states_df['time_months'] = pd.to_numeric(patient_states_df['visit_time'], errors='coerce').fillna(0).astype(int)
    
    # Ensure time_months is integer type for comparison
    patient_states_df['time_months'] = patient_states_df['time_months'].astype(int)
    
    # Get unique patient IDs
    unique_patients = patient_states_df['patient_id'].unique()
    print(f"Found {len(unique_patients)} unique patients")
    
    # For each month, count patients in each state
    monthly_counts = []
    
    # Show progress
    progress_interval = max(1, duration_months // 10)
    
    for month in range(duration_months + 1):
        # For each patient, find their state at this month
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
        
        # Count states
        state_counts = defaultdict(int)
        for state in patient_states_at_month.values():
            state_counts[state] += 1
        
        # Add to results
        for state in PATIENT_STATES:
            monthly_counts.append({
                "time_months": month,
                "state": state,
                "count": state_counts[state]
            })
        
        # Show progress periodically
        if month % progress_interval == 0:
            print(f"Processed month {month}/{duration_months}...")
    
    # Convert to DataFrame
    result_df = pd.DataFrame(monthly_counts)
    
    # IMPORTANT: Verify that every month has the correct total patient count
    for month in range(0, duration_months + 1, duration_months // 5):
        month_data = result_df[result_df['time_months'] == month]
        total = month_data['count'].sum()
        if total != len(unique_patients):
            print(f"WARNING: Month {month} has {total} patients, expected {len(unique_patients)}")
    
    print(f"Aggregation complete: {len(result_df)} records")
    return result_df


def create_streamgraph(results: Dict) -> plt.Figure:
    """
    Create streamgraph visualization of patient states over time.
    
    Args:
        results: Simulation results dictionary
        
    Returns:
        Matplotlib figure
    """
    print("Creating streamgraph visualization...")
    
    # Extract patient histories
    patient_histories = results.get("patient_histories", {})
    if not patient_histories:
        raise ValueError("No patient history data in results")
    
    # Get population size and simulation duration
    population_size = results.get("population_size", len(patient_histories))
    duration_years = results.get("duration_years", 5)
    duration_months = int(duration_years * 12)
    
    print(f"Population size: {population_size}")
    print(f"Duration: {duration_years} years ({duration_months} months)")
    
    # Extract patient states
    patient_states_df = extract_patient_states(patient_histories)
    
    # Aggregate by month
    monthly_counts = aggregate_states_by_month(
        patient_states_df, 
        duration_months,
        population_size
    )
    
    # Pivot for stacking
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
    
    # Plot in the order we defined
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
    
    # Add total line
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


if __name__ == "__main__":
    # Paths to simulation results
    result_paths = [
        "output/simulation_results/ape_simulation_ABS_20250520_101135.json",
        "output/simulation_results/latest_results.json"
    ]
    
    # Find a valid results file
    results = None
    for path in result_paths:
        if os.path.exists(path):
            print(f"Loading simulation results from {path}")
            results = load_simulation_results(path)
            if results:
                break
    
    if not results:
        print("No valid simulation results found. Please run a simulation first.")
        sys.exit(1)
    
    # Create the streamgraph visualization
    try:
        # First, analyze the patient states in the results
        patient_histories = results.get("patient_histories", {})
        
        # Check for discontinuation data
        print("\nChecking for discontinuation data...")
        print(f"Simulation has {len(patient_histories)} patients")
        
        # Check discontinuation counts in the results
        if "discontinuation_counts" in results:
            print("Discontinuation counts found in results:")
            print(results["discontinuation_counts"])
        else:
            print("No discontinuation_counts found in results")
        
        # Check a sample of patients for discontinuation and retreatment flags
        sample_size = min(10, len(patient_histories))
        sample_patients = list(patient_histories.items())[:sample_size]
        
        discontinuation_visits = 0
        retreatment_visits = 0
        discontinuation_reasons = set()
        
        print(f"\nAnalyzing sample of {sample_size} patients:")
        for patient_id, visits in sample_patients:
            patient_disc_visits = 0
            patient_retreat_visits = 0
            
            for visit in visits:
                if visit.get("is_discontinuation_visit", False):
                    discontinuation_visits += 1
                    patient_disc_visits += 1
                    reason = visit.get("discontinuation_reason", "unknown")
                    discontinuation_reasons.add(reason)
                
                if visit.get("is_retreatment_visit", False):
                    retreatment_visits += 1
                    patient_retreat_visits += 1
            
            print(f"Patient {patient_id}: {len(visits)} visits, {patient_disc_visits} discontinuations, {patient_retreat_visits} retreatments")
        
        print(f"\nTotal in sample: {discontinuation_visits} discontinuations, {retreatment_visits} retreatments")
        print(f"Discontinuation reasons found: {discontinuation_reasons}")
        
        # Extract and print states
        patient_states_df = extract_patient_states(patient_histories)
        state_counts = patient_states_df['state'].value_counts()
        print("\nPatient states in the raw data:")
        print(state_counts)
        
        # Get simulation duration
        duration_years = results.get("duration_years", 5)
        duration_months = int(duration_years * 12)
        
        # Aggregate by month
        monthly_counts = aggregate_states_by_month(patient_states_df, duration_months, results.get("population_size", len(patient_histories)))
        
        # Check month 60 (final month) distribution
        final_month = monthly_counts[monthly_counts['time_months'] == duration_months]
        print("\nFinal month state distribution:")
        for state in PATIENT_STATES:
            state_rows = final_month[final_month['state'] == state]
            if not state_rows.empty:
                count = state_rows.iloc[0]['count']
                if count > 0:
                    print(f"{state}: {count}")
        
        # Create and save the figure
        fig = create_streamgraph(results)
        
        # Save the figure
        output_file = "fixed_streamgraph.png"
        fig.savefig(output_file, dpi=150, bbox_inches='tight')
        print(f"Streamgraph saved to {output_file}")
        
        # Also save a raw state distribution chart for debugging
        debug_fig, ax = plt.subplots(figsize=(10, 6))
        states = []
        counts = []
        
        for state in PATIENT_STATES:
            state_rows = final_month[final_month['state'] == state]
            if not state_rows.empty:
                count = state_rows.iloc[0]['count']
                if count > 0:
                    states.append(STATE_DISPLAY_NAMES.get(state, state))
                    counts.append(count)
        
        # Create a simple bar chart of the state distribution
        bars = ax.bar(states, counts, color=[STATE_COLORS.get(state, "#808080") for state in PATIENT_STATES if state in state_counts])
        
        # Add labels on top of bars
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 5,
                    f'{int(height)}',
                    ha='center', va='bottom')
        
        ax.set_ylabel('Number of Patients')
        ax.set_title('Patient States Distribution (Final Month)')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        
        # Save the debug chart
        debug_file = "patient_states_debug.png"
        debug_fig.savefig(debug_file, dpi=150, bbox_inches='tight')
        print(f"Debug chart saved to {debug_file}")
        
        # Show the figure
        plt.show()
    
    except Exception as e:
        import traceback
        print(f"Error creating streamgraph: {e}")
        traceback.print_exc()
        sys.exit(1)