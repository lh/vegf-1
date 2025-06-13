"""
Fix date format issues in the streamgraph data handling.
This converts string dates to datetime objects and then to numeric month values.
"""

import json
import os
import pandas as pd
import numpy as np
from datetime import datetime
import sys
import matplotlib.pyplot as plt

def load_simulation_results(file_path):
    """Load simulation results from a JSON file"""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading simulation results: {e}")
        return None

def fix_date_format(data):
    """Convert all date strings to datetime objects and add time_months column"""
    # Create a flattened list of all visits
    patient_states = []
    for patient_id, visits in data["patient_histories"].items():
        current_state = "active"
        
        # Track transitions
        for visit in sorted(visits, key=lambda v: v.get("date", "")):
            # Check for discontinuation
            if visit.get("is_discontinuation_visit", False):
                disc_type = visit.get("discontinuation_reason", "")
                if disc_type == "stable_max_interval":
                    current_state = "discontinued_stable_max_interval"
                elif disc_type == "random_administrative":
                    current_state = "discontinued_random_administrative"
                elif disc_type == "course_complete_but_not_renewed" or disc_type == "treatment_duration":
                    current_state = "discontinued_course_complete_but_not_renewed"
                elif disc_type == "premature":
                    current_state = "discontinued_premature"
            elif visit.get("is_retreatment_visit", False):
                current_state = "active_retreated"
            
            # Add record for this state
            patient_states.append({
                "patient_id": patient_id,
                "date": visit.get("date", ""),
                "state": current_state
            })
    
    # Convert to dataframe
    df = pd.DataFrame(patient_states)
    
    # Convert date strings to datetime
    df["datetime"] = pd.to_datetime(df["date"])
    
    # Calculate months from start
    min_date = df["datetime"].min()
    df["time_months"] = df["datetime"].apply(lambda dt: int((dt - min_date).days / 30))
    
    # Summarize state counts for visualization
    monthly_data = []
    
    # For each month, track number of patients in each state
    max_months = df["time_months"].max() + 1
    
    # Sample data to check
    print(f"Sample data:")
    print(df.head())
    print(f"Min date: {min_date}, Max month: {max_months}")
    
    # Create month-by-month state counts
    for month in range(max_months):
        # Count patients in each state for this month
        month_states = {}
        
        # For each patient, find their state in this month
        for patient_id in df["patient_id"].unique():
            patient_df = df[df["patient_id"] == patient_id]
            
            # Find visits up to this month
            visits_up_to_month = patient_df[patient_df["time_months"] <= month]
            
            if len(visits_up_to_month) > 0:
                # Get the most recent state
                current_state = visits_up_to_month.iloc[-1]["state"]
                month_states[current_state] = month_states.get(current_state, 0) + 1
        
        # Add the counts for this month
        for state, count in month_states.items():
            monthly_data.append({
                "month": month,
                "state": state,
                "count": count
            })
    
    # Convert to dataframe for visualization
    monthly_df = pd.DataFrame(monthly_data)
    
    # Create visualization
    create_streamgraph(monthly_df)
    
    return monthly_df

def create_streamgraph(monthly_df):
    """Create a streamgraph visualization from the monthly data"""
    # Pivot data for visualization
    pivot_df = monthly_df.pivot(index="month", columns="state", values="count").fillna(0)
    
    # Create visualization
    fig, ax = plt.subplots(figsize=(14, 8))
    
    # Create stacked area plot
    x = pivot_df.index
    bottom = np.zeros(len(x))
    
    # Define colors for states
    colors = {
        "active": "#2E7D32",
        "active_retreated": "#66BB6A",
        "discontinued_stable_max_interval": "#FFA500",
        "discontinued_random_administrative": "#DC143C",
        "discontinued_course_complete_but_not_renewed": "#B22222",
        "discontinued_premature": "#8B0000"
    }
    
    # Create the streamgraph
    for state in pivot_df.columns:
        if state in pivot_df.columns:
            values = pivot_df[state].values
            color = colors.get(state, "#808080")
            ax.fill_between(x, bottom, bottom + values, 
                          label=state,
                          color=color, 
                          alpha=0.8)
            bottom += values
    
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
    
    # Add legend
    ax.legend(bbox_to_anchor=(1.05, 1), 
              loc='upper left',
              frameon=False, 
              fontsize=10)
    
    plt.tight_layout()
    plt.savefig("fixed_streamgraph.png", dpi=150, bbox_inches="tight")
    print("Streamgraph saved to fixed_streamgraph.png")
    
    return fig

def main():
    """Main function to run the fix"""
    # Load the simulation results
    file_path = "full_streamgraph_test_data.json"
    
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found. Run run_full_streamgraph_test.py first.")
        return
    
    data = load_simulation_results(file_path)
    if not data:
        print("Failed to load simulation results")
        return
    
    # Fix the date format and create visualization
    monthly_df = fix_date_format(data)
    
    # Save the fixed data
    monthly_df.to_csv("fixed_monthly_data.csv", index=False)
    print("Fixed monthly data saved to fixed_monthly_data.csv")

if __name__ == "__main__":
    main()