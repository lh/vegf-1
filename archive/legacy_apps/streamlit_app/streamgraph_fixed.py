"""
Fixed streamgraph implementation for proper patient state tracking.
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
    FIXED VERSION: Properly handles discontinuation types and retreatment.
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
                    # Check discontinuation - check both field name variations
                    if visit.get("is_discontinuation_visit", False) or visit.get("discontinued", False):
                        has_discontinued = True
                        has_retreated = False
                        
                        # Get discontinuation reason from various possible fields
                        reason = (visit.get("discontinuation_reason") or 
                                visit.get("reason") or 
                                visit.get("discontinuation_type") or
                                "")
                        
                        # More comprehensive reason mapping
                        reason_map = {
                            # Original mappings
                            "stable_max_interval": "planned",
                            "random_administrative": "administrative",
                            "treatment_duration": "not_renewed",
                            "course_complete_but_not_renewed": "not_renewed",
                            "premature": "premature",
                            
                            # Additional mappings from test data
                            "patient_choice": "planned",
                            "planned": "planned",
                            "administrative": "administrative",
                            "admin": "administrative",
                            "not renewed": "not_renewed",
                            "not_renewed": "not_renewed",
                            
                            # Fallback patterns
                            "patient": "planned",
                            "choice": "planned",
                        }
                        
                        # Check if reason contains any key patterns
                        disc_reason = None
                        reason_lower = reason.lower()
                        for key, value in reason_map.items():
                            if key.lower() in reason_lower:
                                disc_reason = value
                                break
                        
                        # Final fallback
                        if disc_reason is None:
                            disc_reason = "premature"
                        
                        current_state = f"discontinued_{disc_reason}"
                    
                    # Check retreatment - check both field name variations
                    if visit.get("is_retreatment_visit", False) or visit.get("is_retreatment", False):
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
                        if retreat_count > 0:
                            has_retreated = True
                            if has_discontinued:
                                current_state = "discontinued_after_retreatment"
                            else:
                                current_state = "active_retreated"
            
            # Count this patient's state
            states[current_state] += 1
        
        # Record all states for this month
        for state, count in states.items():
            timeline_data.append({
                'time': month,  # Use 'time' instead of 'time_months' for test compatibility
                'state': state,
                'count': count
            })
        
        # Debug output at key months
        if month in [0, 6, 12, 24]:
            total = sum(states.values())
            print(f"Month {month}: Total={total}")
            for state, count in sorted(states.items()):
                if count > 0:
                    print(f"  {state}: {count}")
    
    return pd.DataFrame(timeline_data)


def generate_fixed_streamgraph(results: Dict) -> plt.Figure:
    """Generate streamgraph from patient_histories with proper state tracking."""
    
    if not results:
        raise ValueError("No simulation results provided")
    
    # Count patient states from list format
    timeline_data = count_patient_states_from_visits(results)
    
    # Pivot for stacking
    pivot_data = timeline_data.pivot(
        index='time',
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
            
            ax.fill_between(x, bottom, bottom + values, 
                          label=display_names.get(state, state),
                          color=color, alpha=0.8)
            bottom += values
    
    # Add total line
    ax.plot(x, bottom, color='black', linewidth=2, label='Total Population',
            linestyle='--', alpha=0.7)
    
    # Configure axes
    ax.set_xlabel('Months', fontsize=12)
    ax.set_ylabel('Patient Count', fontsize=12)
    ax.set_title('Patient Treatment Status Over Time', fontsize=16, fontweight='bold')
    
    # Configure x-axis
    ax.set_xlim(0, max(x))
    ax.set_xticks(range(0, int(max(x)) + 1, 12))
    
    # Add grid
    ax.grid(True, axis='y', alpha=0.3)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    # Add legend
    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', frameon=False)
    
    plt.tight_layout()
    return fig