"""Fast time series generator using simple vectorized operations."""

import pandas as pd
import numpy as np
from typing import Optional
import streamlit as st

def generate_patient_state_time_series_fast(
    visits_df: pd.DataFrame,
    time_resolution: str = 'month',
    start_time: float = 0,
    end_time: Optional[float] = None,
    enrollment_df: Optional[pd.DataFrame] = None
) -> pd.DataFrame:
    """
    Generate time series of patient counts by state using simple vectorized operations.
    
    Key optimizations:
    1. Pre-compute enrollment counts using cumulative sum
    2. Use vectorized operations for state determination
    3. Process time points in batches
    """
    # Handle edge cases
    if len(visits_df) == 0:
        return pd.DataFrame(columns=['time_point', 'state', 'patient_count', 'percentage'])
    
    # Convert to months
    visits_df = visits_df.copy()
    visits_df['time_months'] = visits_df['time_days'] / 30.44
    
    # Determine time range
    if end_time is None:
        end_time = visits_df['time_months'].max()
    
    # Create time points
    time_steps = {'week': 0.25, 'quarter': 3.0, 'month': 1.0}
    time_step = time_steps.get(time_resolution, 1.0)
    
    # Limit for performance
    max_points = 500
    if (end_time - start_time) / time_step > max_points:
        time_step = (end_time - start_time) / max_points
        st.info(f"Using {time_step:.1f} month intervals for performance")
    
    time_points = np.arange(start_time, end_time + time_step, time_step)
    
    # Pre-compute enrollment counts efficiently
    if enrollment_df is not None and 'enrollment_time_days' in enrollment_df.columns:
        enrollment_months = enrollment_df['enrollment_time_days'].values / 30.44
        enrollment_months_sorted = np.sort(enrollment_months)
        # Use searchsorted for O(log n) lookup per time point
        enrolled_at_time = np.searchsorted(enrollment_months_sorted, time_points, side='right')
    else:
        total_patients = visits_df['patient_id'].nunique()
        enrolled_at_time = np.full(len(time_points), total_patients)
    
    # Process all time points in one go
    results = process_time_points_vectorized(
        visits_df, time_points, enrollment_df, enrolled_at_time
    )
    
    return pd.DataFrame(results)


def process_time_points_vectorized(visits_df, time_points, enrollment_df, enrolled_counts):
    """Process all time points using vectorized operations."""
    results = []
    
    # Get unique patients and their enrollment times
    all_patients = visits_df['patient_id'].unique()
    
    # Create enrollment lookup
    enrollment_dict = {}
    if enrollment_df is not None and 'enrollment_time_days' in enrollment_df.columns:
        enrollment_dict = dict(zip(
            enrollment_df['patient_id'],
            enrollment_df['enrollment_time_days'] / 30.44
        ))
    
    # For each patient, pre-compute their state transitions
    patient_states = {}
    
    for patient_id in all_patients:
        patient_visits = visits_df[visits_df['patient_id'] == patient_id].copy()
        patient_visits = patient_visits.sort_values('time_months')
        
        enrollment_time = enrollment_dict.get(patient_id, 0)
        
        # Store visit times and states for this patient
        patient_states[patient_id] = {
            'enrollment_time': enrollment_time,
            'visit_times': patient_visits['time_months'].values,
            'visit_states': patient_visits['treatment_state'].values
        }
    
    # Process time points in batches for better performance
    batch_size = 50  # Process 50 time points at once
    
    for batch_start in range(0, len(time_points), batch_size):
        batch_end = min(batch_start + batch_size, len(time_points))
        batch_points = time_points[batch_start:batch_end]
        
        # Process this batch of time points
        for i, t in enumerate(batch_points):
            batch_idx = batch_start + i
            enrolled_count = enrolled_counts[batch_idx]
            
            if enrolled_count == 0:
                continue
            
            # Count states at this time point
            state_counts = count_states_at_time_fast(
                patient_states, t, enrollment_dict
            )
            
            # Add to results
            for state, count in state_counts.items():
                if count > 0:
                    percentage = (count / enrolled_count * 100)
                    results.append({
                        'time_point': t,
                        'state': state,
                        'patient_count': count,
                        'percentage': percentage
                    })
    
    return results


def count_states_at_time_fast(patient_states, time_point, enrollment_dict):
    """Count patient states at a specific time using pre-computed data."""
    state_counts = {}
    
    for patient_id, data in patient_states.items():
        # Check if patient is enrolled
        if data['enrollment_time'] > time_point:
            continue
        
        # Find last visit before this time point
        visit_times = data['visit_times']
        visit_states = data['visit_states']
        
        # Binary search for efficiency
        last_visit_idx = np.searchsorted(visit_times, time_point, side='right') - 1
        
        if last_visit_idx < 0:
            # No visits yet - pre-treatment
            state = 'Pre-Treatment'
        else:
            # Check time since last visit
            time_since_last = time_point - visit_times[last_visit_idx]
            
            if time_since_last > 6:  # 6 months
                state = 'No Further Visits'
            else:
                state = visit_states[last_visit_idx]
        
        # Increment count
        state_counts[state] = state_counts.get(state, 0) + 1
    
    return state_counts


def get_patient_states_at_time_fast(visits_df: pd.DataFrame, time_point: float, 
                                   enrollment_times: dict = None) -> dict:
    """
    Fast version using vectorized operations instead of apply().
    """
    # Filter visits
    past_visits = visits_df[visits_df['time_months'] <= time_point].copy()
    
    # Get enrolled patients efficiently
    all_patients = visits_df['patient_id'].unique()
    
    if enrollment_times:
        # Vectorized enrollment check
        enrolled_mask = np.array([
            enrollment_times.get(pid, 0) <= time_point 
            for pid in all_patients
        ])
        enrolled_patients = set(all_patients[enrolled_mask])
        
        if not enrolled_patients:
            return {}
    else:
        enrolled_patients = set(all_patients)
    
    if len(past_visits) == 0:
        return {'Pre-Treatment': len(enrolled_patients)}
    
    # Get last visit per patient
    idx = past_visits.groupby('patient_id')['time_months'].idxmax()
    last_visits = past_visits.loc[idx].copy()
    
    # Vectorized state determination - this is the key optimization
    time_since_last = time_point - last_visits['time_months']
    
    # Use numpy where for vectorized conditional
    last_visits['current_state'] = np.where(
        time_since_last > 6,
        'No Further Visits',
        last_visits['treatment_state']
    )
    
    # Filter enrolled
    last_visits = last_visits[last_visits['patient_id'].isin(enrolled_patients)]
    
    # Count states
    state_counts = last_visits['current_state'].value_counts().to_dict()
    
    # Add pre-treatment
    patients_with_visits = set(last_visits['patient_id'])
    pre_treatment_count = len(enrolled_patients - patients_with_visits)
    
    if pre_treatment_count > 0:
        state_counts['Pre-Treatment'] = pre_treatment_count
    
    return state_counts