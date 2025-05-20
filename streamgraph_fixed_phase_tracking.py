#!/usr/bin/env python3
"""
Improved streamgraph implementation that properly tracks patient phases and transitions.

This version recognizes phase transitions (treatment -> monitoring -> treatment)
as discontinuation and retreatment events rather than looking for explicit flags.
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

def analyze_phase_transitions(patient_visits: List[Dict]) -> Dict[str, Any]:
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
                     current_visit.get("discontinuation_type"))
            
            # 2. Check the previous visit's interval
            interval = sorted_visits[i-1].get("interval")
            
            # 3. Look for disease state
            disease_state = current_visit.get("disease_state")
            
            # Determine type based on available information
            if reason:
                # Map various reason strings to our standardized types
                reason_lower = str(reason).lower()
                
                if any(k in reason_lower for k in ["stable_max", "planned", "patient_choice", "stable"]):
                    latest_discontinuation_type = "planned"
                elif any(k in reason_lower for k in ["admin", "random_admin"]):
                    latest_discontinuation_type = "administrative"
                elif any(k in reason_lower for k in ["premature", "early"]):
                    latest_discontinuation_type = "premature"
                elif any(k in reason_lower for k in ["not_renewed", "not renewed", "course_complete"]):
                    latest_discontinuation_type = "not_renewed"
                else:
                    # Default fallback
                    latest_discontinuation_type = "not_renewed"
            
            # If no reason found, use interval logic
            elif interval is not None:
                if interval >= 12:
                    # Long interval suggests planned discontinuation
                    latest_discontinuation_type = "planned"
                else:
                    # Shorter interval might be premature
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
            state = f"discontinued_{discontinuation_type}"
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
            analysis = analyze_phase_transitions(visits_to_month)
            
            # Determine patient state
            state = determine_patient_state(analysis)
            
            # Count this patient's state
            states[state] += 1
        
        # Record all states for this month
        for state, count in states.items():
            timeline_data.append({
                'time': month,
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
    fig, ax = plt.subplots(figsize=(12, 8))
    
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
    
    for state in state_order:
        if state in pivot_data.columns:
            values = pivot_data[state].values
            color = TRAFFIC_LIGHT_COLORS.get(state, "#808080")
            
            ax.fill_between(x, bottom, bottom + values, 
                          label=STATE_DISPLAY_NAMES.get(state, state),
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

# This function can be called directly from command line scripts
if __name__ == "__main__":
    import json
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python streamgraph_fixed_phase_tracking.py <results_file.json>")
        sys.exit(1)
    
    results_file = sys.argv[1]
    
    try:
        with open(results_file, 'r') as f:
            results = json.load(f)
        
        fig = generate_phase_tracking_streamgraph(results)
        
        output_file = results_file.replace('.json', '_streamgraph_phase.png')
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