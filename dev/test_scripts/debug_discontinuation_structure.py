"""
Debug the discontinuation data structure to understand why we're not seeing states.
"""

import json
import os
import pandas as pd
from pprint import pprint

def load_latest_simulation():
    """Load the latest simulation results file"""
    sim_dir = "output/simulation_results"
    sim_files = [os.path.join(sim_dir, f) for f in os.listdir(sim_dir) if f.endswith('.json')]
    if not sim_files:
        return None
    
    sim_files.sort(key=os.path.getmtime, reverse=True)
    latest_file = sim_files[0]
    
    try:
        with open(latest_file, 'r') as f:
            data = json.load(f)
            print(f"Loaded data from {latest_file}")
            return data, latest_file
    except Exception as e:
        print(f"Error loading {latest_file}: {e}")
        return None, None

def analyze_discontinuation_data(results):
    """Analyze the discontinuation data in patient histories"""
    if not results or "patient_histories" not in results:
        print("No patient histories found")
        return
    
    patient_histories = results["patient_histories"]
    print(f"Found {len(patient_histories)} patient histories")
    
    # Check discontinuation counts from results metadata
    print("\nDiscontinuation counts from metadata:")
    disc_counts = results.get("discontinuation_counts", {})
    if disc_counts:
        for reason, count in disc_counts.items():
            print(f"  {reason}: {count}")
        print(f"  Total: {sum(disc_counts.values())}")
    else:
        print("  No discontinuation counts in metadata")
    
    # Detailed inspection of patient histories
    disc_visits = []
    retreat_visits = []
    
    # Track counts of different discontinuation flags
    flag_counts = {
        "is_discontinuation_visit": 0,
        "discontinuation_reason": 0, 
        "discontinuation_type": 0,
        "is_retreatment_visit": 0
    }
    
    # Track counts of different discontinuation reasons/types
    reason_counts = {}
    
    # Sample structure of each type
    samples = {}
    
    # Check a few random patients for discontinuation visits
    for i, (patient_id, visits) in enumerate(patient_histories.items()):
        if i >= 100:  # Just check first 100 patients
            break
            
        for visit in visits:
            # Check for discontinuation flags
            if visit.get("is_discontinuation_visit", False):
                flag_counts["is_discontinuation_visit"] += 1
                disc_visits.append({
                    "patient_id": patient_id,
                    "visit": visit
                })
                
                # Check for reason or type
                reason = visit.get("discontinuation_reason", "")
                if reason:
                    flag_counts["discontinuation_reason"] += 1
                    reason_counts[reason] = reason_counts.get(reason, 0) + 1
                    
                    # Save sample
                    if reason not in samples:
                        samples[reason] = {
                            "patient_id": patient_id,
                            "visit": visit
                        }
                
                dtype = visit.get("discontinuation_type", "")
                if dtype:
                    flag_counts["discontinuation_type"] += 1
                    reason_counts[dtype] = reason_counts.get(dtype, 0) + 1
                    
                    # Save sample
                    if dtype not in samples:
                        samples[dtype] = {
                            "patient_id": patient_id,
                            "visit": visit
                        }
            
            # Check for retreatment
            if visit.get("is_retreatment_visit", False):
                flag_counts["is_retreatment_visit"] += 1
                retreat_visits.append({
                    "patient_id": patient_id,
                    "visit": visit
                })
    
    # Report findings
    print("\nFlag counts in visits:")
    for flag, count in flag_counts.items():
        print(f"  {flag}: {count}")
    
    print("\nDiscontinuation reason/type counts:")
    for reason, count in reason_counts.items():
        print(f"  {reason}: {count}")
    
    # Sample discontinuation visit
    if disc_visits:
        print("\nSample discontinuation visit:")
        pprint(disc_visits[0])
    else:
        print("\nNo discontinuation visits found in sample")
    
    # Sample retreatment visit
    if retreat_visits:
        print("\nSample retreatment visit:")
        pprint(retreat_visits[0])
    else:
        print("\nNo retreatment visits found in sample")
    
    # Print samples of each discontinuation type
    print("\nSamples of each discontinuation type:")
    for reason, sample in samples.items():
        print(f"\n{reason}:")
        pprint(sample["visit"])
    
    return flag_counts, reason_counts, disc_visits, retreat_visits

def main():
    """Main debug function"""
    results, file_path = load_latest_simulation()
    if not results:
        print("Could not load simulation results")
        return
    
    print(f"Loaded simulation results with {len(results.get('patient_histories', {}))} patients")
    
    # Analyze discontinuation data
    analyze_discontinuation_data(results)
    
    # Export a simplified results file with discontinuation flags
    output_file = "debug_discontinuation_data.json"
    
    try:
        # Create a simpler version for testing
        simple_results = {
            "simulation_type": results.get("simulation_type", "ABS"),
            "duration_years": results.get("duration_years", 5),
            "population_size": results.get("population_size", 100),
            "discontinuation_counts": results.get("discontinuation_counts", {}),
            "patient_histories": {}
        }
        
        # Get a patient ID for each discontinuation type
        disc_types = ["stable_max_interval", "random_administrative", 
                     "treatment_duration", "premature", "course_complete_but_not_renewed"]
        
        # Find some representative patients
        patient_histories = results["patient_histories"]
        sample_patients = {}
        
        for patient_id, visits in patient_histories.items():
            found_disc = False
            disc_type = None
            
            for visit in visits:
                if visit.get("is_discontinuation_visit", False):
                    found_disc = True
                    disc_type = visit.get("discontinuation_reason", visit.get("discontinuation_type", "unknown"))
                    break
            
            if found_disc and disc_type not in sample_patients:
                sample_patients[disc_type] = patient_id
                print(f"Found sample patient {patient_id} for {disc_type}")
            
            # If we have a sample for each type, stop
            if len(sample_patients) >= len(disc_types):
                break
        
        # Add sample patients to the output
        for disc_type, patient_id in sample_patients.items():
            simple_results["patient_histories"][patient_id] = patient_histories[patient_id]
        
        # Add manually flagged discontinuation data for testing
        # Create test data with explicit discontinuation visits
        if len(simple_results["patient_histories"]) < 5:
            print("Adding synthetic test patients with discontinuation visits")
            
            # Add test patients with discontinuation and retreatment visits
            for i, disc_type in enumerate(["stable_max_interval", "random_administrative", 
                                         "course_complete_but_not_renewed", "premature"]):
                pid = f"TEST_PATIENT_{i:03d}"
                
                simple_results["patient_histories"][pid] = [
                    {"time": "2023-01-01T02:00:00", "is_discontinuation_visit": False},
                    {"time": "2023-05-01T02:00:00", "is_discontinuation_visit": True,
                     "discontinuation_reason": disc_type,
                     "discontinuation_type": disc_type},
                    {"time": "2023-09-01T02:00:00", "is_retreatment_visit": True}
                ]
        
        # Save the simplified results
        with open(output_file, "w") as f:
            json.dump(simple_results, f, indent=2)
            print(f"Saved simplified results to {output_file}")
    
    except Exception as e:
        import traceback
        print(f"Error creating simplified results: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()