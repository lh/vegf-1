"""
Streamgraph for the actual data format where patient_histories[patient_id] is a list of visits.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from typing import Dict
from collections import defaultdict
from datetime import datetime, timedelta

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


def count_patient_states_from_visits(results: Dict) -> pd.DataFrame:
    """
    Count patient states where patient_histories[patient_id] is a list of visits.
    """
    # Get patient_histories - dict where values are lists of visits
    patient_histories = results.get("patient_histories", {})
    
    if not patient_histories:
        raise ValueError("No patient history data in results['patient_histories']")
    
    duration_years = results.get("duration_years", 5)
    duration_months = int(duration_years * 12)
    
    timeline_data = []
    
    # Count states at each month
    for month in range(duration_months + 1):
        states = defaultdict(int)
        
        # Process each patient
        for patient_id, visits in patient_histories.items():
            # visits is a list of visit dicts
            
            # Track patient state at this time
            current_state = "active"
            has_discontinued = False
            has_retreated = False
            disc_reason = None
            retreat_count = 0
            
            # Process visits chronologically
            for visit in visits:
                # visit is a dict with time/date information
                visit_time = visit.get("time", visit.get("date", 0))
                
                # Convert visit time to months
                if isinstance(visit_time, (datetime, pd.Timestamp)):
                    # If it's a datetime, we need to figure out the reference point
                    # Usually simulation starts at day 0, so this might be a timedelta
                    # or it could be actual dates - let's check the first visit
                    if not hasattr(count_patient_states_from_visits, 'start_date'):
                        # Find the earliest date across all patients as reference
                        all_times = []
                        for pid, pvs in patient_histories.items():
                            for v in pvs:
                                t = v.get("time", v.get("date", None))
                                if isinstance(t, (datetime, pd.Timestamp)):
                                    all_times.append(t)
                        if all_times:
                            count_patient_states_from_visits.start_date = min(all_times)
                        else:
                            count_patient_states_from_visits.start_date = datetime.now()
                    
                    # Calculate months from start
                    if hasattr(count_patient_states_from_visits, 'start_date'):
                        delta = visit_time - count_patient_states_from_visits.start_date
                        visit_month = int(delta.days / 30)
                    else:
                        visit_month = 0
                elif isinstance(visit_time, timedelta):
                    # It's a timedelta from start
                    visit_month = int(visit_time.days / 30)
                elif isinstance(visit_time, (int, float)):
                    # Assume time is in days, convert to months
                    visit_month = int(visit_time / 30)
                else:
                    visit_month = 0
                
                if visit_month <= month:
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
                        retreat_count += 1
                        has_retreated = True
                        if retreat_count > 1:
                            current_state = "discontinued_after_retreatment"
                        else:
                            current_state = "active_retreated"
                            has_discontinued = False
                    
                    # Also check retreatment count in visit data
                    if "retreatment_count" in visit:
                        retreat_count = visit["retreatment_count"]
            
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


def generate_list_format_streamgraph(results: Dict) -> plt.Figure:
    """Generate streamgraph from patient_histories list format."""
    
    if not results:
        raise ValueError("No simulation results provided")
    
    # Count patient states from list format
    timeline_data = count_patient_states_from_visits(results)
    
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