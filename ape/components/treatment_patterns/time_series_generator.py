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
    enrollment_df: Optional[pd.DataFrame] = None,
    results: Optional[object] = None
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
    
    # Add discontinued information if results provided
    if results is not None:
        from ape.components.treatment_patterns.discontinued_utils import add_discontinued_info_to_visits
        visits_df = add_discontinued_info_to_visits(visits_df, results)
    
    # Convert patient-relative time to calendar time
    visits_df = visits_df.copy()
    
    # Convert enrollment times to months for consistency
    if enrollment_df is not None and 'enrollment_time_days' in enrollment_df.columns:
        enrollment_times = dict(zip(
            enrollment_df['patient_id'],
            enrollment_df['enrollment_time_days'] / 30.44
        ))
        
        # Convert patient-relative visit times to calendar times (vectorized)
        # Calendar time = enrollment time + patient time
        visits_df['patient_time_months'] = visits_df['time_days'] / 30.44
        visits_df['enrollment_time_months'] = visits_df['patient_id'].map(enrollment_times).fillna(0)
        visits_df['calendar_time_months'] = visits_df['enrollment_time_months'] + visits_df['patient_time_months']
        visits_df['time_months'] = visits_df['calendar_time_months']
    else:
        # If no enrollment data, assume all patients enrolled at time 0
        # So patient time = calendar time
        visits_df['time_months'] = visits_df['time_days'] / 30.44
        enrollment_times = {}
    
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
    
    # Pre-compute enrolled counts for all time points (enrollment_times already computed above)
    if enrollment_times:
        # Pre-compute enrolled counts for all time points at once (major optimization)
        enrollment_months = enrollment_df['enrollment_time_days'].values / 30.44
        enrollment_months_sorted = np.sort(enrollment_months)
        # Use searchsorted for O(log n) lookup per time point instead of O(n)
        enrolled_at_time = np.searchsorted(enrollment_months_sorted, time_points, side='right')
    else:
        # If no enrollment data, all patients enrolled at time 0
        enrolled_at_time = np.full(len(time_points), total_patients)
    
    # Prepare result list
    time_series_results = []
    
    # For each time point, determine each patient's state
    for i, t in enumerate(time_points):
        # Count patients in each state at this time
        state_counts = get_patient_states_at_time(visits_df, t, end_time, enrollment_times, results)
        
        # Get pre-computed enrolled count (much faster than counting in loop)
        enrolled_count = enrolled_at_time[i]
        
        # Add to results
        for state, count in state_counts.items():
            percentage = (count / enrolled_count * 100) if enrolled_count > 0 else 0
            
            time_series_results.append({
                'time_point': t,
                'state': state,
                'patient_count': count,
                'percentage': percentage
            })
    
    return pd.DataFrame(time_series_results)

def get_patient_states_at_time(visits_df: pd.DataFrame, time_point: float, sim_end_time: float, 
                              enrollment_times: dict = None, results: Optional[object] = None) -> dict:
    """
    Determine patient states at a specific time point using vectorized operations.
    
    Args:
        visits_df: Visit data (may include patient_discontinued column)
        time_point: Time point in months
        sim_end_time: Simulation end time in months
        enrollment_times: Dict of {patient_id: enrollment_time_months}
        results: Optional results object for discontinued info
    
    Returns dict of {state: count}
    """
    # Filter visits before or at this time point
    past_visits = visits_df[visits_df['time_months'] <= time_point].copy()
    
    # Get all unique patients (no need for set conversion)
    all_patients = visits_df['patient_id'].unique()
    
    # If we have enrollment times, filter to only enrolled patients
    if enrollment_times:
        # Vectorized enrollment check for better performance
        enrolled_mask = np.array([
            enrollment_times.get(pid, 0) <= time_point 
            for pid in all_patients
        ])
        enrolled_patients = set(all_patients[enrolled_mask])
        
        if not enrolled_patients:
            return {}  # No patients enrolled yet
    else:
        # If no enrollment data, assume all patients enrolled at time 0
        enrolled_patients = set(all_patients)
    
    if len(past_visits) == 0:
        # All enrolled patients are pre-treatment
        return {'Pre-Treatment': len(enrolled_patients)}
    
    # Get the most recent visit for each patient
    idx = past_visits.groupby('patient_id')['time_months'].idxmax()
    last_visits = past_visits.loc[idx].copy()
    
    # Calculate time since last visit
    time_since_last = time_point - last_visits['time_months']
    
    # Special handling for Initial Treatment state
    # A patient is in "Initial Treatment" if:
    # 1. They are enrolled but have not had their first visit yet, OR
    # 2. They have had their first visit but it was marked as "Initial Treatment"
    #    and not enough time has passed for a second visit
    
    # Check if each patient's most recent visit is their first visit
    is_first_visit = last_visits['visit_num'] == 0
    
    # For patients whose most recent visit is their first visit,
    # they could still be in "Initial Treatment" phase
    # We'll keep them in Initial Treatment for a reasonable period (e.g., up to 2 months)
    # after their first visit to represent the initial treatment period
    
    # Check if we have discontinued information
    has_discontinued_info = 'patient_discontinued' in last_visits.columns
    
    if has_discontinued_info:
        # Check discontinuation time if available
        if 'discontinuation_time_days' in last_visits.columns:
            # Convert time point to days for comparison
            time_point_days = time_point * 30.44
            
            # Patient is discontinued if:
            # 1. They have the discontinued flag AND
            # 2. The discontinuation happened before current time point
            is_discontinued = (
                last_visits['patient_discontinued'] & 
                (last_visits['discontinuation_time_days'] <= time_point_days)
            )
        else:
            # Just use the flag if no time info
            is_discontinued = last_visits['patient_discontinued']
        
        # Vectorized state determination with discontinued info
        conditions = [
            is_discontinued,  # Discontinued patients
            is_first_visit & (time_since_last <= 2) & (last_visits['treatment_state'] == 'Initial Treatment'),
            True  # Default case
        ]
        
        choices = [
            'Discontinued',  # Use "Discontinued" not "No Further Visits"
            'Initial Treatment',
            last_visits['treatment_state']  # Use actual treatment state
        ]
    else:
        # Fall back to time-based logic if no discontinued info
        # But use a more conservative cutoff and different label
        conditions = [
            time_since_last > 12,  # Only after 12 months, not 6
            is_first_visit & (time_since_last <= 2) & (last_visits['treatment_state'] == 'Initial Treatment'),
            True  # Default case
        ]
        
        choices = [
            'Lost to Follow-up',  # More accurate than "No Further Visits"
            'Initial Treatment',
            last_visits['treatment_state']
        ]
    
    last_visits['current_state'] = np.select(conditions, choices)
    
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