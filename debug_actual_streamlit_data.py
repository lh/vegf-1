#!/usr/bin/env python3
"""
Debug the actual data flow in the Streamlit app to understand the individual points issue.
"""
import json
import numpy as np
import pandas as pd
from datetime import datetime

# Load an actual simulation result file to see the data structure
with open('/Users/rose/Code/CC/output/simulation_results/ape_simulation_ABS_20250514_221752.json', 'r') as f:
    results = json.loads(f.read())

print("=== ANALYZING ACTUAL SIMULATION DATA ===")
print(f"Keys in results: {list(results.keys())}")

# Check patient_histories structure
if 'patient_histories' in results:
    patient_histories = results['patient_histories']
    print(f"\npatient_histories type: {type(patient_histories)}")
    
    # Get a sample patient
    sample_id = list(patient_histories.keys())[0]
    sample_patient = patient_histories[sample_id]
    print(f"Sample patient ID: {sample_id}")
    print(f"Sample patient type: {type(sample_patient)}")
    
    if isinstance(sample_patient, list) and sample_patient:
        print(f"Number of visits: {len(sample_patient)}")
        print(f"First visit: {sample_patient[0]}")
        print(f"Last visit: {sample_patient[-1]}")
        
        # Check date types
        if 'date' in sample_patient[0]:
            first_date = sample_patient[0]['date']
            print(f"First date type: {type(first_date)}")
            print(f"First date value: {first_date}")

# Check mean_va_data structure
if 'mean_va_data' in results:
    mean_va_data = results['mean_va_data']
    print(f"\nmean_va_data type: {type(mean_va_data)}")
    print(f"Number of time points: {len(mean_va_data)}")
    
    # Create a DataFrame to analyze
    df = pd.DataFrame(mean_va_data)
    print("\nDataFrame columns:", df.columns.tolist())
    print("\nFirst few rows:")
    print(df.head())
    print("\nLast few rows:")
    print(df.tail())
    
    # Check sample sizes
    if 'sample_size' in df.columns:
        print("\nSample sizes by time:")
        print(df[['time', 'sample_size']])
        
        # Find where sample size drops below 30
        small_samples = df[df['sample_size'] <= 30]
        print(f"\nTime points with sample size <= 30:")
        print(small_samples[['time', 'sample_size']])

# Check simulation_start_date
if 'simulation_start_date' in results:
    start_date = results['simulation_start_date']
    print(f"\nSimulation start date: {start_date}")
    print(f"Start date type: {type(start_date)}")

# Analyze time distribution in patient visits
print("\n=== ANALYZING VISIT TIME DISTRIBUTION ===")
if 'patient_histories' in results:
    all_visit_times = []
    
    for patient_id, visits in patient_histories.items():
        if isinstance(visits, list):
            for visit in visits:
                if isinstance(visit, dict) and 'date' in visit:
                    all_visit_times.append(visit['date'])
    
    print(f"Total visits across all patients: {len(all_visit_times)}")
    
    # Convert to months from start
    if all_visit_times and 'simulation_start_date' in results:
        start_date_str = results['simulation_start_date']
        # Parse the date string
        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d %H:%M:%S")
        except:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
        
        visit_months = []
        for visit_date_str in all_visit_times[:1000]:  # Sample first 1000
            try:
                if isinstance(visit_date_str, str):
                    visit_date = datetime.strptime(visit_date_str, "%Y-%m-%d %H:%M:%S")
                else:
                    visit_date = visit_date_str
                months = (visit_date - start_date).days / 30.44
                visit_months.append(months)
            except:
                pass
        
        if visit_months:
            visit_months = sorted(visit_months)
            print(f"Visit months range: {min(visit_months):.1f} to {max(visit_months):.1f}")
            print(f"Visit months distribution (quartiles):")
            print(f"  Q1: {np.percentile(visit_months, 25):.1f}")
            print(f"  Q2: {np.percentile(visit_months, 50):.1f}")
            print(f"  Q3: {np.percentile(visit_months, 75):.1f}")