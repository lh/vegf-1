"""
Streamgraph using REAL patient state counts from actual visit data.
NO synthetic curves, NO made-up data.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from typing import Dict
from collections import defaultdict

# Fix the import path
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# TODO: Add these traffic light colors to SEMANTIC_COLORS in the future
TRAFFIC_LIGHT_COLORS = {
    "active": "#006400",  # Strong green
    "active_retreated": "#228B22",  # Medium green
    "discontinued_planned": "#FFA500",  # Amber
    "discontinued_administrative": "#DC143C",  # Red
    "discontinued_not_renewed": "#B22222",  # Red
    "discontinued_premature": "#8B0000",  # Dark red
    "discontinued_after_retreatment": "#CD5C5C"  # Light red
}


def count_actual_patient_states(results: Dict) -> pd.DataFrame:
    """
    Count ACTUAL patient states at each time point from REAL visit data.
    No curves, no interpolation, just counting what actually happened.
    """
    patient_histories = results.get("patient_histories", {})
    
    if not patient_histories:
        raise ValueError("No patient history data available - cannot create visualization")
    
    duration_years = results.get("duration_years", 5)
    duration_months = int(duration_years * 12)
    
    # First, let's examine a sample patient to understand the data
    sample_patient_id = list(patient_histories.keys())[0]
    sample_patient = patient_histories[sample_patient_id]
    
    print("=== SAMPLE PATIENT DATA ===")
    print(f"Patient ID: {sample_patient_id}")
    print(f"Keys: {list(sample_patient.keys())}")
    
    visits = sample_patient.get("visits", [])
    if visits:
        print(f"\nFirst visit keys: {list(visits[0].keys())}")
        print(f"First visit: {visits[0]}")
    
    # Now count states for every month
    timeline_data = []
    
    for month in range(duration_months + 1):
        states = defaultdict(int)
        
        # Count each patient's state at this specific time
        for patient_id, patient_data in patient_histories.items():
            visits = patient_data.get("visits", [])
            
            # Track this patient's state at this month
            current_state = "active"  # Everyone starts active
            has_discontinued = False
            has_retreated = False
            disc_reason = None
            retreat_count = 0
            
            # Process visits chronologically up to this month
            for visit in visits:
                # Get visit time - handle both 'time' and 'date' fields
                visit_time = visit.get("time", visit.get("date", 0))
                
                # Only consider visits up to current month
                if visit_time <= month:
                    # Check for discontinuation
                    if visit.get("is_discontinuation_visit", False):
                        has_discontinued = True
                        has_retreated = False  # Reset retreatment status
                        
                        # Map discontinuation reasons to our categories
                        reason = visit.get("discontinuation_reason", "")
                        reason_map = {
                            "stable_max_interval": "planned",
                            "random_administrative": "administrative", 
                            "treatment_duration": "not_renewed",
                            "course_complete_but_not_renewed": "not_renewed",
                            "premature": "premature"
                        }
                        disc_reason = reason_map.get(reason, "premature")
                        current_state = f"discontinued_{disc_reason}"
                    
                    # Check for retreatment
                    if visit.get("is_retreatment", False):
                        retreat_count += 1
                        has_retreated = True
                        
                        if retreat_count > 1:
                            # Multiple retreatments - they discontinued again
                            current_state = "discontinued_after_retreatment"
                        else:
                            # First retreatment - they're active again
                            current_state = "active_retreated"
                            has_discontinued = False
            
            # Count this patient in their current state
            states[current_state] += 1
        
        # Verify patient conservation
        total = sum(states.values())
        if total != len(patient_histories):
            print(f"WARNING: Month {month} - Total {total} != {len(patient_histories)}")
        
        # Record all states for this month
        for state, count in states.items():
            timeline_data.append({
                'time_months': month,
                'state': state,
                'count': count
            })
        
        # Debug output for key time points
        if month in [0, 6, 12, 24, 36, 48, 60]:
            print(f"\nMonth {month}:")
            for state, count in sorted(states.items()):
                if count > 0:
                    print(f"  {state}: {count}")
    
    return pd.DataFrame(timeline_data)


def generate_real_streamgraph(results: Dict) -> plt.Figure:
    """Generate streamgraph from ACTUAL patient state counts."""
    
    if not results:
        raise ValueError("No simulation results provided")
    
    # Count actual patient states from real data
    timeline_data = count_actual_patient_states(results)
    
    # Pivot for stacking
    pivot_data = timeline_data.pivot(
        index='time_months',
        columns='state', 
        values='count'
    ).fillna(0)
    
    # Create figure
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # State ordering (bottom to top)
    state_order = [
        'active',
        'active_retreated',
        'discontinued_planned',
        'discontinued_administrative',
        'discontinued_not_renewed',
        'discontinued_premature',
        'discontinued_after_retreatment'
    ]
    
    # Display names
    display_names = {
        'active': 'Active (Never Discontinued)',
        'active_retreated': 'Active (Retreated)',
        'discontinued_planned': 'Discontinued Planned',
        'discontinued_administrative': 'Discontinued Administrative',
        'discontinued_not_renewed': 'Discontinued Not Renewed',
        'discontinued_premature': 'Discontinued Premature',
        'discontinued_after_retreatment': 'Discontinued After Retreatment'
    }
    
    # Create stacked area plot with actual data
    x = pivot_data.index
    bottom = np.zeros(len(x))
    
    for state in state_order:
        if state in pivot_data.columns:
            values = pivot_data[state].values
            color = TRAFFIC_LIGHT_COLORS.get(state, "#808080")
            label = display_names.get(state, state)
            
            ax.fill_between(
                x, bottom, bottom + values,
                color=color,
                alpha=0.8,
                label=label
            )
            bottom += values
    
    # Styling
    ax.set_xlabel("Time (Months)")
    ax.set_ylabel("Number of Patients")
    ax.set_title("Patient Cohort Flow Through Treatment States (ACTUAL DATA)", fontsize=14, loc="left")
    
    # Set axis limits
    ax.set_xlim(0, max(x))
    ax.set_ylim(0, results.get("population_size", 1000) * 1.05)
    
    # Clean style
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    
    ax.grid(axis='y', linestyle=':', alpha=0.3)
    ax.set_axisbelow(True)
    
    # Legend
    ax.legend(
        loc='center left',
        bbox_to_anchor=(1.02, 0.5),
        frameon=False,
        fontsize=9
    )
    
    plt.tight_layout()
    
    # Add summary annotation with ACTUAL counts
    disc_counts = results.get("discontinuation_counts", {})
    total_disc = sum(disc_counts.values())
    
    raw_stats = results.get("raw_discontinuation_stats", {})
    total_retreat = raw_stats.get("retreatments", results.get("recurrences", {}).get("total", 0))
    
    annotation_text = f"Actual Total Discontinuations: {total_disc}\\nActual Total Retreatments: {total_retreat}"
    ax.text(
        0.02, 0.98,
        annotation_text,
        transform=ax.transAxes,
        verticalalignment='top',
        fontsize=10,
        bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.8)
    )
    
    return fig