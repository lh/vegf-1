"""Generate time series data for treatment state visualization."""

import pandas as pd
import numpy as np
from typing import Optional
import streamlit as st

def generate_patient_state_time_series(
    visits_df: pd.DataFrame,
    time_resolution: str = 'month',
    start_time: float = 0,
    end_time: Optional[float] = None,
    enrollment_df: Optional[pd.DataFrame] = None
) -> pd.DataFrame:
    """
    Generate time series of patient counts by state.
    
    Args:
        visits_df: DataFrame with columns: patient_id, time_days, treatment_state
        time_resolution: 'week' or 'month'
        start_time: Start time in months
        end_time: End time in months (None = max from data)
        enrollment_df: Optional DataFrame with patient enrollment info (patient_id, enrollment_time_days)
    
    Returns:
        DataFrame with columns:
        - time_point: Time in months
        - state: Treatment state name
        - patient_count: Number of patients in state
        - percentage: Percentage of total patients
    """
    # Handle edge cases
    if len(visits_df) == 0:
        return pd.DataFrame(columns=['time_point', 'state', 'patient_count', 'percentage'])
    
    # Validate data
    if visits_df['patient_id'].nunique() == 1:
        st.warning("Streamgraph may not be meaningful with single patient")
    
    # Convert to months for consistency
    visits_df = visits_df.copy()
    visits_df['time_months'] = visits_df['time_days'] / 30.44
    
    # Determine time range
    if end_time is None:
        end_time = visits_df['time_months'].max()
    
    # Create time points based on resolution
    if time_resolution == 'week':
        time_step = 0.25  # ~1 week in months
    elif time_resolution == 'quarter':
        time_step = 3.0   # 3 months
    else:  # month
        time_step = 1.0
    
    # Limit number of time points for performance
    max_points = 500
    if (end_time - start_time) / time_step > max_points:
        time_step = (end_time - start_time) / max_points
        st.info(f"Using {time_step:.1f} month intervals for performance")
    
    time_points = np.arange(start_time, end_time + time_step, time_step)
    
    # Get all unique patients
    all_patients = visits_df['patient_id'].unique()
    total_patients = len(all_patients)
    
    # Get enrollment times if available
    enrollment_times = {}
    if enrollment_df is not None and 'enrollment_time_days' in enrollment_df.columns:
        # Convert to months
        enrollment_times = dict(zip(
            enrollment_df['patient_id'],
            enrollment_df['enrollment_time_days'] / 30.44
        ))
    
    # Prepare result list
    results = []
    
    # For each time point, determine each patient's state
    for t in time_points:
        # Count patients in each state at this time
        state_counts = get_patient_states_at_time(visits_df, t, end_time, enrollment_times)
        
        # Add to results
        for state, count in state_counts.items():
            # For percentage, use only enrolled patients at this time
            enrolled_count = sum(1 for pid in all_patients 
                               if enrollment_times.get(pid, 0) <= t)
            percentage = (count / enrolled_count * 100) if enrolled_count > 0 else 0
            
            results.append({
                'time_point': t,
                'state': state,
                'patient_count': count,
                'percentage': percentage
            })
    
    return pd.DataFrame(results)

def get_patient_states_at_time(visits_df: pd.DataFrame, time_point: float, sim_end_time: float, 
                              enrollment_times: dict = None) -> dict:
    """
    Determine patient states at a specific time point using vectorized operations.
    
    Args:
        visits_df: Visit data
        time_point: Time point in months
        sim_end_time: Simulation end time in months
        enrollment_times: Dict of {patient_id: enrollment_time_months}
    
    Returns dict of {state: count}
    """
    # Filter visits before or at this time point
    past_visits = visits_df[visits_df['time_months'] <= time_point].copy()
    
    # Get all unique patients
    all_patients = set(visits_df['patient_id'].unique())
    
    # If we have enrollment times, filter to only enrolled patients
    if enrollment_times:
        enrolled_patients = {pid for pid in all_patients 
                           if enrollment_times.get(pid, 0) <= time_point}
        # Not-yet-enrolled patients don't count
        if not enrolled_patients:
            return {}  # No patients enrolled yet
    else:
        # If no enrollment data, assume all patients enrolled at time 0
        enrolled_patients = all_patients
    
    if len(past_visits) == 0:
        # All enrolled patients are pre-treatment
        return {'Pre-Treatment': len(enrolled_patients)}
    
    # Get the most recent visit for each patient
    idx = past_visits.groupby('patient_id')['time_months'].idxmax()
    last_visits = past_visits.loc[idx].copy()
    
    # Calculate time since last visit
    last_visits['time_since_last'] = time_point - last_visits['time_months']
    
    # Determine states
    last_visits['current_state'] = last_visits.apply(
        lambda row: 'No Further Visits' if row['time_since_last'] > 6 else row['treatment_state'],
        axis=1
    )
    
    # Filter to only enrolled patients
    last_visits = last_visits[last_visits['patient_id'].isin(enrolled_patients)]
    
    # Count states
    state_counts = last_visits['current_state'].value_counts().to_dict()
    
    # Add pre-treatment patients (enrolled but not yet visited)
    patients_with_visits = set(last_visits['patient_id'].unique())
    pre_treatment_count = len(enrolled_patients - patients_with_visits)
    
    if pre_treatment_count > 0:
        state_counts['Pre-Treatment'] = pre_treatment_count
    
    return state_counts

def validate_time_series_data(time_series_df: pd.DataFrame, total_patients: int):
    """Validate that patient counts are conserved."""
    # Check each time point
    for time_point in time_series_df['time_point'].unique():
        point_data = time_series_df[time_series_df['time_point'] == time_point]
        total_at_point = point_data['patient_count'].sum()
        
        if abs(total_at_point - total_patients) > 1:  # Allow for rounding
            st.error(f"Patient count mismatch at t={time_point}: {total_at_point} vs {total_patients}")
            return False
    
    return True