#!/usr/bin/env python3
"""
Analyze an existing simulation results file to test the updated phase tracking code.
This script loads a previously saved simulation results file and applies the
improved phase tracking functions to validate that all states are correctly identified.
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

# Add project root to path
root_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(root_dir)
from streamgraph_fixed_phase_tracking import (
    generate_phase_tracking_streamgraph,
    analyze_phase_transitions,
    determine_patient_state
)

def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Analyze existing simulation results.")
    parser.add_argument("--input", type=str, required=True,
                       help="Path to simulation results JSON file")
    return parser.parse_args()

def load_simulation_results(file_path):
    """Load simulation results from a JSON file."""
    print(f"Loading simulation results from {file_path}")
    
    try:
        with open(file_path, 'r') as f:
            results = json.load(f)
        
        # Check if the file contains patient histories
        if "patient_histories" not in results:
            print("Error: No patient histories found in the file")
            return None
        
        print(f"Successfully loaded results with {len(results['patient_histories'])} patients")
        return results
    
    except Exception as e:
        print(f"Error loading simulation results: {e}")
        return None

def analyze_simulation_results(results):
    """Analyze the simulation results and count discontinuation types."""
    print("\n=== Analyzing Simulation Results ===\n")
    
    # Get discontinuation counts from manager if available
    disc_counts = results.get("discontinuation_counts", {})
    if disc_counts:
        print("Discontinuation counts from manager:")
        total_disc = sum(disc_counts.values())
        for type_name, count in disc_counts.items():
            percent = (count / total_disc) * 100 if total_disc > 0 else 0
            print(f"  {type_name}: {count} ({percent:.1f}%)")
    
    # Count patient states using our phase tracking logic
    patient_histories = results.get("patient_histories", {})
    if not patient_histories:
        print("No patient histories found")
        return
    
    # Get duration years, defaulting to 5 if not specified
    duration_years = results.get("duration_years", 5)
    
    # Check state distribution at month 60 (5 years) or the closest we have
    month = min(60, int(duration_years * 12))
    print(f"\nAnalyzing patient states at month {month}:")
    
    # Find the earliest visit date to use as reference
    all_dates = []
    for patient_id, visits in patient_histories.items():
        for visit in visits:
            date_val = visit.get("date", visit.get("time"))
            if date_val and isinstance(date_val, (datetime, str, pd.Timestamp)):
                all_dates.append(date_val)
                break
    
    # Get reference date
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
    
    # Count states at each month
    month_cutoff = start_date + timedelta(days=month*30)
    state_counts = defaultdict(int)
    
    # Track detected reasons for debugging
    detected_reasons = defaultdict(int)
    detected_phases = defaultdict(int)
    detected_phase_transitions = defaultdict(int)
    
    # Look for administrative and not_renewed discontinuations specifically
    admin_discontinuations = []
    not_renewed_discontinuations = []
    
    # Process each patient
    for patient_id, visits in patient_histories.items():
        # Get visits up to the current month
        visits_to_month = []
        
        # Track phases for this patient
        patient_phases = []
        
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
                
                # Track phases
                phase = visit.get("phase", "unknown")
                patient_phases.append(phase)
                detected_phases[phase] += 1
                
                # Track discontinuation reasons for debugging
                reason = (visit.get("discontinuation_reason") or 
                         visit.get("reason") or 
                         visit.get("cessation_type"))
                
                # Look for administrative discontinuations
                if reason and "admin" in str(reason).lower():
                    admin_discontinuations.append({
                        "patient_id": patient_id,
                        "visit": visit,
                        "reason": reason
                    })
                
                # Look for not_renewed discontinuations
                if reason and ("not_renewed" in str(reason).lower() or 
                             "course_complete" in str(reason).lower()):
                    not_renewed_discontinuations.append({
                        "patient_id": patient_id,
                        "visit": visit,
                        "reason": reason
                    })
                
                if reason:
                    detected_reasons[str(reason).lower()] += 1
        
        # Track phase transitions
        for i in range(1, len(patient_phases)):
            transition = f"{patient_phases[i-1]} → {patient_phases[i]}"
            detected_phase_transitions[transition] += 1
        
        # Analyze the patient's phase transitions
        analysis = analyze_phase_transitions(visits_to_month)
        
        # Determine patient state
        state = determine_patient_state(analysis)
        
        # Count this patient's state
        state_counts[state] += 1
    
    # Print state counts
    print(f"States detected in visualization at month {month}:")
    total_patients = sum(state_counts.values())
    for state, count in sorted(state_counts.items()):
        percent = (count / total_patients) * 100 if total_patients > 0 else 0
        print(f"  {state}: {count} ({percent:.1f}%)")
    
    # Print phase distribution
    print("\nPhases detected in visits:")
    total_phases = sum(detected_phases.values())
    for phase, count in sorted(detected_phases.items(), key=lambda x: x[1], reverse=True):
        percent = (count / total_phases) * 100 if total_phases > 0 else 0
        print(f"  {phase}: {count} ({percent:.1f}%)")
    
    # Print phase transitions
    print("\nPhase transitions detected:")
    total_transitions = sum(detected_phase_transitions.values())
    for transition, count in sorted(detected_phase_transitions.items(), key=lambda x: x[1], reverse=True)[:10]:
        percent = (count / total_transitions) * 100 if total_transitions > 0 else 0
        print(f"  {transition}: {count} ({percent:.1f}%)")
    
    # Print discontinuation reason distribution
    if detected_reasons:
        print("\nDiscontinuation reasons detected in visits:")
        total_reasons = sum(detected_reasons.values())
        for reason, count in sorted(detected_reasons.items(), key=lambda x: x[1], reverse=True):
            percent = (count / total_reasons) * 100 if total_reasons > 0 else 0
            print(f"  {reason}: {count} ({percent:.1f}%)")
    
    # Print information about administrative discontinuations
    if admin_discontinuations:
        print(f"\nFound {len(admin_discontinuations)} administrative discontinuations:")
        for i, disc in enumerate(admin_discontinuations[:5]):  # Show first 5 only
            print(f"  {i+1}. Patient {disc['patient_id']}, Reason: {disc['reason']}")
    else:
        print("\nNo administrative discontinuations found in visits")
    
    # Print information about not_renewed discontinuations
    if not_renewed_discontinuations:
        print(f"\nFound {len(not_renewed_discontinuations)} not_renewed discontinuations:")
        for i, disc in enumerate(not_renewed_discontinuations[:5]):  # Show first 5 only
            print(f"  {i+1}. Patient {disc['patient_id']}, Reason: {disc['reason']}")
    else:
        print("\nNo not_renewed discontinuations found in visits")
    
    # Compare discontinuation counts with state counts
    if disc_counts:
        print("\nComparing discontinuation manager counts vs. phase analysis counts:")
        
        # Expected mapping to states
        map_to_state = {
            "Planned": "discontinued_planned",
            "Administrative": "discontinued_administrative",
            "Not Renewed": "discontinued_not_renewed",
            "Premature": "discontinued_premature"
        }
        
        total_discontinued_manager = sum(disc_counts.values())
        total_discontinued_states = sum(state_counts.get(state, 0) for state in [
            "discontinued_planned", "discontinued_administrative", 
            "discontinued_not_renewed", "discontinued_premature"
        ])
        
        print(f"Total discontinued (from manager): {total_discontinued_manager}")
        print(f"Total discontinued (from states): {total_discontinued_states}")
        
        for type_name, state_name in map_to_state.items():
            manager_count = disc_counts.get(type_name, 0)
            state_count = state_counts.get(state_name, 0)
            
            print(f"  {type_name}:")
            print(f"    Manager count: {manager_count}")
            print(f"    State count:   {state_count}")
            
            if manager_count == state_count:
                print(f"    MATCH")
            else:
                difference = abs(manager_count - state_count)
                percent_diff = (difference / max(1, manager_count)) * 100
                print(f"    MISMATCH: Difference of {difference} ({percent_diff:.1f}%)")
    
    return state_counts

def main():
    """Main function to analyze simulation results."""
    # Parse command-line arguments
    args = parse_args()
    
    # Load simulation results
    results = load_simulation_results(args.input)
    if not results:
        return
    
    # Analyze results
    state_counts = analyze_simulation_results(results)
    
    # Generate visualization
    print("\nGenerating phase tracking streamgraph...")
    fig = generate_phase_tracking_streamgraph(results)
    
    # Save the visualization
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_name = os.path.basename(args.input).replace(".json", "")
    output_file = f"{base_name}_phase_tracking_{timestamp}.png"
    fig.savefig(output_file, dpi=300, bbox_inches="tight")
    print(f"Saved streamgraph to {output_file}\n")
    
    # Display the plot
    plt.show()

if __name__ == "__main__":
    main()