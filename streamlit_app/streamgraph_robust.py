"""
Robust streamgraph that handles actual patient data structure.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, List, Union
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


def diagnose_data_structure(results: Dict) -> tuple:
    """Diagnose the actual structure of patient data and return the right field."""
    
    print("=== DIAGNOSING DATA STRUCTURE ===")
    
    # Check what type patient_histories is
    patient_histories = results.get("patient_histories", {})
    
    print(f"patient_histories type: {type(patient_histories)}")
    
    if isinstance(patient_histories, list):
        print(f"  It's a list with {len(patient_histories)} items")
        if patient_histories:
            first_item = patient_histories[0]
            print(f"  First item type: {type(first_item)}")
            if isinstance(first_item, dict):
                print(f"  First item keys: {list(first_item.keys())[:10]}")
                # Convert list to dict with patient_id as key if needed
                if 'patient_id' in first_item:
                    patient_dict = {p['patient_id']: p for p in patient_histories}
                    return patient_dict, "list_with_id"
                else:
                    # Use index as key
                    patient_dict = {str(i): p for i, p in enumerate(patient_histories)}
                    return patient_dict, "list_indexed"
        return {}, "empty_list"
        
    elif isinstance(patient_histories, dict):
        print(f"  It's a dict with {len(patient_histories)} keys")
        if patient_histories:
            first_key = list(patient_histories.keys())[0]
            first_patient = patient_histories[first_key]
            print(f"  First key: {first_key}")
            print(f"  First patient type: {type(first_patient)}")
            if isinstance(first_patient, dict):
                print(f"  First patient keys: {list(first_patient.keys())[:10]}")
            elif isinstance(first_patient, list):
                print(f"  First patient is a list with {len(first_patient)} items")
        return patient_histories, "dict"
    
    else:
        print(f"  Unexpected type: {type(patient_histories)}")
        return {}, "unknown"


def count_patient_states_robust(results: Dict) -> pd.DataFrame:
    """
    Count actual patient states from real data, handling different structures.
    """
    # Diagnose and get the correct patient data
    patient_data, data_type = diagnose_data_structure(results)
    
    if not patient_data:
        raise ValueError(f"No patient data available (type: {data_type})")
    
    duration_years = results.get("duration_years", 5)
    duration_months = int(duration_years * 12)
    population_size = results.get("population_size", 1000)
    
    print(f"\nProcessing {len(patient_data)} patients over {duration_months} months")
    
    # Sample a patient to understand structure
    sample_key = list(patient_data.keys())[0]
    sample_patient = patient_data[sample_key]
    
    print(f"\nSample patient key: {sample_key}")
    print(f"Sample patient type: {type(sample_patient)}")
    
    if isinstance(sample_patient, dict):
        print(f"Sample patient keys: {list(sample_patient.keys())[:10]}")
        visits = sample_patient.get("visits", [])
        print(f"Number of visits: {len(visits)}")
        if visits and isinstance(visits[0], dict):
            print(f"First visit keys: {list(visits[0].keys())}")
            print(f"First visit: {visits[0]}")
    
    # Count states for every month
    timeline_data = []
    
    for month in range(duration_months + 1):
        states = defaultdict(int)
        
        # Process each patient
        for patient_id, patient in patient_data.items():
            # Handle different patient data structures
            if isinstance(patient, dict):
                visits = patient.get("visits", [])
            elif isinstance(patient, list):
                # Patient might be a list of visits
                visits = patient
            else:
                visits = []
            
            # Track state at this month
            current_state = "active"
            disc_reason = None
            retreat_count = 0
            
            # Process visits up to current month
            for visit in visits:
                if isinstance(visit, dict):
                    # Get visit time
                    visit_time = visit.get("time", visit.get("date", visit.get("month", 0)))
                    
                    if visit_time <= month:
                        # Check discontinuation
                        if visit.get("is_discontinuation_visit", False) or visit.get("discontinuation", False):
                            # Map reasons
                            reason = visit.get("discontinuation_reason", visit.get("reason", ""))
                            reason_map = {
                                "stable_max_interval": "planned",
                                "planned": "planned",
                                "random_administrative": "administrative",
                                "administrative": "administrative",
                                "treatment_duration": "not_renewed",
                                "course_complete_but_not_renewed": "not_renewed",
                                "not_renewed": "not_renewed",
                                "premature": "premature"
                            }
                            disc_reason = reason_map.get(reason, "premature")
                            current_state = f"discontinued_{disc_reason}"
                        
                        # Check retreatment
                        if visit.get("is_retreatment", False) or visit.get("retreatment", False):
                            retreat_count += 1
                            if retreat_count > 1:
                                current_state = "discontinued_after_retreatment"
                            else:
                                current_state = "active_retreated"
            
            states[current_state] += 1
        
        # Verify conservation
        total = sum(states.values())
        if abs(total - population_size) > 1:
            print(f"WARNING: Month {month} - Total {total} != {population_size}")
        
        # Record states
        for state, count in states.items():
            timeline_data.append({
                'time_months': month,
                'state': state,
                'count': count
            })
        
        # Debug key months
        if month in [0, 12, 24, 36, 48, 60]:
            print(f"\nMonth {month}:")
            for state, count in sorted(states.items()):
                if count > 0:
                    print(f"  {state}: {count}")
    
    return pd.DataFrame(timeline_data)


def generate_robust_streamgraph(results: Dict) -> plt.Figure:
    """Generate streamgraph handling different data structures."""
    
    if not results:
        raise ValueError("No simulation results provided")
    
    # Count actual patient states
    timeline_data = count_patient_states_robust(results)
    
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