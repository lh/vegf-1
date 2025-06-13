"""
Comprehensive Plotly-based streamgraph visualization for patient treatment states.

This visualization shows the full patient cohort flow through different treatment
states over time, including:
- Active patients (never discontinued)
- Patients who were retreated
- Various discontinuation reasons
- Treatment gaps and patterns

CRITICAL: Uses only REAL data from simulations - no synthetic data generation.
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import streamlit as st
from pathlib import Path
from typing import Optional, Dict, List, Tuple
import json
from collections import defaultdict

# Import style constants for consistent theming
from ape.utils.style_constants import StyleConstants


# Color scheme for patient states
STATE_COLORS = {
    # Active states
    "Active (Never Discontinued)": "#4a90e2",  # Blue
    "Active (Retreated)": "#7fba00",  # Green
    "Active (High Frequency)": "#5c8a00",  # Dark green
    "Active (Extended Interval)": "#2d5016",  # Darker green
    
    # Treatment gap states
    "Treatment Gap": "#ffd700",  # Gold
    "Extended Gap": "#ff9500",  # Orange
    
    # Discontinuation states
    "Discontinued (Planned)": "#90ee90",  # Light green
    "Discontinued (Administrative)": "#ff6b6b",  # Red
    "Discontinued (Premature)": "#ffb366",  # Light orange
    "Discontinued (Poor Response)": "#cc0000",  # Dark red
    "Discontinued (Adverse Event)": "#ff9999",  # Pink
    "Discontinued (After Retreatment)": "#dda0dd",  # Plum
    
    # Other states
    "Lost to Follow-up": "#999999",  # Gray
    "Unknown": "#cccccc"  # Light gray
}


def extract_patient_states_comprehensive(
    results,
    time_resolution: str = 'month'
) -> Tuple[pd.DataFrame, Dict[str, int]]:
    """
    Extract comprehensive patient states over time from real simulation data.
    
    Returns:
        - DataFrame with state counts over time
        - Dictionary with summary statistics
    """
    DAYS_PER_MONTH = 365.25 / 12
    
    # Load patient and visit data
    if hasattr(results, 'data_path'):
        patients_df = pd.read_parquet(results.data_path / 'patients.parquet')
        visits_df = pd.read_parquet(results.data_path / 'visits.parquet')
    else:
        raise ValueError("Expected ParquetResults with data_path attribute")
    
    # Get simulation duration
    max_time_days = visits_df['time_days'].max()
    
    # Create time points
    if time_resolution == 'month':
        num_periods = int(max_time_days / DAYS_PER_MONTH) + 1
        time_points = np.arange(0, num_periods + 1)
        time_label = 'months'
        days_per_unit = DAYS_PER_MONTH
    else:  # week
        num_periods = int(max_time_days / 7) + 1
        time_points = np.arange(0, num_periods + 1)
        time_label = 'weeks' 
        days_per_unit = 7.0
    
    # Analyze each patient's journey
    patient_states = analyze_patient_journeys(patients_df, visits_df)
    
    # Count states at each time point
    state_counts_over_time = []
    
    for t in time_points:
        time_days = t * days_per_unit
        state_counts = count_states_at_time(patient_states, time_days)
        state_counts['time'] = t
        state_counts_over_time.append(state_counts)
    
    # Create DataFrame
    states_df = pd.DataFrame(state_counts_over_time)
    
    # Calculate summary statistics
    summary_stats = calculate_summary_statistics(patient_states, patients_df)
    
    return states_df, summary_stats


def analyze_patient_journeys(patients_df: pd.DataFrame, visits_df: pd.DataFrame) -> Dict:
    """
    Analyze each patient's treatment journey to determine their state at each time point.
    """
    patient_states = {}
    
    # Get max time from visits for fallback
    max_time_days = visits_df['time_days'].max() if len(visits_df) > 0 else 0
    
    # Group visits by patient
    visits_by_patient = visits_df.groupby('patient_id')
    
    for patient_id, patient_visits in visits_by_patient:
        patient_info = patients_df[patients_df['patient_id'] == patient_id].iloc[0]
        
        # Sort visits by time
        patient_visits = patient_visits.sort_values('time_days')
        visits_list = patient_visits.to_dict('records')
        
        # Calculate intervals between visits
        intervals = []
        for i in range(1, len(visits_list)):
            interval = visits_list[i]['time_days'] - visits_list[i-1]['time_days']
            intervals.append(interval)
        
        # Detect treatment gaps (> 6 months between visits)
        has_gap = any(interval > 180 for interval in intervals)
        
        # Detect retreatment (gap followed by resumption)
        retreatment_indices = []
        for i, interval in enumerate(intervals):
            if interval > 180:  # 6+ month gap
                retreatment_indices.append(i + 1)  # Index of visit after gap
        
        # Determine patient category
        is_discontinued = patient_info['discontinued']
        retreatment_count = patient_info.get('retreatment_count', 0)
        
        if is_discontinued:
            disc_type = patient_info.get('discontinuation_type', 'unknown')
            disc_time = patient_info.get('discontinuation_time', max_time_days)
            
            # Map discontinuation types
            if disc_type == 'planned':
                if retreatment_count > 0:
                    state = "Discontinued (After Retreatment)"
                else:
                    state = "Discontinued (Planned)"
            elif disc_type == 'adverse':
                state = "Discontinued (Adverse Event)"
            elif disc_type == 'ineffective':
                state = "Discontinued (Poor Response)"
            elif disc_type == 'administrative':
                state = "Discontinued (Administrative)"
            else:
                # Check if early discontinuation
                if disc_time < 365:  # Less than 1 year
                    state = "Discontinued (Premature)"
                else:
                    state = "Discontinued (Planned)"
        else:
            # Active patients
            if retreatment_count > 0 or has_gap:
                state = "Active (Retreated)"
            elif len(intervals) > 0:
                avg_interval = np.mean(intervals)
                if avg_interval <= 35:  # Monthly or more frequent
                    state = "Active (High Frequency)"
                elif avg_interval >= 84:  # 12+ weeks
                    state = "Active (Extended Interval)"
                else:
                    state = "Active (Never Discontinued)"
            else:
                state = "Active (Never Discontinued)"
        
        # Store patient timeline
        patient_states[patient_id] = {
            'visits': visits_list,
            'final_state': state,
            'discontinued': is_discontinued,
            'discontinuation_time': patient_info.get('discontinuation_time', None),
            'retreatment_count': retreatment_count,
            'has_gap': has_gap,
            'retreatment_visits': retreatment_indices
        }
    
    return patient_states


def count_states_at_time(patient_states: Dict, time_days: float) -> Dict[str, int]:
    """
    Count patient states at a specific time point.
    """
    state_counts = defaultdict(int)
    
    for patient_id, patient_data in patient_states.items():
        visits = patient_data['visits']
        
        # Check if patient has started treatment by this time
        if len(visits) == 0 or visits[0]['time_days'] > time_days:
            continue  # Patient hasn't started yet
        
        # Check if patient is discontinued by this time
        if patient_data['discontinued'] and patient_data['discontinuation_time']:
            if patient_data['discontinuation_time'] <= time_days:
                state_counts[patient_data['final_state']] += 1
                continue
        
        # Patient is active at this time - determine their state
        # Find the most recent visit before this time
        recent_visits = [v for v in visits if v['time_days'] <= time_days]
        
        if not recent_visits:
            continue
        
        # Check for treatment gaps at this point
        if len(recent_visits) >= 2:
            last_interval = recent_visits[-1]['time_days'] - recent_visits[-2]['time_days']
            
            if last_interval > 180:  # Currently in a gap
                state_counts["Treatment Gap"] += 1
            elif last_interval > 112:  # Extended gap
                state_counts["Extended Gap"] += 1
            else:
                # Determine active state based on treatment pattern
                if patient_data['retreatment_count'] > 0 or patient_data['has_gap']:
                    state_counts["Active (Retreated)"] += 1
                else:
                    # Calculate average interval up to this point
                    intervals = []
                    for i in range(1, len(recent_visits)):
                        interval = recent_visits[i]['time_days'] - recent_visits[i-1]['time_days']
                        intervals.append(interval)
                    
                    if intervals:
                        avg_interval = np.mean(intervals)
                        if avg_interval <= 35:
                            state_counts["Active (High Frequency)"] += 1
                        elif avg_interval >= 84:
                            state_counts["Active (Extended Interval)"] += 1
                        else:
                            state_counts["Active (Never Discontinued)"] += 1
                    else:
                        state_counts["Active (Never Discontinued)"] += 1
        else:
            # Only one visit so far
            state_counts["Active (Never Discontinued)"] += 1
    
    return dict(state_counts)


def calculate_summary_statistics(patient_states: Dict, patients_df: pd.DataFrame) -> Dict[str, int]:
    """
    Calculate summary statistics from patient states.
    """
    total_patients = len(patient_states)
    total_discontinued = sum(1 for p in patient_states.values() if p['discontinued'])
    total_retreated = sum(1 for p in patient_states.values() if p['retreatment_count'] > 0)
    
    # Count by discontinuation type
    disc_by_type = defaultdict(int)
    for patient_data in patient_states.values():
        if patient_data['discontinued']:
            disc_by_type[patient_data['final_state']] += 1
    
    return {
        'total_patients': total_patients,
        'total_discontinuations': total_discontinued,
        'total_retreatments': total_retreated,
        'discontinuation_by_type': dict(disc_by_type)
    }


def create_comprehensive_streamgraph(
    results,
    time_resolution: str = 'month',
    title: Optional[str] = None,
    height: int = 600
) -> go.Figure:
    """
    Create a comprehensive Plotly streamgraph showing patient treatment states over time.
    """
    # Extract patient states
    states_df, summary_stats = extract_patient_states_comprehensive(results, time_resolution)
    
    # Get all unique states (excluding 'time' column)
    state_columns = [col for col in states_df.columns if col != 'time']
    
    # Order states for better visualization (discontinued states at bottom)
    active_states = [s for s in state_columns if 'Active' in s]
    gap_states = [s for s in state_columns if 'Gap' in s]
    disc_states = [s for s in state_columns if 'Discontinued' in s]
    other_states = [s for s in state_columns if s not in active_states + gap_states + disc_states]
    
    ordered_states = active_states + gap_states + disc_states + other_states
    
    # Create the figure
    fig = go.Figure()
    
    # Add traces for each state
    for state in ordered_states:
        if state in states_df.columns:
            fig.add_trace(go.Scatter(
                x=states_df['time'],
                y=states_df[state],
                name=state,
                mode='lines',
                stackgroup='one',
                fillcolor=STATE_COLORS.get(state, '#cccccc'),
                line=dict(width=0.5, color=STATE_COLORS.get(state, '#cccccc'))
            ))
    
    # Update layout
    time_label = 'Months' if time_resolution == 'month' else 'Weeks'
    
    fig.update_layout(
        title={
            'text': title or f"Patient Treatment States Over Time<br>" + 
                    f"<sup>Total Patients: {summary_stats['total_patients']} | " +
                    f"Total Discontinuations: {summary_stats['total_discontinuations']} | " +
                    f"Total Retreatments: {summary_stats['total_retreatments']}</sup>",
            'x': 0.5,
            'xanchor': 'center'
        },
        xaxis=dict(
            title=f"Time ({time_label})",
            showgrid=True,
            gridcolor='rgba(128, 128, 128, 0.2)'
        ),
        yaxis=dict(
            title="Number of Patients",
            showgrid=True,
            gridcolor='rgba(128, 128, 128, 0.2)'
        ),
        hovermode='x unified',
        showlegend=True,
        legend=dict(
            orientation="v",
            yanchor="middle",
            y=0.5,
            xanchor="left",
            x=1.02
        ),
        height=height,
        margin=dict(l=80, r=200, t=100, b=80),
        plot_bgcolor='white',
        paper_bgcolor='white'
    )
    
    # Add annotations for key insights
    if summary_stats['total_discontinuations'] > 0:
        disc_text = "Discontinuation breakdown:<br>"
        for disc_type, count in summary_stats['discontinuation_by_type'].items():
            disc_text += f"{disc_type}: {count}<br>"
        
        fig.add_annotation(
            xref="paper", yref="paper",
            x=0.02, y=0.98,
            text=disc_text,
            showarrow=False,
            bgcolor="rgba(255, 255, 255, 0.8)",
            bordercolor="gray",
            borderwidth=1,
            align="left",
            font=dict(size=10)
        )
    
    return fig


def display_in_streamlit(results, key_prefix: str = "streamgraph_plotly"):
    """
    Display the comprehensive streamgraph in Streamlit with controls.
    """
    st.subheader("Patient Treatment Flow Analysis")
    
    col1, col2 = st.columns([3, 1])
    
    with col2:
        time_resolution = st.radio(
            "Time Resolution",
            ["month", "week"],
            key=f"{key_prefix}_time_res"
        )
        
        show_percentages = st.checkbox(
            "Show as Percentages",
            value=False,
            key=f"{key_prefix}_show_pct"
        )
    
    # Create the visualization
    fig = create_comprehensive_streamgraph(
        results,
        time_resolution=time_resolution,
        title="Patient Cohort Treatment Journey"
    )
    
    # Display in Streamlit
    with col1:
        st.plotly_chart(fig, use_container_width=True)
    
    # Show summary statistics
    with st.expander("Summary Statistics"):
        states_df, summary_stats = extract_patient_states_comprehensive(results, time_resolution)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Patients", summary_stats['total_patients'])
        with col2:
            st.metric("Total Discontinuations", summary_stats['total_discontinuations'])
        with col3:
            st.metric("Total Retreatments", summary_stats['total_retreatments'])
        
        if summary_stats['discontinuation_by_type']:
            st.write("**Discontinuation Breakdown:**")
            for disc_type, count in summary_stats['discontinuation_by_type'].items():
                pct = (count / summary_stats['total_patients']) * 100
                st.write(f"- {disc_type}: {count} ({pct:.1f}%)")