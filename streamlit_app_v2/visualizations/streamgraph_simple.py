"""
Simple streamgraph visualization for patient states over time.

This creates a basic active/discontinued view without the complexity
of treatment-specific tracking.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import streamlit as st
from pathlib import Path
from typing import Optional

# Import ChartBuilder for consistent styling
from utils.chart_builder import ChartBuilder
from utils.style_constants import StyleConstants


def calculate_patient_states_simple(
    _results,  # Leading underscore tells Streamlit not to hash this parameter
    time_resolution: str = 'month'
) -> pd.DataFrame:
    """
    Calculate simple patient states (active/discontinued) over time.
    
    Works with ParquetResults.
    """
    # All results are now ParquetResults
    if not hasattr(_results, 'data_path'):
        raise ValueError("Expected ParquetResults with data_path attribute")
        
    # ParquetResults - load from files
    # discontinuation_time should already be in days (integer) from ParquetWriter
    patients_df = pd.read_parquet(_results.data_path / 'patients.parquet')
    visits_df = pd.read_parquet(_results.data_path / 'visits.parquet')
    
    # Get max time in days
    if len(visits_df) == 0:
        raise ValueError("No visit data available - cannot create streamgraph")
    
    max_time_days = visits_df['time_days'].max()
    
    # Create time points based on days
    if time_resolution == 'month':
        # One point per month
        num_months = int(max_time_days / 30) + 1
        time_points = np.arange(0, num_months + 1)
        time_label = 'months'
        days_per_unit = 30.0
    else:  # week
        # One point per week
        num_weeks = int(max_time_days / 7) + 1
        time_points = np.arange(0, num_weeks + 1)
        time_label = 'weeks'
        days_per_unit = 7.0
    
    # For each time point, count active vs discontinued
    state_data = []
    total_patients = len(patients_df)
    
    # Get discontinuation times if available
    disc_patients = patients_df[patients_df['discontinued'] == True]
    
    for t in time_points:
        time_days = int(t * days_per_unit)
        
        # Count discontinued patients at this time
        if 'discontinuation_time' not in disc_patients.columns:
            raise ValueError("Discontinuation data missing 'discontinuation_time' column")
            
        if len(disc_patients) > 0:
            # discontinuation_time should now be in days (converted above)
            valid_times = disc_patients['discontinuation_time'].notna()
            if not valid_times.any():
                raise ValueError("All discontinuation times are null - cannot create accurate streamgraph")
                
            # Count patients discontinued by this time
            discontinued_count = len(disc_patients[valid_times & (disc_patients['discontinuation_time'] <= time_days)])
        else:
            # No discontinued patients
            discontinued_count = 0
        
        active_count = total_patients - discontinued_count
        
        state_data.append({
            'time': t,
            'active': active_count,
            'discontinued': discontinued_count
        })
    
    return pd.DataFrame(state_data)


def create_simple_streamgraph(
    results, 
    time_resolution: str = 'month',
    title: Optional[str] = None,
    height: int = 400
):
    """
    Create a simple streamgraph visualization of patient states.
    
    Args:
        results: SimulationResults object
        time_resolution: 'month' or 'week' 
        title: Optional custom title
        height: Figure height in pixels
        
    Returns:
        matplotlib figure
    """
    # Calculate states
    states_df = calculate_patient_states_simple(results, time_resolution)
    
    # Create stacked area chart using ChartBuilder
    fig = (ChartBuilder(title or "Patient Status Over Time")
           .with_labels(
               xlabel='Time (months)' if time_resolution == 'month' else 'Time (weeks)',
               ylabel='Number of Patients'
           )
           .with_count_axis('y')
           .plot(lambda ax, colors: 
                 ax.stackplot(states_df['time'], 
                            states_df['discontinued'],
                            states_df['active'],
                            labels=['Discontinued', 'Active'],
                            colors=[colors['warning'], colors['success']],
                            alpha=0.8))
           .with_legend(loc='upper right')
           .build()
           .figure)
    
    # Add total patients line
    ax = fig.get_axes()[0]
    total_patients = states_df['active'].iloc[0] + states_df['discontinued'].iloc[0]
    ax.axhline(y=total_patients, color='gray', linestyle='--', alpha=0.5, 
               label=f'Total: {total_patients:,}')
    
    # Update legend
    ax.legend(loc='upper right')
    
    return fig