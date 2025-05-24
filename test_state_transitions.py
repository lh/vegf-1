#!/usr/bin/env python3
"""
Test script to directly verify state transitions in the patient data.
"""

import json
import pandas as pd
import numpy as np
from datetime import datetime
from collections import defaultdict

def test_patient_transitions(data_file):
    """Examine patient state transitions in detail."""
    try:
        # Load the data
        with open(data_file, 'r') as f:
            results = json.load(f)
        
        patient_histories = results.get("patient_histories", {})
        
        # Check if patient histories exist
        if not patient_histories:
            print("No patient histories found in the data!")
            return
        
        print(f"Loaded patient data with {len(patient_histories)} patients")
        
        # Analyze each patient for discontinuations
        patients_with_disc = 0
        disc_visits_total = 0
        disc_by_type = defaultdict(int)
        
        for patient_id, visits in patient_histories.items():
            # Check for discontinuation visits
            disc_visits = [v for v in visits if v.get("is_discontinuation_visit", False)]
            
            if disc_visits:
                patients_with_disc += 1
                disc_visits_total += len(disc_visits)
                
                # Count by type
                for visit in disc_visits:
                    disc_type = visit.get("discontinuation_type", "unknown")
                    disc_by_type[disc_type] += 1
        
        print(f"\nDiscontinuation summary:")
        print(f"- {patients_with_disc} patients have discontinuation visits ({patients_with_disc/len(patient_histories)*100:.1f}%)")
        print(f"- {disc_visits_total} total discontinuation visits")
        print("\nDiscontinuation types:")
        for disc_type, count in disc_by_type.items():
            print(f"- {disc_type}: {count}")
        
        # Manually trace a few patients' entire histories
        print("\nDetailed patient visit histories for patients with discontinuations:")
        patients_to_check = 3
        
        tracked_patients = []
        for patient_id, visits in patient_histories.items():
            if any(v.get("is_discontinuation_visit", False) for v in visits):
                tracked_patients.append(patient_id)
                if len(tracked_patients) >= patients_to_check:
                    break
        
        for patient_id in tracked_patients:
            visits = patient_histories[patient_id]
            print(f"\nPatient {patient_id} visit history:")
            
            for i, visit in enumerate(visits):
                # Get visit details
                visit_time = visit.get("time", visit.get("date", "Unknown"))
                is_disc = "YES" if visit.get("is_discontinuation_visit", False) else "NO"
                disc_type = visit.get("discontinuation_type", "N/A")
                visit_phase = visit.get("phase", "unknown")
                
                print(f"  Visit {i+1}: Time={visit_time}, Phase={visit_phase}, Is Discontinuation={is_disc}, Type={disc_type}")
        
        # Now try to manually build the state transition timeline
        print("\nManually building state timeline for one patient:")
        if tracked_patients:
            patient_id = tracked_patients[0]
            visits = patient_histories[patient_id]
            print(f"Building timeline for Patient {patient_id} with {len(visits)} visits")
            
            # Initialize state
            current_state = "active"
            
            # Track the timeline
            timeline = []
            
            for i, visit in enumerate(visits):
                # Get visit details
                visit_time = visit.get("time", visit.get("date", "Unknown"))
                is_disc = visit.get("is_discontinuation_visit", False)
                disc_type = visit.get("discontinuation_type", None)
                is_retreat = visit.get("is_retreatment_visit", False)
                
                # Update state based on visit
                if is_disc and disc_type:
                    if disc_type == "stable_max_interval":
                        current_state = "discontinued_stable_max_interval"
                    elif disc_type == "random_administrative":
                        current_state = "discontinued_random_administrative"
                    elif disc_type == "treatment_duration":
                        current_state = "discontinued_course_complete_but_not_renewed"
                    elif disc_type == "premature":
                        current_state = "discontinued_premature"
                    else:
                        current_state = f"discontinued_{disc_type}"
                
                # Add to timeline
                timeline.append({
                    "visit_num": i+1,
                    "time": visit_time,
                    "state": current_state,
                    "is_discontinuation": is_disc,
                    "is_retreatment": is_retreat
                })
            
            # Print the timeline
            print("\nState timeline:")
            for entry in timeline:
                print(f"  Visit {entry['visit_num']}: Time={entry['time']}, State={entry['state']}")
            
    except Exception as e:
        import traceback
        print(f"Error analyzing data: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    # Test the last generated data file
    test_patient_transitions("full_streamgraph_test_data.json")