"""
Test to demonstrate the performance improvement from vectorization.
"""

import time
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


def create_test_visits(n_patients=1000, n_visits_per_patient=20):
    """Create test visit data."""
    visits = []
    start_date = datetime(2024, 1, 1)
    
    for patient_id in range(n_patients):
        patient_start = start_date + timedelta(days=patient_id)
        for visit_num in range(n_visits_per_patient):
            visit_date = patient_start + timedelta(days=visit_num * 30)
            visits.append({
                'patient_id': f'P{patient_id:04d}',
                'time_years': (visit_date - start_date).days / 365.0,
                'date': visit_date,
                'visit_number': visit_num
            })
    
    return pd.DataFrame(visits)


def calculate_intervals_with_loops(visits_df):
    """Old method with for loops."""
    intervals = []
    for patient_id in visits_df['patient_id'].unique():
        patient_visits = visits_df[visits_df['patient_id'] == patient_id].sort_values('time_years')
        
        if len(patient_visits) > 1:
            times = patient_visits['time_years'].values * 365
            for i in range(1, len(times)):
                intervals.append({
                    'patient_id': patient_id,
                    'visit_number': i,
                    'interval_days': times[i] - times[i-1]
                })
                    
    return pd.DataFrame(intervals)


def calculate_intervals_vectorized(visits_df):
    """New vectorized method."""
    # Sort by patient and time once
    visits_df = visits_df.sort_values(['patient_id', 'time_years'])
    
    # Calculate intervals using shift - fully vectorized!
    visits_df['prev_time'] = visits_df.groupby('patient_id')['time_years'].shift(1)
    visits_df['interval_days'] = (visits_df['time_years'] - visits_df['prev_time']) * 365
    
    # Add visit number for each patient
    visits_df['visit_number'] = visits_df.groupby('patient_id').cumcount()
    
    # Filter out first visits (no previous interval) and return
    intervals_df = visits_df[visits_df['prev_time'].notna()].copy()
    
    return intervals_df[['patient_id', 'visit_number', 'interval_days']].reset_index(drop=True)


def test_performance():
    """Compare performance of both methods."""
    print("Creating test data...")
    visits_df = create_test_visits(n_patients=1000, n_visits_per_patient=20)
    print(f"Test data: {len(visits_df):,} visits from {visits_df['patient_id'].nunique()} patients")
    
    # Test loop method
    print("\n1. Testing loop-based method...")
    start = time.time()
    result_loops = calculate_intervals_with_loops(visits_df.copy())
    time_loops = time.time() - start
    print(f"   Time: {time_loops:.3f} seconds")
    print(f"   Result: {len(result_loops):,} intervals")
    
    # Test vectorized method
    print("\n2. Testing vectorized method...")
    start = time.time()
    result_vectorized = calculate_intervals_vectorized(visits_df.copy())
    time_vectorized = time.time() - start
    print(f"   Time: {time_vectorized:.3f} seconds")
    print(f"   Result: {len(result_vectorized):,} intervals")
    
    # Compare performance
    speedup = time_loops / time_vectorized
    print(f"\n🚀 Speedup: {speedup:.1f}x faster!")
    
    # Verify results are the same
    print("\nVerifying results match...")
    # Sort both for comparison
    result_loops_sorted = result_loops.sort_values(['patient_id', 'visit_number']).reset_index(drop=True)
    result_vectorized_sorted = result_vectorized.sort_values(['patient_id', 'visit_number']).reset_index(drop=True)
    
    # Compare interval values
    intervals_match = np.allclose(
        result_loops_sorted['interval_days'].values,
        result_vectorized_sorted['interval_days'].values,
        rtol=1e-10
    )
    print(f"✓ Intervals match: {intervals_match}")
    print(f"✓ Same number of intervals: {len(result_loops) == len(result_vectorized)}")


if __name__ == "__main__":
    test_performance()