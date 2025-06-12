"""
Comprehensive streamgraph visualization for treatment states.
This module wraps the new streamgraph_treatment_states functionality
to provide the interface expected by the Analysis page.
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import streamlit as st
from pathlib import Path
from typing import Optional, Dict, Tuple, Any
from collections import defaultdict

# Import the new implementation
from .streamgraph_treatment_states import create_treatment_state_streamgraph
from components.treatment_patterns.time_series_generator import generate_patient_state_time_series
from components.treatment_patterns.data_manager import get_treatment_pattern_data


def create_cohort_flow_streamgraph(results, time_resolution: str = 'month'):
    """
    Create a comprehensive patient cohort flow streamgraph.
    
    This is a wrapper around the new streamgraph implementation to provide
    the interface expected by the Analysis page.
    
    Args:
        results: Simulation results object
        time_resolution: Time resolution ('week' or 'month')
        
    Returns:
        Plotly figure object
    """
    # Simply delegate to the streamgraph function
    return create_treatment_state_streamgraph(
        results,
        time_resolution=time_resolution,
        normalize=False  # Default to absolute counts
    )


def calculate_patient_cohort_flow(results, time_resolution: str = 'month') -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Calculate patient cohort flow statistics.
    
    Args:
        results: Simulation results object
        time_resolution: Time resolution for analysis
        
    Returns:
        Tuple of (states_df, summary_stats)
    """
    # Get treatment pattern data
    transitions_df, visits_df = get_treatment_pattern_data(results)
    
    if visits_df is None or visits_df.empty:
        return pd.DataFrame(), {}
    
    # Generate time series data
    sim_end_time = results.metadata.duration_years * 12  # Convert to months
    time_series_data = generate_patient_state_time_series(
        visits_df, 
        time_resolution=time_resolution,
        end_time=sim_end_time
    )
    
    # Convert to DataFrame
    states_df = pd.DataFrame(time_series_data)
    
    # Calculate summary statistics
    summary_stats = {
        'total_patients': results.metadata.n_patients,
        'total_discontinuations': 0,
        'total_retreatments': 0,
        'discontinuation_breakdown': {}
    }
    
    # Count discontinuations (patients who end in "No Further Visits")
    if not states_df.empty:
        last_time_point = states_df.iloc[-1]
        if 'No Further Visits' in last_time_point:
            summary_stats['total_discontinuations'] = last_time_point['No Further Visits']
        
        # Count retreatments (patients who have "Restarted After Gap" at any point)
        if 'Restarted After Gap' in states_df.columns:
            summary_stats['total_retreatments'] = states_df['Restarted After Gap'].max()
    
    # Get discontinuation breakdown from results if available
    if hasattr(results, 'get_summary_statistics'):
        stats = results.get_summary_statistics()
        if 'discontinuation_stats' in stats:
            summary_stats['discontinuation_breakdown'] = stats['discontinuation_stats']
    
    return states_df, summary_stats


def extract_patient_states_comprehensive(results) -> pd.DataFrame:
    """
    Extract comprehensive patient state information.
    
    This function is kept for backward compatibility.
    
    Args:
        results: Simulation results object
        
    Returns:
        DataFrame with patient state information
    """
    # Get treatment pattern data
    data_manager = TreatmentPatternDataManager()
    visits_df = data_manager.get_visits_df(results)
    
    if visits_df is None:
        return pd.DataFrame()
    
    return visits_df