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

from ape.utils.style_constants import StyleConstants

# Tufte-style constants for clean visualization
TUFTE_FONT_SIZES = {
    'title': 16,          # Reduced from typical titles
    'subtitle': 14,
    'label': 14,          # Minimum for readability
    'tick': 12,           # Minimum for readability
    'annotation': 11,
}

TUFTE_LINE_WEIGHTS = {
    'data': 2.5,          # Thick enough for clarity
    'axis': 1.0,
    'grid': 0.5,
    'annotation': 1.0,
}

TUFTE_COLORS = {
    'neutral': '#264653',      # Dark blue-gray
    'grid': '#E0E0E0',         # Light gray
    'annotation': '#666666',   # Medium gray
}


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
        key=lambda x: x[1]['workload_intensity'],
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
            text=[f"{p:.1f}%" if p < 1 else f"{p:.0f}%" for p in patient_percentages],  # 2 sig figs
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
            text=[f"{v:.1f}%" if v < 1 else f"{v:.0f}%" for v in visit_percentages],  # 2 sig figs
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
            title="",  # Remove title for cleaner Tufte style
            xaxis_title="Treatment Intensity Category",
            yaxis_title="Percentage",
            barmode='group',  # This ensures bars are grouped side by side
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="top",
                y=0.99,
                xanchor="right",
                x=0.99,
                font=dict(size=TUFTE_FONT_SIZES['tick']),
                bgcolor="rgba(255,255,255,0.8)",
                bordercolor=TUFTE_COLORS['grid'],
                borderwidth=1
            ),
            plot_bgcolor='white',
            paper_bgcolor='white',
            font=dict(family='Arial', size=TUFTE_FONT_SIZES['tick']),
            margin=dict(l=60, r=40, t=40, b=80),  # Reduced top margin without title
            height=500
        )
        
        # Clean axes following Tufte principles
        fig.update_xaxes(
            showline=True,
            linewidth=TUFTE_LINE_WEIGHTS['axis'],
            linecolor=TUFTE_COLORS['neutral'],
            showgrid=False,  # No vertical grid
            tickangle=0,  # Horizontal labels
            tickfont=dict(size=TUFTE_FONT_SIZES['tick']),
            title_font=dict(size=TUFTE_FONT_SIZES['label']),
            ticks='outside',
            ticklen=5,
            tickwidth=TUFTE_LINE_WEIGHTS['axis'],
            tickcolor=TUFTE_COLORS['neutral']
        )
        
        fig.update_yaxes(
            showline=True,
            linewidth=TUFTE_LINE_WEIGHTS['axis'],
            linecolor=TUFTE_COLORS['neutral'],
            showgrid=False,  # No grid lines since we have data labels
            zeroline=False,  # Remove zero line
            tickfont=dict(size=TUFTE_FONT_SIZES['tick']),
            title_font=dict(size=TUFTE_FONT_SIZES['label']),
            ticks='outside',
            ticklen=5,
            tickwidth=TUFTE_LINE_WEIGHTS['axis'],
            tickcolor=TUFTE_COLORS['neutral'],
            range=[0, max(max(patient_percentages), max(visit_percentages)) * 1.15]  # More space for labels
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
        key=lambda x: x[1]['workload_intensity'],
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
            title="",  # Remove title for cleaner Tufte style
            showlegend=False,
            font=dict(family='Arial', size=TUFTE_FONT_SIZES['tick']),
            plot_bgcolor='white',
            paper_bgcolor='white',
            margin=dict(l=40, r=40, t=60, b=40),  # Reduced top margin
            height=600
        )
        
        # Update subplot titles with Tufte styling
        for annotation in fig['layout']['annotations']:
            if 'text' in annotation and annotation['text'] in ["Patient Distribution", "Visit Generation"]:
                annotation['font']['size'] = TUFTE_FONT_SIZES['subtitle']
                annotation['font']['color'] = TUFTE_COLORS['neutral']
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
        efficiencies.append(stats['workload_intensity'])
        categories.append(category)
        
        color = category_definitions.get(category, {}).get('color', '#cccccc')
        colors.append(color)
        
        # Create detailed hover text
        hover_text = (
            f"<b>{category}</b><br>"
            f"Patients: {stats['patient_count']} ({stats['patient_percentage']:.1f}%)<br>"
            f"Visits: {stats['visit_count']} ({stats['visit_percentage']:.1f}%)<br>"
            f"Visits/Patient: {stats['visits_per_patient']:.1f}<br>"
            f"Workload Efficiency: {stats['workload_intensity']:.1f}x"
        )
        hover_texts.append(hover_text)
    
    # Create scatter plot
    fig = go.Figure()
    
    # Add diagonal reference line (equal patient and visit percentages) - more visible
    max_val = max(max(patient_pcts), max(visit_pcts))
    fig.add_trace(
        go.Scatter(
            x=[0, max_val],
            y=[0, max_val],
            mode='lines',
            line=dict(
                dash='solid',  # Solid line for better visibility
                color=TUFTE_COLORS['neutral'],  # Darker color
                width=TUFTE_LINE_WEIGHTS['data']  # Thicker line
            ),
            name='Equal Distribution',
            hoverinfo='skip',
            showlegend=False
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
            textposition="top center",  # Labels above bubbles
            textfont=dict(size=TUFTE_FONT_SIZES['tick'], color=TUFTE_COLORS['neutral']),  # Black text
            hovertemplate="%{customdata}<extra></extra>",
            customdata=hover_texts,
            name='Treatment Categories'
        )
    )
    
    # Update layout
    if tufte_mode:
        fig.update_layout(
            title="",  # Remove title for cleaner Tufte style
            xaxis_title="Patient Percentage (%)",
            yaxis_title="Visit Percentage (%)",
            showlegend=False,
            plot_bgcolor='white',
            paper_bgcolor='white',
            font=dict(family='Arial', size=TUFTE_FONT_SIZES['tick']),
            margin=dict(l=60, r=40, t=40, b=60),  # Reduced top margin
            height=500,
            width=600  # Fixed width for half-page display
        )
        
        # Clean axes following Tufte principles
        fig.update_xaxes(
            showline=True,
            linewidth=TUFTE_LINE_WEIGHTS['axis'],
            linecolor=TUFTE_COLORS['neutral'],
            showgrid=True,
            gridwidth=TUFTE_LINE_WEIGHTS['grid'] * 0.3,  # Much lighter grid
            gridcolor='rgba(224, 224, 224, 0.3)',  # Very subtle
            zeroline=False,
            tickfont=dict(size=TUFTE_FONT_SIZES['tick']),
            title_font=dict(size=TUFTE_FONT_SIZES['label']),
            ticks='outside',
            ticklen=5,
            tickwidth=TUFTE_LINE_WEIGHTS['axis'],
            tickcolor=TUFTE_COLORS['neutral']
        )
        
        fig.update_yaxes(
            showline=True,
            linewidth=TUFTE_LINE_WEIGHTS['axis'],
            linecolor=TUFTE_COLORS['neutral'],
            showgrid=True,
            gridwidth=TUFTE_LINE_WEIGHTS['grid'] * 0.3,  # Much lighter grid
            gridcolor='rgba(224, 224, 224, 0.3)',  # Very subtle
            zeroline=False,
            tickfont=dict(size=TUFTE_FONT_SIZES['tick']),
            title_font=dict(size=TUFTE_FONT_SIZES['label']),
            ticks='outside',
            ticklen=5,
            tickwidth=TUFTE_LINE_WEIGHTS['axis'],
            tickcolor=TUFTE_COLORS['neutral']
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
    
    # Add annotation explaining the chart - Tufte style
    fig.add_annotation(
        x=0.02,
        y=0.98,
        xref="paper",
        yref="paper",
        text="Bubble size indicates workload efficiency<br>Points above diagonal show higher visit generation",
        showarrow=False,
        font=dict(size=TUFTE_FONT_SIZES['annotation'], color=TUFTE_COLORS['annotation']),
        bgcolor="rgba(255,255,255,0.9)",
        bordercolor=TUFTE_COLORS['grid'],
        borderwidth=TUFTE_LINE_WEIGHTS['annotation'],
        borderpad=4
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
        key=lambda x: x[1]['workload_intensity'],
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
            f"({top_stats['workload_intensity']:.1f}x efficiency)"
        )
    
    # Most balanced category (closest to 1.0x efficiency)
    balanced_category = min(
        sorted_stats,
        key=lambda x: abs(x[1]['workload_intensity'] - 1.0)
    )
    if balanced_category:
        cat_name, cat_stats = balanced_category
        insights.append(
            f"**Most Balanced:** {cat_name.lower()} patients have {cat_stats['workload_intensity']:.1f}x efficiency "
            f"({cat_stats['patient_percentage']:.1f}% patients → {cat_stats['visit_percentage']:.1f}% visits)"
        )
    
    return "\n\n".join(insights)