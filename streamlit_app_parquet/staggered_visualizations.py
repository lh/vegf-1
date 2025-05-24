"""
Staggered Visualizations - Calendar-time perspective visualizations.

This module provides visualization functions for clinic activity and
patient outcomes from a calendar-time perspective.
"""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


def create_clinic_activity_timeline(
    clinic_metrics_df: pd.DataFrame,
    title: str = "Clinic Activity Over Time"
) -> go.Figure:
    """
    Create an interactive timeline showing clinic activity metrics.
    
    Args:
        clinic_metrics_df: DataFrame with monthly clinic metrics
        title: Chart title
    
    Returns:
        Plotly figure
    """
    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        subplot_titles=("Total Visits", "Visit Types", "New vs Returning Patients"),
        vertical_spacing=0.1,
        row_heights=[0.4, 0.3, 0.3]
    )
    
    # Total visits with unique patients
    fig.add_trace(
        go.Scatter(
            x=clinic_metrics_df['month'],
            y=clinic_metrics_df['total_visits'],
            name='Total Visits',
            mode='lines+markers',
            line=dict(color='#1f77b4', width=2),
            marker=dict(size=6)
        ),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Scatter(
            x=clinic_metrics_df['month'],
            y=clinic_metrics_df['unique_patients'],
            name='Unique Patients',
            mode='lines+markers',
            line=dict(color='#ff7f0e', width=2, dash='dash'),
            marker=dict(size=6)
        ),
        row=1, col=1
    )
    
    # Visit types (stacked area)
    fig.add_trace(
        go.Scatter(
            x=clinic_metrics_df['month'],
            y=clinic_metrics_df['injection_visits'],
            name='Injection Visits',
            mode='lines',
            line=dict(width=0),
            fillcolor='rgba(31, 119, 180, 0.7)',
            stackgroup='visits',
            hovertemplate='%{y} injection visits<extra></extra>'
        ),
        row=2, col=1
    )
    
    fig.add_trace(
        go.Scatter(
            x=clinic_metrics_df['month'],
            y=clinic_metrics_df['monitoring_visits'],
            name='Monitoring Visits',
            mode='lines',
            line=dict(width=0),
            fillcolor='rgba(255, 127, 14, 0.7)',
            stackgroup='visits',
            hovertemplate='%{y} monitoring visits<extra></extra>'
        ),
        row=2, col=1
    )
    
    # New vs returning patients
    fig.add_trace(
        go.Bar(
            x=clinic_metrics_df['month'],
            y=clinic_metrics_df['new_patients'],
            name='New Patients',
            marker_color='rgba(44, 160, 44, 0.7)',
            hovertemplate='%{y} new patients<extra></extra>'
        ),
        row=3, col=1
    )
    
    returning_patients = clinic_metrics_df['unique_patients'] - clinic_metrics_df['new_patients']
    fig.add_trace(
        go.Bar(
            x=clinic_metrics_df['month'],
            y=returning_patients,
            name='Returning Patients',
            marker_color='rgba(31, 119, 180, 0.7)',
            hovertemplate='%{y} returning patients<extra></extra>'
        ),
        row=3, col=1
    )
    
    # Update layout
    fig.update_layout(
        title=title,
        height=800,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        hovermode='x unified'
    )
    
    # Update axes
    fig.update_xaxes(title_text="Month", row=3, col=1)
    fig.update_yaxes(title_text="Count", row=1, col=1)
    fig.update_yaxes(title_text="Visits", row=2, col=1)
    fig.update_yaxes(title_text="Patients", row=3, col=1)
    
    return fig


def create_resource_utilization_chart(
    resources_df: pd.DataFrame,
    target_clinicians: Optional[float] = None,
    title: str = "Resource Utilization Analysis"
) -> go.Figure:
    """
    Create a chart showing resource requirements and utilization.
    
    Args:
        resources_df: DataFrame with resource calculations
        target_clinicians: Target number of FTE clinicians (for utilization %)
        title: Chart title
    
    Returns:
        Plotly figure
    """
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        subplot_titles=("FTE Clinicians Required", "Capacity Utilization %"),
        vertical_spacing=0.15
    )
    
    # FTE clinicians required
    fig.add_trace(
        go.Scatter(
            x=resources_df['month'],
            y=resources_df['fte_clinicians_needed'],
            name='FTE Required',
            mode='lines+markers',
            line=dict(color='#2ca02c', width=2),
            fill='tozeroy',
            fillcolor='rgba(44, 160, 44, 0.3)'
        ),
        row=1, col=1
    )
    
    if target_clinicians:
        # Add target line
        fig.add_hline(
            y=target_clinicians,
            line_dash="dash",
            line_color="red",
            annotation_text=f"Target: {target_clinicians} FTE",
            row=1, col=1
        )
        
        # Calculate and show utilization
        utilization = (resources_df['fte_clinicians_needed'] / target_clinicians * 100).clip(upper=100)
        
        fig.add_trace(
            go.Scatter(
                x=resources_df['month'],
                y=utilization,
                name='Utilization %',
                mode='lines+markers',
                line=dict(color='#d62728', width=2),
                fill='tozeroy',
                fillcolor='rgba(214, 39, 40, 0.3)'
            ),
            row=2, col=1
        )
        
        # Add 100% line
        fig.add_hline(
            y=100,
            line_dash="dash",
            line_color="gray",
            annotation_text="100% Capacity",
            row=2, col=1
        )
    
    # Update layout
    fig.update_layout(
        title=title,
        height=600,
        showlegend=True,
        hovermode='x unified'
    )
    
    # Update axes
    fig.update_xaxes(title_text="Month", row=2, col=1)
    fig.update_yaxes(title_text="FTE", row=1, col=1)
    fig.update_yaxes(title_text="%", range=[0, 120], row=2, col=1)
    
    return fig


def create_enrollment_flow_diagram(
    calendar_visits_df: pd.DataFrame,
    title: str = "Patient Enrollment and Flow"
) -> go.Figure:
    """
    Create a Sankey diagram showing patient flow through the clinic.
    
    Args:
        calendar_visits_df: DataFrame with calendar-time visits
        title: Chart title
    
    Returns:
        Plotly figure
    """
    # Calculate quarterly cohorts
    calendar_visits_df['enrollment_quarter'] = pd.to_datetime(
        calendar_visits_df['enrollment_date']
    ).dt.to_period('QE')
    
    # Get patient status at different time points
    patient_status = []
    
    for patient_id in calendar_visits_df['patient_id'].unique():
        patient_data = calendar_visits_df[calendar_visits_df['patient_id'] == patient_id]
        
        status = {
            'patient_id': patient_id,
            'enrollment_quarter': str(patient_data['enrollment_quarter'].iloc[0]),
            'month_6_status': get_patient_status_at_month(patient_data, 6),
            'month_12_status': get_patient_status_at_month(patient_data, 12),
            'month_24_status': get_patient_status_at_month(patient_data, 24),
            'final_status': get_final_patient_status(patient_data)
        }
        patient_status.append(status)
    
    status_df = pd.DataFrame(patient_status)
    
    # Build Sankey diagram data
    labels = []
    sources = []
    targets = []
    values = []
    colors = []
    
    # Define status colors
    status_colors = {
        'Active': 'rgba(44, 160, 44, 0.8)',
        'Discontinued': 'rgba(214, 39, 40, 0.8)',
        'Lost': 'rgba(128, 128, 128, 0.8)'
    }
    
    # Add enrollment cohorts as sources
    for quarter in status_df['enrollment_quarter'].unique():
        labels.append(f"Q{quarter}")
    
    # Add status nodes for each time point
    for timepoint in ['6mo', '12mo', '24mo', 'Final']:
        for status in ['Active', 'Discontinued', 'Lost']:
            labels.append(f"{status} ({timepoint})")
    
    # Create flows
    # ... (implement flow calculation logic)
    
    # Create Sankey diagram
    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=labels,
            color=[status_colors.get(label.split()[0], 'rgba(128, 128, 128, 0.8)') for label in labels]
        ),
        link=dict(
            source=sources,
            target=targets,
            value=values,
            color=colors
        )
    )])
    
    fig.update_layout(
        title=title,
        height=600,
        font_size=12
    )
    
    return fig


def create_cohort_outcomes_comparison(
    cohort_summary_df: pd.DataFrame,
    title: str = "Outcomes by Enrollment Cohort"
) -> go.Figure:
    """
    Create a comparison chart of outcomes across enrollment cohorts.
    
    Args:
        cohort_summary_df: DataFrame with cohort-aggregated outcomes
        title: Chart title
    
    Returns:
        Plotly figure
    """
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            "Mean Vision Change",
            "Discontinuation Rate",
            "Average Total Injections",
            "Months Followed"
        ),
        vertical_spacing=0.15,
        horizontal_spacing=0.12
    )
    
    cohort_labels = [str(c) for c in cohort_summary_df.index]
    
    # Vision change
    fig.add_trace(
        go.Bar(
            x=cohort_labels,
            y=cohort_summary_df['mean_vision_change'],
            name='Vision Change',
            marker_color='#1f77b4',
            text=cohort_summary_df['mean_vision_change'].round(1),
            textposition='auto'
        ),
        row=1, col=1
    )
    
    # Discontinuation rate
    fig.add_trace(
        go.Bar(
            x=cohort_labels,
            y=cohort_summary_df['discontinuation_rate'] * 100,
            name='Discontinuation %',
            marker_color='#d62728',
            text=(cohort_summary_df['discontinuation_rate'] * 100).round(1),
            textposition='auto'
        ),
        row=1, col=2
    )
    
    # Average injections
    fig.add_trace(
        go.Bar(
            x=cohort_labels,
            y=cohort_summary_df['total_injections'],
            name='Avg Injections',
            marker_color='#2ca02c',
            text=cohort_summary_df['total_injections'].round(1),
            textposition='auto'
        ),
        row=2, col=1
    )
    
    # Months followed
    fig.add_trace(
        go.Bar(
            x=cohort_labels,
            y=cohort_summary_df['months_followed'],
            name='Months Followed',
            marker_color='#ff7f0e',
            text=cohort_summary_df['months_followed'].round(1),
            textposition='auto'
        ),
        row=2, col=2
    )
    
    # Update layout
    fig.update_layout(
        title=title,
        height=700,
        showlegend=False
    )
    
    # Update axes
    fig.update_xaxes(title_text="Enrollment Cohort", row=2, col=1)
    fig.update_xaxes(title_text="Enrollment Cohort", row=2, col=2)
    fig.update_yaxes(title_text="Letters", row=1, col=1)
    fig.update_yaxes(title_text="%", row=1, col=2)
    fig.update_yaxes(title_text="Count", row=2, col=1)
    fig.update_yaxes(title_text="Months", row=2, col=2)
    
    return fig


def create_phase_distribution_heatmap(
    calendar_visits_df: pd.DataFrame,
    title: str = "Treatment Phase Distribution Over Time"
) -> go.Figure:
    """
    Create a heatmap showing distribution of patients in different phases over time.
    
    Args:
        calendar_visits_df: DataFrame with calendar-time visits
        title: Chart title
    
    Returns:
        Plotly figure
    """
    # Group by month and phase
    monthly_phase = calendar_visits_df.groupby([
        pd.Grouper(key='calendar_date', freq='ME'),
        'phase'
    ])['patient_id'].nunique().reset_index()
    
    # Pivot for heatmap
    heatmap_data = monthly_phase.pivot(
        index='phase',
        columns='calendar_date',
        values='patient_id'
    ).fillna(0)
    
    # Create heatmap
    fig = go.Figure(data=go.Heatmap(
        z=heatmap_data.values,
        x=[d.strftime('%Y-%m') for d in heatmap_data.columns],
        y=heatmap_data.index,
        colorscale='Viridis',
        text=heatmap_data.values.astype(int),
        texttemplate='%{text}',
        textfont={"size": 10},
        hoverongaps=False
    ))
    
    fig.update_layout(
        title=title,
        xaxis_title="Month",
        yaxis_title="Treatment Phase",
        height=500
    )
    
    return fig


# Helper functions
def get_patient_status_at_month(patient_data: pd.DataFrame, month: int) -> str:
    """Determine patient status at a specific month since enrollment."""
    visits_at_month = patient_data[patient_data['months_since_enrollment'] <= month]
    
    if len(visits_at_month) == 0:
        return 'Not Enrolled'
    
    last_visit = visits_at_month.iloc[-1]
    
    if last_visit.get('discontinued', False):
        return 'Discontinued'
    elif (month - last_visit['months_since_enrollment']) > 3:
        return 'Lost'
    else:
        return 'Active'


def get_final_patient_status(patient_data: pd.DataFrame) -> str:
    """Determine final patient status."""
    last_visit = patient_data.iloc[-1]
    
    if last_visit.get('discontinued', False):
        return 'Discontinued'
    elif patient_data['months_since_enrollment'].max() < 12:
        return 'Active'
    else:
        return 'Completed'