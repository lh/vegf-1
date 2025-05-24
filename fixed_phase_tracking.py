#!/usr/bin/env python3
"""
Script to test the fixed phase tracking visualization.
This script loads a previously saved simulation results file and analyzes
the patient states to identify discontinuation types correctly.
"""

import os
import sys
import json
import argparse
import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict
from datetime import datetime, timedelta
import pandas as pd

def analyze_phase_transitions(patient_visits):
    """
    Analyze a patient's treatment phases to identify discontinuations and retreatments.
    
    Parameters
    ----------
    patient_visits : List[Dict]
        List of visit dictionaries for a single patient
        
    Returns
    -------
    Dict[str, Any]
        Dictionary with discontinuation and retreatment information
    """
    if not patient_visits:
        return {
            "has_discontinued": False,
            "has_retreated": False,
            "discontinuation_type": None,
            "phase_transitions": []
        }
    
    # Sort visits by date
    sorted_visits = sorted(patient_visits, key=lambda v: v.get("date", v.get("time", 0)))
    
    # Track phase transitions
    phases = []
    phase_transition_indices = []
    
    for i, visit in enumerate(sorted_visits):
        phase = visit.get("phase", "unknown")
        phases.append(phase)
        
        # Check for phase transition
        if i > 0 and phase != phases[i-1]:
            phase_transition_indices.append(i)
    
    # Identify discontinuation and retreatment events
    has_discontinued = False
    has_retreated = False
    discontinuation_type = None
    retreatment_count = 0
    
    # Process phase transitions
    phase_transitions = []
    
    # Track the latest discontinuation type
    latest_discontinuation_type = None
    latest_discontinuation_index = -1
    
    for i in phase_transition_indices:
        prev_phase = phases[i-1]
        curr_phase = phases[i]
        
        phase_transitions.append({
            "index": i,
            "from_phase": prev_phase,
            "to_phase": curr_phase,
            "visit": sorted_visits[i]
        })
        
        # Treatment -> Monitoring transition = discontinuation
        if curr_phase == "monitoring" and prev_phase in ["loading", "maintenance"]:
            has_discontinued = True
            
            # Store the index for this discontinuation
            latest_discontinuation_index = i
            
            # Try to determine discontinuation type from various sources
            
            # 1. Check if the visit has a specific discontinuation reason
            current_visit = sorted_visits[i]
            reason = (current_visit.get("discontinuation_reason") or 
                     current_visit.get("reason") or 
                     current_visit.get("cessation_type"))
            
            # Debug discontinuation reason
            # print(f"DEBUG: Detected discontinuation reason: {reason}")
            
            # 2. Check the previous visit's interval
            interval = sorted_visits[i-1].get("interval")
            
            # 3. Look for disease state
            disease_state = current_visit.get("disease_state")
            
            # Determine type based on available information
            if reason:
                # Map various reason strings to our standardized types
                reason_lower = str(reason).lower()
                
                # Enhanced pattern matching for all discontinuation types
                if any(k in reason_lower for k in ["stable_max", "stable_max_interval", "planned", "patient_choice", "stable"]):
                    latest_discontinuation_type = "planned"
                elif any(k in reason_lower for k in ["admin", "administrative", "random_admin", "random_administrative"]):
                    latest_discontinuation_type = "administrative"
                elif any(k in reason_lower for k in ["premature", "early", "therapy_failure"]):
                    latest_discontinuation_type = "premature"
                elif any(k in reason_lower for k in ["not_renewed", "not renewed", "course_complete", "course_complete_but_not_renewed", "treatment_duration"]):
                    latest_discontinuation_type = "not_renewed"
                else:
                    # Debug unrecognized reason
                    print(f"WARNING: Unrecognized discontinuation reason: {reason_lower}")
                    # Default fallback
                    latest_discontinuation_type = "not_renewed"
            
            # If no reason found, look for cessation_type directly in the visit
            elif current_visit.get("cessation_type"):
                latest_discontinuation_type = current_visit.get("cessation_type")
            # Try previous visit cessation_type
            elif sorted_visits[i-1].get("cessation_type"):
                latest_discontinuation_type = sorted_visits[i-1].get("cessation_type")
            # Use interval logic as a fallback
            elif interval is not None:
                if interval >= 12:
                    # Long interval suggests planned discontinuation
                    latest_discontinuation_type = "planned"
                else:
                    # Shorter interval might be premature
                    latest_discontinuation_type = "premature"
            else:
                # Check for administrative and not_renewed patterns
                visit_type = current_visit.get("visit_type", "").lower()
                if "administrative" in visit_type or "admin" in visit_type:
                    latest_discontinuation_type = "administrative"
                elif "course_complete" in visit_type or "not_renewed" in visit_type:
                    latest_discontinuation_type = "not_renewed"
                else:
                    # Default
                    latest_discontinuation_type = "not_renewed"
        
        # Monitoring -> Treatment transition = retreatment
        if curr_phase in ["loading", "maintenance"] and prev_phase == "monitoring":
            has_retreated = True
            retreatment_count += 1
    
    # Use the most recent discontinuation type
    discontinuation_type = latest_discontinuation_type
    
    return {
        "has_discontinued": has_discontinued,
        "has_retreated": has_retreated,
        "discontinuation_type": discontinuation_type,
        "retreat_count": retreatment_count,
        "phase_transitions": phase_transitions
    }

def determine_patient_state(patient_analysis):
    """
    Determine a patient's current state based on phase transition analysis.
    
    Parameters
    ----------
    patient_analysis : Dict[str, Any]
        Result from analyze_phase_transitions
        
    Returns
    -------
    str
        Patient state code
    """
    has_discontinued = patient_analysis["has_discontinued"]
    has_retreated = patient_analysis["has_retreated"]
    discontinuation_type = patient_analysis["discontinuation_type"]
    retreat_count = patient_analysis.get("retreat_count", 0)
    
    # Get final phase if available
    final_phase = None
    if len(patient_analysis.get("phase_transitions", [])) > 0:
        # Get the last transition's phase
        final_phase = patient_analysis["phase_transitions"][-1]["to_phase"]
    
    # Initialize state
    state = "active"
    
    # Determine the current state based on most recent status
    
    # Case 1: Currently in a monitoring phase (discontinued)
    if final_phase == "monitoring":
        # Patient is in a discontinued state
        if discontinuation_type:
            # Normalize the discontinuation type to one of our expected types
            normalized_type = discontinuation_type
            if "stable" in discontinuation_type or "planned" in discontinuation_type:
                normalized_type = "planned"
            elif "admin" in discontinuation_type:
                normalized_type = "administrative"
            elif "premature" in discontinuation_type or "early" in discontinuation_type:
                normalized_type = "premature"
            elif "not_renewed" in discontinuation_type or "course_complete" in discontinuation_type:
                normalized_type = "not_renewed"
            
            state = f"discontinued_{normalized_type}"
        else:
            state = "discontinued_not_renewed"  # Default type if unknown
    
    # Case 2: Currently in treatment phase
    else:
        # Check if this is a retreated patient
        if has_retreated:
            state = "active_retreated"
        else:
            state = "active"
    
    return state

def analyze_patient_states(results):
    """Analyze patient states from simulation results."""
    patient_histories = results.get("patient_histories", {})
    if not patient_histories:
        print("No patient histories found")
        return {}
    
    # Get reference date
    all_dates = []
    for patient_id, visits in patient_histories.items():
        for visit in visits:
            date_val = visit.get("date", visit.get("time"))
            if date_val and isinstance(date_val, (datetime, str, pd.Timestamp)):
                all_dates.append(date_val)
                break
    
    if all_dates:
        if isinstance(all_dates[0], str):
            try:
                start_date = datetime.fromisoformat(all_dates[0].replace(" ", "T"))
            except ValueError:
                start_date = pd.to_datetime(all_dates[0])
        else:
            start_date = all_dates[0]
    else:
        start_date = datetime.now()
    
    # Define all expected states
    all_states = [
        'active',
        'active_retreated',
        'discontinued_planned',
        'discontinued_administrative',
        'discontinued_not_renewed',
        'discontinued_premature'
    ]
    
    # Count states at each time point
    duration_years = results.get("duration_years", 5)
    duration_months = int(duration_years * 12)
    
    timeline_data = []
    
    # Process each month
    for month in range(duration_months + 1):
        states = defaultdict(int)
        
        # Month cutoff
        month_cutoff = start_date + timedelta(days=month*30)
        
        # Process each patient
        for patient_id, visits in patient_histories.items():
            # Get visits up to the current month
            visits_to_month = []
            for visit in visits:
                visit_date = visit.get("date", visit.get("time"))
                
                # Convert to datetime if needed
                if isinstance(visit_date, str):
                    try:
                        visit_date = datetime.fromisoformat(visit_date.replace(" ", "T"))
                    except ValueError:
                        visit_date = pd.to_datetime(visit_date)
                elif isinstance(visit_date, (int, float)):
                    visit_date = start_date + timedelta(days=visit_date)
                
                if visit_date <= month_cutoff:
                    visits_to_month.append(visit)
            
            # Analyze phase transitions
            analysis = analyze_phase_transitions(visits_to_month)
            
            # Determine patient state
            state = determine_patient_state(analysis)
            
            # Count this state
            states[state] += 1
        
        # Record all states for this month, including zeros
        for state in all_states:
            timeline_data.append({
                'time': month,
                'state': state,
                'count': states.get(state, 0)  # Use 0 if not counted
            })
        
        # Debug output at key timepoints
        if month in [0, 12, 24, 36, 48, 60]:
            print(f"\nMonth {month}:")
            for state in all_states:
                print(f"  {state}: {states.get(state, 0)}")
    
    # Create dataframe
    return pd.DataFrame(timeline_data)

def generate_streamgraph(timeline_data, output_file=None):
    """Generate a streamgraph visualization."""
    # Pivot for stacking
    pivot_data = timeline_data.pivot(
        index='time',
        columns='state',
        values='count'
    ).fillna(0)
    
    # Create figure
    fig, ax = plt.subplots(figsize=(14, 8))
    
    # State ordering
    state_order = [
        'active',
        'active_retreated',
        'discontinued_planned',
        'discontinued_administrative',
        'discontinued_not_renewed',
        'discontinued_premature'
    ]
    
    # Traffic light colors for patient states
    TRAFFIC_LIGHT_COLORS = {
        "active": "#006400",  # Strong green
        "active_retreated": "#228B22",  # Medium green
        "discontinued_planned": "#FFA500",  # Amber
        "discontinued_administrative": "#DC143C",  # Red
        "discontinued_not_renewed": "#B22222",  # Red
        "discontinued_premature": "#8B0000"  # Dark red
    }
    
    # Display names for states
    STATE_DISPLAY_NAMES = {
        'active': 'Active (Never Discontinued)',
        'active_retreated': 'Active (Retreated)',
        'discontinued_planned': 'Discontinued Planned',
        'discontinued_administrative': 'Discontinued Administrative',
        'discontinued_not_renewed': 'Discontinued Not Renewed',
        'discontinued_premature': 'Discontinued Premature'
    }
    
    # Create stacked area plot
    x = pivot_data.index
    bottom = np.zeros(len(x))
    
    # Track which states are actually in the data with non-zero values
    states_with_data = []
    
    for state in state_order:
        if state in pivot_data.columns:
            values = pivot_data[state].values
            max_value = values.max() if len(values) > 0 else 0
            
            # Always show the state even if counts are zero
            color = TRAFFIC_LIGHT_COLORS.get(state, "#808080")
            label = STATE_DISPLAY_NAMES.get(state, state)
                
            ax.fill_between(x, bottom, bottom + values, 
                         label=label, color=color, alpha=0.8)
            bottom += values
            
            if max_value > 0:
                states_with_data.append(state)
                print(f"State: {state}, Max value: {max_value}")
    
    # Configure axes
    ax.set_xlabel('Months', fontsize=12)
    ax.set_ylabel('Patient Count', fontsize=12)
    ax.set_title('Patient Treatment Status Over Time', fontsize=16, fontweight='bold')
    
    # Configure x-axis
    ax.set_xlim(0, max(x))
    ax.set_xticks(range(0, int(max(x)) + 1, 12))
    ax.set_xticklabels([f'{y}' for y in range(0, (int(max(x)) // 12) + 1)])
    ax.set_xlabel('Time (years)', fontsize=12)
    
    # Add grid
    ax.grid(True, axis='y', alpha=0.3)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    # Add legend
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles, labels, bbox_to_anchor=(1.05, 1), 
              loc='upper left', frameon=False, fontsize=10)
    
    plt.tight_layout()
    
    # Save if output file specified
    if output_file:
        fig.savefig(output_file, dpi=300, bbox_inches="tight")
        print(f"Saved streamgraph to {output_file}")
    
    return fig

def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Generate fixed phase tracking visualization.")
    parser.add_argument("--input", type=str, required=True,
                       help="Path to simulation results JSON file")
    parser.add_argument("--output", type=str, default=None,
                       help="Path to save output visualization")
    return parser.parse_args()

def main():
    """Main function."""
    # Parse arguments
    args = parse_args()
    
    # Load results
    print(f"Loading simulation results from {args.input}")
    with open(args.input, 'r') as f:
        results = json.load(f)
    
    # Analyze patient states
    print("Analyzing patient states...")
    timeline_data = analyze_patient_states(results)
    
    # Generate visualization
    print("Generating streamgraph visualization...")
    output_file = args.output
    if not output_file:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"fixed_phase_tracking_{timestamp}.png"
    
    fig = generate_streamgraph(timeline_data, output_file)
    
    # Show visualization
    plt.show()

if __name__ == "__main__":
    main()