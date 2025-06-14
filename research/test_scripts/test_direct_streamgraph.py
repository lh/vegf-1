#!/usr/bin/env python3
"""
Direct test for enhanced discontinuation streamgraph visualization.
This script bypasses the existing streamgraph code to directly verify discontinuation states.
"""

import json
import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict
from datetime import datetime

def extract_time_in_months(visit_time):
    """Convert visit time to months since start."""
    if isinstance(visit_time, str):
        # Parse datetime string
        try:
            visit_time = datetime.fromisoformat(visit_time.replace('Z', '+00:00'))
        except ValueError:
            # Alternative parsing approach
            try:
                visit_time = datetime.strptime(visit_time, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                # If all parsing fails, return 0
                return 0
    
    # Calculate months from a reference date (2023-01-01)
    if isinstance(visit_time, datetime):
        reference_date = datetime(2023, 1, 1)
        delta = visit_time - reference_date
        return int(delta.days / 30)
    
    # Fallback for numeric types
    if isinstance(visit_time, (int, float)):
        # Assume days, convert to months
        return int(visit_time / 30)
    
    # Default fallback
    return 0

def track_patient_states(data_file):
    """
    Track patient states over time from simulation data.
    
    Args:
        data_file: Path to simulation results JSON file
    """
    # Load data
    try:
        with open(data_file, 'r') as f:
            results = json.load(f)
    except Exception as e:
        print(f"Error loading data: {e}")
        return {}
    
    # Get patient histories
    patient_histories = results.get("patient_histories", {})
    if not patient_histories:
        print("No patient histories found!")
        return {}
    
    # Get duration in months
    duration_years = results.get("duration_years", 5)
    duration_months = int(duration_years * 12)
    
    # Track patient states over time
    patient_states = {}
    discontinuations = []
    
    # Create a matrix of states over time
    months = range(duration_months + 1)
    
    # Initialize state tracking for each patient
    for patient_id in patient_histories:
        patient_states[patient_id] = {
            "current_state": "active",
            "history": [{"month": 0, "state": "active"}]
        }
    
    # Process each patient's visit history
    for patient_id, visits in patient_histories.items():
        # Sort visits by time
        sorted_visits = sorted(visits, key=lambda v: v.get("time", v.get("date", 0)))
        
        # Extract discontinuation visits
        disc_visits = [v for v in sorted_visits if v.get("is_discontinuation_visit", False)]
        for visit in disc_visits:
            discontinuations.append({
                "patient_id": patient_id,
                "time": visit.get("time", visit.get("date", "")),
                "type": visit.get("discontinuation_type", visit.get("discontinuation_reason", "unknown"))
            })
        
        # Track state changes
        current_state = "active"
        
        for visit in sorted_visits:
            # Get visit time in months
            visit_time = visit.get("time", visit.get("date", 0))
            visit_month = extract_time_in_months(visit_time)
            
            # Check for state change
            if visit.get("is_discontinuation_visit", False):
                # Get discontinuation type
                disc_type = visit.get("discontinuation_type", "")
                if not disc_type:
                    disc_type = visit.get("discontinuation_reason", "")
                
                # Map to state
                if disc_type == "stable_max_interval":
                    current_state = "discontinued_stable_max_interval"
                elif disc_type == "random_administrative":
                    current_state = "discontinued_random_administrative"
                elif disc_type == "treatment_duration":
                    current_state = "discontinued_course_complete"
                elif disc_type == "course_complete_but_not_renewed":
                    current_state = "discontinued_course_complete"
                elif disc_type == "premature":
                    current_state = "discontinued_premature"
                else:
                    print(f"Unknown discontinuation type: {disc_type}")
                    current_state = "discontinued_unknown"
                
                # Record state change
                patient_states[patient_id]["history"].append({
                    "month": visit_month,
                    "state": current_state
                })
            
            # Update current state
            patient_states[patient_id]["current_state"] = current_state
    
    # Generate state counts by month
    monthly_state_counts = []
    
    for month in range(duration_months + 1):
        # Count states at this month
        state_counts = defaultdict(int)
        
        # For each patient, find their state at this month
        for patient_id, tracker in patient_states.items():
            # Default to active
            patient_state = "active"
            
            # Find last state change before this month
            state_changes = tracker["history"]
            for change in reversed(state_changes):
                if change["month"] <= month:
                    patient_state = change["state"]
                    break
            
            # Count this patient's state
            state_counts[patient_state] += 1
        
        # Store counts for this month
        monthly_state_counts.append({
            "month": month,
            "counts": dict(state_counts)
        })
        
        # Print state counts at key months
        if month in [0, 12, 24, 36, 48, 60]:
            print(f"\nMonth {month} state counts:")
            total = sum(state_counts.values())
            print(f"Total patients: {total}")
            for state, count in sorted(state_counts.items()):
                if count > 0:
                    print(f"  {state}: {count}")
    
    # Summary of discontinuations
    print("\nDiscontinuation summary:")
    disc_by_type = defaultdict(int)
    for disc in discontinuations:
        disc_by_type[disc["type"]] += 1
    
    for disc_type, count in sorted(disc_by_type.items()):
        print(f"  {disc_type}: {count}")
    
    return {
        "patient_states": patient_states,
        "monthly_counts": monthly_state_counts,
        "discontinuations": discontinuations
    }

def create_direct_streamgraph(monthly_data):
    """
    Create a streamgraph visualization from monthly patient state counts.
    
    Args:
        monthly_data: List of dictionaries with month and state counts
    """
    # Extract months and state counts
    months = [item["month"] for item in monthly_data]
    
    # Get all unique states
    all_states = set()
    for item in monthly_data:
        all_states.update(item["counts"].keys())
    
    # Define state order and colors
    state_order = [
        "active",
        "discontinued_stable_max_interval",
        "discontinued_random_administrative",
        "discontinued_course_complete",
        "discontinued_premature",
        "discontinued_unknown"
    ]
    
    # Filter to states that actually appear
    state_order = [s for s in state_order if s in all_states]
    
    # Define colors
    colors = {
        "active": "#2E7D32",  # Dark green
        "discontinued_stable_max_interval": "#FFA500",  # Orange
        "discontinued_random_administrative": "#E91E63",  # Pink
        "discontinued_course_complete": "#F44336",  # Red
        "discontinued_premature": "#B71C1C",  # Dark red
        "discontinued_unknown": "#9E9E9E"  # Gray
    }
    
    # Create figure
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Create stacked area chart
    x = np.array(months)
    y_bottom = np.zeros(len(x))
    
    # State labels for legend
    state_labels = {
        "active": "Active",
        "discontinued_stable_max_interval": "Discontinued (Planned)",
        "discontinued_random_administrative": "Discontinued (Administrative)",
        "discontinued_course_complete": "Discontinued (Course Complete)",
        "discontinued_premature": "Discontinued (Premature)",
        "discontinued_unknown": "Discontinued (Unknown)"
    }
    
    # Track which states are used
    used_states = []
    
    # Plot states in order
    for state in state_order:
        # Extract counts for this state
        y_values = np.array([item["counts"].get(state, 0) for item in monthly_data])
        
        # Only plot states with non-zero values
        if np.any(y_values > 0):
            ax.fill_between(
                x, y_bottom, y_bottom + y_values,
                label=state_labels.get(state, state),
                color=colors.get(state, "#808080"),
                alpha=0.8
            )
            y_bottom += y_values
            used_states.append(state)
    
    # Add total line
    ax.plot(x, y_bottom, color='black', linewidth=2, label='Total Population', 
            linestyle='--', alpha=0.7)
    
    # Configure axes
    ax.set_xlabel('Months', fontsize=12)
    ax.set_ylabel('Number of Patients', fontsize=12)
    ax.set_title('Patient Treatment Status Over Time', fontsize=16, fontweight='bold')
    
    # Set x-axis ticks at yearly intervals
    ax.set_xlim(0, max(x))
    year_ticks = list(range(0, duration_months + 1, 12))
    ax.set_xticks(year_ticks)
    ax.set_xticklabels([f'{y//12}' for y in year_ticks])
    ax.set_xlabel('Time (years)', fontsize=12)
    
    # Configure grid and spines
    ax.grid(True, axis='y', alpha=0.3)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    # Add legend
    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', frameon=False)
    
    plt.tight_layout()
    return fig

if __name__ == "__main__":
    # Set duration for tracking
    duration_months = 60
    
    # Track patient states
    print("Analyzing patient states...")
    results = track_patient_states("full_streamgraph_test_data.json")
    
    # Create streamgraph
    print("\nCreating direct streamgraph visualization...")
    fig = create_direct_streamgraph(results["monthly_counts"])
    
    # Save the figure
    output_file = "direct_streamgraph_test.png"
    fig.savefig(output_file, dpi=300, bbox_inches="tight")
    print(f"Streamgraph saved to {output_file}")
    
    print("Done!")