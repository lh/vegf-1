#!/usr/bin/env python3
"""
Debug the individual points logic in the visualization.
"""
import json
import numpy as np
import pandas as pd
from datetime import datetime

# Load actual data
with open('/Users/rose/Code/CC/output/simulation_results/ape_simulation_ABS_20250514_221752.json', 'r') as f:
    results = json.loads(f.read())

# Create DataFrame from mean_va_data
df = pd.DataFrame(results['mean_va_data'])

# Find indices where sample size <= 30
individual_threshold = 30
use_individual_indices = df.index[df["sample_size"] <= individual_threshold].tolist()

print("=== INDIVIDUAL POINTS LOGIC ===")
print(f"Individual threshold: {individual_threshold}")
print(f"Number of time points with individual points: {len(use_individual_indices)}")
print(f"Time points requiring individual display: {df.iloc[use_individual_indices]['time'].tolist()[:10]}...")

# Check patient data structure
patient_data = results.get("patient_histories", {})
print(f"\nPatient data type: {type(patient_data)}")
print(f"Number of patients: {len(patient_data)}")

# Check simulation start date
simulation_start_date = results.get("simulation_start_date")
print(f"\nSimulation start date: {simulation_start_date}")

# Parse the start date
try:
    start_date = datetime.strptime(simulation_start_date, "%Y-%m-%d %H:%M:%S")
except:
    start_date = datetime.strptime(simulation_start_date, "%Y-%m-%d")

# Test the logic for a specific time point
test_time_idx = use_individual_indices[0] if use_individual_indices else 0
test_time_month = df["time_months"].iloc[test_time_idx] if "time_months" in df.columns else df["time"].iloc[test_time_idx]

print(f"\n=== TESTING TIME POINT {test_time_month} ===")
print(f"Sample size at this time: {df['sample_size'].iloc[test_time_idx]}")

# Check time tolerance
time_tolerance = 0.5  # months

# Look for visits near this time
found_visits = 0
patient_count = 0

for patient_id, visits in list(patient_data.items())[:10]:  # Check first 10 patients
    patient_count += 1
    print(f"\nPatient {patient_id}:")
    
    if not isinstance(visits, list):
        print(f"  Visits is not a list: {type(visits)}")
        continue
    
    print(f"  Number of visits: {len(visits)}")
    
    # Check visits near our target time
    best_visit = None
    best_time_diff = float('inf')
    
    for visit in visits:
        if not isinstance(visit, dict):
            continue
            
        if "date" in visit:
            visit_date_str = visit["date"]
            try:
                # Parse the visit date
                if isinstance(visit_date_str, str):
                    visit_date = datetime.strptime(visit_date_str.replace("T", " "), "%Y-%m-%d %H:%M:%S")
                else:
                    visit_date = visit_date_str
                
                # Calculate months from start
                visit_month = (visit_date - start_date).days / 30.44
                
                # Check if within tolerance
                time_diff = abs(visit_month - test_time_month)
                
                if time_diff <= time_tolerance:
                    if time_diff < best_time_diff:
                        best_time_diff = time_diff
                        best_visit = (visit_month, visit)
                        print(f"    Found visit at month {visit_month:.1f} (diff: {time_diff:.3f})")
            except Exception as e:
                print(f"    Error parsing date '{visit_date_str}': {e}")
    
    if best_visit:
        found_visits += 1
        visit_month, visit = best_visit
        va = visit.get("visual_acuity", visit.get("vision"))
        print(f"  Best match: month {visit_month:.1f}, VA: {va}")
    else:
        print(f"  No visits found near month {test_time_month}")

print(f"\n=== SUMMARY ===")
print(f"Checked {patient_count} patients")
print(f"Found {found_visits} visits near month {test_time_month}")
print(f"Target month: {test_time_month}")
print(f"Tolerance: ±{time_tolerance} months")