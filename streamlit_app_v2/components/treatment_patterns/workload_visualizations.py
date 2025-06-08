"""Clinical Workload Visualizations - Multiple approaches to show workload attribution.

This module provides three different visualization approaches for clinical workload data:
1. Dual Bar Chart - Patient distribution vs visit volume
2. Impact Pyramid - Visual flow representation 
3. Bubble Chart - Detailed relationship analysis

All visualizations share the same data analysis core from workload_analyzer.py
"""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple

from utils.style_constants import StyleConstants


def create_dual_bar_chart(workload_data: Dict[str, Any], tufte_mode: bool = True) -> go.Figure:
    """
    Create dual bar chart showing patient distribution vs visit volume.
    
    This visualization clearly shows the contrast between how many patients
    are in each category vs how much clinical work they generate.
    
    Args:
        workload_data: Output from calculate_clinical_workload_attribution
        tufte_mode: Whether to use clean Tufte styling
        
    Returns:
        Plotly figure with dual bar chart
    """
    if not workload_data['summary_stats']:
        return _create_empty_chart("No workload data available")
    
    # Prepare data for visualization
    categories = []
    patient_percentages = []
    visit_percentages = []
    colors = []
    
    # Sort categories by workload efficiency (highest first)
    sorted_stats = sorted(
        workload_data['summary_stats'].items(),
        key=lambda x: x[1]['workload_efficiency'],
        reverse=True
    )
    
    category_definitions = workload_data['category_definitions']
    
    for category, stats in sorted_stats:
        categories.append(category)
        patient_percentages.append(stats['patient_percentage'])
        visit_percentages.append(stats['visit_percentage'])
        
        # Get color from category definitions
        color = category_definitions.get(category, {}).get('color', '#cccccc')
        colors.append(color)
    
    # Create subplot with secondary y-axis
    fig = make_subplots(
        rows=1, cols=1,
        specs=[[{"secondary_y": False}]],
        subplot_titles=["Clinical Workload Attribution"]
    )
    
    # Add patient percentage bars
    fig.add_trace(
        go.Bar(
            name="% of Patients",
            x=categories,
            y=patient_percentages,
            marker_color=[f"rgba{_hex_to_rgba(c, 0.6)}" for c in colors],
            marker_line=dict(width=0 if tufte_mode else 1),
            text=[f"{p:.1f}%" for p in patient_percentages],
            textposition="outside",
            textfont=dict(size=10),
            hovertemplate="<b>%{x}</b><br>" +
                         "Patient Percentage: %{y:.1f}%<br>" +
                         "<extra></extra>",
            offsetgroup=1
        )
    )
    
    # Add visit percentage bars (offset position)
    fig.add_trace(
        go.Bar(
            name="% of Visits",
            x=categories,
            y=visit_percentages,
            marker_color=colors,
            marker_line=dict(width=0 if tufte_mode else 1),
            text=[f"{v:.1f}%" for v in visit_percentages],
            textposition="outside",
            textfont=dict(size=10),
            hovertemplate="<b>%{x}</b><br>" +
                         "Visit Percentage: %{y:.1f}%<br>" +
                         "<extra></extra>",
            offsetgroup=2
        )
    )
    
    # Update layout for clean appearance
    if tufte_mode:
        fig.update_layout(
            title="Clinical Workload Attribution: Patient Distribution vs Visit Volume",
            title_font_size=16,
            title_x=0.02,
            xaxis_title="Treatment Intensity Category",
            yaxis_title="Percentage",
            barmode='group',  # This ensures bars are grouped side by side
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            plot_bgcolor='white',
            paper_bgcolor='white',
            font=dict(family='Arial', size=12),
            margin=dict(l=60, r=40, t=80, b=60),
            height=500
        )
        
        # Clean axes
        fig.update_xaxes(
            showline=True,
            linewidth=1,
            linecolor='black',
            showgrid=False,
            tickangle=45
        )
        
        fig.update_yaxes(
            showline=True,
            linewidth=1,
            linecolor='black',
            showgrid=True,
            gridwidth=0.5,
            gridcolor='lightgray',
            range=[0, max(max(patient_percentages), max(visit_percentages)) * 1.1]
        )
    else:
        # Presentation mode with more visual elements
        fig.update_layout(
            title="Clinical Workload Attribution Analysis",
            title_font_size=18,
            barmode='group',  # This ensures bars are grouped side by side
            showlegend=True,
            plot_bgcolor='white',
            font=dict(family='Arial', size=12),
            height=500
        )
    
    return fig


def create_impact_pyramid(workload_data: Dict[str, Any], tufte_mode: bool = True) -> go.Figure:
    """
    Create impact pyramid showing visual flow from patients to visits.
    
    This uses a funnel-like visualization to show how patient categories
    contribute disproportionately to clinical workload.
    
    Args:
        workload_data: Output from calculate_clinical_workload_attribution
        tufte_mode: Whether to use clean Tufte styling
        
    Returns:
        Plotly figure with impact pyramid
    """
    if not workload_data['summary_stats']:
        return _create_empty_chart("No workload data available")
    
    
    # Prepare data - sort by workload efficiency
    sorted_stats = sorted(
        workload_data['summary_stats'].items(),
        key=lambda x: x[1]['workload_efficiency'],
        reverse=True
    )
    
    category_definitions = workload_data['category_definitions']
    
    # Create two side-by-side funnels
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=["Patient Distribution", "Visit Generation"],
        specs=[[{"type": "funnel"}, {"type": "funnel"}]],
        horizontal_spacing=0.1
    )
    
    # Patient funnel (left side)
    patient_values = []
    visit_values = []
    labels = []
    colors = []
    
    for category, stats in sorted_stats:
        labels.append(f"{category}<br>({stats['patient_count']} patients)")
        patient_values.append(stats['patient_percentage'])
        visit_values.append(stats['visit_percentage'])
        
        color = category_definitions.get(category, {}).get('color', '#cccccc')
        colors.append(color)
    
    # Add patient distribution funnel
    fig.add_trace(
        go.Funnel(
            y=labels,
            x=patient_values,
            textinfo="value+percent initial",
            textposition="inside",
            textfont=dict(size=10),
            marker=dict(
                color=colors,
                line=dict(width=0 if tufte_mode else 2)
            ),
            connector=dict(visible=not tufte_mode),
            hovertemplate="<b>%{y}</b><br>" +
                         "Patient Percentage: %{x:.1f}%<br>" +
                         "<extra></extra>"
        ),
        row=1, col=1
    )
    
    # Add visit generation funnel
    fig.add_trace(
        go.Funnel(
            y=labels,
            x=visit_values,
            textinfo="value+percent initial",
            textposition="inside", 
            textfont=dict(size=10),
            marker=dict(
                color=colors,
                line=dict(width=0 if tufte_mode else 2)
            ),
            connector=dict(visible=not tufte_mode),
            hovertemplate="<b>%{y}</b><br>" +
                         "Visit Percentage: %{x:.1f}%<br>" +
                         "<extra></extra>"
        ),
        row=1, col=2
    )
    
    # Update layout
    if tufte_mode:
        fig.update_layout(
            title="Clinical Impact Pyramid: From Patients to Workload",
            title_font_size=16,
            title_x=0.02,
            showlegend=False,
            font=dict(family='Arial', size=12),
            plot_bgcolor='white',
            paper_bgcolor='white',
            margin=dict(l=40, r=40, t=80, b=40),
            height=600
        )
    else:
        fig.update_layout(
            title="Clinical Impact Analysis",
            title_font_size=18,
            showlegend=False,
            font=dict(family='Arial', size=12),
            height=600
        )
    
    return fig


def create_bubble_chart(workload_data: Dict[str, Any], tufte_mode: bool = True) -> go.Figure:
    """
    Create bubble chart showing detailed relationship analysis.
    
    This shows each category as a bubble where:
    - X-axis: Patient percentage
    - Y-axis: Visit percentage  
    - Bubble size: Workload efficiency
    - Color: Category type
    
    Args:
        workload_data: Output from calculate_clinical_workload_attribution
        tufte_mode: Whether to use clean Tufte styling
        
    Returns:
        Plotly figure with bubble chart
    """
    if not workload_data['summary_stats']:
        return _create_empty_chart("No workload data available")
    
    # Prepare data
    patient_pcts = []
    visit_pcts = []
    efficiencies = []
    categories = []
    colors = []
    hover_texts = []
    
    category_definitions = workload_data['category_definitions']
    
    for category, stats in workload_data['summary_stats'].items():
        patient_pcts.append(stats['patient_percentage'])
        visit_pcts.append(stats['visit_percentage'])
        efficiencies.append(stats['workload_efficiency'])
        categories.append(category)
        
        color = category_definitions.get(category, {}).get('color', '#cccccc')
        colors.append(color)
        
        # Create detailed hover text
        hover_text = (
            f"<b>{category}</b><br>"
            f"Patients: {stats['patient_count']} ({stats['patient_percentage']:.1f}%)<br>"
            f"Visits: {stats['visit_count']} ({stats['visit_percentage']:.1f}%)<br>"
            f"Visits/Patient: {stats['visits_per_patient']:.1f}<br>"
            f"Workload Efficiency: {stats['workload_efficiency']:.1f}x"
        )
        hover_texts.append(hover_text)
    
    # Create scatter plot
    fig = go.Figure()
    
    # Add diagonal reference line (equal patient and visit percentages)
    max_val = max(max(patient_pcts), max(visit_pcts))
    fig.add_trace(
        go.Scatter(
            x=[0, max_val],
            y=[0, max_val],
            mode='lines',
            line=dict(
                dash='dash',
                color='gray',
                width=1
            ),
            name='Equal Distribution',
            hoverinfo='skip',
            showlegend=not tufte_mode
        )
    )
    
    # Add bubbles for each category
    fig.add_trace(
        go.Scatter(
            x=patient_pcts,
            y=visit_pcts,
            mode='markers+text',
            marker=dict(
                size=[e * 20 + 10 for e in efficiencies],  # Scale bubble size
                color=colors,
                line=dict(width=1 if not tufte_mode else 0, color='white'),
                opacity=0.8
            ),
            text=categories,
            textposition="middle center",
            textfont=dict(size=10, color='white'),
            hovertemplate="%{customdata}<extra></extra>",
            customdata=hover_texts,
            name='Treatment Categories'
        )
    )
    
    # Update layout
    if tufte_mode:
        fig.update_layout(
            title="Clinical Workload Efficiency Analysis",
            title_font_size=16,
            title_x=0.02,
            xaxis_title="Patient Percentage (%)",
            yaxis_title="Visit Percentage (%)",
            showlegend=False,
            plot_bgcolor='white',
            paper_bgcolor='white',
            font=dict(family='Arial', size=12),
            margin=dict(l=60, r=40, t=80, b=60),
            height=500
        )
        
        # Clean axes
        fig.update_xaxes(
            showline=True,
            linewidth=1,
            linecolor='black',
            showgrid=True,
            gridwidth=0.5,
            gridcolor='lightgray'
        )
        
        fig.update_yaxes(
            showline=True,
            linewidth=1,
            linecolor='black',
            showgrid=True,
            gridwidth=0.5,
            gridcolor='lightgray'
        )
    else:
        fig.update_layout(
            title="Clinical Workload Relationship Analysis",
            title_font_size=18,
            xaxis_title="Patient Percentage (%)",
            yaxis_title="Visit Percentage (%)",
            font=dict(family='Arial', size=12),
            height=500
        )
    
    # Add annotation explaining the chart
    fig.add_annotation(
        x=0.02,
        y=0.98,
        xref="paper",
        yref="paper",
        text="Bubble size = Workload efficiency<br>Above diagonal = Higher visit generation",
        showarrow=False,
        font=dict(size=10),
        bgcolor="rgba(255,255,255,0.8)",
        bordercolor="gray",
        borderwidth=1
    )
    
    return fig


def _create_empty_chart(message: str) -> go.Figure:
    """Create an empty chart with a message."""
    fig = go.Figure()
    
    fig.add_annotation(
        x=0.5,
        y=0.5,
        xref="paper",
        yref="paper",
        text=message,
        showarrow=False,
        font=dict(size=16, color="gray"),
        align="center"
    )
    
    fig.update_layout(
        showlegend=False,
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        plot_bgcolor='white',
        height=400
    )
    
    return fig


def _hex_to_rgba(hex_color: str, alpha: float) -> str:
    """Convert hex color to RGBA tuple string."""
    if hex_color.startswith('#'):
        hex_color = hex_color[1:]
    
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    
    return f"({r},{g},{b},{alpha})"


def get_workload_insight_summary(workload_data: Dict[str, Any]) -> str:
    """
    Generate a formatted summary of key workload insights.
    
    Args:
        workload_data: Output from calculate_clinical_workload_attribution
        
    Returns:
        Formatted string with key insights
    """
    if not workload_data['summary_stats']:
        return "No workload data available for analysis."
    
    # Find top contributors
    sorted_stats = sorted(
        workload_data['summary_stats'].items(),
        key=lambda x: x[1]['workload_efficiency'],
        reverse=True
    )
    
    insights = []
    
    # Overall summary
    total_patients = workload_data['total_patients']
    total_visits = workload_data['total_visits']
    insights.append(f"**Total Analysis:** {total_patients:,} patients generating {total_visits:,} visits")
    
    # Top workload contributor
    if sorted_stats:
        top_category, top_stats = sorted_stats[0]
        insights.append(
            f"**Highest Impact:** {top_stats['patient_percentage']:.1f}% of patients "
            f"({top_category.lower()}) generate {top_stats['visit_percentage']:.1f}% of visits "
            f"({top_stats['workload_efficiency']:.1f}x efficiency)"
        )
    
    # Most balanced category (closest to 1.0x efficiency)
    balanced_category = min(
        sorted_stats,
        key=lambda x: abs(x[1]['workload_efficiency'] - 1.0)
    )
    if balanced_category:
        cat_name, cat_stats = balanced_category
        insights.append(
            f"**Most Balanced:** {cat_name.lower()} patients have {cat_stats['workload_efficiency']:.1f}x efficiency "
            f"({cat_stats['patient_percentage']:.1f}% patients → {cat_stats['visit_percentage']:.1f}% visits)"
        )
    
    return "\n\n".join(insights)