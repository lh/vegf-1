"""Utilities for handling discontinued patient information."""

import pandas as pd
from typing import Dict, Set, Optional

def get_discontinued_patients(results) -> Dict[str, dict]:
    """
    Extract discontinued patient information from results.
    
    Returns:
        Dict mapping patient_id to discontinuation info:
        {
            'patient_id': {
                'discontinued': True,
                'discontinuation_time': float (days),
                'reason': str (if available)
            }
        }
    """
    discontinued_info = {}
    
    # Handle different result types
    if hasattr(results, 'iterate_patients'):
        # ParquetResults - iterate through patients
        for batch in results.iterate_patients(batch_size=500):
            for patient in batch:
                patient_id = patient['patient_id']
                if patient.get('discontinued', False):
                    discontinued_info[patient_id] = {
                        'discontinued': True,
                        'discontinuation_time': patient.get('discontinuation_time'),
                        'reason': patient.get('discontinuation_reason', 'unknown')
                    }
                else:
                    discontinued_info[patient_id] = {
                        'discontinued': False,
                        'discontinuation_time': None,
                        'reason': None
                    }
    else:
        # In-memory results
        patient_histories = results.patient_histories if hasattr(results, 'patient_histories') else {}
        for patient_id, history in patient_histories.items():
            if history.get('discontinued', False):
                discontinued_info[patient_id] = {
                    'discontinued': True,
                    'discontinuation_time': history.get('discontinuation_time'),
                    'reason': history.get('discontinuation_reason', 'unknown')
                }
            else:
                discontinued_info[patient_id] = {
                    'discontinued': False,
                    'discontinuation_time': None,
                    'reason': None
                }
    
    return discontinued_info


def add_discontinued_info_to_visits(visits_df: pd.DataFrame, results) -> pd.DataFrame:
    """
    Add discontinued information to visits dataframe.
    
    Adds columns:
    - patient_discontinued: bool - whether patient is discontinued
    - discontinuation_time_days: float - when discontinued (if applicable)
    """
    # Get discontinued info
    discontinued_info = get_discontinued_patients(results)
    
    # Add to visits dataframe
    visits_df = visits_df.copy()
    
    # Add discontinued flag
    visits_df['patient_discontinued'] = visits_df['patient_id'].map(
        lambda pid: discontinued_info.get(pid, {}).get('discontinued', False)
    )
    
    # Add discontinuation time
    visits_df['discontinuation_time_days'] = visits_df['patient_id'].map(
        lambda pid: discontinued_info.get(pid, {}).get('discontinuation_time')
    )
    
    return visits_df


def get_patient_state_at_time_with_discontinued(
    visits_df: pd.DataFrame, 
    time_point: float,
    patient_id: str,
    sim_end_time: float
) -> str:
    """
    Determine a patient's state at a specific time, considering discontinued status.
    
    Returns:
        State name (e.g., "Discontinued", "Regular (6-8 weeks)", etc.)
    """
    # Get patient's visits up to this time point
    patient_visits = visits_df[
        (visits_df['patient_id'] == patient_id) & 
        (visits_df['time_months'] <= time_point)
    ]
    
    if len(patient_visits) == 0:
        return 'Pre-Treatment'
    
    # Check if patient is discontinued
    if patient_visits.iloc[0]['patient_discontinued']:
        disc_time = patient_visits.iloc[0].get('discontinuation_time_days', 0) / 30.44
        if disc_time <= time_point:
            return 'Discontinued'
    
    # Get most recent visit
    last_visit = patient_visits.iloc[-1]
    time_since_last = time_point - last_visit['time_months']
    
    # If still receiving regular visits (within reasonable interval)
    # Use actual treatment state, not time-based cutoff
    if time_since_last <= 4:  # Within 4 months is reasonable for any protocol
        return last_visit['treatment_state']
    else:
        # Only mark as "No Further Visits" if actually discontinued
        if last_visit['patient_discontinued']:
            return 'Discontinued'
        else:
            # Patient is still active but between visits
            return last_visit['treatment_state']