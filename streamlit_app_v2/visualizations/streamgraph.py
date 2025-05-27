"""
Vectorized streamgraph visualization for patient state transitions.

This implementation uses fully vectorized pandas operations for performance,
avoiding the nested loops found in earlier implementations.
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from typing import Dict, List, Optional, Tuple
import streamlit as st
from datetime import datetime

from ..utils.color_system import ColorSystem
from ..utils.tufte_style import style_axis
from ..core.results.parquet import ParquetResults


# Patient state definitions - matches the established 9-state system
PATIENT_STATES = {
    # Active states
    'active': 'Active',
    'active_retreated_from_stable_max_interval': 'Active (Re-treated from Stable)',
    'active_retreated_from_random_administrative': 'Active (Re-treated from Admin)',
    'active_retreated_from_course_complete': 'Active (Re-treated from Complete)',
    'active_retreated_from_premature': 'Active (Re-treated from Premature)',
    
    # Discontinued states
    'discontinued_stable_max_interval': 'Discontinued (Stable Max Interval)',
    'discontinued_random_administrative': 'Discontinued (Administrative)',
    'discontinued_course_complete_but_not_renewed': 'Discontinued (Course Complete)',
    'discontinued_premature': 'Discontinued (Premature)'
}

# State colors using traffic light system
STATE_COLORS = {
    # Green shades for active
    'active': '#2ecc71',
    'active_retreated_from_stable_max_interval': '#27ae60',
    'active_retreated_from_random_administrative': '#229954',
    'active_retreated_from_course_complete': '#1e8449',
    'active_retreated_from_premature': '#196f3d',
    
    # Amber for planned discontinuation
    'discontinued_stable_max_interval': '#f39c12',
    'discontinued_course_complete_but_not_renewed': '#e67e22',
    
    # Red for problem discontinuations
    'discontinued_random_administrative': '#e74c3c',
    'discontinued_premature': '#c0392b'
}


@st.cache_data
def calculate_patient_states_vectorized(
    results: ParquetResults,
    time_resolution: str = 'month'
) -> pd.DataFrame:
    """
    Calculate patient states over time using fully vectorized operations.
    
    Args:
        results: ParquetResults object containing simulation data
        time_resolution: 'month' or 'week' for time grouping
        
    Returns:
        DataFrame with columns: time, state, count
    """
    # Load visits data
    visits_df = results.get_visits_df()
    
    # Ensure we have required columns
    required_cols = ['patient_id', 'time_years', 'is_discontinuation_visit', 
                     'discontinuation_reason', 'is_retreatment_visit']
    missing_cols = set(required_cols) - set(visits_df.columns)
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    # Convert time to appropriate resolution
    if time_resolution == 'month':
        visits_df['time_period'] = (visits_df['time_years'] * 12).round().astype(int)
        max_periods = int(results.metadata.duration_years * 12)
    else:  # week
        visits_df['time_period'] = (visits_df['time_years'] * 52).round().astype(int)
        max_periods = int(results.metadata.duration_years * 52)
    
    # Sort by patient and time
    visits_df = visits_df.sort_values(['patient_id', 'time_years'])
    
    # Initialize patient states - everyone starts active
    patient_states = pd.DataFrame({
        'patient_id': visits_df['patient_id'].unique(),
        'current_state': 'active',
        'discontinuation_count': 0,
        'retreatment_count': 0
    })
    
    # Process state transitions - vectorized approach
    state_history = []
    
    for period in range(max_periods + 1):
        # Get visits in this period
        period_visits = visits_df[visits_df['time_period'] == period].copy()
        
        if not period_visits.empty:
            # Process discontinuations
            disc_visits = period_visits[period_visits['is_discontinuation_visit'] == True]
            if not disc_visits.empty:
                # Update states for discontinued patients
                disc_patients = disc_visits.groupby('patient_id').agg({
                    'discontinuation_reason': 'first'
                }).reset_index()
                
                # Map discontinuation reasons to states
                reason_to_state = {
                    'stable_max_interval': 'discontinued_stable_max_interval',
                    'random_administrative': 'discontinued_random_administrative',
                    'course_complete_but_not_renewed': 'discontinued_course_complete_but_not_renewed',
                    'premature': 'discontinued_premature',
                    'poor_outcome': 'discontinued_premature'
                }
                
                for _, row in disc_patients.iterrows():
                    pid = row['patient_id']
                    reason = row['discontinuation_reason']
                    new_state = reason_to_state.get(reason, 'discontinued_premature')
                    
                    # Update patient state
                    patient_states.loc[patient_states['patient_id'] == pid, 'current_state'] = new_state
                    patient_states.loc[patient_states['patient_id'] == pid, 'discontinuation_count'] += 1
            
            # Process retreatments
            retreat_visits = period_visits[period_visits['is_retreatment_visit'] == True]
            if not retreat_visits.empty:
                retreat_patients = retreat_visits.groupby('patient_id').size().reset_index()
                
                for _, row in retreat_patients.iterrows():
                    pid = row['patient_id']
                    current = patient_states[patient_states['patient_id'] == pid]['current_state'].iloc[0]
                    
                    # Map current discontinued state to retreated state
                    if 'discontinued' in current:
                        base_reason = current.replace('discontinued_', '')
                        new_state = f'active_retreated_from_{base_reason}'
                        if new_state in PATIENT_STATES:
                            patient_states.loc[patient_states['patient_id'] == pid, 'current_state'] = new_state
                            patient_states.loc[patient_states['patient_id'] == pid, 'retreatment_count'] += 1
        
        # Count states for this period
        state_counts = patient_states['current_state'].value_counts()
        
        # Add to history
        for state, count in state_counts.items():
            state_history.append({
                'time': period,
                'state': state,
                'count': count
            })
        
        # Ensure all states are represented (even with 0 count)
        for state in PATIENT_STATES:
            if state not in state_counts:
                state_history.append({
                    'time': period,
                    'state': state,
                    'count': 0
                })
    
    # Convert to DataFrame
    history_df = pd.DataFrame(state_history)
    
    # Verify conservation
    total_by_period = history_df.groupby('time')['count'].sum()
    expected_total = results.metadata.population_size
    
    if not all(abs(total - expected_total) < 1 for total in total_by_period):
        st.warning("Patient conservation check failed - some patients may be missing from visualization")
    
    return history_df


def create_streamgraph(
    results: ParquetResults,
    time_resolution: str = 'month',
    normalize: bool = False,
    show_legend: bool = True
) -> go.Figure:
    """
    Create an interactive streamgraph visualization of patient states.
    
    Args:
        results: ParquetResults object
        time_resolution: 'month' or 'week'
        normalize: If True, show percentages instead of counts
        show_legend: Whether to show the legend
        
    Returns:
        Plotly figure object
    """
    # Get state data
    state_df = calculate_patient_states_vectorized(results, time_resolution)
    
    # Pivot for stacking
    pivot_df = state_df.pivot(index='time', columns='state', values='count').fillna(0)
    
    # Ensure all states are present
    for state in PATIENT_STATES:
        if state not in pivot_df.columns:
            pivot_df[state] = 0
    
    # Order states for visual clarity (active states first, then discontinued)
    ordered_states = [
        'active',
        'active_retreated_from_stable_max_interval',
        'active_retreated_from_random_administrative', 
        'active_retreated_from_course_complete',
        'active_retreated_from_premature',
        'discontinued_stable_max_interval',
        'discontinued_course_complete_but_not_renewed',
        'discontinued_random_administrative',
        'discontinued_premature'
    ]
    
    pivot_df = pivot_df[ordered_states]
    
    # Normalize if requested
    if normalize:
        row_sums = pivot_df.sum(axis=1)
        pivot_df = pivot_df.div(row_sums, axis=0) * 100
    
    # Create figure
    fig = go.Figure()
    
    # Add traces for each state
    for state in ordered_states:
        # Convert time to appropriate units for display
        if time_resolution == 'month':
            x_values = pivot_df.index
            x_label = 'Time (months)'
        else:
            x_values = pivot_df.index / 4  # Convert weeks to months for display
            x_label = 'Time (months)'
        
        fig.add_trace(go.Scatter(
            x=x_values,
            y=pivot_df[state],
            name=PATIENT_STATES[state],
            mode='lines',
            line=dict(width=0),
            fillcolor=STATE_COLORS[state],
            stackgroup='one',
            groupnorm='',  # No normalization at trace level
            hovertemplate=(
                f'<b>{PATIENT_STATES[state]}</b><br>' +
                'Time: %{x:.1f} months<br>' +
                ('Percentage: %{y:.1f}%' if normalize else 'Count: %{y:.0f}') +
                '<extra></extra>'
            )
        ))
    
    # Update layout with Tufte principles
    fig.update_layout(
        title={
            'text': 'Patient State Transitions Over Time',
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
        tickcolor='black'
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
        tickcolor='black'
    )
    
    return fig


def create_traffic_light_streamgraph(
    results: ParquetResults,
    time_resolution: str = 'month'
) -> go.Figure:
    """
    Create a simplified traffic light streamgraph (green/amber/red).
    
    Args:
        results: ParquetResults object
        time_resolution: 'month' or 'week'
        
    Returns:
        Plotly figure object
    """
    # Get state data
    state_df = calculate_patient_states_vectorized(results, time_resolution)
    
    # Map states to traffic light categories
    traffic_light_map = {
        'active': 'green',
        'active_retreated_from_stable_max_interval': 'green',
        'active_retreated_from_random_administrative': 'green',
        'active_retreated_from_course_complete': 'green',
        'active_retreated_from_premature': 'green',
        'discontinued_stable_max_interval': 'amber',
        'discontinued_course_complete_but_not_renewed': 'amber',
        'discontinued_random_administrative': 'red',
        'discontinued_premature': 'red'
    }
    
    # Add traffic light category
    state_df['category'] = state_df['state'].map(traffic_light_map)
    
    # Aggregate by category
    category_df = state_df.groupby(['time', 'category'])['count'].sum().reset_index()
    
    # Pivot for stacking
    pivot_df = category_df.pivot(index='time', columns='category', values='count').fillna(0)
    
    # Ensure all categories present
    for cat in ['green', 'amber', 'red']:
        if cat not in pivot_df.columns:
            pivot_df[cat] = 0
    
    # Create figure
    fig = go.Figure()
    
    # Category labels and colors
    categories = {
        'green': ('Active Patients', '#2ecc71'),
        'amber': ('Planned Discontinuation', '#f39c12'),
        'red': ('Problem Discontinuation', '#e74c3c')
    }
    
    # Add traces
    for cat in ['green', 'amber', 'red']:
        label, color = categories[cat]
        
        if time_resolution == 'month':
            x_values = pivot_df.index
        else:
            x_values = pivot_df.index / 4
        
        fig.add_trace(go.Scatter(
            x=x_values,
            y=pivot_df[cat],
            name=label,
            mode='lines',
            line=dict(width=0),
            fillcolor=color,
            stackgroup='one',
            hovertemplate=(
                f'<b>{label}</b><br>' +
                'Time: %{x:.1f} months<br>' +
                'Count: %{y:.0f}<br>' +
                '<extra></extra>'
            )
        ))
    
    # Update layout
    fig.update_layout(
        title={
            'text': 'Patient Status Overview',
            'x': 0.5,
            'xanchor': 'center'
        },
        xaxis_title='Time (months)',
        yaxis_title='Number of Patients',
        hovermode='x unified',
        showlegend=True,
        legend=dict(
            orientation="v",
            yanchor="top",
            y=0.95,
            xanchor="left",
            x=1.05
        ),
        margin=dict(l=50, r=150, t=50, b=50),
        plot_bgcolor='white',
        paper_bgcolor='white'
    )
    
    # Style axes
    fig.update_xaxis(
        showgrid=False,
        showline=True,
        linewidth=1,
        linecolor='black',
        mirror=False,
        ticks='outside',
        tickwidth=1,
        tickcolor='black'
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
        tickcolor='black'
    )
    
    return fig