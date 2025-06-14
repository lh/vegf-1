#!/usr/bin/env python3
"""
Debug script to examine what's actually in the simulation data.
"""

import sys
from pathlib import Path
import pandas as pd
import json

sys.path.append(str(Path(__file__).parent.parent))
from core.results.factory import ResultsFactory

# Load the simulation
sim_path = Path(__file__).parent.parent / "simulation_results" / "sim_20250527_220446_bc6fdd90"
print(f"Loading simulation from: {sim_path}")

# Load results
results = ResultsFactory.load_results(sim_path)
print(f"Results type: {type(results)}")

# Get visits data
print("\n=== Checking visits data ===")
visits_df = results.get_visits_df()
print(f"Total visits: {len(visits_df)}")
print(f"Visits columns: {list(visits_df.columns)}")
print(f"Unique patients: {visits_df['patient_id'].nunique()}")

# Check for discontinuation info in visits
print("\n=== Discontinuation info in visits ===")
if 'is_discontinuation_visit' in visits_df.columns:
    disc_visits = visits_df[visits_df['is_discontinuation_visit'] == True]
    print(f"Discontinuation visits: {len(disc_visits)}")
    if 'discontinuation_reason' in visits_df.columns:
        print("Discontinuation reasons:")
        print(disc_visits['discontinuation_reason'].value_counts())
else:
    print("No is_discontinuation_visit column found")

# Check patients data
print("\n=== Checking patients data ===")
patients_df = pd.read_parquet(results.data_path / 'patients.parquet')
print(f"Total patients: {len(patients_df)}")
print(f"Patient columns: {list(patients_df.columns)}")

# Check discontinuation status
print(f"\nDiscontinued patients: {patients_df['discontinued'].sum()}")
if 'discontinuation_type' in patients_df.columns:
    print("Discontinuation types:")
    print(patients_df[patients_df['discontinued']]['discontinuation_type'].value_counts())
if 'discontinuation_reason' in patients_df.columns:
    print("Discontinuation reasons:")
    print(patients_df[patients_df['discontinued']]['discontinuation_reason'].value_counts())

# Check for specific discontinuation types
print("\n=== Looking for specific outcomes ===")
for col in patients_df.columns:
    if 'death' in col.lower() or 'mortality' in col.lower():
        print(f"Found mortality column: {col}")
        print(patients_df[col].value_counts())

# Sample some patient journeys
print("\n=== Sample patient journeys ===")
sample_patients = patients_df.sample(5)['patient_id'].tolist()
for pid in sample_patients:
    patient_visits = visits_df[visits_df['patient_id'] == pid].sort_values('time_days')
    print(f"\nPatient {pid}:")
    print(f"  Visits: {len(patient_visits)}")
    print(f"  Time span: {patient_visits['time_days'].min():.1f} - {patient_visits['time_days'].max():.1f} days")
    
    # Check for gaps
    if len(patient_visits) > 1:
        time_diffs = patient_visits['time_days'].diff()
        max_gap = time_diffs.max()
        print(f"  Max gap between visits: {max_gap:.1f} days")
        if max_gap > 180:  # 6 months
            print(f"  WARNING: Large gap detected! Possible retreatment scenario")
    
    # Check patient outcome
    patient_info = patients_df[patients_df['patient_id'] == pid].iloc[0]
    if patient_info['discontinued']:
        print(f"  Discontinued: Yes")
        if 'discontinuation_type' in patients_df.columns:
            print(f"  Discontinuation type: {patient_info['discontinuation_type']}")

# Check interval patterns
print("\n=== Interval patterns ===")
if 'interval_days' in visits_df.columns:
    print("Treatment interval distribution:")
    print(visits_df['interval_days'].describe())
    print("\nPatients at max interval (>= 112 days):")
    max_interval_visits = visits_df[visits_df['interval_days'] >= 112]
    print(f"  Visits at max interval: {len(max_interval_visits)}")
    print(f"  Unique patients at max interval: {max_interval_visits['patient_id'].nunique()}")

# Look for retreatment patterns
print("\n=== Looking for retreatment patterns ===")
if 'is_retreatment_visit' in visits_df.columns:
    retreatment_visits = visits_df[visits_df['is_retreatment_visit'] == True]
    print(f"Retreatment visits found: {len(retreatment_visits)}")
else:
    print("No explicit retreatment column")
    
    # Look for gaps that might indicate retreatment
    print("\nChecking for large gaps that might indicate retreatment...")
    visits_sorted = visits_df.sort_values(['patient_id', 'time_days'])
    visits_sorted['prev_time'] = visits_sorted.groupby('patient_id')['time_days'].shift(1)
    visits_sorted['gap_days'] = visits_sorted['time_days'] - visits_sorted['prev_time']
    
    large_gaps = visits_sorted[visits_sorted['gap_days'] > 180]  # 6+ months
    print(f"Visits after 6+ month gaps: {len(large_gaps)}")
    print(f"Patients with 6+ month gaps: {large_gaps['patient_id'].nunique()}")
    
    if len(large_gaps) > 0:
        print("\nSample large gaps:")
        print(large_gaps[['patient_id', 'time_days', 'gap_days']].head(10))