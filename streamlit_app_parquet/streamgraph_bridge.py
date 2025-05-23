"""
Bridge module to convert Streamlit simulation results to streamgraph visualization format.

This module provides functions to transform the nested dictionary structure from
Streamlit simulations into the DataFrame format expected by streamgraph visualization
functions.
"""

import pandas as pd
from datetime import datetime
from typing import Dict, List, Tuple, Any
import logging

logger = logging.getLogger(__name__)


def convert_streamlit_to_streamgraph_format(
    streamlit_results: Dict[str, Any],
    simulation_name: str = "streamlit_simulation"
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Convert Streamlit simulation results to streamgraph format.
    
    Parameters
    ----------
    streamlit_results : dict
        Results dictionary from Streamlit simulation runner containing:
        - patient_histories: Dict mapping patient IDs to visit lists
        - metadata: Simulation metadata
        - summary_stats: Summary statistics
        
    simulation_name : str, optional
        Name for the simulation (default: "streamlit_simulation")
        
    Returns
    -------
    tuple of (visits_df, metadata_df, stats_df)
        DataFrames in the format expected by streamgraph functions
    """
    # Extract patient histories
    patient_histories = streamlit_results.get('patient_histories', {})
    
    if not patient_histories:
        raise ValueError("No patient histories found in results")
    
    # Convert patient histories to visits DataFrame
    visits_df = _create_visits_dataframe(patient_histories)
    
    # Create metadata DataFrame
    metadata_df = _create_metadata_dataframe(streamlit_results, simulation_name)
    
    # Create statistics DataFrame
    stats_df = _create_stats_dataframe(streamlit_results, visits_df)
    
    return visits_df, metadata_df, stats_df


def _create_visits_dataframe(patient_histories: Dict[str, List[Dict]]) -> pd.DataFrame:
    """
    Convert patient histories dictionary to visits DataFrame.
    
    Parameters
    ----------
    patient_histories : dict
        Dictionary mapping patient IDs to lists of visit records
        
    Returns
    -------
    pd.DataFrame
        DataFrame with columns: patient_id, date, phase, discontinuation_type, etc.
    """
    visit_records = []
    
    for patient_id, visits in patient_histories.items():
        for visit in visits:
            # Extract core visit information
            record = {
                'patient_id': patient_id,
                'date': visit.get('date', visit.get('time', 0)),  # Handle both date and time fields
                'phase': visit.get('phase', 'Unknown'),
                'vision': visit.get('vision', None),
                'actions': visit.get('actions', []),
                'is_discontinuation_visit': visit.get('is_discontinuation_visit', False),
                'discontinuation_reason': visit.get('discontinuation_reason', None),
                'is_retreatment_visit': visit.get('is_retreatment_visit', False),
                'time_since_last_injection': visit.get('time_since_last_injection', None),
                'cumulative_injections': visit.get('cumulative_injections', 0)
            }
            
            # Map discontinuation reason to standardized type
            if record['is_discontinuation_visit'] and record['discontinuation_reason']:
                record['discontinuation_type'] = _map_discontinuation_type(
                    record['discontinuation_reason']
                )
            else:
                record['discontinuation_type'] = None
            
            visit_records.append(record)
    
    # Create DataFrame
    visits_df = pd.DataFrame(visit_records)
    
    # Ensure date column is datetime
    if 'date' in visits_df.columns:
        # Handle both datetime objects and numeric time values
        if pd.api.types.is_numeric_dtype(visits_df['date']):
            # Convert numeric months to datetime
            visits_df['date'] = pd.to_datetime('2020-01-01') + pd.to_timedelta(visits_df['date'] * 30.44, unit='D')
        else:
            visits_df['date'] = pd.to_datetime(visits_df['date'])
    
    # Sort by patient and date
    visits_df = visits_df.sort_values(['patient_id', 'date']).reset_index(drop=True)
    
    return visits_df


def _create_metadata_dataframe(
    streamlit_results: Dict[str, Any], 
    simulation_name: str
) -> pd.DataFrame:
    """
    Create metadata DataFrame from simulation results.
    
    Parameters
    ----------
    streamlit_results : dict
        Results dictionary from Streamlit simulation
    simulation_name : str
        Name for the simulation
        
    Returns
    -------
    pd.DataFrame
        Metadata DataFrame with simulation information
    """
    metadata = streamlit_results.get('metadata', {})
    
    # Calculate values expected by streamgraph functions
    n_patients = metadata.get('n_patients', len(streamlit_results.get('patient_histories', {})))
    duration_months = metadata.get('duration_months', 36)
    duration_years = duration_months / 12.0
    
    # Extract key metadata in format expected by streamgraph
    metadata_records = [{
        'simulation_name': simulation_name,
        'simulation_time': metadata.get('simulation_time', datetime.now()),
        'patients': n_patients,  # Changed from n_patients to patients
        'duration_years': duration_years,  # Added duration_years
        'duration_months': duration_months,
        'simulation_type': metadata.get('simulation_type', 'ABS'),  # Added simulation_type
        'protocol': metadata.get('protocol', 'Unknown'),
        'drug': metadata.get('drug', 'Unknown'),
        'config_path': metadata.get('config_path', None),
        'random_seed': metadata.get('random_seed', None)
    }]
    
    return pd.DataFrame(metadata_records)


def _create_stats_dataframe(
    streamlit_results: Dict[str, Any],
    visits_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Create statistics DataFrame from simulation results.
    
    Parameters
    ----------
    streamlit_results : dict
        Results dictionary from Streamlit simulation
    visits_df : pd.DataFrame
        Visits DataFrame to calculate additional statistics
        
    Returns
    -------
    pd.DataFrame
        Statistics DataFrame with summary metrics
    """
    summary_stats = streamlit_results.get('summary_stats', {})
    
    # Calculate discontinuation statistics from visits
    total_patients = visits_df['patient_id'].nunique()
    discontinuation_counts = visits_df[visits_df['is_discontinuation_visit']].groupby('discontinuation_type').size()
    
    # Create stats records
    stats_records = []
    
    # Add overall statistics
    stats_records.append({
        'metric': 'total_patients',
        'value': total_patients,
        'category': 'overall'
    })
    
    stats_records.append({
        'metric': 'total_visits',
        'value': len(visits_df),
        'category': 'overall'
    })
    
    # Add discontinuation statistics
    for disc_type, count in discontinuation_counts.items():
        stats_records.append({
            'metric': f'discontinuation_{disc_type}',
            'value': count,
            'category': 'discontinuation'
        })
    
    # Add any summary stats from results
    for key, value in summary_stats.items():
        if isinstance(value, (int, float)):
            stats_records.append({
                'metric': key,
                'value': value,
                'category': 'summary'
            })
    
    return pd.DataFrame(stats_records)


def _map_discontinuation_type(reason: str) -> str:
    """
    Map discontinuation reason text to standardized type.
    
    Based on patient_state_visualization_definitions_20250522.md mapping.
    
    Parameters
    ----------
    reason : str
        Discontinuation reason from simulation
        
    Returns
    -------
    str
        Standardized discontinuation type
    """
    if not reason:
        return None
        
    reason_lower = reason.lower()
    
    # Map to standardized types from patient state definitions
    if 'stable' in reason_lower or 'max_interval' in reason_lower:
        return 'stable_max_interval'  # Maps to "Untreated - remission"
    elif 'admin' in reason_lower or 'non-attendance' in reason_lower or 'random_administrative' in reason_lower:
        return 'random_administrative'  # Maps to "Not booked"
    elif 'course_complete' in reason_lower or 'not_renewed' in reason_lower:
        return 'course_complete_but_not_renewed'  # Maps to "Not renewed"
    elif 'planned' in reason_lower or 'treatment complete' in reason_lower:
        return 'planned'
    elif 'adverse' in reason_lower or 'side effect' in reason_lower:
        return 'adverse'
    elif 'death' in reason_lower:
        return 'death'
    elif 'vision' in reason_lower or 'va' in reason_lower or 'poor_outcome' in reason_lower:
        return 'poor_outcome'  # Future: "Stopped - poor outcome"
    else:
        return 'other'  # Maps to "Discontinued without reason"


def prepare_streamgraph_data(
    visits_df: pd.DataFrame,
    metadata_df: pd.DataFrame,
    stats_df: pd.DataFrame
) -> Dict[str, Any]:
    """
    Prepare data in the exact format expected by streamgraph functions.
    
    Parameters
    ----------
    visits_df : pd.DataFrame
        Visits DataFrame
    metadata_df : pd.DataFrame
        Metadata DataFrame
    stats_df : pd.DataFrame
        Statistics DataFrame
        
    Returns
    -------
    dict
        Data formatted for streamgraph visualization functions
    """
    return {
        'visits': visits_df,
        'metadata': metadata_df,
        'stats': stats_df,
        'patient_histories': _reconstruct_patient_histories(visits_df)
    }


def _reconstruct_patient_histories(visits_df: pd.DataFrame) -> Dict[str, Dict]:
    """
    Reconstruct patient histories dictionary from visits DataFrame.
    
    This is needed for functions that expect the patient_histories format.
    
    Parameters
    ----------
    visits_df : pd.DataFrame
        Visits DataFrame
        
    Returns
    -------
    dict
        Patient histories in nested dictionary format
    """
    patient_histories = {}
    
    for patient_id, patient_visits in visits_df.groupby('patient_id'):
        visits_list = patient_visits.to_dict('records')
        
        # Convert date back to numeric time if needed
        for visit in visits_list:
            if 'date' in visit and pd.notna(visit['date']):
                # Calculate months from start
                start_date = visits_df['date'].min()
                visit['time'] = (visit['date'] - start_date).days / 30.44
        
        patient_histories[patient_id] = {
            'patient_id': patient_id,
            'visits': visits_list
        }
    
    return patient_histories