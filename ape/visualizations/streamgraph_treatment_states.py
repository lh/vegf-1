"""Treatment state streamgraph visualization using Plotly."""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import streamlit as st
from typing import Optional

from ape.utils.visualization_modes import get_mode_colors
from ape.components.treatment_patterns.pattern_analyzer import STATE_COLOR_MAPPING
from ape.components.treatment_patterns.data_manager import get_treatment_pattern_data
from ape.components.treatment_patterns.time_series_generator import generate_patient_state_time_series

# Define state ordering (bottom to top in streamgraph)
STATE_ORDER = [
    'Pre-Treatment',
    'Initial Treatment',
    'Intensive (Monthly)',
    'Regular (6-8 weeks)', 
    'Extended (12+ weeks)',
    'Maximum Extension (16 weeks)',
    'Restarted After Gap',
    'Treatment Gap (3-6 months)',
    'Extended Gap (6-12 months)',
    'Long Gap (12+ months)',
    'No Further Visits',
    'Discontinued',  # True discontinued patients
    'Lost to Follow-up'  # Fallback for time-based cutoff
]

def create_treatment_state_streamgraph(
    results,
    time_resolution: str = 'month',
    normalize: bool = False,
    height: int = 500,
    show_title: bool = True
) -> go.Figure:
    """
    Create interactive Plotly streamgraph of treatment states.
    
    Args:
        results: Simulation results object
        time_resolution: 'week', 'month', or 'quarter'
        normalize: Show as percentage vs absolute counts
        height: Chart height in pixels
        show_title: Whether to show chart title
        
    Returns:
        Plotly figure object
    """
    # Get treatment pattern data
    transitions_df, visits_df = get_treatment_pattern_data(results)
    
    if len(visits_df) == 0:
        # Return empty figure with message
        fig = go.Figure()
        fig.add_annotation(
            text="No visit data available for streamgraph",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=16)
        )
        fig.update_layout(height=height)
        return fig
    
    # Import cache functions
    from ape.components.treatment_patterns.time_series_cache import (
        get_cached_time_series_data, compute_df_hash
    )
    
    # Compute hashes for cache invalidation
    visits_hash = compute_df_hash(visits_df)
    enrollment_hash = None
    if hasattr(results, 'get_patients_df'):
        enrollment_df = results.get_patients_df()
        enrollment_hash = compute_df_hash(enrollment_df)
    
    # Get cached time series data - expensive computation happens only once
    with st.spinner("Loading time series data..."):
        time_series_df = get_cached_time_series_data(
            results.metadata.sim_id,
            visits_hash,
            time_resolution,
            enrollment_hash
        )
    
    if len(time_series_df) == 0:
        fig = go.Figure()
        fig.add_annotation(
            text="Unable to generate time series data",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=16)
        )
        fig.update_layout(height=height)
        return fig
    
    # Get colors from semantic system
    colors = get_mode_colors()
    state_colors = {}
    for state, color_key in STATE_COLOR_MAPPING.items():
        state_colors[state] = colors.get(color_key, '#cccccc')
    
    # Add colors for states not in mapping
    state_colors['Pre-Treatment'] = '#f0f0f0'  # Light gray for pre-treatment
    
    # Pivot data for stacked area chart
    pivot_df = time_series_df.pivot(
        index='time_point',
        columns='state',
        values='patient_count' if not normalize else 'percentage'
    ).fillna(0)
    
    # Ensure all states are present in correct order
    for state in STATE_ORDER:
        if state not in pivot_df.columns:
            pivot_df[state] = 0
    
    # Reorder columns according to STATE_ORDER
    ordered_states = [s for s in STATE_ORDER if s in pivot_df.columns]
    pivot_df = pivot_df[ordered_states]
    
    # Create figure
    fig = go.Figure()
    
    # Add traces for each state
    for state in ordered_states:
        fig.add_trace(go.Scatter(
            x=pivot_df.index,
            y=pivot_df[state],
            mode='lines',
            stackgroup='one',
            name=state,
            line=dict(width=0.5, color=state_colors.get(state, '#cccccc')),
            fillcolor=state_colors.get(state, '#cccccc'),
            hovertemplate=(
                f'<b>{state}</b><br>' +
                'Time: %{x:.1f} months<br>' +
                ('Patients: %{y:,.0f}' if not normalize else 'Percentage: %{y:.1f}%') +
                '<extra></extra>'
            )
        ))
    
    # Update layout
    title = "Patient Treatment States Over Time"
    if normalize:
        title += " (Percentage)"
    
    # Add memorable name if available
    if hasattr(results.metadata, 'memorable_name') and results.metadata.memorable_name:
        title += f" - {results.metadata.memorable_name}"
    
    fig.update_layout(
        title=title if show_title else None,
        xaxis_title="Time (months)",
        yaxis_title="Number of Patients" if not normalize else "Percentage of Patients",
        hovermode='x unified',
        height=height,
        showlegend=True,
        legend=dict(
            orientation="v",
            yanchor="middle",
            y=0.5,
            xanchor="left",
            x=1.02
        )
    )
    
    # Apply clean styling
    fig.update_xaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor='rgba(128,128,128,0.2)',
        zeroline=True,
        zerolinewidth=1,
        zerolinecolor='rgba(128,128,128,0.5)'
    )
    
    fig.update_yaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor='rgba(128,128,128,0.2)',
        zeroline=True,
        zerolinewidth=1,
        zerolinecolor='rgba(128,128,128,0.5)'
    )
    
    return fig

def create_streamgraph_with_sampling(results, max_points: int = 1000) -> go.Figure:
    """
    Create streamgraph with intelligent sampling for large datasets.
    
    Automatically adjusts time resolution based on simulation duration
    to keep visualization performant.
    """
    duration_months = results.metadata.duration_years * 12
    
    # Determine optimal time resolution
    if duration_months / max_points > 3:
        time_resolution = 'quarter'  # 3-month intervals
    elif duration_months / max_points > 1:
        time_resolution = 'month'
    else:
        time_resolution = 'week'
    
    return create_treatment_state_streamgraph(
        results, 
        time_resolution=time_resolution
    )