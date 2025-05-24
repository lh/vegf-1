#!/usr/bin/env python3
"""
Debug the time mismatch issue.
"""
import json
import pandas as pd

# Load actual simulation results
with open('/Users/rose/Code/CC/output/simulation_results/ape_simulation_ABS_20250514_221752.json', 'r') as f:
    results = json.loads(f.read())

# Create DataFrame from mean_va_data
df = pd.DataFrame(results['mean_va_data'])

print("=== TIME POINTS ANALYSIS ===")
print(f"Columns in mean_va_data: {df.columns.tolist()}")
print(f"\nFirst few rows:")
print(df.head())
print(f"\nLast few rows:")
print(df.tail())

# Check if we have 'time' or 'time_months'
time_col = 'time_months' if 'time_months' in df.columns else 'time'
print(f"\nUsing time column: {time_col}")

# Find where sample size <= 30
small_samples = df[df['sample_size'] <= 30]
print(f"\nTime points with sample size <= 30:")
print(small_samples[[time_col, 'sample_size']].head(10))

# Get actual time values
time_values = df[time_col].values
print(f"\nTime values range: {min(time_values)} to {max(time_values)}")
print(f"Number of time points: {len(time_values)}")

# Check the actual visits time range
patient_histories = results['patient_histories']
sample_patient = patient_histories[list(patient_histories.keys())[0]]
print(f"\nSample patient has {len(sample_patient)} visits")

# Get visit times
from datetime import datetime
start_date = datetime(2023, 1, 1)  # Default start date

visit_months = []
for visit in sample_patient:
    if 'date' in visit:
        visit_date_str = visit['date']
        try:
            visit_date = datetime.strptime(visit_date_str.replace('T', ' '), "%Y-%m-%d %H:%M:%S")
            months = (visit_date - start_date).days / 30.44
            visit_months.append(months)
        except:
            pass

if visit_months:
    print(f"Visit months range: {min(visit_months):.1f} to {max(visit_months):.1f}")
    print(f"Visit months: {[f'{m:.1f}' for m in sorted(visit_months)[:10]]}...")

# Check what's causing the mismatch
print(f"\nComparing time points:")
print(f"Time points in mean_va_data: {df[time_col].values[:10].tolist()}...")
print(f"Time points needing individual display: {small_samples[time_col].values[:10].tolist()}...")
print(f"Actual visit months (0-60): {[f'{m:.1f}' for m in sorted(visit_months)[:10]]}...")