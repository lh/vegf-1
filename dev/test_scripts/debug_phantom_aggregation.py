#!/usr/bin/env python3
"""
Debug the phantom aggregation issue.
"""
import json
import pandas as pd
import numpy as np
from datetime import datetime

# Load actual simulation results
with open('/Users/rose/Code/CC/output/simulation_results/ape_simulation_ABS_20250514_221752.json', 'r') as f:
    results = json.loads(f.read())

print("=== DEBUGGING PHANTOM AGGREGATION ===")

# Extract VA data exactly like process_simulation_results
patient_histories = results.get('patient_histories', {})
va_data = []

print(f"Processing {len(patient_histories)} patients...")

# Track problematic patients
problematic_patients = []

for patient_id, patient in patient_histories.items():
    if not isinstance(patient, list):
        continue
    
    cumulative_time = 0
    visit_times = []
    
    for i, visit in enumerate(patient):
        if isinstance(visit, dict) and 'vision' in visit:
            # Calculate time exactly like in the aggregation code
            if i == 0:
                visit_time = 0
            else:
                visit_time = i  # Using index as fallback
                
            # Store the data
            va_data.append({
                "patient_id": patient_id,
                "time": visit_time,
                "visual_acuity": visit['vision']
            })
            
            visit_times.append(visit_time)
    
    # Check if this patient has problematic times
    if visit_times and max(visit_times) > 60:
        problematic_patients.append({
            'patient_id': patient_id,
            'max_time': max(visit_times),
            'visit_count': len(visit_times),
            'times': visit_times[:10]  # First 10 times
        })

print(f"\nTotal VA data points: {len(va_data)}")
print(f"Problematic patients: {len(problematic_patients)}")

# Create DataFrame and apply rounding
va_df = pd.DataFrame(va_data)
print(f"\nRaw time range: {va_df['time'].min():.2f} to {va_df['time'].max():.2f}")

# Apply the same binning
va_df["time_month"] = va_df["time"].round().astype(int)
print(f"Binned time range: {va_df['time_month'].min()} to {va_df['time_month'].max()}")

# Group by time_month
grouped = va_df.groupby("time_month")["visual_acuity"]
mean_va_by_month = grouped.mean()
count_va_by_month = grouped.count()

print(f"\nGrouped months: {len(mean_va_by_month)}")
print(f"Month range: {mean_va_by_month.index.min()} to {mean_va_by_month.index.max()}")

# Show which months have data
months_with_data = sorted(mean_va_by_month.index.tolist())
print(f"\nMonths with data: {months_with_data[:20]}...")
if len(months_with_data) > 60:
    print(f"Months beyond 60: {[m for m in months_with_data if m > 60][:20]}...")

# Check if the issue is with using visit index as time
print("\n=== CHECKING INDEX-AS-TIME ISSUE ===")
max_visit_count = 0
patient_with_most_visits = None

for patient_id, patient in patient_histories.items():
    if isinstance(patient, list) and len(patient) > max_visit_count:
        max_visit_count = len(patient)
        patient_with_most_visits = patient_id

print(f"Patient with most visits: {patient_with_most_visits} ({max_visit_count} visits)")

# Show this patient's visit structure
if patient_with_most_visits:
    patient_visits = patient_histories[patient_with_most_visits]
    print(f"\nFirst 10 visits for patient {patient_with_most_visits}:")
    for i, visit in enumerate(patient_visits[:10]):
        if isinstance(visit, dict):
            interval = visit.get('interval', 'None')
            date = visit.get('date', 'None')
            print(f"  Visit {i}: interval={interval}, date={date[:10] if isinstance(date, str) else date}")