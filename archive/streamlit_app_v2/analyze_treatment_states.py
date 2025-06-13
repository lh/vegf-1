#!/usr/bin/env python3
"""Analyze what treatment states we can derive from visit intervals."""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

import pandas as pd
import numpy as np
from core.results.parquet import ParquetResults

# Find a recent simulation
sim_dir = Path("simulation_results")
recent_sim = sorted([d for d in sim_dir.iterdir() if d.is_dir() and d.name.startswith("sim_")], 
                    key=lambda x: x.name, reverse=True)[0]

print(f"Analyzing: {recent_sim.name}")

# Load the simulation
results = ParquetResults.load(recent_sim)
patients_df = pd.read_parquet(recent_sim / 'patients.parquet')
visits_df = pd.read_parquet(recent_sim / 'visits.parquet')

print(f"\nTotal patients: {len(patients_df)}")
print(f"Total visits: {len(visits_df)}")

# Analyze visit intervals to understand treatment patterns
print("\n=== VISIT INTERVAL ANALYSIS ===")

# Calculate intervals between visits for each patient
intervals_data = []
patients_with_gaps = 0
patients_with_retreatment = 0

for patient_id in patients_df['patient_id'].unique()[:100]:  # Sample first 100 patients
    patient_visits = visits_df[visits_df['patient_id'] == patient_id].sort_values('time_days')
    
    if len(patient_visits) < 2:
        continue
        
    # Calculate intervals
    times = patient_visits['time_days'].values
    intervals = np.diff(times)
    
    # Check for treatment gaps (>120 days = 4 months)
    has_gap = any(interval > 120 for interval in intervals)
    if has_gap:
        patients_with_gaps += 1
        
    # Check for retreatment (gap followed by resumption)
    for i, interval in enumerate(intervals):
        if interval > 180:  # 6 month gap
            if i < len(intervals) - 1:  # More visits after gap
                patients_with_retreatment += 1
                break
    
    for i, interval in enumerate(intervals):
        intervals_data.append({
            'patient_id': patient_id,
            'visit_number': i + 1,
            'interval_days': interval,
            'interval_category': categorize_interval(interval)
        })

print(f"\nPatients with treatment gaps (>4 months): {patients_with_gaps}")
print(f"Patients with retreatment (visits after 6+ month gap): {patients_with_retreatment}")

# Show interval distribution
intervals_df = pd.DataFrame(intervals_data)
print("\nInterval category distribution:")
print(intervals_df['interval_category'].value_counts())

# Check what happens at specific time points
print("\n=== PATIENT STATES AT SPECIFIC TIMES ===")
for month in [1, 6, 12, 24, 60]:
    days = month * 30.4375
    # Count patients at different states at this time
    active_count = 0
    discontinued_count = 0
    in_gap_count = 0
    
    for patient_id in patients_df['patient_id'].unique()[:100]:
        patient_visits = visits_df[visits_df['patient_id'] == patient_id]
        patient_info = patients_df[patients_df['patient_id'] == patient_id].iloc[0]
        
        # Check if patient has started by this time
        if patient_visits['time_days'].min() > days:
            continue  # Not started yet
            
        # Check if discontinued
        if patient_info['discontinued'] and patient_info.get('discontinuation_time', float('inf')) <= days:
            discontinued_count += 1
        else:
            # Check last visit before this time
            visits_before = patient_visits[patient_visits['time_days'] <= days]
            if len(visits_before) > 0:
                last_visit_time = visits_before['time_days'].max()
                time_since_last = days - last_visit_time
                
                if time_since_last > 120:  # 4+ months
                    in_gap_count += 1
                else:
                    active_count += 1
    
    print(f"\nMonth {month}: Active={active_count}, In Gap={in_gap_count}, Discontinued={discontinued_count}")


def categorize_interval(interval_days):
    """Categorize interval based on days between visits."""
    if interval_days <= 35:  # ~4 weeks
        return "intensive_monthly"
    elif interval_days <= 63:  # ~6-8 weeks
        return "regular_6_8_weeks"
    elif interval_days <= 84:  # ~12 weeks
        return "extended_12_weeks"
    elif interval_days <= 119:  # ~16 weeks
        return "maximum_extension"
    elif interval_days <= 180:  # 3-6 months
        return "treatment_gap_3_6"
    elif interval_days <= 365:  # 6-12 months
        return "extended_gap_6_12"
    else:
        return "long_gap_12_plus"