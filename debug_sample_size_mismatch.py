#!/usr/bin/env python3
"""
Debug why we're finding way more visits than the claimed sample size.
"""
import json
import pandas as pd
from datetime import datetime

# Load actual simulation results
with open('/Users/rose/Code/CC/output/simulation_results/ape_simulation_ABS_20250514_221752.json', 'r') as f:
    results = json.loads(f.read())

print("=== SAMPLE SIZE MISMATCH INVESTIGATION ===")

# Get the mean_va_data
mean_va_data = results['mean_va_data']
df = pd.DataFrame(mean_va_data)

# Look at a specific problem time point
time_point = 45
time_data = df[df['time'] == time_point].iloc[0]
claimed_sample_size = time_data['sample_size']

print(f"At month {time_point}:")
print(f"Claimed sample size: {claimed_sample_size}")
print(f"Visual acuity: {time_data['visual_acuity']:.1f}")

# Now let's see what patients are actually contributing to this time point
patient_histories = results['patient_histories']
start_date = datetime(2023, 1, 1)
time_tolerance = 0.5

# Track which patients have visits near this time
patients_at_time = set()
all_visits_at_time = []

for patient_id, visits in patient_histories.items():
    if not isinstance(visits, list):
        continue
    
    for visit in visits:
        if not isinstance(visit, dict) or 'date' not in visit:
            continue
        
        try:
            visit_date_str = visit['date']
            visit_date = datetime.strptime(visit_date_str.replace('T', ' '), "%Y-%m-%d %H:%M:%S")
            visit_month = (visit_date - start_date).days / 30.44
            
            if abs(visit_month - time_point) <= time_tolerance:
                patients_at_time.add(patient_id)
                all_visits_at_time.append({
                    'patient_id': patient_id,
                    'visit_month': visit_month,
                    'va': visit.get('vision', visit.get('visual_acuity', visit.get('va')))
                })
        except:
            pass

print(f"\nActual patients with visits: {len(patients_at_time)}")
print(f"Total visits found: {len(all_visits_at_time)}")

# Check if a patient's last visit was before this time (they've discontinued)
still_active_patients = set()

for patient_id, visits in patient_histories.items():
    if not isinstance(visits, list) or not visits:
        continue
    
    # Find the last visit time for this patient
    last_visit_month = 0
    for visit in visits:
        if not isinstance(visit, dict) or 'date' not in visit:
            continue
        try:
            visit_date_str = visit['date']
            visit_date = datetime.strptime(visit_date_str.replace('T', ' '), "%Y-%m-%d %H:%M:%S")
            visit_month = (visit_date - start_date).days / 30.44
            if visit_month > last_visit_month:
                last_visit_month = visit_month
        except:
            pass
    
    # If their last visit is at or after this time point, they're still active
    if last_visit_month >= time_point - time_tolerance:
        still_active_patients.add(patient_id)

print(f"\nPatients still active at month {time_point}: {len(still_active_patients)}")

# This might be closer to the claimed sample size
active_with_visit = patients_at_time.intersection(still_active_patients)
print(f"Active patients with visits at this time: {len(active_with_visit)}")

# Let's see how the sample size is actually calculated in the mean_va_data
print("\n=== HOW IS SAMPLE SIZE CALCULATED? ===")
# Look at a few time points
for t in [0, 10, 20, 30, 40, 45, 50, 55, 60]:
    time_data = df[df['time'] == t]
    if not time_data.empty:
        sample_size = time_data.iloc[0]['sample_size']
        # Count actual visits at this time
        visit_count = 0
        active_count = 0
        
        for patient_id, visits in patient_histories.items():
            has_visit_at_time = False
            last_visit = 0
            
            for visit in visits:
                if isinstance(visit, dict) and 'date' in visit:
                    try:
                        visit_date_str = visit['date']
                        visit_date = datetime.strptime(visit_date_str.replace('T', ' '), "%Y-%m-%d %H:%M:%S")
                        month = (visit_date - start_date).days / 30.44
                        
                        if abs(month - t) <= time_tolerance:
                            has_visit_at_time = True
                            visit_count += 1
                        if month > last_visit:
                            last_visit = month
                    except:
                        pass
            
            if last_visit >= t - time_tolerance:
                active_count += 1
        
        print(f"Month {t:2d}: claimed={int(sample_size):4d}, visits={visit_count:4d}, still_active={active_count:4d}")