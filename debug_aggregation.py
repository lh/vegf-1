#!/usr/bin/env python3
"""
Debug the aggregation process to understand how phantom data is created.
"""
import json
import pandas as pd
import numpy as np
from datetime import datetime

# Load actual simulation results
with open('/Users/rose/Code/CC/output/simulation_results/ape_simulation_ABS_20250514_221752.json', 'r') as f:
    results = json.loads(f.read())

print("=== DEBUGGING AGGREGATION PROCESS ===")

# Follow the same process as process_simulation_results
patient_histories = results.get('patient_histories', {})
va_data = []

print(f"Processing {len(patient_histories)} patients...")

# Track raw time values
time_values = []
patient_visit_times = {}

for patient_id, patient in patient_histories.items():
    if not isinstance(patient, list):
        continue
        
    # Track visits for this patient
    patient_times = []
    cumulative_time = 0
    baseline_time = None
    
    for i, visit in enumerate(patient):
        if isinstance(visit, dict) and 'vision' in visit:
            # Calculate time
            if i == 0:
                visit_time = 0
                if 'date' in visit and isinstance(visit['date'], str):
                    baseline_time = datetime.strptime(visit['date'].replace('T', ' '), "%Y-%m-%d %H:%M:%S")
            else:
                # Calculate time from interval or date
                if 'interval' in visit and isinstance(visit['interval'], (int, float)):
                    cumulative_time += visit['interval']
                    visit_time = cumulative_time / 30.44  # Convert days to months
                elif 'date' in visit and baseline_time is not None:
                    try:
                        visit_date = datetime.strptime(visit['date'].replace('T', ' '), "%Y-%m-%d %H:%M:%S")
                        visit_time = (visit_date - baseline_time).days / 30.44
                    except:
                        visit_time = i  # Fallback to index
                else:
                    visit_time = i  # Fallback to index
            
            # Store raw time
            time_values.append(visit_time)
            patient_times.append(visit_time)
            
            # Add to va_data
            va_data.append({
                "patient_id": patient_id,
                "time": visit_time,
                "visual_acuity": visit['vision']
            })
    
    if patient_times:
        patient_visit_times[patient_id] = patient_times

# Analyze time values
print(f"\nTotal VA data points: {len(va_data)}")
print(f"Time value statistics:")
print(f"  Min: {min(time_values):.2f}")
print(f"  Max: {max(time_values):.2f}")
print(f"  Mean: {np.mean(time_values):.2f}")
print(f"  Std: {np.std(time_values):.2f}")

# Create DataFrame and apply same rounding
va_df = pd.DataFrame(va_data)
va_df["time_month"] = va_df["time"].round().astype(int)

# Find which raw times map to months > 60
high_months = va_df[va_df["time_month"] > 60]
print(f"\nData points mapping to months > 60: {len(high_months)}")

# Show examples of raw times that round to > 60
if len(high_months) > 0:
    print("\nExamples of times that round to > 60:")
    sample = high_months.head(20)
    for _, row in sample.iterrows():
        print(f"  Patient {row['patient_id']}: time {row['time']:.3f} -> month {row['time_month']}")

# Check for outlier patients
print("\n=== PATIENT ANALYSIS ===")
for patient_id, times in patient_visit_times.items():
    max_time = max(times)
    if max_time > 60:
        print(f"Patient {patient_id}: max time {max_time:.2f} months, {len(times)} visits")
        # Show their visit times
        print(f"  Visit times: {[f'{t:.1f}' for t in times[:10]]}...")
        if len(times) > 10:
            print(f"  ... and {len(times) - 10} more visits")

# Check aggregation result
grouped = va_df.groupby("time_month")["visual_acuity"]
mean_va_by_month = grouped.mean()
count_va_by_month = grouped.count()

print("\n=== AGGREGATION RESULTS ===")
print(f"Months with data: {len(mean_va_by_month)}")
print(f"Max month in aggregation: {mean_va_by_month.index.max()}")

# Show sample sizes for high months
high_month_data = pd.DataFrame({
    'time': mean_va_by_month.index[mean_va_by_month.index > 60],
    'sample_size': count_va_by_month[count_va_by_month.index > 60].values,
    'mean_va': mean_va_by_month[mean_va_by_month.index > 60].values
})

if len(high_month_data) > 0:
    print(f"\nData for months > 60:")
    print(high_month_data.head(10))