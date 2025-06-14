#!/usr/bin/env python3
"""
Debug what's wrong with the data - are there any visits beyond 60 months?
"""
import json
import pandas as pd
from datetime import datetime

# Load actual simulation results
with open('/Users/rose/Code/CC/output/simulation_results/ape_simulation_ABS_20250514_221752.json', 'r') as f:
    results = json.loads(f.read())

print("=== DATA INVESTIGATION ===")

# Check simulation parameters
print(f"Simulation duration: {results.get('duration_years')} years")

# Analyze mean_va_data
mean_va_data = results['mean_va_data']
df = pd.DataFrame(mean_va_data)

print(f"\nMean VA data shape: {df.shape}")
print(f"Time column range: {df['time'].min()} to {df['time'].max()} months")

# Check sample sizes over time
small_samples = df[df['sample_size'] <= 30]
print(f"\nTime points with sample size <= 30:")
print(small_samples[['time', 'sample_size']].head(10))
print("...")
print(small_samples[['time', 'sample_size']].tail(10))

# Analyze actual visit times in patient histories
patient_histories = results['patient_histories']
all_visit_months = []

# Sample first few patients to see their visit ranges
sample_patients = list(patient_histories.keys())[:5]
start_date = datetime(2023, 1, 1)  # Default start date

print("\n=== SAMPLE PATIENT VISIT RANGES ===")
for patient_id in sample_patients:
    visits = patient_histories[patient_id]
    if isinstance(visits, list) and visits:
        visit_months = []
        for visit in visits:
            if isinstance(visit, dict) and 'date' in visit:
                visit_date_str = visit['date']
                try:
                    visit_date = datetime.strptime(visit_date_str.replace('T', ' '), "%Y-%m-%d %H:%M:%S")
                    months = (visit_date - start_date).days / 30.44
                    visit_months.append(months)
                    all_visit_months.append(months)
                except:
                    pass
        
        if visit_months:
            print(f"{patient_id}: {len(visit_months)} visits, from month {min(visit_months):.1f} to {max(visit_months):.1f}")

# Check overall visit distribution
if all_visit_months:
    print(f"\n=== OVERALL VISIT DISTRIBUTION ===")
    print(f"Total visits analyzed: {len(all_visit_months)}")
    print(f"Visit range: {min(all_visit_months):.1f} to {max(all_visit_months):.1f} months")
    
    # Check distribution by decade
    print("\nVisits by month range:")
    for start in range(0, 101, 10):
        end = start + 10
        count = sum(1 for m in all_visit_months if start <= m < end)
        print(f"Months {start:2d}-{end:2d}: {count:5d} visits")

# Check if there's a mismatch between mean_va_data times and actual visit times
print("\n=== TIME MISMATCH ANALYSIS ===")
print(f"Mean VA data goes up to month {df['time'].max()}")
print(f"Actual visits go up to month {max(all_visit_months):.1f}")

# Check sample sizes after month 60
late_samples = df[df['time'] > 60]
print(f"\nTime points after month 60:")
print(late_samples[['time', 'sample_size']].head(10))
print(f"Number of time points after month 60: {len(late_samples)}")
print(f"Total sample size sum after month 60: {late_samples['sample_size'].sum()}")