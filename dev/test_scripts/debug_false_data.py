#!/usr/bin/env python3
"""
Debug where the false data after month 60 is coming from.
"""
import json
import pandas as pd
from datetime import datetime

# Load actual simulation results
with open('/Users/rose/Code/CC/output/simulation_results/ape_simulation_ABS_20250514_221752.json', 'r') as f:
    results = json.loads(f.read())

print("=== INVESTIGATING FALSE DATA AFTER MONTH 60 ===")

# Get the mean_va_data with false time points
mean_va_data = results['mean_va_data']
df = pd.DataFrame(mean_va_data)

# Filter for time points after 60 months
late_data = df[df['time'] > 60]

print(f"Number of data points after month 60: {len(late_data)}")
print("\nSample of data after month 60:")
print(late_data[['time', 'visual_acuity', 'sample_size']].head(10))

# Check patient histories to confirm no visits after month 60
patient_histories = results['patient_histories']
visits_after_60 = 0
latest_visit_month = 0

for patient_id, visits in patient_histories.items():
    if not isinstance(visits, list):
        continue
        
    for visit in visits:
        if not isinstance(visit, dict) or 'date' not in visit:
            continue
            
        try:
            visit_date_str = visit['date']
            visit_date = datetime.strptime(visit_date_str.replace('T', ' '), "%Y-%m-%d %H:%M:%S")
            start_date = datetime(2023, 1, 1)
            visit_month = (visit_date - start_date).days / 30.44
            
            if visit_month > latest_visit_month:
                latest_visit_month = visit_month
                
            if visit_month > 60:
                visits_after_60 += 1
                print(f"Found visit after month 60: patient {patient_id}, month {visit_month:.1f}")
                
        except Exception as e:
            pass

print(f"\nLatest actual visit month: {latest_visit_month:.1f}")
print(f"Number of visits after month 60: {visits_after_60}")

# Check the visual acuity values for late data points
print("\n=== VISUAL ACUITY VALUES AFTER MONTH 60 ===")
print("These should not exist since there are no visits!")
print(late_data[['time', 'visual_acuity', 'sample_size']].describe())

# Check if there's a pattern to the false sample sizes
print("\n=== FALSE SAMPLE SIZES ===")
print("Sample sizes claimed after month 60:")
print(late_data['sample_size'].value_counts().sort_index())

# Check specific patients that the data claims exist at month 90+
very_late = df[df['time'] >= 90]
print(f"\n=== CLAIMED DATA AT MONTH 90+ ===")
print(very_late[['time', 'visual_acuity', 'sample_size']])