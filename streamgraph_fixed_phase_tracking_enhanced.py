#!/usr/bin/env python3
"""
Enhanced streamgraph implementation that properly tracks patient phases and transitions.

This version recognizes phase transitions (treatment -> monitoring -> treatment)
as discontinuation and retreatment events rather than looking for explicit flags.

It includes enhanced detection logic for all discontinuation types, particularly
administrative and not_renewed discontinuations which were previously missed.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List, Any, Optional, Tuple

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

def analyze_phase_transitions(patient_visits: List[Dict], 
                             patient_id: Optional[str] = None,
                             discontinuation_types: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """
    Analyze a patient's treatment phases to identify discontinuations and retreatments.
    
    Enhanced to better detect all discontinuation types, especially administrative
    and not_renewed discontinuations.
    
    Parameters
    ----------
    patient_visits : List[Dict]
        List of visit dictionaries for a single patient
    patient_id : Optional[str]
        ID of the patient, for accessing discontinuation_types if available
    discontinuation_types : Optional[Dict[str, str]]
        Mapping of patient_id to discontinuation type from discontinuation manager
        
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
    
    # Direct access to discontinuation type if available
    if discontinuation_types and patient_id in discontinuation_types:
        # Use the discontinuation type directly from the manager
        direct_type = discontinuation_types[patient_id]
        if direct_type:
            # Normalize the type
            if "admin" in direct_type:
                latest_discontinuation_type = "administrative"
            elif "not_renewed" in direct_type or "course_complete" in direct_type:
                latest_discontinuation_type = "not_renewed"
            elif "premature" in direct_type:
                latest_discontinuation_type = "premature"
            elif "planned" in direct_type or "stable" in direct_type:
                latest_discontinuation_type = "planned"
            else:
                latest_discontinuation_type = direct_type
    
    # Look for explicit discontinuation flags even without phase transitions
    for i, visit in enumerate(sorted_visits):
        if visit.get("is_discontinuation_visit", False):
            has_discontinued = True
            
            # Try to determine discontinuation type from visit
            reason = (visit.get("discontinuation_reason") or 
                     visit.get("reason") or 
                     visit.get("cessation_type") or
                     visit.get("discontinuation_type"))
            
            if reason:
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
    
    # Process phase transitions
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
            
            # If we already have a discontinuation type from direct access, don't override it
            if not latest_discontinuation_type:
                # Try to determine discontinuation type from various sources
                
                # 1. Check if the visit has a specific discontinuation reason
                current_visit = sorted_visits[i]
                reason = (current_visit.get("discontinuation_reason") or 
                         current_visit.get("reason") or 
                         current_visit.get("cessation_type") or
                         current_visit.get("discontinuation_type"))
                
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
                        # Default fallback
                        latest_discontinuation_type = "not_renewed"
                
                # If no reason found, look for cessation_type directly in the visit
                elif current_visit.get("cessation_type"):
                    direct_type = current_visit.get("cessation_type")
                    # Normalize the type
                    if "admin" in direct_type:
                        latest_discontinuation_type = "administrative"
                    elif "not_renewed" in direct_type or "course_complete" in direct_type:
                        latest_discontinuation_type = "not_renewed"
                    elif "premature" in direct_type:
                        latest_discontinuation_type = "premature"
                    elif "planned" in direct_type or "stable" in direct_type:
                        latest_discontinuation_type = "planned"
                    else:
                        latest_discontinuation_type = direct_type
                # Try previous visit cessation_type
                elif i > 0 and sorted_visits[i-1].get("cessation_type"):
                    direct_type = sorted_visits[i-1].get("cessation_type")
                    # Normalize the type
                    if "admin" in direct_type:
                        latest_discontinuation_type = "administrative"
                    elif "not_renewed" in direct_type or "course_complete" in direct_type:
                        latest_discontinuation_type = "not_renewed"
                    elif "premature" in direct_type:
                        latest_discontinuation_type = "premature"
                    elif "planned" in direct_type or "stable" in direct_type:
                        latest_discontinuation_type = "planned"
                    else:
                        latest_discontinuation_type = direct_type
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
                        # Look at treatment duration
                        first_visit_time = sorted_visits[0].get("time")
                        if isinstance(first_visit_time, (int, float)) and \
                           isinstance(current_visit.get("time"), (int, float)):
                            treatment_weeks = (current_visit.get("time") - first_visit_time) / 7
                            if treatment_weeks >= 52:
                                # Approximately 1 year of treatment suggests completed course
                                latest_discontinuation_type = "not_renewed"
                            else:
                                # Default
                                latest_discontinuation_type = "premature"
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

def determine_patient_state(patient_analysis: Dict[str, Any]) -> str:
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
            if isinstance(normalized_type, str):
                if "stable" in normalized_type or "planned" in normalized_type:
                    normalized_type = "planned"
                elif "admin" in normalized_type:
                    normalized_type = "administrative"
                elif "premature" in normalized_type or "early" in normalized_type:
                    normalized_type = "premature"
                elif "not_renewed" in normalized_type or "course_complete" in normalized_type:
                    normalized_type = "not_renewed"
            
            state = f"discontinued_{normalized_type}"
        else:
            state = "discontinued_not_renewed"  # Default type if unknown
    
    # Case 2: Discontinued but then retreated
    elif has_discontinued and has_retreated:
        state = "active_retreated"
    
    # Case 3: Never discontinued
    else:
        state = "active"
    
    return state

def count_patient_states_by_phase(results: Dict) -> pd.DataFrame:
    """
    Count patient states based on phase transitions in visit data.
    
    Parameters
    ----------
    results : Dict
        Simulation results dictionary
        
    Returns
    -------
    pd.DataFrame
        DataFrame with patient state counts over time
    """
    # Get patient_histories - dict where values are lists of visits
    patient_histories = results.get("patient_histories", {})
    
    if not patient_histories:
        raise ValueError("No patient history data in results['patient_histories']")
    
    duration_years = results.get("duration_years", 5)
    duration_months = int(duration_years * 12)
    
    # Find the earliest visit date across all patients
    all_dates = []
    for patient_id, visits in patient_histories.items():
        for visit in visits:
            date_val = visit.get("date", visit.get("time"))
            if date_val and isinstance(date_val, (datetime, pd.Timestamp)):
                all_dates.append(date_val)
    
    # Get reference date
    if all_dates:
        start_date = min(all_dates)
    else:
        start_date = datetime.now()
    
    timeline_data = []
    
    # Define all expected states
    all_states = [
        'active',
        'active_retreated',
        'discontinued_planned',
        'discontinued_administrative',
        'discontinued_not_renewed',
        'discontinued_premature'
    ]
    
    # Try to get discontinuation types directly from manager if available
    direct_discontinuation_types = {}
    if "raw_discontinuation_stats" in results:
        # Extract discontinuation types from raw stats if available
        raw_stats = results.get("raw_discontinuation_stats", {})
        if "discontinuation_types" in raw_stats:
            direct_discontinuation_types = raw_stats["discontinuation_types"]
    
    # Count states at each month
    for month in range(duration_months + 1):
        states = defaultdict(int)
        
        # Process each patient
        for patient_id, visits in patient_histories.items():
            # Get visits up to the current month
            month_cutoff = start_date + timedelta(days=month*30)
            
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
            
            # Analyze the patient's phase transitions
            analysis = analyze_phase_transitions(
                visits_to_month, 
                patient_id=patient_id,
                discontinuation_types=direct_discontinuation_types
            )
            
            # Determine patient state
            state = determine_patient_state(analysis)
            
            # Count this patient's state
            states[state] += 1
        
        # Record all states for this month - important: include ALL possible states
        for state in all_states:
            timeline_data.append({
                'time': month,
                'state': state,
                'count': states.get(state, 0)  # Use 0 if the state wasn't detected
            })
        
        # Debug output at key months
        if month in [0, 6, 12, 24, 36, 48, 60]:
            total = sum(states.values())
            print(f"Month {month}: Total={total}")
            print(f"  States present: {len([s for s in states if states[s] > 0])}/{len(all_states)}")
            for state in all_states:
                # Print all states, even those with zero count for debugging
                count = states.get(state, 0)
                print(f"  {state}: {count}")
            
            # If we have discontinuation types from the manager, print them
            if month == duration_months:
                # Only print at the final month
                disc_types = {}
                for patient_id, state in direct_discontinuation_types.items():
                    if state not in disc_types:
                        disc_types[state] = 0
                    disc_types[state] += 1
                
                if disc_types:
                    print("\n  Discontinuation types from manager:")
                    for type_name, count in sorted(disc_types.items()):
                        print(f"    {type_name}: {count}")
    
    return pd.DataFrame(timeline_data)

def generate_phase_tracking_streamgraph(results: Dict) -> plt.Figure:
    """
    Generate streamgraph from patient_histories with phase transition tracking.
    
    Parameters
    ----------
    results : Dict
        Simulation results
        
    Returns
    -------
    plt.Figure
        Matplotlib figure with streamgraph
    """
    if not results:
        raise ValueError("No simulation results provided")
    
    # Count patient states from phase transitions
    timeline_data = count_patient_states_by_phase(results)
    
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
    
    # Create stacked area plot
    x = pivot_data.index
    bottom = np.zeros(len(x))
    
    # Track which states are actually in the data with non-zero values
    states_with_data = []
    
    for state in state_order:
        # Force display of all states, even if they have low or zero counts
        # This ensures all 6 states appear in the visualization
        if state in pivot_data.columns:
            values = pivot_data[state].values
            max_value = values.max() if len(values) > 0 else 0
            
            # Print state information to help with debugging
            print(f"State: {state}, Max value: {max_value}")
            
            # Always show the state even if counts are zero
            # This ensures all 6 states are visible in the legend
            color = TRAFFIC_LIGHT_COLORS.get(state, "#808080")
            label = STATE_DISPLAY_NAMES.get(state, state)
                
            ax.fill_between(x, bottom, bottom + values, 
                         label=label, color=color, alpha=0.8)
            bottom += values
            
            if max_value > 0:
                states_with_data.append(state)
    
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
    
    # Create legend with just the state entries (no total line)
    handles, labels = ax.get_legend_handles_labels()
    
    # Add legend - show all states, even if zero counts
    ax.legend(handles, labels, bbox_to_anchor=(1.05, 1), 
              loc='upper left', frameon=False, fontsize=10)
    
    # Add annotation showing which states have data
    states_info = f"States with data: {len(states_with_data)}/{len(state_order)}\n"
    states_info += "\n".join(states_with_data)
    
    # Add annotation with discontinuation counts and total population
    disc_counts = results.get("discontinuation_counts", {})
    total_patients = results.get("patient_count", sum(pivot_data.iloc[-1, :].values))
    
    states_info += f"\n\nTotal Population: {total_patients}\n"
    if disc_counts:
        states_info += "\nDiscontinuation counts:\n"
        for type_name, count in disc_counts.items():
            percent = (count / total_patients) * 100 if total_patients > 0 else 0
            states_info += f"{type_name}: {count} ({percent:.1f}%)\n"
    
    # Position the text at the bottom right
    plt.figtext(0.98, 0.02, states_info, 
                horizontalalignment='right', 
                verticalalignment='bottom',
                fontsize=8, alpha=0.7)
    
    plt.tight_layout()
    return fig

# This function can be called directly from command line scripts
if __name__ == "__main__":
    import json
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python streamgraph_fixed_phase_tracking_enhanced.py <results_file.json>")
        sys.exit(1)
    
    results_file = sys.argv[1]
    
    try:
        with open(results_file, 'r') as f:
            results = json.load(f)
        
        fig = generate_phase_tracking_streamgraph(results)
        
        output_file = results_file.replace('.json', '_streamgraph_enhanced.png')
        fig.savefig(output_file, dpi=300, bbox_inches="tight")
        print(f"Streamgraph saved to {output_file}")
        
        # Show figure for 10 seconds then automatically close it
        from matplotlib.animation import FuncAnimation
        
        # Set up a timer to close the figure after 10 seconds
        def close_figure(frame):
            plt.close()
            
        # Create a simple animation that triggers the close function after 10 seconds
        ani = FuncAnimation(fig, close_figure, frames=[0], interval=10000, repeat=False)
        
        print("Figure will automatically close after 10 seconds...")
        plt.show()
    except Exception as e:
        import traceback
        print(f"Error: {e}")
        traceback.print_exc()