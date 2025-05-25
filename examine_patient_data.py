#!/usr/bin/env python3
"""
Examine the patient data structure to understand discontinuation and retreatment visits.
"""

import json
import sys
import os

def main():
    # Load a sample simulation result file
    result_dir = "output/simulation_results"
    result_files = [os.path.join(result_dir, f) for f in os.listdir(result_dir) 
                   if f.endswith('.json')]
    
    if not result_files:
        print("No simulation result files found")
        return
    
    # Sort by modification time (newest first)
    result_files.sort(key=os.path.getmtime, reverse=True)
    result_file = result_files[0]
    
    print(f"Loading {result_file}...")
    with open(result_file, 'r') as f:
        data = json.load(f)
    
    # Check for patient histories
    if "patient_histories" not in data:
        print("No patient_histories found in data")
        return
    
    patient_histories = data["patient_histories"]
    print(f"Found {len(patient_histories)} patients")
    
    # Get a random sample of patients to increase chances of finding discontinuations
    import random
    patient_ids = random.sample(list(patient_histories.keys()), 20)
    
    for patient_id in patient_ids:
        patient = patient_histories[patient_id]
        print(f"\nPatient {patient_id}: {len(patient)} visits")
        
        # Collect all visit fields
        visit_fields = set()
        for visit in patient:
            visit_fields.update(visit.keys())
        
        print(f"Fields in visits: {sorted(list(visit_fields))}")
        
        # Look for discontinuation visits
        disc_visits = [v for v in patient if v.get("type") == "discontinuation"]
        if disc_visits:
            print(f"Found {len(disc_visits)} discontinuation visits")
            print("First discontinuation visit:")
            print(json.dumps(disc_visits[0], indent=2))
        else:
            print("No discontinuation visits found")
        
        # Look for retreatment visits
        retreat_visits = [v for v in patient if v.get("type") == "retreatment"]
        if retreat_visits:
            print(f"Found {len(retreat_visits)} retreatment visits")
            print("First retreatment visit:")
            print(json.dumps(retreat_visits[0], indent=2))
        else:
            print("No retreatment visits found")

if __name__ == "__main__":
    main()