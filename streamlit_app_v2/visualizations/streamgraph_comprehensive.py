"""
Comprehensive streamgraph visualization for patient cohort flow.

This creates a visualization similar to the reference image showing:
- Active patients (with different treatment frequencies)
- Discontinued patients (by type)
- Retreatment status

Uses REAL simulation data - no synthetic curves.
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import streamlit as st
from pathlib import Path
from typing import Optional, Dict, Tuple
from collections import defaultdict

# Import semantic colors from visualization modes
from utils.visualization_modes import get_mode_colors


def get_patient_state_at_time(patient_data: dict, time_days: float, 
                             discontinuation_time: Optional[float]) -> str:
    """
    Determine a patient's state at a specific time point.
    """
    visits = patient_data['visits']
    
    # If patient hasn't started treatment yet
    if not visits or visits[0]['time_days'] > time_days:
        return None
    
    # If patient is discontinued by this time
    if patient_data['discontinued'] and discontinuation_time and discontinuation_time <= time_days:
        # Determine discontinuation category
        disc_type = patient_data.get('discontinuation_type', 'other')
        retreated = patient_data.get('retreatment_count', 0) > 0
        
        if retreated:
            return 'Discontinued After Retreatment'
        elif disc_type == 'planned':
            return 'Discontinued Planned'
        elif disc_type == 'administrative':
            return 'Discontinued Administrative'
        else:
            # Check if early discontinuation (< 1 year)
            if discontinuation_time < 365:
                return 'Discontinued Premature'
            else:
                return 'Discontinued Planned'
    
    # Patient is active - determine treatment intensity
    # Find visits up to this time
    visits_to_time = [v for v in visits if v['time_days'] <= time_days]
    
    if len(visits_to_time) < 2:
        return 'Active (Never Discontinued)'
    
    # Check if patient has been retreated
    if patient_data.get('retreatment_count', 0) > 0:
        return 'Active (Retreated)'
    
    # Look at recent treatment pattern
    # Calculate intervals for last 3 visits
    recent_intervals = []
    for i in range(max(1, len(visits_to_time) - 3), len(visits_to_time)):
        interval = visits_to_time[i]['time_days'] - visits_to_time[i-1]['time_days']
        recent_intervals.append(interval)
    
    if recent_intervals:
        avg_interval = np.mean(recent_intervals)
        if avg_interval > 180:  # Gap > 6 months
            return 'Active (Never Discontinued)'  # Will restart
        elif avg_interval <= 35:
            return 'Active (Never Discontinued)'  # High frequency
        elif avg_interval >= 84:
            return 'Active (Never Discontinued)'  # Extended interval
        else:
            return 'Active (Never Discontinued)'  # Regular
    
    return 'Active (Never Discontinued)'


@st.cache_data
def calculate_patient_cohort_flow(
    _results,
    time_resolution: str = 'month'
) -> Tuple[pd.DataFrame, Dict[str, int]]:
    """
    Calculate patient cohort flow through treatment states over time.
    
    Returns:
        - DataFrame with state counts at each time point
        - Summary statistics dictionary
    """
    # Load data from ParquetResults
    if not hasattr(_results, 'data_path'):
        raise ValueError("Expected ParquetResults with data_path attribute")
    
    patients_df = pd.read_parquet(_results.data_path / 'patients.parquet')
    visits_df = pd.read_parquet(_results.data_path / 'visits.parquet')
    
    if len(visits_df) == 0:
        raise ValueError("No visit data available")
    
    # Setup time points
    max_time_days = visits_df['time_days'].max()
    if time_resolution == 'month':
        days_per_unit = 30.4375  # Average days per month
        num_units = int(max_time_days / days_per_unit) + 1
    else:
        days_per_unit = 7.0
        num_units = int(max_time_days / days_per_unit) + 1
    
    time_points = np.arange(0, num_units + 1)
    
    # Process each patient
    patient_histories = {}
    retreatment_count = 0
    
    for _, patient in patients_df.iterrows():
        pid = patient['patient_id']
        patient_visits = visits_df[visits_df['patient_id'] == pid].sort_values('time_days')
        
        patient_histories[pid] = {
            'visits': patient_visits.to_dict('records'),
            'discontinued': patient.get('discontinued', False),
            'discontinuation_time': patient.get('discontinuation_time', None),
            'discontinuation_type': patient.get('discontinuation_type', None),
            'retreatment_count': patient.get('retreatment_count', 0)
        }
        
        if patient.get('retreatment_count', 0) > 0:
            retreatment_count += 1
    
    # Count states at each time point
    state_counts_over_time = []
    
    for t in time_points:
        time_days = t * days_per_unit
        state_counts = defaultdict(int)
        
        for pid, patient_data in patient_histories.items():
            patient = patients_df[patients_df['patient_id'] == pid].iloc[0]
            disc_time = patient.get('discontinuation_time', None)
            
            state = get_patient_state_at_time(patient_data, time_days, disc_time)
            if state:
                state_counts[state] += 1
        
        # Add time point
        row = {'time': t}
        row.update(dict(state_counts))
        state_counts_over_time.append(row)
    
    # Convert to DataFrame
    states_df = pd.DataFrame(state_counts_over_time).fillna(0)
    
    # Calculate summary statistics
    total_discontinued = patients_df['discontinued'].sum()
    disc_breakdown = {}
    
    if 'discontinuation_type' in patients_df.columns:
        disc_types = patients_df[patients_df['discontinued']]['discontinuation_type'].value_counts()
        for disc_type, count in disc_types.items():
            if disc_type == 'planned':
                disc_breakdown['Discontinued Planned'] = count
            elif disc_type == 'administrative':
                disc_breakdown['Discontinued Administrative'] = count
            else:
                disc_breakdown['Discontinued Premature'] = count
    
    summary_stats = {
        'total_patients': len(patients_df),
        'total_discontinuations': int(total_discontinued),
        'total_retreatments': retreatment_count,
        'discontinuation_breakdown': disc_breakdown
    }
    
    return states_df, summary_stats


def create_cohort_flow_streamgraph(
    results,
    time_resolution: str = 'month',
    height: int = 600
) -> go.Figure:
    """
    Create a Plotly streamgraph showing patient cohort flow through treatment states.
    """
    # Get the data
    states_df, summary_stats = calculate_patient_cohort_flow(results, time_resolution)
    
    # Get semantic colors
    colors = get_mode_colors()
    
    # Define state colors using semantic colors where possible
    state_colors = {
        # Active states - shades of green
        'Active (Never Discontinued)': colors.get('terminal_active', '#27ae60'),
        'Active (Retreated)': colors.get('restarted_after_gap', '#8FC15C'),
        
        # Discontinued states - use appropriate semantic colors
        'Discontinued Planned': colors.get('regular_6_8_weeks', '#7FBA00'),  # Light green
        'Discontinued Administrative': colors.get('terminal_discontinued', '#e74c3c'),  # Red
        'Discontinued Premature': colors.get('extended_gap_6_12', '#FF9500'),  # Orange
        'Discontinued After Retreatment': colors.get('long_gap_12_plus', '#FF6347'),  # Tomato
    }
    
    # Order states for stacking (active at bottom, discontinued on top)
    active_states = [col for col in states_df.columns if col != 'time' and 'Active' in col]
    disc_states = [col for col in states_df.columns if col != 'time' and 'Discontinued' in col]
    
    ordered_states = active_states + disc_states
    
    # Create figure
    fig = go.Figure()
    
    # Add traces in order
    for state in ordered_states:
        if state in states_df.columns and states_df[state].sum() > 0:  # Only add if data exists
            fig.add_trace(go.Scatter(
                x=states_df['time'],
                y=states_df[state],
                name=state,
                mode='lines',
                line=dict(width=0.5),
                fillcolor=state_colors.get(state, '#999999'),
                stackgroup='one',
                groupnorm='',  # Don't normalize
                hovertemplate=f'<b>{state}</b><br>' +
                             'Time: %{x:.0f} ' + ('months' if time_resolution == 'month' else 'weeks') + '<br>' +
                             'Patients: %{y:.0f}<br>' +
                             '<extra></extra>'
            ))
    
    # Update layout
    time_label = 'Time (Months)' if time_resolution == 'month' else 'Time (Weeks)'
    
    # Create title with summary stats
    title_text = "Patient Cohort Flow Through Treatment States<br>"
    title_text += f"<sup>Total Discontinuations: {summary_stats['total_discontinuations']} | "
    title_text += f"Total Retreatments: {summary_stats['total_retreatments']}</sup>"
    
    fig.update_layout(
        title={
            'text': title_text,
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 16}
        },
        xaxis=dict(
            title=time_label,
            showgrid=True,
            gridcolor='rgba(128, 128, 128, 0.2)',
            showline=True,
            linewidth=1,
            linecolor='black',
            ticks='outside',
            tickwidth=1,
            tickcolor='black'
        ),
        yaxis=dict(
            title="Number of Patients",
            showgrid=True,
            gridcolor='rgba(128, 128, 128, 0.2)',
            showline=True,
            linewidth=1,
            linecolor='black',
            ticks='outside',
            tickwidth=1,
            tickcolor='black'
        ),
        hovermode='x unified',
        showlegend=True,
        legend=dict(
            orientation="v",
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=1.01,
            bgcolor="rgba(255, 255, 255, 0.8)",
            bordercolor="gray",
            borderwidth=1
        ),
        height=height,
        margin=dict(l=80, r=250, t=100, b=80),
        plot_bgcolor='white',
        paper_bgcolor='white'
    )
    
    # Add total patient count line if there's significant dropout
    total_at_each_time = states_df[ordered_states].sum(axis=1)
    if total_at_each_time.iloc[-1] < total_at_each_time.iloc[0] * 0.9:  # >10% dropout
        fig.add_trace(go.Scatter(
            x=states_df['time'],
            y=total_at_each_time,
            name='Total Patients',
            mode='lines',
            line=dict(color='black', width=2, dash='dash'),
            showlegend=True,
            hovertemplate='Total: %{y:.0f}<extra></extra>'
        ))
    
    return fig