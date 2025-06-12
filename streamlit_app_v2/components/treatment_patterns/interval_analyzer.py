"""Interval and gap analysis functions for treatment patterns."""

import numpy as np
import pandas as pd
import plotly.graph_objects as go

# Tufte-style constants
TUFTE_FONT_SIZES = {
    'title': 16,
    'label': 14,
    'tick': 12,
    'annotation': 11,
}

TUFTE_LINE_WEIGHTS = {
    'axis': 1.0,
    'grid': 0.5,
    'annotation': 1.0,
}

TUFTE_COLORS = {
    'neutral': '#264653',
    'grid': '#E0E0E0',
}


def create_interval_distribution_chart(transitions_df):
    """Create distribution of treatment intervals."""
    # Get intervals from transitions
    interval_data = transitions_df[transitions_df['interval_days'] > 0]['interval_days']
    
    # Create histogram
    fig = go.Figure()
    
    # Define bins for common intervals
    bins = [0, 35, 63, 84, 112, 180, 365, 1000]
    labels = ['Monthly', '6-8 weeks', '9-11 weeks', '12-16 weeks', '3-6 months', '6-12 months', '12+ months']
    
    hist, bin_edges = np.histogram(interval_data, bins=bins)
    
    # Create bar chart
    fig.add_trace(go.Bar(
        x=labels,
        y=hist,
        marker_color=['#4a90e2', '#7fba00', '#5c8a00', '#2d5016', '#ffd700', '#ff9500', '#ff6347'],
        text=hist,
        textposition='auto',
    ))
    
    fig.update_layout(
        title="",  # Remove title for Tufte style
        xaxis=dict(
            title="Interval Category",
            titlefont=dict(size=TUFTE_FONT_SIZES['label']),
            tickfont=dict(size=TUFTE_FONT_SIZES['tick']),
            showline=True,
            linewidth=TUFTE_LINE_WEIGHTS['axis'],
            linecolor=TUFTE_COLORS['neutral'],
            showgrid=False,
            ticks='outside',
            ticklen=5,
            tickwidth=TUFTE_LINE_WEIGHTS['axis'],
            tickcolor=TUFTE_COLORS['neutral']
        ),
        yaxis=dict(
            title="Number of Visits",
            titlefont=dict(size=TUFTE_FONT_SIZES['label']),
            tickfont=dict(size=TUFTE_FONT_SIZES['tick']),
            showline=True,
            linewidth=TUFTE_LINE_WEIGHTS['axis'],
            linecolor=TUFTE_COLORS['neutral'],
            showgrid=True,
            gridwidth=TUFTE_LINE_WEIGHTS['grid'],
            gridcolor=TUFTE_COLORS['grid'],
            zeroline=False,
            ticks='outside',
            ticklen=5,
            tickwidth=TUFTE_LINE_WEIGHTS['axis'],
            tickcolor=TUFTE_COLORS['neutral']
        ),
        height=400,
        showlegend=False,
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(size=TUFTE_FONT_SIZES['tick']),
        margin=dict(t=40, b=60, l=60, r=40)
    )
    
    return fig


def create_gap_analysis_chart_tufte(visits_df):
    """Analyze treatment gaps by patient using Tufte-style visualization."""
    # Get all unique patients
    all_patients = visits_df['patient_id'].unique()
    
    # Filter to only rows with valid intervals (exclude first visits)
    valid_intervals = visits_df[visits_df['interval_days'].notna()]
    
    # Calculate max gap per patient (only for those with intervals)
    if len(valid_intervals) > 0:
        patient_gaps = valid_intervals.groupby('patient_id')['interval_days'].agg(['max', 'mean', 'count']).reset_index()
        patient_gaps.columns = ['patient_id', 'max_gap_days', 'mean_interval_days', 'interval_count']
        
        # Add patients with only one visit (no intervals) as having no gaps
        patients_with_intervals = set(patient_gaps['patient_id'])
        patients_without_intervals = set(all_patients) - patients_with_intervals
        
        if len(patients_without_intervals) > 0:
            no_interval_df = pd.DataFrame({
                'patient_id': list(patients_without_intervals),
                'max_gap_days': 0,  # No intervals means no gaps
                'mean_interval_days': 0,
                'interval_count': 0
            })
            patient_gaps = pd.concat([patient_gaps, no_interval_df], ignore_index=True)
    else:
        # If no intervals at all, all patients have single visits
        patient_gaps = pd.DataFrame({
            'patient_id': all_patients,
            'max_gap_days': 0,
            'mean_interval_days': 0,
            'interval_count': 0
        })
    
    # Categorize patients by their maximum gap - using more granular thresholds
    # that match the actual data distribution
    gap_categories = pd.cut(
        patient_gaps['max_gap_days'],
        bins=[0, 42, 63, 84, 112, float('inf')],
        labels=[
            'Very frequent (≤6 weeks)', 
            'Frequent (6-9 weeks)', 
            'Regular (9-12 weeks)', 
            'Extended (12-16 weeks)',
            'Gaps (>16 weeks)'
        ],
        include_lowest=True  # Include 0 in the first bin
    )
    
    gap_summary = gap_categories.value_counts()
    
    # Sort categories for horizontal bar chart
    gap_summary = gap_summary.sort_values(ascending=True)
    
    # Create a clean horizontal bar chart (Tufte-style)
    fig = go.Figure()
    
    # Add bars
    fig.add_trace(go.Bar(
        y=gap_summary.index,
        x=gap_summary.values,
        orientation='h',
        text=[f'{val:,} ({val/len(patient_gaps)*100:.1f}%)' for val in gap_summary.values],
        textposition='outside',
        marker_color=['#4a90e2' if '≤6 weeks' in str(idx) else
                     '#7fba00' if '6-9 weeks' in str(idx) else
                     '#5c8a00' if '9-12 weeks' in str(idx) else
                     '#ffd700' if '12-16 weeks' in str(idx) else
                     '#ff6347' for idx in gap_summary.index],
        showlegend=False
    ))
    
    # Tufte-style clean layout
    fig.update_layout(
        title="",  # Empty title to avoid "undefined" display
        xaxis=dict(
            title="Number of Patients",
            titlefont=dict(size=TUFTE_FONT_SIZES['label']),
            tickfont=dict(size=TUFTE_FONT_SIZES['tick']),
            showgrid=False,
            zeroline=False,
            showline=True,  # Show bottom line
            linewidth=TUFTE_LINE_WEIGHTS['axis'],
            linecolor=TUFTE_COLORS['neutral'],
            ticks='outside',
            ticklen=5,
            tickwidth=TUFTE_LINE_WEIGHTS['axis'],
            tickcolor=TUFTE_COLORS['neutral']
        ),
        yaxis=dict(
            title=None,
            tickfont=dict(size=TUFTE_FONT_SIZES['tick']),
            showgrid=False,
            zeroline=False,
            showline=False,
            ticks='',
        ),
        height=300,
        margin=dict(l=150, r=100, t=20, b=40),
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(size=TUFTE_FONT_SIZES['tick'])
    )
    
    # Add subtle reference lines at 25%, 50%, 75% - Tufte style
    for pct in [0.25, 0.5, 0.75]:
        fig.add_vline(
            x=len(patient_gaps) * pct,
            line_dash="dot",
            line_color=TUFTE_COLORS['grid'],
            line_width=TUFTE_LINE_WEIGHTS['annotation'],
            opacity=0.3  # More subtle
        )
    
    return fig


def calculate_interval_statistics(visits_df):
    """Calculate summary statistics for treatment intervals."""
    # Filter to only visits with intervals
    interval_data = visits_df[visits_df['interval_days'].notna()]['interval_days']
    
    if len(interval_data) == 0:
        return {
            'median': 0,
            'mean': 0,
            'std': 0,
            'min': 0,
            'max': 0,
            'extended_pct': 0,
            'gap_pct': 0
        }
    
    return {
        'median': interval_data.median(),
        'mean': interval_data.mean(),
        'std': interval_data.std(),
        'min': interval_data.min(),
        'max': interval_data.max(),
        'extended_pct': (interval_data > 84).sum() / len(interval_data) * 100,
        'gap_pct': (interval_data > 180).sum() / len(interval_data) * 100
    }