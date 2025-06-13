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
from ape.utils.chart_builder import ChartBuilder
from ape.utils.style_constants import StyleConstants


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
    
    # Get last visit time for each patient to know how long they were followed
    patient_last_visit = visits_df.groupby('patient_id')['time_days'].max().reset_index()
    patient_last_visit.columns = ['patient_id', 'last_visit_days']
    
    # Merge with patient data
    patients_with_duration = patients_df.merge(patient_last_visit, on='patient_id', how='left')
    
    # Get discontinuation times if available
    disc_patients = patients_with_duration[patients_with_duration['discontinued'] == True]
    
    for t in time_points:
        time_days = int(t * days_per_unit)
        
        # Only count patients who have data up to this time point
        # (i.e., their last visit is at or after this time)
        patients_at_time = patients_with_duration[patients_with_duration['last_visit_days'] >= time_days]
        
        if len(patients_at_time) == 0:
            # No patients have reached this time point
            state_data.append({
                'time': t,
                'active': 0,
                'discontinued': 0,
                'total': 0
            })
            continue
        
        # Count discontinued patients at this time (among those who reached this time)
        if 'discontinuation_time' in disc_patients.columns and len(disc_patients) > 0:
            # Only consider patients who: 
            # 1. Have reached this time point
            # 2. Are discontinued 
            # 3. Were discontinued by this time
            disc_at_time = disc_patients[
                (disc_patients['last_visit_days'] >= time_days) & 
                (disc_patients['discontinuation_time'].notna()) &
                (disc_patients['discontinuation_time'] <= time_days)
            ]
            discontinued_count = len(disc_at_time)
        else:
            discontinued_count = 0
        
        # Active = patients who reached this time - those discontinued by this time
        total_at_time = len(patients_at_time)
        active_count = total_at_time - discontinued_count
        
        state_data.append({
            'time': t,
            'active': active_count,
            'discontinued': discontinued_count,
            'total': total_at_time
        })
    
    return pd.DataFrame(state_data)


def create_simple_streamgraph(
    results, 
    time_resolution: str = 'month',
    normalize: bool = False,
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
    
    # Handle normalization if requested
    if normalize:
        # Convert to percentages based on total at each time point
        states_df['active_pct'] = (states_df['active'] / states_df['total'] * 100).fillna(0)
        states_df['discontinued_pct'] = (states_df['discontinued'] / states_df['total'] * 100).fillna(0)
    
    # Create stacked area chart using ChartBuilder
    if normalize:
        # Percentage view
        fig = (ChartBuilder(title or "Patient Status Over Time (Patient Time)")
               .with_labels(
                   xlabel='Time Since First Visit (months)' if time_resolution == 'month' else 'Time Since First Visit (weeks)',
                   ylabel='Percentage of Patients'
               )
               .plot(lambda ax, colors: 
                     ax.stackplot(states_df['time'], 
                                states_df['active_pct'],
                                states_df['discontinued_pct'],
                                labels=['Active %', 'Discontinued %'],
                                colors=[colors['success'], colors['warning']],
                                alpha=0.8))
               .with_legend(loc='upper right')
               .build()
               .figure)
    else:
        # Absolute numbers view
        fig = (ChartBuilder(title or "Patient Status Over Time (Patient Time)")
               .with_labels(
                   xlabel='Time Since First Visit (months)' if time_resolution == 'month' else 'Time Since First Visit (weeks)',
                   ylabel='Number of Patients'
               )
               .with_count_axis('y')
               .plot(lambda ax, colors: 
                     ax.stackplot(states_df['time'], 
                                states_df['active'],
                                states_df['discontinued'],
                                labels=['Active', 'Discontinued'],
                                colors=[colors['success'], colors['warning']],
                                alpha=0.8))
               .with_legend(loc='upper right')
               .build()
               .figure)
    
    # Add reference lines based on view type
    ax = fig.get_axes()[0]
    
    if not normalize:
        # Add declining total line to show patients with data at each time point
        ax.plot(states_df['time'], states_df['total'], 
                color='black', linestyle='--', linewidth=2, alpha=0.7,
                label='Patients with data')
        
        # Add annotation about the declining total (only if enough data)
        if len(states_df) > 10 and states_df['total'].iloc[-1] > 0:
            ax.annotate(
                'Total declines as fewer patients\nhave reached later time points',
                xy=(states_df['time'].iloc[-1] * 0.7, states_df['total'].iloc[-1] * 1.1),
                fontsize=10, alpha=0.7,
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor='gray', alpha=0.8)
            )
    else:
        # For percentage view, add 100% line
        ax.axhline(y=100, color='gray', linestyle='--', alpha=0.5)
        ax.set_ylim(0, 105)  # Set y-axis to 0-100%
    
    # Update legend
    ax.legend(loc='upper right')
    
    return fig