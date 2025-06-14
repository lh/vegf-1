"""
Check what format time is stored in the patient visits.
"""

import json
from datetime import datetime

# Create a test to check time format
test_code = '''
def check_time_format(results):
    """Check the format of time in patient visits."""
    
    patient_histories = results.get("patient_histories", {})
    
    if not patient_histories:
        print("No patient histories found")
        return
    
    # Get first patient
    patient_id = list(patient_histories.keys())[0]
    visits = patient_histories[patient_id]
    
    print(f"First patient ID: {patient_id}")
    print(f"Number of visits: {len(visits)}")
    
    if visits:
        first_visit = visits[0]
        print(f"\\nFirst visit keys: {list(first_visit.keys())}")
        
        # Check time field
        time_value = first_visit.get("time", first_visit.get("date", None))
        print(f"\\nTime value: {time_value}")
        print(f"Time type: {type(time_value)}")
        
        if time_value is not None:
            print(f"Has timestamp attr: {hasattr(time_value, 'timestamp')}")
            print(f"Is datetime: {isinstance(time_value, datetime)}")
            print(f"Is numeric: {isinstance(time_value, (int, float))}")
            
        # Check a few more visits
        print("\\nChecking multiple visits:")
        for i, visit in enumerate(visits[:5]):
            time_val = visit.get("time", visit.get("date", None))
            print(f"  Visit {i}: {time_val} (type: {type(time_val).__name__})")
'''

print(test_code)