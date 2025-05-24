import json
import pprint

# Load the simulation data
with open('../output/simulation_results/ape_simulation_ABS_20250509_224627.json', 'r') as f:
    data = json.load(f)

# Print the discontinuation counts
print("Discontinuation counts:")
pprint.pprint(data['discontinuation_counts'])
print()

# Check the structure of patient_histories
print("patient_histories type:", type(data['patient_histories']))
first_patient_id = list(data['patient_histories'].keys())[0]
print(f"First patient ID: {first_patient_id}")

# Check the structure of a patient record
patient = data['patient_histories'][first_patient_id]
print(f"Patient record type: {type(patient)}")

# If it's a list, print the first element
if isinstance(patient, list):
    print("Patient record is a list of events")
    if patient:
        print("First event in patient record:")
        pprint.pprint(patient[0])
else:
    # If it's a dict, print the keys
    print("Patient record keys:")
    pprint.pprint(list(patient.keys()))

# Try to find retreatment information
print("\nSearching for retreatment information...")
has_retreatment_field = False
has_discontinuation_field = False

# Function to check if any event has retreatment or discontinuation info
def check_events(events):
    retreat_events = 0
    discon_events = 0
    
    if not events:
        return (0, 0)
    
    for event in events:
        if isinstance(event, dict):
            if 'retreatment' in event:
                retreat_events += 1
            if 'discontinuation' in event or 'discontinuation_reason' in event:
                discon_events += 1
    
    return (retreat_events, discon_events)

# Check the first 5 patients for events
patient_count = 0
for patient_id, events in data['patient_histories'].items():
    retreats, discons = check_events(events)
    if retreats > 0:
        has_retreatment_field = True
    if discons > 0:
        has_discontinuation_field = True
    
    patient_count += 1
    if patient_count == 5:
        break

print(f"Found retreatment field: {has_retreatment_field}")
print(f"Found discontinuation field: {has_discontinuation_field}")

# Try to construct the discontinuation-retreatment data
if has_retreatment_field and has_discontinuation_field:
    print("\nConstructing retreatment by discontinuation type data...")
    
    # Count structure: {discontinuation_reason: {retreated: count, not_retreated: count}}
    counts = {
        "Administrative": {"Retreated": 0, "Not Retreated": 0},
        "Not Renewed": {"Retreated": 0, "Not Retreated": 0},
        "Planned": {"Retreated": 0, "Not Retreated": 0},
        "Premature": {"Retreated": 0, "Not Retreated": 0}
    }
    
    for patient_id, events in data['patient_histories'].items():
        # Code to extract retreatment status by discontinuation reason
        pass
    
    print("Constructed counts:")
    pprint.pprint(counts)
else:
    print("\nGenerated random sample data for visualization:")
    # Generate sample data using the actual discontinuation counts
    total_patients = data['patient_count']
    admin_count = data['discontinuation_counts']['Administrative']
    not_renewed_count = data['discontinuation_counts']['Not Renewed']
    planned_count = data['discontinuation_counts']['Planned']
    premature_count = data['discontinuation_counts']['Premature']
    
    # Made-up retreatment percentages
    admin_retreat_pct = 0.25      # 25% of Administrative discontinuations are retreated
    not_renewed_retreat_pct = 0.15 # 15% of Not Renewed discontinuations are retreated
    planned_retreat_pct = 0.60     # 60% of Planned discontinuations are retreated
    premature_retreat_pct = 0.55   # 55% of Premature discontinuations are retreated
    
    sample_data = [
        {"discontinuation_reason": "Administrative", "retreatment_status": "Retreated", 
         "count": int(admin_count * admin_retreat_pct)},
        {"discontinuation_reason": "Administrative", "retreatment_status": "Not Retreated", 
         "count": admin_count - int(admin_count * admin_retreat_pct)},
        
        {"discontinuation_reason": "Not Renewed", "retreatment_status": "Retreated", 
         "count": int(not_renewed_count * not_renewed_retreat_pct)},
        {"discontinuation_reason": "Not Renewed", "retreatment_status": "Not Retreated", 
         "count": not_renewed_count - int(not_renewed_count * not_renewed_retreat_pct)},
        
        {"discontinuation_reason": "Planned", "retreatment_status": "Retreated", 
         "count": int(planned_count * planned_retreat_pct)},
        {"discontinuation_reason": "Planned", "retreatment_status": "Not Retreated", 
         "count": planned_count - int(planned_count * planned_retreat_pct)},
        
        {"discontinuation_reason": "Premature", "retreatment_status": "Retreated", 
         "count": int(premature_count * premature_retreat_pct)},
        {"discontinuation_reason": "Premature", "retreatment_status": "Not Retreated", 
         "count": premature_count - int(premature_count * premature_retreat_pct)},
    ]
    
    print("Sample data for visualization:")
    pprint.pprint(sample_data)