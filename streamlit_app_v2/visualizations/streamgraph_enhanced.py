"""
Enhanced streamgraph visualization that works with current data structure.

This version creates a richer visualization from the limited discontinuation
data currently available (planned vs None), while being ready to support
the full 9-state system when more detailed data becomes available.
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from typing import Optional, TYPE_CHECKING
import streamlit as st

# Use TYPE_CHECKING to avoid circular imports
if TYPE_CHECKING:
    from core.results.parquet import ParquetResults


# Enhanced color scheme for better differentiation
STATE_COLORS = {
    'Active': '#2ecc71',                    # Green - active patients
    'Discontinued (Planned)': '#f39c12',     # Amber - planned discontinuation
    'Discontinued (Other)': '#e74c3c',       # Red - other discontinuation
}


@st.cache_data
def calculate_patient_states_enhanced(
    _results,  # Leading underscore tells Streamlit not to hash this parameter
    time_resolution: str = 'month'
) -> pd.DataFrame:
    """
    Calculate enhanced patient states over time using available data.
    
    Works with ParquetResults and creates a richer visualization 
    from limited discontinuation types.
    """
    # All results are now ParquetResults
    if not hasattr(_results, 'data_path'):
        raise ValueError("Expected ParquetResults with data_path attribute")
        
    # ParquetResults - load from files
    patients_df = pd.read_parquet(_results.data_path / 'patients.parquet')
    visits_df = pd.read_parquet(_results.data_path / 'visits.parquet')
    
    # Get max time in days
    if len(visits_df) == 0:
        raise ValueError("No visit data available - cannot create streamgraph")
    
    max_time_days = visits_df['time_days'].max()
    
    # Create time points based on days
    if time_resolution == 'month':
        num_months = int(max_time_days / 30) + 1
        time_points = np.arange(0, num_months + 1)
        time_label = 'months'
        days_per_unit = 30.0
    else:  # week
        num_weeks = int(max_time_days / 7) + 1
        time_points = np.arange(0, num_weeks + 1)
        time_label = 'weeks'
        days_per_unit = 7.0
    
    # For each time point, count patient states
    state_data = []
    total_patients = len(patients_df)
    
    # Get discontinued patients by type
    disc_planned = patients_df[
        (patients_df['discontinued'] == True) & 
        (patients_df['discontinuation_type'] == 'planned')
    ]
    disc_other = patients_df[
        (patients_df['discontinued'] == True) & 
        (patients_df['discontinuation_type'] != 'planned')
    ]
    
    for t in time_points:
        time_days = int(t * days_per_unit)
        
        # Count discontinued patients by type at this time
        planned_count = 0
        other_count = 0
        
        # Planned discontinuations
        if len(disc_planned) > 0:
            valid_times = disc_planned['discontinuation_time'].notna()
            if valid_times.any():
                planned_count = len(disc_planned[
                    valid_times & (disc_planned['discontinuation_time'] <= time_days)
                ])
        
        # Other discontinuations
        if len(disc_other) > 0:
            valid_times = disc_other['discontinuation_time'].notna()
            if valid_times.any():
                other_count = len(disc_other[
                    valid_times & (disc_other['discontinuation_time'] <= time_days)
                ])
        
        active_count = total_patients - planned_count - other_count
        
        state_data.append({
            'time': t,
            'Active': active_count,
            'Discontinued (Planned)': planned_count,
            'Discontinued (Other)': other_count
        })
    
    return pd.DataFrame(state_data)


def create_enhanced_streamgraph(
    results,  # ParquetResults - type annotation removed to avoid import
    time_resolution: str = 'month',
    normalize: bool = False,
    show_legend: bool = True
) -> go.Figure:
    """
    Create an enhanced streamgraph showing patient states with better categorization.
    """
    # Get state data
    state_df = calculate_patient_states_enhanced(results, time_resolution)
    
    # Normalize if requested
    if normalize:
        total = state_df['Active'] + state_df['Discontinued (Planned)'] + state_df['Discontinued (Other)']
        state_df['Active'] = (state_df['Active'] / total) * 100
        state_df['Discontinued (Planned)'] = (state_df['Discontinued (Planned)'] / total) * 100
        state_df['Discontinued (Other)'] = (state_df['Discontinued (Other)'] / total) * 100
    
    # Create figure
    fig = go.Figure()
    
    # Time axis
    if time_resolution == 'month':
        x_values = state_df['time']
        x_label = 'Time (months)'
    else:
        x_values = state_df['time'] / 4.33  # Convert weeks to months for display
        x_label = 'Time (months)'
    
    # Add traces in order (Active, Planned, Other)
    states = ['Active', 'Discontinued (Planned)', 'Discontinued (Other)']
    
    for state in states:
        fig.add_trace(go.Scatter(
            x=x_values,
            y=state_df[state],
            name=state,
            mode='lines',
            line=dict(width=0),
            fillcolor=STATE_COLORS[state],
            stackgroup='one',
            hovertemplate=(
                f'<b>{state}</b><br>' +
                'Time: %{x:.1f} months<br>' +
                ('Percentage: %{y:.1f}%' if normalize else 'Count: %{y:.0f}') +
                '<extra></extra>'
            )
        ))
    
    # Update layout with Tufte principles
    fig.update_layout(
        title={
            'text': 'Patient Status Over Time',
            'x': 0.5,
            'xanchor': 'center'
        },
        xaxis_title=x_label,
        yaxis_title='Percentage of Patients' if normalize else 'Number of Patients',
        hovermode='x unified',
        showlegend=show_legend,
        legend=dict(
            orientation="v",
            yanchor="middle",
            y=0.5,
            xanchor="left",
            x=1.05
        ),
        margin=dict(l=50, r=200 if show_legend else 50, t=50, b=50),
        plot_bgcolor='white',
        paper_bgcolor='white'
    )
    
    # Style axes - Tufte style
    fig.update_xaxis(
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
    
    fig.update_yaxis(
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