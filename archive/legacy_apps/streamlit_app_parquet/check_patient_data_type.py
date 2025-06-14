"""
Check the actual type and structure of patient_histories.
"""

import json

# Load debug data to see the actual structure
try:
    with open('/Users/rose/Code/CC/streamlit_debug_data.json', 'r') as f:
        debug_data = json.load(f)
    
    print("=== DEBUG DATA CHECK ===")
    print(f"Has patient_histories: {debug_data.get('has_patient_histories', False)}")
    
    # Check what type patient_histories might be
    result_keys = debug_data.get("result_keys", [])
    print(f"\nResult keys that might contain patient data:")
    for key in result_keys:
        if 'patient' in key.lower() or 'visit' in key.lower():
            print(f"  - {key}")
    
except Exception as e:
    print(f"Error: {e}")

# Let me create a more robust function that handles both list and dict
diagnosis_code = '''
def diagnose_patient_data(results):
    """Diagnose the actual structure of patient data."""
    
    print("=== DIAGNOSING PATIENT DATA STRUCTURE ===")
    
    # Check all possible patient data fields
    possible_fields = [
        'patient_histories',
        'patients', 
        'patient_data',
        'patient_visits',
        'visit_data'
    ]
    
    for field in possible_fields:
        if field in results:
            data = results[field]
            print(f"\\nFound '{field}':")
            print(f"  Type: {type(data)}")
            
            if isinstance(data, dict):
                print(f"  Keys: {list(data.keys())[:5]}...")  # First 5 keys
                if data:
                    first_key = list(data.keys())[0]
                    first_item = data[first_key]
                    print(f"  First item type: {type(first_item)}")
                    if isinstance(first_item, dict):
                        print(f"  First item keys: {list(first_item.keys())}")
                    elif isinstance(first_item, list):
                        print(f"  First item length: {len(first_item)}")
                        if first_item:
                            print(f"  First item[0] type: {type(first_item[0])}")
                            
            elif isinstance(data, list):
                print(f"  Length: {len(data)}")
                if data:
                    first_item = data[0]
                    print(f"  First item type: {type(first_item)}")
                    if isinstance(first_item, dict):
                        print(f"  First item keys: {list(first_item.keys())}")
                    else:
                        print(f"  First item: {first_item}")
    
    # Also check for raw data
    if 'raw_discontinuation_stats' in results:
        raw_stats = results['raw_discontinuation_stats']
        print(f"\\nRaw discontinuation stats keys: {list(raw_stats.keys())}")
        
        # Check for patient-level data
        for key in raw_stats:
            if 'patient' in key.lower():
                print(f"  {key}: {type(raw_stats[key])}")
'''

print(diagnosis_code)