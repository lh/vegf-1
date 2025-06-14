"""
Direct streamgraph implementation using the known patient_histories structure.
No figuring out - we know it's a dict with patient_id as keys.
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


def count_patient_states(results: Dict) -> pd.DataFrame:
    """
    Count patient states from patient_histories.
    We know patient_histories is a dict with patient_id keys.
    """
    # Get patient_histories - it's a dict, period.
    patient_histories = results.get("patient_histories", {})
    
    if not patient_histories:
        raise ValueError("No patient history data in results['patient_histories']")
    
    duration_years = results.get("duration_years", 5)
    duration_months = int(duration_years * 12)
    
    timeline_data = []
    
    # Count states at each month
    for month in range(duration_months + 1):
        states = defaultdict(int)
        
        # Process each patient (patient_histories is a dict)
        for patient_id, patient_data in patient_histories.items():
            # patient_data is a dict with 'visits' key
            visits = patient_data.get("visits", [])
            
            # Track patient state at this time
            current_state = "active"
            has_discontinued = False
            has_retreated = False
            disc_reason = None
            retreat_count = patient_data.get("retreatment_count", 0)
            
            # Process visits chronologically
            for visit in visits:
                # visit is a dict with 'time' or 'date' key
                visit_time = visit.get("time", visit.get("date", 0))
                
                if visit_time <= month:
                    # Check discontinuation
                    if visit.get("is_discontinuation_visit", False):
                        has_discontinued = True
                        has_retreated = False
                        
                        # Map discontinuation reasons
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
                    
                    # Check retreatment
                    if visit.get("is_retreatment", False):
                        has_retreated = True
                        if retreat_count > 1:
                            current_state = "discontinued_after_retreatment"
                        else:
                            current_state = "active_retreated"
                            has_discontinued = False
            
            # Count this patient's state
            states[current_state] += 1
        
        # Record all states for this month
        for state, count in states.items():
            timeline_data.append({
                'time_months': month,
                'state': state,
                'count': count
            })
        
        # Debug output at key months
        if month in [0, 6, 12, 24, 36, 48, 60]:
            total = sum(states.values())
            print(f"Month {month}: Total={total}")
            for state, count in sorted(states.items()):
                if count > 0:
                    print(f"  {state}: {count}")
    
    return pd.DataFrame(timeline_data)


def generate_direct_streamgraph(results: Dict) -> plt.Figure:
    """Generate streamgraph from known data structure."""
    
    if not results:
        raise ValueError("No simulation results provided")
    
    # Count patient states directly
    timeline_data = count_patient_states(results)
    
    # Pivot for stacking
    pivot_data = timeline_data.pivot(
        index='time_months',
        columns='state',
        values='count'
    ).fillna(0)
    
    # Create figure
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # State ordering
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
    
    # Create stacked area plot
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
    ax.set_title("Patient Cohort Flow Through Treatment States", fontsize=14, loc="left")
    
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
    
    # Add summary annotation
    disc_counts = results.get("discontinuation_counts", {})
    total_disc = sum(disc_counts.values())
    
    raw_stats = results.get("raw_discontinuation_stats", {})
    total_retreat = raw_stats.get("retreatments", results.get("recurrences", {}).get("total", 0))
    
    annotation_text = f"Total Discontinuations: {total_disc}\\nTotal Retreatments: {total_retreat}"
    ax.text(
        0.02, 0.98,
        annotation_text,
        transform=ax.transAxes,
        verticalalignment='top',
        fontsize=10,
        bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.8)
    )
    
    return fig