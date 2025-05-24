"""
Inspect the actual data structure to understand what we're working with.
"""

import json
import pprint

# First, let's look at what's in the debug data file
print("=== EXAMINING ACTUAL DATA STRUCTURE ===\n")

# Load the debug data to see what fields we have
try:
    with open('/Users/rose/Code/CC/streamlit_debug_data.json', 'r') as f:
        debug_data = json.load(f)
    
    print("Available fields in results:")
    for key in debug_data.get("result_keys", []):
        print(f"  - {key}")
    
    print(f"\nHas patient_histories: {debug_data.get('has_patient_histories', False)}")
    print(f"Population size: {debug_data.get('population_size', 'MISSING')}")
    print(f"Duration years: {debug_data.get('duration_years', 'MISSING')}")
    
    print("\nDiscontinuation counts:")
    for disc_type, count in debug_data.get("discontinuation_counts", {}).items():
        print(f"  {disc_type}: {count}")
    
    print("\nRecurrences data:")
    recurrences = debug_data.get("recurrences", {})
    print(f"  Total: {recurrences.get('total', 0)}")
    print(f"  Unique count: {recurrences.get('unique_count', 0)}")
    
except Exception as e:
    print(f"Error loading debug data: {e}")

# Now let's create a script that will examine actual patient histories
print("\n=== SCRIPT TO EXAMINE PATIENT HISTORIES ===\n")

examine_script = '''
def examine_patient_histories(results):
    """Examine the actual structure of patient history data."""
    
    patient_histories = results.get("patient_histories", {})
    
    if not patient_histories:
        print("NO PATIENT HISTORIES AVAILABLE")
        return
    
    # Get a sample patient
    patient_ids = list(patient_histories.keys())
    print(f"Total patients: {len(patient_ids)}")
    
    # Examine first patient in detail
    first_patient_id = patient_ids[0]
    first_patient = patient_histories[first_patient_id]
    
    print(f"\\nFirst patient ID: {first_patient_id}")
    print(f"Patient data keys: {list(first_patient.keys())}")
    
    # Look at visits structure
    visits = first_patient.get("visits", [])
    print(f"\\nNumber of visits: {len(visits)}")
    
    if visits:
        print("\\nFirst visit structure:")
        first_visit = visits[0]
        for key, value in first_visit.items():
            print(f"  {key}: {value} (type: {type(value).__name__})")
        
        # Find discontinuation visits
        disc_visits = [v for v in visits if v.get("is_discontinuation_visit", False)]
        print(f"\\nDiscontinuation visits: {len(disc_visits)}")
        
        if disc_visits:
            print("First discontinuation visit:")
            for key, value in disc_visits[0].items():
                print(f"  {key}: {value}")
        
        # Find retreatment visits
        retreat_visits = [v for v in visits if v.get("is_retreatment", False)]
        print(f"\\nRetreatment visits: {len(retreat_visits)}")
        
        if retreat_visits:
            print("First retreatment visit:")
            for key, value in retreat_visits[0].items():
                print(f"  {key}: {value}")
    
    # Check other patient fields
    print(f"\\nOther patient fields:")
    print(f"  discontinuation_reasons: {first_patient.get('discontinuation_reasons', 'MISSING')}")
    print(f"  retreatment_count: {first_patient.get('retreatment_count', 'MISSING')}")
    print(f"  initial_observation_time: {first_patient.get('initial_observation_time', 'MISSING')}")
    
    # Count actual states at specific time points
    print("\\n=== ACTUAL STATE COUNTS AT SPECIFIC TIMES ===")
    
    for month in [0, 6, 12, 24, 36, 48, 60]:
        states = {
            "active": 0,
            "discontinued": 0,
            "retreated": 0
        }
        
        for patient_id, patient_data in patient_histories.items():
            visits = patient_data.get("visits", [])
            
            # Find patient state at this month
            is_active = True
            last_disc = False
            has_retreated = False
            
            for visit in visits:
                visit_time = visit.get("time", visit.get("date", 0))
                if visit_time <= month:
                    if visit.get("is_discontinuation_visit", False):
                        is_active = False
                        last_disc = True
                    if visit.get("is_retreatment", False):
                        is_active = True
                        has_retreated = True
                        last_disc = False
            
            if is_active:
                if has_retreated:
                    states["retreated"] += 1
                else:
                    states["active"] += 1
            else:
                states["discontinued"] += 1
        
        total = sum(states.values())
        print(f"\\nMonth {month}: Total={total}")
        for state, count in states.items():
            print(f"  {state}: {count}")

# This function should be called with the actual results data
'''

print(examine_script)

print("\n=== TO USE THIS SCRIPT ===")
print("Run this in your simulation to examine the actual data:")
print("examine_patient_histories(results)")