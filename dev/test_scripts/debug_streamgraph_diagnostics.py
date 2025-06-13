"""
Diagnostic tool for streamgraph visualization issues.
This script analyzes patient data to identify potential problems with state transitions,
time handling, and population conservation.
"""

import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List, Tuple, Any
import sys

# Import existing implementations to compare with
try:
    from streamlit_app.streamgraph_patient_states import (
        extract_patient_states, 
        aggregate_states_by_month,
        create_streamgraph,
        PATIENT_STATES
    )
except ImportError:
    print("Could not import existing streamgraph implementation. Using fallbacks.")
    # Define fallback constants
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

def load_sample_data(file_path=None):
    """Load sample patient data from file or generate test data."""
    if file_path:
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                print(f"Loaded data from {file_path}")
                return data
        except Exception as e:
            print(f"Error loading file: {e}")
    
    # Generate minimal test data if no file provided
    print("Generating test data...")
    return generate_test_data()

def generate_test_data():
    """Generate minimal test data for debugging."""
    test_data = {
        "patient_histories": {},
        "duration_years": 5
    }
    
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
        
        test_data["patient_histories"][patient_id] = visits
    
    return test_data

def inspect_data_structure(patient_histories):
    """Inspect the patient data structure to identify potential issues."""
    print("\n=== DATA STRUCTURE INSPECTION ===")
    
    # Check basic structure
    patient_count = len(patient_histories)
    print(f"Total patients: {patient_count}")
    
    # Check for empty patient histories
    empty_histories = sum(1 for visits in patient_histories.values() if not visits)
    print(f"Patients with empty visit history: {empty_histories}")
    
    # Check time formats
    time_formats = defaultdict(int)
    for patient_id, visits in patient_histories.items():
        for visit in visits:
            if "time" in visit:
                time_type = type(visit["time"]).__name__
                time_formats[time_type] += 1
    
    print(f"Time value formats: {dict(time_formats)}")
    
    # Check discontinuation events
    disc_visits = [v for p in patient_histories.values() 
                  for v in p if v.get("is_discontinuation_visit")]
    print(f"Total discontinuation events: {len(disc_visits)}")
    
    # Check discontinuation reasons
    disc_reasons = defaultdict(int)
    for visit in disc_visits:
        reason = visit.get("discontinuation_reason")
        disc_reasons[reason] += 1
    
    print(f"Discontinuation reasons: {dict(disc_reasons)}")
    
    # Check retreatment events
    retreat_visits = [v for p in patient_histories.values() 
                     for v in p if v.get("is_retreatment_visit")]
    print(f"Total retreatment events: {len(retreat_visits)}")
    
    # Check for patients with multiple discontinuations
    disc_counts = defaultdict(int)
    for patient_id, visits in patient_histories.items():
        count = sum(1 for v in visits if v.get("is_discontinuation_visit"))
        disc_counts[count] += 1
    
    print(f"Patients by discontinuation count: {dict(disc_counts)}")
    
    # Return a sample of visit data for further inspection
    first_patient_id = next(iter(patient_histories))
    sample_data = {
        "first_patient_id": first_patient_id,
        "first_patient_visits": patient_histories[first_patient_id][:5]
    }
    
    return sample_data

def inspect_state_transitions(patient_histories):
    """Inspect state transitions for debugging."""
    print("\n=== STATE TRANSITION INSPECTION ===")
    transitions = []
    
    # Take a sample of patients for inspection
    sample_patients = list(patient_histories.keys())[:5]
    
    for patient_id in sample_patients:
        visits = patient_histories[patient_id]
        
        # Extract key events
        discontinuations = [visit for visit in visits if visit.get("is_discontinuation_visit", False)]
        retreatments = [visit for visit in visits if visit.get("is_retreatment_visit", False)]
        
        # Report findings
        patient_info = {
            "patient_id": patient_id,
            "total_visits": len(visits),
            "discontinuations": [
                {
                    "time": str(visit.get("time", "unknown")),
                    "reason": visit.get("discontinuation_reason", "unknown")
                }
                for visit in discontinuations
            ],
            "retreatments": [
                {
                    "time": str(visit.get("time", "unknown"))
                }
                for visit in retreatments
            ]
        }
        
        transitions.append(patient_info)
    
    # Print for inspection
    for patient in transitions:
        print(f"\nPatient {patient['patient_id']} (visits: {patient['total_visits']})")
        
        if patient['discontinuations']:
            print("  Discontinuations:")
            for d in patient['discontinuations']:
                print(f"    Time: {d['time']}, Reason: {d['reason']}")
        else:
            print("  No discontinuations")
            
        if patient['retreatments']:
            print("  Retreatments:")
            for r in patient['retreatments']:
                print(f"    Time: {r['time']}")
        else:
            print("  No retreatments")
    
    return transitions

def verify_population_conservation(monthly_data):
    """Verify total population is conserved across all months."""
    print("\n=== POPULATION CONSERVATION CHECK ===")
    months = monthly_data["time_months"].unique()
    
    previous_total = None
    conservation_issues = []
    
    for month in sorted(months):
        month_data = monthly_data[monthly_data["time_months"] == month]
        total = month_data["count"].sum()
        
        if previous_total is not None and total != previous_total:
            issue = f"Month {month}: Previous: {previous_total}, Current: {total}, Diff: {total - previous_total}"
            conservation_issues.append(issue)
            print(f"WARNING: Population not conserved at month {month}. {issue}")
        
        previous_total = total
    
    print(f"Final population count: {previous_total}")
    if not conservation_issues:
        print("Population is conserved across all time points.")
    else:
        print(f"Found {len(conservation_issues)} conservation issues.")
    
    return previous_total, conservation_issues

def track_patient_states(patient_histories):
    """Manually track patient states to verify the visualization logic."""
    print("\n=== MANUAL STATE TRACKING ===")
    
    states_by_time = defaultdict(lambda: defaultdict(int))
    
    for patient_id, visits in patient_histories.items():
        current_state = "active"
        last_discontinuation_type = None
        has_been_retreated = False
        
        # Initialize at time 0
        states_by_time[0][current_state] += 1
        
        for visit in sorted(visits, key=lambda v: v.get("time", 0)):
            time = visit.get("time", 0)
            month = int(time / 30)  # Convert to months
            
            # Check for discontinuation
            if visit.get("is_discontinuation_visit", False):
                disc_type = visit.get("discontinuation_reason", "")
                
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
            
            # Check for retreatment
            elif visit.get("is_retreatment_visit", False):
                has_been_retreated = True
                
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
            
            # Update state at this time
            states_by_time[month][current_state] += 1
    
    # Count total patients at each timepoint
    print("Time (months) | Total Patients | State Distribution")
    print("-" * 70)
    
    # Sort by month
    for month in sorted(states_by_time.keys()):
        total = sum(states_by_time[month].values())
        top_states = sorted(states_by_time[month].items(), key=lambda x: x[1], reverse=True)[:3]
        state_str = ", ".join([f"{state}: {count}" for state, count in top_states])
        print(f"{month:12d} | {total:14d} | {state_str}")
    
    return states_by_time

def create_new_streamgraph(patient_histories, duration_years=5):
    """Create a new streamgraph visualization with robust error handling."""
    print("\n=== CREATING STREAMGRAPH ===")
    
    # Extract patient states
    def extract_states(patient_histories):
        patient_states = []
        
        for patient_id, visits in patient_histories.items():
            # Track patient's state
            current_state = "active"
            last_discontinuation_type = None
            
            # Process visits in time order
            for visit in sorted(visits, key=lambda v: v.get("time", 0)):
                # Get visit time in months
                visit_time = visit.get("time", 0)
                
                # Convert to months
                if isinstance(visit_time, (datetime, pd.Timestamp)):
                    months = visit_time  # Will be handled in aggregation
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
                        # Default fallback - but log this
                        print(f"Unknown discontinuation reason: {disc_type}")
                        current_state = "discontinued_premature"
                        last_discontinuation_type = "premature"
                
                # Check for retreatment
                elif visit.get("is_retreatment_visit", False):
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
        
        return pd.DataFrame(patient_states)
    
    # Aggregate states by month
    def aggregate_by_month(patient_states_df, duration_months):
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
                    patient_states_df['time_months'] = pd.to_numeric(
                        patient_states_df['visit_time'], errors='coerce'
                    ).fillna(0).astype(int)
        
        # Ensure time_months is integer type for comparison
        patient_states_df['time_months'] = patient_states_df['time_months'].astype(int)
        
        # Get unique patient IDs
        unique_patients = patient_states_df['patient_id'].unique()
        
        # For each month, count patients in each state
        monthly_counts = []
        
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
            
            # Add to results - make sure ALL states are included (even zeros)
            for state in PATIENT_STATES:
                monthly_counts.append({
                    "time_months": month,
                    "state": state,
                    "count": state_counts[state]
                })
        
        return pd.DataFrame(monthly_counts)
    
    # Create and verify the visualization
    try:
        # 1. Extract patient states
        print("Extracting patient states...")
        patient_states_df = extract_states(patient_histories)
        print(f"Extracted {len(patient_states_df)} state records for {patient_states_df['patient_id'].nunique()} patients.")
        
        # 2. Aggregate by month
        print("Aggregating states by month...")
        duration_months = int(duration_years * 12)
        monthly_counts = aggregate_by_month(patient_states_df, duration_months)
        print(f"Aggregated into {len(monthly_counts)} monthly state counts across {duration_months+1} months.")
        
        # 3. Verify population conservation
        total_patients, issues = verify_population_conservation(monthly_counts)
        
        # 4. Create the visualization using the original function or fallback
        if "create_streamgraph" in globals() and callable(create_streamgraph):
            print("Using existing create_streamgraph function.")
            results = {"patient_histories": patient_histories, "duration_years": duration_years}
            fig = create_streamgraph(results)
        else:
            print("Using fallback streamgraph implementation.")
            fig = create_fallback_streamgraph(monthly_counts, duration_months)
        
        return fig, monthly_counts, patient_states_df
        
    except Exception as e:
        print(f"Error creating streamgraph: {e}")
        import traceback
        traceback.print_exc()
        return None, None, None

def create_fallback_streamgraph(monthly_counts, duration_months):
    """Create a fallback streamgraph implementation."""
    # Define state colors for visualization
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
    
    # Pivot data for plotting
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

def main():
    """Main function to run diagnostic tests."""
    import argparse
    parser = argparse.ArgumentParser(description='Streamgraph visualization diagnostics')
    parser.add_argument('--input', help='Input JSON file with patient data')
    parser.add_argument('--output', help='Output file for visualization (.png)')
    args = parser.parse_args()
    
    # Load data
    data = load_sample_data(args.input)
    patient_histories = data["patient_histories"]
    
    # Run inspections
    inspect_data_structure(patient_histories)
    inspect_state_transitions(patient_histories)
    track_patient_states(patient_histories)
    
    # Create new streamgraph
    fig, monthly_counts, patient_states = create_new_streamgraph(
        patient_histories, 
        duration_years=data.get("duration_years", 5)
    )
    
    # Save or show results
    if fig:
        if args.output:
            fig.savefig(args.output, dpi=100, bbox_inches="tight")
            print(f"Saved visualization to {args.output}")
        else:
            plt.show()
    
    print("\nDiagnostics complete. Review the output for potential issues.")

if __name__ == "__main__":
    main()