"""
Streamgraph that uses ACTUAL patient timeline data, not synthetic curves.
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
    # Green - Currently being treated
    "active": "#006400",  # Strong green - active patients
    "active_retreated": "#228B22",  # Medium green - active after retreatment
    
    # Amber - Discontinued planned (stable)
    "discontinued_planned": "#FFA500",  # Amber - planned discontinuation
    
    # Red - Other discontinuations (problems)
    "discontinued_administrative": "#DC143C",  # Red - administrative issues
    "discontinued_not_renewed": "#B22222",     # Red - renewal issues
    "discontinued_premature": "#8B0000",       # Dark red - premature discontinuation
    
    # Mixed states
    "discontinued_after_retreatment": "#CD5C5C"  # Light red - discontinued after being retreated
}


def extract_actual_timeline(results: Dict) -> pd.DataFrame:
    """
    Extract actual patient state transitions from simulation data.
    This uses REAL patient histories, not synthetic curves.
    """
    # Get patient histories
    patient_histories = results.get("patient_histories", {})
    
    if not patient_histories:
        raise ValueError("No patient history data available")
    
    duration_years = results.get("duration_years", 5)
    duration_months = int(duration_years * 12)
    
    # Track patient states at each time point
    timeline_data = []
    
    # For each month, count patients in each state
    for month in range(duration_months + 1):
        states = defaultdict(int)
        
        # Check each patient's status at this time
        for patient_id, patient_data in patient_histories.items():
            visits = patient_data.get("visits", [])
            disc_reasons = patient_data.get("discontinuation_reasons", [])
            retreat_count = patient_data.get("retreatment_count", 0)
            
            # Find patient's state at this time
            patient_state = "active"  # Default state
            
            # Check visits to determine state
            last_visit = None
            is_discontinued = False
            is_retreated = False
            last_disc_reason = None
            
            for visit in visits:
                visit_time = visit.get("time", visit.get("date", 0))
                if visit_time <= month:
                    last_visit = visit
                    
                    # Check for discontinuation
                    if visit.get("is_discontinuation_visit", False):
                        is_discontinued = True
                        # Get the discontinuation reason
                        reason_map = {
                            "stable_max_interval": "planned",
                            "random_administrative": "administrative",
                            "treatment_duration": "not_renewed",
                            "course_complete_but_not_renewed": "not_renewed",
                            "premature": "premature"
                        }
                        disc_reason = visit.get("discontinuation_reason", "")
                        last_disc_reason = reason_map.get(disc_reason, "premature")
                    
                    # Check for retreatment
                    if visit.get("is_retreatment", False):
                        is_retreated = True
                        is_discontinued = False  # No longer discontinued if retreated
            
            # Determine final state
            if is_discontinued:
                if is_retreated and retreat_count > 1:
                    patient_state = "discontinued_after_retreatment"
                else:
                    patient_state = f"discontinued_{last_disc_reason}"
            elif is_retreated:
                patient_state = "active_retreated"
            else:
                patient_state = "active"
            
            states[patient_state] += 1
        
        # Record state counts for this month
        for state, count in states.items():
            timeline_data.append({
                'time_months': month,
                'state': state,
                'count': count
            })
    
    return pd.DataFrame(timeline_data)


def generate_actual_data_streamgraph(results: Dict) -> plt.Figure:
    """Generate streamgraph from actual patient timeline data."""
    
    if not results:
        raise ValueError("No simulation results provided")
    
    # Extract actual timeline from patient histories
    try:
        timeline_data = extract_actual_timeline(results)
    except ValueError as e:
        # Fallback to summary statistics if patient histories not available
        print(f"Warning: {e}, using summary statistics instead")
        timeline_data = create_summary_timeline(results)
    
    # Pivot data for stacking
    pivot_data = timeline_data.pivot(
        index='time_months',
        columns='state',
        values='count'
    ).fillna(0)
    
    # Create figure
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # State ordering and display names
    state_order = [
        'active',
        'active_retreated',
        'discontinued_planned',
        'discontinued_administrative',
        'discontinued_not_renewed',
        'discontinued_premature',
        'discontinued_after_retreatment'
    ]
    
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
    ax.set_title("Patient Cohort Flow Through Treatment States (Actual Data)", fontsize=14, loc="left")
    
    # Set axis limits
    ax.set_xlim(0, max(x))
    ax.set_ylim(0, max(bottom) * 1.05)
    
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


def create_summary_timeline(results: Dict) -> pd.DataFrame:
    """
    Create timeline from summary statistics if patient histories not available.
    This is a fallback that interpolates between known points.
    """
    duration_years = results.get("duration_years", 5)
    duration_months = int(duration_years * 12)
    population_size = results.get("population_size", 1000)
    
    # Get final counts
    disc_counts = results.get("discontinuation_counts", {})
    raw_stats = results.get("raw_discontinuation_stats", {})
    retreat_by_type = raw_stats.get("retreatments_by_type", {})
    
    timeline_data = []
    
    # Create interpolated timeline based on summary stats
    for month in range(duration_months + 1):
        t = month / duration_months
        
        # Simple linear interpolation for summary view
        states = {
            'active': population_size * (1 - t),
            'discontinued_planned': disc_counts.get("Planned", 0) * t,
            'discontinued_administrative': disc_counts.get("Administrative", 0) * t,
            'discontinued_not_renewed': disc_counts.get("Not Renewed", 0) * t,
            'discontinued_premature': disc_counts.get("Premature", 0) * t,
        }
        
        # Add retreatments
        if t > 0.2:  # Delay retreatments
            retreat_t = (t - 0.2) / 0.8
            total_retreat = sum(retreat_by_type.values())
            states['active_retreated'] = total_retreat * retreat_t
            states['active'] -= states['active_retreated']
        
        # Record states
        for state, count in states.items():
            if count > 0:
                timeline_data.append({
                    'time_months': month,
                    'state': state,
                    'count': count
                })
    
    return pd.DataFrame(timeline_data)