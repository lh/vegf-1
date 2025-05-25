"""
Patient state tracking streamgraph for ABS simulation.
Tracks 9 distinct states based on treatment and discontinuation history.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, List, Tuple
from collections import defaultdict
from datetime import datetime, timedelta


def convert_timestamp_to_months(timestamp, start_date=None):
    """
    Convert timestamp to months from the start date.
    
    Args:
        timestamp: Timestamp in nanoseconds epoch format (as seen in the data)
        start_date: Optional start date as a reference point. If None, uses the
                    timestamp itself converted to datetime
    
    Returns:
        Relative months (int)
    """
    # Convert nanosecond timestamp to datetime
    if isinstance(timestamp, (int, float)) and timestamp > 1e18:  # Nanosecond timestamp
        dt = pd.to_datetime(timestamp, unit='ns')
    elif isinstance(timestamp, (int, float)):
        dt = pd.to_datetime(timestamp, unit='s')
    else:
        dt = pd.to_datetime(timestamp)
    
    # If no start date, use the timestamp itself
    if start_date is None:
        return 0
    
    # Calculate months between dates
    if isinstance(start_date, (int, float)):
        start_date = pd.to_datetime(start_date, unit='ns' if start_date > 1e18 else 's')
    elif not isinstance(start_date, (datetime, pd.Timestamp)):
        start_date = pd.to_datetime(start_date)
    
    # Calculate difference in days and convert to months
    days_diff = (dt - start_date).days
    months_diff = int(days_diff / 30)
    
    return months_diff


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


def extract_patient_states(patient_histories: Dict) -> pd.DataFrame:
    """
    Extract patient states at each time point from simulation results.
    
    Args:
        patient_histories: Dict mapping patient_id to list of visits
        
    Returns:
        DataFrame with columns: patient_id, time_months, state
    """
    patient_states = []
    
    # Debug counts for tracking state transitions
    state_transition_counts = defaultdict(int)
    
    # Track retreatment events for debugging
    retreatment_events = 0
    retreatment_by_type = defaultdict(int)
    
    for patient_id, visits in patient_histories.items():
        # Track patient's discontinuation history
        current_state = "active"
        last_discontinuation_type = None
        has_been_retreated = False
        
        # Process visits in chronological order
        # The date field is used in the new simulation format
        sorted_visits = sorted(visits, key=lambda v: v.get("time", v.get("date", 0)))
        
        # Get ordered index of state changes for this patient
        visit_states = []
        
        for visit in sorted_visits:
            # Get visit time - in new format it's in the "date" field
            visit_time = visit.get("time", visit.get("date", 0))
            
            # Check for discontinuation
            old_state = current_state
            
            if visit.get("is_discontinuation_visit", False):
                # Get discontinuation type
                disc_type = visit.get("discontinuation_reason", "")
                if not disc_type:
                    disc_type = visit.get("discontinuation_type", "")
                
                # Map to our state names
                if disc_type == "stable_max_interval":
                    current_state = "discontinued_stable_max_interval"
                    last_discontinuation_type = "stable_max_interval"
                elif disc_type == "random_administrative":
                    current_state = "discontinued_random_administrative"
                    last_discontinuation_type = "random_administrative"
                elif disc_type == "course_complete_but_not_renewed" or disc_type == "treatment_duration":
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
            
            # Check for retreatment - look for multiple variant field names
            elif visit.get("is_retreatment_visit", False) or visit.get("is_retreatment", False):
                has_been_retreated = True
                retreatment_events += 1
                retreatment_by_type[last_discontinuation_type or "unknown"] += 1
                
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
                    print(f"Retreatment without prior discontinuation type for patient {patient_id}")
                    current_state = "active"
            
            # Track state transitions for debugging
            if current_state != old_state:
                transition_key = f"{old_state}->{current_state}"
                state_transition_counts[transition_key] += 1
                
                # Mark this as a state transition point in the timeline
                if patient_id.startswith("PATIENT00"):  # Debug for first few patients
                    print(f"Patient {patient_id} transition at {visit_time}: {old_state} -> {current_state}")
            
            # Record state for this visit
            visit_states.append({
                "time": visit_time,
                "state": current_state
            })
        
        # Now create records for this patient
        for vs in visit_states:
            patient_states.append({
                "patient_id": patient_id,
                "state": vs["state"],
                "visit_time": vs["time"]  # Keep original time value for conversion to months
            })
    
    # Print summary of state transitions
    print("\nState transition counts:")
    for transition, count in state_transition_counts.items():
        print(f"  {transition}: {count}")
    
    # Print retreatment summary
    print(f"\nTotal retreatment events: {retreatment_events}")
    print("Retreatments by discontinuation type:")
    for disc_type, count in retreatment_by_type.items():
        print(f"  {disc_type}: {count}")
    
    # If no retreatment events were found, attempt to detect them from other fields
    if retreatment_events == 0:
        print("\nWarning: No explicit retreatment events found. Checking for implicit retreatment data...")
        
        # Try to find retreatment info in other formats (sometimes stored at patient level)
        for patient_id, visits in patient_histories.items():
            # Check if visits is a dict with additional metadata
            if isinstance(visits, dict) and "visits" in visits:
                patient_data = visits
                patient_visits = patient_data["visits"]
                
                # Look for retreatment info in metadata
                if "retreatment_count" in patient_data and patient_data["retreatment_count"] > 0:
                    print(f"Found retreatment info in patient metadata for {patient_id}: {patient_data['retreatment_count']} retreatments")
                    
                    # Look for state transitions to infer retreatment timing
                    patient_states_from_visits = []
                    current_state = "active"
                    last_discontinuation_type = None
                    
                    # Sort visits chronologically
                    sorted_visits = sorted(patient_visits, key=lambda v: v.get("time", v.get("date", 0)))
                    
                    # Process this patient's visits - this time we'll infer retreatment status
                    # from discontinuation patterns
                    for i, visit in enumerate(sorted_visits):
                        visit_time = visit.get("time", visit.get("date", 0))
                        old_state = current_state
                        
                        # Check for discontinuation
                        if visit.get("is_discontinuation_visit", False):
                            disc_type = visit.get("discontinuation_reason", "")
                            if not disc_type:
                                disc_type = visit.get("discontinuation_type", "")
                            
                            # Map to state names
                            if disc_type == "stable_max_interval":
                                current_state = "discontinued_stable_max_interval"
                                last_discontinuation_type = "stable_max_interval"
                            elif disc_type == "random_administrative":
                                current_state = "discontinued_random_administrative"
                                last_discontinuation_type = "random_administrative"
                            elif disc_type == "course_complete_but_not_renewed" or disc_type == "treatment_duration":
                                current_state = "discontinued_course_complete_but_not_renewed"
                                last_discontinuation_type = "course_complete"
                            elif disc_type == "premature":
                                current_state = "discontinued_premature"
                                last_discontinuation_type = "premature"
                            else:
                                current_state = "discontinued_premature"
                                last_discontinuation_type = "premature"
                        
                        # If this patient was previously discontinued but gets an injection, treat as retreatment
                        elif (current_state.startswith("discontinued_") and 
                              visit.get("injection_count", 0) > 0 and
                              i > 0):  # Make sure it's not the first visit
                            # Infer retreatment
                            print(f"Inferred retreatment for patient {patient_id} at visit time {visit_time}")
                            
                            if last_discontinuation_type == "stable_max_interval":
                                current_state = "active_retreated_from_stable_max_interval"
                            elif last_discontinuation_type == "random_administrative":
                                current_state = "active_retreated_from_random_administrative"
                            elif last_discontinuation_type == "course_complete":
                                current_state = "active_retreated_from_course_complete"
                            elif last_discontinuation_type == "premature":
                                current_state = "active_retreated_from_premature"
                            else:
                                current_state = "active"
                            
                            retreatment_events += 1
                        
                        # Track state changes
                        if current_state != old_state:
                            print(f"Patient {patient_id} inferred transition at {visit_time}: {old_state} -> {current_state}")
                        
                        patient_states_from_visits.append({
                            "patient_id": patient_id,
                            "state": current_state,
                            "visit_time": visit_time
                        })
                    
                    # Add these inferred states to the main list
                    patient_states.extend(patient_states_from_visits)
    
    return pd.DataFrame(patient_states)


def aggregate_states_by_month(patient_states_df: pd.DataFrame, 
                            duration_months: int) -> pd.DataFrame:
    """
    Aggregate patient states by month for streamgraph.
    
    Args:
        patient_states_df: DataFrame with patient states
        duration_months: Total simulation duration in months
        
    Returns:
        DataFrame with columns: time_months, state, count
    """
    # First, ensure time_months column is numeric and correctly reflects months
    if 'visit_time' in patient_states_df.columns:
        # Get sample timestamps to determine format
        sample = patient_states_df['visit_time'].iloc[0]
        print(f"Sample timestamp: {sample}, type: {type(sample)}")
        
        # Find earliest date as reference
        min_date = patient_states_df['visit_time'].min()
        print(f"Min date: {min_date}, type: {type(min_date)}")
        
        # Convert timestamps to months from start - handle different formats
        if isinstance(sample, (int, float)) and sample > 1e18:  # Nanosecond epoch timestamp
            print("Detected nanosecond epoch timestamps")
            min_date_dt = pd.to_datetime(min_date, unit='ns')
            patient_states_df['time_months'] = patient_states_df['visit_time'].apply(
                lambda x: convert_timestamp_to_months(x, min_date)
            )
        elif isinstance(sample, (int, float)):  # Second epoch timestamp
            print("Detected second epoch timestamps")
            min_date_dt = pd.to_datetime(min_date, unit='s')
            patient_states_df['time_months'] = patient_states_df['visit_time'].apply(
                lambda x: int((pd.to_datetime(x, unit='s') - min_date_dt).days / 30)
            )
        elif isinstance(sample, (datetime, pd.Timestamp)):  # Already datetime
            print("Detected datetime objects")
            patient_states_df['time_months'] = patient_states_df['visit_time'].apply(
                lambda x: int((x - min_date).days / 30)
            )
        else:  # String dates or other formats
            print(f"Converting unknown timestamp format: {sample}")
            # Try to parse as datetime string
            min_date_dt = pd.to_datetime(min_date)
            patient_states_df['time_months'] = patient_states_df['visit_time'].apply(
                lambda x: int((pd.to_datetime(x) - min_date_dt).days / 30)
            )
        
        # Print some validation of the conversion
        print(f"First few time_months values: {patient_states_df['time_months'].head().tolist()}")
    
    # Ensure time_months is integer type for comparison
    patient_states_df['time_months'] = patient_states_df['time_months'].astype(int)
    
    # Get unique patient IDs
    unique_patients = patient_states_df['patient_id'].unique()
    
    # Debug patient counts and time range
    print(f"Aggregating states for {len(unique_patients)} patients over {duration_months} months")
    
    # For debugging, get all unique states in the input data
    unique_states = patient_states_df['state'].unique()
    print(f"Unique states in input data: {unique_states}")
    
    # For each month, count patients in each state
    monthly_counts = []
    
    # Create a debug list to track patient transitions
    state_transitions = {}
    
    # Set up a patient state tracker - this will keep track of each patient's state over time
    patient_state_tracker = {}
    for patient_id in unique_patients:
        patient_state_tracker[patient_id] = {
            'current_state': 'active',
            'transitions': []
        }
    
    # First pass - identify all state transitions for each patient
    for patient_id in unique_patients:
        patient_data = patient_states_df[patient_states_df['patient_id'] == patient_id].sort_values('time_months')
        
        # Debug information about time columns
        if patient_id == list(unique_patients)[0]:
            first_row = patient_data.iloc[0] if not patient_data.empty else None
            print(f"Sample first row for patient {patient_id}:")
            if first_row is not None:
                print(f"  time_months = {first_row.get('time_months')}")
                print(f"  visit_time = {first_row.get('visit_time')}")
                print(f"  time_months column type: {patient_data['time_months'].dtype}")
        
        # Track this patient's state changes
        current_state = 'active'
        
        # Process each visit for this patient chronologically
        for idx, row in patient_data.iterrows():
            visit_month = int(row['time_months'])  # Ensure it's an integer
            visit_state = row['state']
            
            # If state changed, record the transition
            if visit_state != current_state:
                patient_state_tracker[patient_id]['transitions'].append({
                    'month': visit_month,
                    'new_state': visit_state
                })
                current_state = visit_state
        
        # Record the final state
        patient_state_tracker[patient_id]['current_state'] = current_state
    
    # Debug - show some state transitions
    transition_counts = 0
    for patient_id, tracker in list(patient_state_tracker.items())[:10]:  # Just show first 10
        transitions = tracker['transitions']
        if transitions:
            transition_counts += len(transitions)
            print(f"Patient {patient_id} transitions:")
            for t in transitions:
                print(f"  Month {t['month']}: -> {t['new_state']}")
    
    print(f"Found {transition_counts} transitions in first 10 patients")
    
    # Now build the monthly counts across all months
    for month in range(duration_months + 1):
        # For each state, count patients in that state at this month
        state_counts = defaultdict(int)
        
        # For each patient, determine their state at this month
        for patient_id, tracker in patient_state_tracker.items():
            # Start with active state
            patient_state = 'active'
            
            # Apply transitions up to this month
            for transition in tracker['transitions']:
                if transition['month'] <= month:
                    patient_state = transition['new_state']
                else:
                    # Stop once we hit transitions beyond this month
                    break
            
            # Count this patient in their current state
            state_counts[patient_state] += 1
        
        # Count the number of patients in each retreated state
        retreated_patients = 0
        for state, count in state_counts.items():
            if state.startswith("active_retreated"):
                retreated_patients += count
        
        # Print state counts at key months
        if month in [0, 12, 24, 36, 48, 60]:
            print(f"\nMonth {month} state counts:")
            total_patients = sum(state_counts.values())
            print(f"Total patients: {total_patients}")
            print(f"Retreated patients: {retreated_patients}")
            for state, count in sorted(state_counts.items()):
                if count > 0:
                    print(f"  {state}: {count}")
        
        # Add counts for this month to results
        for state, count in state_counts.items():
            monthly_counts.append({
                'time_months': month,
                'state': state,
                'count': count
            })
    
    # Print summary of states in monthly data
    state_sums = {}
    for state in unique_states:
        state_data = [item for item in monthly_counts if item['state'] == state]
        state_sums[state] = sum(item['count'] for item in state_data)
    
    print("\nSummary of states in monthly data:")
    for state, total in state_sums.items():
        print(f"  {state}: {total}")
    
    # Also look for retreated patient states
    retreated_states = [s for s in state_sums.keys() if s.startswith("active_retreated")]
    print("\nRetreated patient states found:")
    for state in retreated_states:
        print(f"  {state}: {state_sums.get(state, 0)}")
    
    return pd.DataFrame(monthly_counts)


def create_streamgraph(results: Dict) -> plt.Figure:
    """
    Create streamgraph visualization of patient states over time.
    
    Args:
        results: Simulation results dictionary
        
    Returns:
        Matplotlib figure
    """
    # Extract patient histories
    patient_histories = results.get("patient_histories", {})
    if not patient_histories:
        raise ValueError("No patient history data in results")
    
    # Get simulation duration
    duration_years = results.get("duration_years", 5)
    duration_months = int(duration_years * 12)
    
    # Extract patient states
    patient_states_df = extract_patient_states(patient_histories)
    
    # Debug state extraction
    print(f"\nState counts after extraction:")
    state_counts = patient_states_df['state'].value_counts()
    for state, count in state_counts.items():
        print(f"  {state}: {count}")
    
    # Aggregate by month
    monthly_counts = aggregate_states_by_month(patient_states_df, duration_months)
    
    # Debug monthly aggregation
    print(f"\nAvailable states in monthly data:")
    available_states = monthly_counts['state'].unique()
    for state in available_states:
        count = monthly_counts[monthly_counts['state'] == state]['count'].sum()
        print(f"  {state}: {count}")
    
    # Pivot for stacking
    pivot_data = monthly_counts.pivot(
        index='time_months',
        columns='state',
        values='count'
    ).fillna(0)
    
    # Debug pivot data
    print(f"\nColumns in pivot data: {list(pivot_data.columns)}")
    
    # Create figure
    fig, ax = plt.subplots(figsize=(14, 8))
    
    # Create stacked area plot
    x = pivot_data.index
    bottom = np.zeros(len(x))
    
    # Track which states are actually present (for legend)
    used_states = []
    
    # Debug for each state
    for state in PATIENT_STATES:
        if state in pivot_data.columns:
            values = pivot_data[state].values
            has_values = np.any(values > 0)
            print(f"State '{state}': In pivot columns, has non-zero values: {has_values}")
        else:
            print(f"State '{state}': Not in pivot columns")
    
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
                print(f"Added state '{state}' to the plot")
    
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


# For debugging - standalone test
if __name__ == "__main__":
    # Create test data
    test_results = {
        "patient_histories": {
            "P001": [
                {"time": 0, "is_discontinuation_visit": False},
                {"time": 180, "is_discontinuation_visit": True, 
                 "discontinuation_reason": "stable_max_interval"},
                {"time": 360, "is_retreatment_visit": True},
                {"time": 540, "is_discontinuation_visit": True,
                 "discontinuation_reason": "premature"}
            ],
            "P002": [
                {"time": 0, "is_discontinuation_visit": False},
                {"time": 90, "is_discontinuation_visit": True,
                 "discontinuation_reason": "random_administrative"}
            ]
        },
        "duration_years": 2
    }
    
    fig = create_streamgraph(test_results)
    plt.show()