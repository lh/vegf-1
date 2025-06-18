"""
Enhanced pattern analyzer that includes "Still in Treatment" transitions.

This module extends the basic pattern analyzer to show patients who remain
in their treatment state at the end of the simulation period.
"""

import pandas as pd
import numpy as np
from typing import Tuple, Dict, List
from ape.utils.visualization_modes import get_mode_colors


def create_terminal_transitions(visits_df: pd.DataFrame, transitions_df: pd.DataFrame, 
                              simulation_end_days: float, results=None) -> pd.DataFrame:
    """
    Create artificial transitions for patients still in treatment at simulation end.
    
    Args:
        visits_df: DataFrame with all visits
        transitions_df: Original transitions between states
        simulation_end_days: Total simulation duration in days
        results: Optional results object to get discontinued information
        
    Returns:
        Enhanced transitions DataFrame including terminal transitions
    """
    # Get the last visit for each patient - use idxmax to preserve all columns
    last_visit_idx = visits_df.groupby('patient_id')['time_days'].idxmax()
    last_visits = visits_df.loc[last_visit_idx].copy()
    
    # Get discontinued information if available
    if results is not None:
        from ape.components.treatment_patterns.discontinued_utils import get_discontinued_patients
        discontinued_info = get_discontinued_patients(results)
        
        # Add discontinued status to last visits
        last_visits['is_discontinued'] = last_visits['patient_id'].map(
            lambda pid: discontinued_info.get(pid, {}).get('discontinued', False)
        )
        
        # Only consider patients who are NOT discontinued
        active_at_end = last_visits[~last_visits['is_discontinued']].copy()
    else:
        # Fallback to time-based logic if no results provided
        cutoff_days = simulation_end_days - 30  # Within last month
        active_at_end = last_visits[last_visits['time_days'] < cutoff_days].copy()
    
    # Create terminal transitions
    terminal_transitions = []
    
    # Add transitions for active patients
    for _, patient in active_at_end.iterrows():
        # Use the treatment_state from the last visit
        current_state = patient['treatment_state']
        
        # Create terminal state name
        terminal_state = f"Still in {current_state} (Year {int(simulation_end_days/365)})"
        
        # Create a complete transition record with all expected columns
        terminal_transitions.append({
            'patient_id': patient['patient_id'],
            'from_state': current_state,
            'to_state': terminal_state,
            'from_time_days': patient['time_days'],
            'to_time_days': simulation_end_days,  # End of simulation
            'from_time': patient['time_days'] / (365.25 / 12),
            'to_time': simulation_end_days / (365.25 / 12),
            'duration_days': simulation_end_days - patient['time_days'],
            'duration': (simulation_end_days - patient['time_days']) / (365.25 / 12),
            'interval_days': np.nan  # No actual interval since it's terminal
        })
    
    # Add transitions for discontinued patients if we have the info
    if results is not None and 'is_discontinued' in last_visits.columns:
        # Get discontinued patients  
        discontinued_patients = last_visits[last_visits['is_discontinued']].copy()
        
        for _, patient in discontinued_patients.iterrows():
            # Use their last treatment state
            current_state = patient['treatment_state']
            
            # Create transition to "Discontinued"
            terminal_transitions.append({
                'patient_id': patient['patient_id'],
                'from_state': current_state,
                'to_state': 'Discontinued',
                'from_time_days': patient['time_days'],
                'to_time_days': patient['time_days'],  # Discontinuation at last visit
                'from_time': patient['time_days'] / (365.25 / 12),
                'to_time': patient['time_days'] / (365.25 / 12),
                'duration_days': 0,  # Instant transition to discontinued
                'duration': 0,
                'interval_days': np.nan
            })
    
    # Combine with original transitions
    if terminal_transitions:
        terminal_df = pd.DataFrame(terminal_transitions)
        
        # Ensure consistent column dtypes to avoid FutureWarning
        # Since we're now using np.nan instead of None, pandas should infer correct dtypes
        # But let's be explicit about matching the dtypes
        for col in terminal_df.columns:
            if col in transitions_df.columns and col != 'patient_id':
                # Ensure numeric columns have consistent dtype
                if transitions_df[col].dtype in [np.float64, np.float32]:
                    terminal_df[col] = terminal_df[col].astype(transitions_df[col].dtype)
        
        # Now concat with matching structure and dtypes
        enhanced_transitions = pd.concat([transitions_df, terminal_df], ignore_index=True)
    else:
        enhanced_transitions = transitions_df
    
    return enhanced_transitions


def extract_treatment_patterns_with_terminals(results) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Extract treatment patterns including terminal states for active patients.
    
    This wraps the original extract_treatment_patterns_vectorized function
    and adds terminal transitions for patients still in treatment.
    """
    # Import here to avoid circular imports
    from ape.components.treatment_patterns import extract_treatment_patterns_vectorized
    
    # Get original transitions
    transitions_df, visits_df = extract_treatment_patterns_vectorized(results)
    
    # Remove "No Further Visits" transitions - we'll replace with proper "Discontinued" 
    transitions_df = transitions_df[transitions_df['to_state'] != 'No Further Visits']
    
    # Get simulation duration
    simulation_days = results.metadata.duration_years * 365
    
    # Add terminal transitions
    enhanced_transitions = create_terminal_transitions(
        visits_df, transitions_df, simulation_days, results
    )
    
    # Don't print during web app usage - only for debugging
    
    return enhanced_transitions, visits_df


def get_terminal_node_colors() -> Dict[str, str]:
    """
    Get colors for terminal nodes that are visually distinct.
    
    Returns dictionary of state_name -> color for terminal nodes.
    """
    # Get colors from central system
    colors = get_mode_colors()
    
    # Map terminal states to their color keys in the central system
    return {
        "Still in Initial Treatment": colors.get('terminal_initial', "rgba(158, 202, 225, 0.5)"),
        "Still in Intensive (Monthly)": colors.get('terminal_intensive', "rgba(74, 144, 226, 0.5)"),
        "Still in Regular (6-8 weeks)": colors.get('terminal_regular', "rgba(127, 186, 0, 0.5)"),
        "Still in Extended (12+ weeks)": colors.get('terminal_extended', "rgba(90, 142, 0, 0.5)"),
        "Still in Maximum Extension (16 weeks)": colors.get('terminal_maximum', "rgba(60, 95, 0, 0.5)"),
    }