"""
Simple streamgraph visualization for patient states.

This version works with the basic data available in ParquetResults,
showing active vs discontinued patients over time.
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from typing import Dict, Optional, TYPE_CHECKING
import streamlit as st

# Use TYPE_CHECKING to avoid circular imports
if TYPE_CHECKING:
    from core.results.parquet import ParquetResults


@st.cache_data
def calculate_patient_states_simple(
    _results,  # Leading underscore tells Streamlit not to hash this parameter
    time_resolution: str = 'month'
) -> pd.DataFrame:
    """
    Calculate simple patient states (active/discontinued) over time.
    
    Works with both InMemoryResults and ParquetResults.
    """
    # Check if this is ParquetResults or InMemoryResults
    if hasattr(_results, 'data_path'):
        # ParquetResults - load from files
        # discontinuation_time should already be in days (integer) from ParquetWriter
        patients_df = pd.read_parquet(_results.data_path / 'patients.parquet')
        visits_df = pd.read_parquet(_results.data_path / 'visits.parquet')
    else:
        # InMemoryResults - extract from raw_results
        # First, find the earliest visit date to use as reference
        start_date = None
        for patient_id, patient in _results.raw_results.patient_histories.items():
            visits = getattr(patient, 'visit_history', [])
            if visits and isinstance(visits[0], dict) and 'date' in visits[0]:
                visit_date = visits[0]['date']
                if start_date is None or visit_date < start_date:
                    start_date = visit_date
        
        # Get patient data with discontinuation times converted to days
        patients_data = []
        for patient_id, patient in _results.raw_results.patient_histories.items():
            disc_date = getattr(patient, 'discontinuation_date', None)
            disc_time_days = None
            if disc_date and start_date:
                # Convert datetime to days from start
                time_delta = disc_date - start_date
                disc_time_days = int(time_delta.total_seconds() / (24 * 3600))
            
            patients_data.append({
                'patient_id': patient_id,
                'discontinued': getattr(patient, 'is_discontinued', False),
                'discontinuation_time': disc_time_days  # Now in days, not datetime
            })
        patients_df = pd.DataFrame(patients_data)
        
        # Get visit data with proper time conversion
        visits_data = []
        for patient_id, patient in _results.raw_results.patient_histories.items():
            visits = getattr(patient, 'visit_history', [])
            for i, visit in enumerate(visits):
                if not isinstance(visit, dict) or 'date' not in visit:
                    raise ValueError(f"Visit {i} for patient {patient_id} missing required 'date' field")
                if not start_date:
                    raise ValueError("No start date found - cannot calculate time deltas")
                    
                # Calculate days from start date
                visit_date = visit['date']
                time_delta = visit_date - start_date
                time_days = int(time_delta.total_seconds() / (24 * 3600))
                visits_data.append({
                    'patient_id': patient_id,
                    'time_days': time_days
                })
        visits_df = pd.DataFrame(visits_data)
    
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
            'Active': active_count,
            'Discontinued': discontinued_count
        })
    
    return pd.DataFrame(state_data)


def create_simple_streamgraph(
    results,  # ParquetResults - type annotation removed to avoid import
    time_resolution: str = 'month',
    normalize: bool = False
) -> go.Figure:
    """
    Create a simple streamgraph showing active vs discontinued patients.
    """
    # Get state data
    state_df = calculate_patient_states_simple(results, time_resolution)
    
    # Normalize if requested
    if normalize:
        total = state_df['Active'] + state_df['Discontinued']
        state_df['Active'] = (state_df['Active'] / total) * 100
        state_df['Discontinued'] = (state_df['Discontinued'] / total) * 100
    
    # Create figure
    fig = go.Figure()
    
    # Time axis
    if time_resolution == 'month':
        x_values = state_df['time']
        x_label = 'Time (months)'
    else:
        x_values = state_df['time'] / 4.33  # Convert weeks to months for display
        x_label = 'Time (months)'
    
    # Add traces
    fig.add_trace(go.Scatter(
        x=x_values,
        y=state_df['Active'],
        name='Active',
        mode='lines',
        line=dict(width=0),
        fillcolor='#2ecc71',  # Green
        stackgroup='one',
        hovertemplate=(
            '<b>Active Patients</b><br>' +
            'Time: %{x:.1f} months<br>' +
            ('Percentage: %{y:.1f}%' if normalize else 'Count: %{y:.0f}') +
            '<extra></extra>'
        )
    ))
    
    fig.add_trace(go.Scatter(
        x=x_values,
        y=state_df['Discontinued'],
        name='Discontinued',
        mode='lines',
        line=dict(width=0),
        fillcolor='#e74c3c',  # Red
        stackgroup='one',
        hovertemplate=(
            '<b>Discontinued Patients</b><br>' +
            'Time: %{x:.1f} months<br>' +
            ('Percentage: %{y:.1f}%' if normalize else 'Count: %{y:.0f}') +
            '<extra></extra>'
        )
    ))
    
    # Update layout
    fig.update_layout(
        title={
            'text': 'Patient Status Over Time',
            'x': 0.5,
            'xanchor': 'center'
        },
        xaxis_title=x_label,
        yaxis_title='Percentage of Patients' if normalize else 'Number of Patients',
        hovermode='x unified',
        showlegend=True,
        legend=dict(
            orientation="v",
            yanchor="middle",
            y=0.5,
            xanchor="left",
            x=1.05
        ),
        margin=dict(l=50, r=150, t=50, b=50),
        plot_bgcolor='white',
        paper_bgcolor='white'
    )
    
    # Style axes
    fig.update_xaxes(
        showgrid=False,
        showline=True,
        linewidth=1,
        linecolor='black',
        mirror=False,
        ticks='outside',
        tickwidth=1,
        tickcolor='black',
        # Set ticks at yearly intervals
        dtick=12 if time_resolution == 'month' else 52
    )
    
    fig.update_yaxes(
        showgrid=True,
        gridwidth=0.5,
        gridcolor='lightgray',
        showline=True,
        linewidth=1,
        linecolor='black',
        mirror=False,
        ticks='outside',
        tickwidth=1,
        tickcolor='black',
        rangemode='tozero'  # Always start at 0
    )
    
    return fig