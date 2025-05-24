#!/usr/bin/env python3
"""
Debug if visits are actually occurring after month 60.
"""
import json
import numpy as np
from datetime import datetime

# Load actual simulation results
with open('/Users/rose/Code/CC/output/simulation_results/ape_simulation_ABS_20250514_221752.json', 'r') as f:
    results = json.loads(f.read())

print("=== CHECKING ACTUAL VISIT TIMES ===")

patient_histories = results.get('patient_histories', {})
all_visit_times = []
max_time_patient = None
max_time_value = 0

# Analyze each patient
for patient_id, visits in patient_histories.items():
    if not isinstance(visits, list):
        continue
    
    patient_visit_times = []
    cumulative_time = 0
    
    for i, visit in enumerate(visits):
        if not isinstance(visit, dict):
            continue
            
        # Calculate visit time
        if 'interval' in visit and i > 0 and visit['interval'] is not None:
            cumulative_time += visit['interval']
            visit_time_days = cumulative_time
        elif i == 0:
            visit_time_days = 0
            cumulative_time = 0
        else:
            visit_time_days = cumulative_time
            
        visit_time_months = visit_time_days / 30.44
        patient_visit_times.append(visit_time_months)
        all_visit_times.append(visit_time_months)
        
        # Track maximum
        if visit_time_months > max_time_value:
            max_time_value = visit_time_months
            max_time_patient = patient_id

print(f"Total visits analyzed: {len(all_visit_times)}")
print(f"Maximum visit time: {max_time_value:.2f} months")
print(f"Patient with max time: {max_time_patient}")

# Check distribution
print(f"\nVisit time statistics:")
print(f"  Min: {np.min(all_visit_times):.2f} months")
print(f"  Max: {np.max(all_visit_times):.2f} months")
print(f"  Mean: {np.mean(all_visit_times):.2f} months")
print(f"  Std: {np.std(all_visit_times):.2f} months")

# Count visits after month 60
visits_after_60 = sum(1 for t in all_visit_times if t > 60)
print(f"\nVisits after month 60: {visits_after_60}")

# Check if there's a pattern in late visits
if visits_after_60 > 0:
    late_visits = [t for t in all_visit_times if t > 60]
    print(f"Late visit times: {late_visits[:10]}...")
else:
    print("No visits found after month 60")

# Now check the mean_va_data to compare
mean_va_data = results.get('mean_va_data', [])
print(f"\n=== MEAN_VA_DATA COMPARISON ===")
print(f"Total points in mean_va_data: {len(mean_va_data)}")

# Count points after month 60 in mean_va_data
late_points = 0
for point in mean_va_data:
    if point.get('time', 0) > 60:
        late_points += 1

print(f"Points in mean_va_data after month 60: {late_points}")

# Show the last actual visit vs the last data point
if all_visit_times and mean_va_data:
    print(f"\nLast actual visit: {max(all_visit_times):.2f} months")
    last_data_point = max(point.get('time', 0) for point in mean_va_data)
    print(f"Last data point in mean_va_data: {last_data_point:.2f} months")
    print(f"Difference: {last_data_point - max(all_visit_times):.2f} months")