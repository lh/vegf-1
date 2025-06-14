"""Clinical Workload Visualizations using Altair - Faster alternative to Plotly.

This module provides Altair-based visualizations that are 2-3x faster than Plotly
while maintaining visual quality and interactivity.
"""

import altair as alt
import pandas as pd
from typing import Dict, Any
import streamlit as st

# Import color system
from ape.utils.visualization_modes import get_mode_colors

# Enable Altair data transformer for larger datasets
alt.data_transformers.enable('default', max_rows=None)

# Tufte-style constants
TUFTE_FONT_SIZES = {
    'title': 16,
    'label': 14,
    'tick': 12,
}

TUFTE_COLORS = {
    'neutral': '#264653',
    'grid': '#E0E0E0',
}


def create_dual_bar_chart_altair(workload_data: Dict[str, Any], tufte_mode: bool = True) -> alt.Chart:
    """
    Create dual bar chart using Altair - simplified version.
    
    Args:
        workload_data: Output from calculate_clinical_workload_attribution
        tufte_mode: Whether to use clean Tufte styling (always True)
        
    Returns:
        Altair chart object
    """
    if not workload_data['summary_stats']:
        return alt.Chart(pd.DataFrame()).mark_text(
            text='No workload data available', size=16, color='gray'
        ).properties(width=500, height=350)
    
    # Prepare data
    records = []
    sorted_stats = sorted(workload_data['summary_stats'].items(), 
                         key=lambda x: x[1]['workload_intensity'], 
                         reverse=True)
    
    for idx, (category, stats) in enumerate(sorted_stats):
        color = workload_data['category_definitions'].get(category, {}).get('color', '#999999')
        # Add both patient and visit percentages
        for metric, value in [('% of Patients', stats['patient_percentage']), 
                             ('% of Visits', stats['visit_percentage'])]:
            records.append({
                'Category': category,
                'Metric': metric,
                'Value': value,
                'Color': color,
                'SortOrder': idx,
                'Label': f"{value:.0f}%" if value >= 1 else f"{value:.1f}%"
            })
    
    df = pd.DataFrame(records)
    
    # Get unique categories and their colors for the scale
    unique_cats = df[['Category', 'Color', 'SortOrder']].drop_duplicates().sort_values('SortOrder')
    
    # Create the chart
    chart = alt.Chart(df).mark_bar().encode(
        x=alt.X('Category:N', 
                sort=alt.SortField('SortOrder'),
                title='Treatment Intensity Category',
                axis=alt.Axis(labelAngle=0)),
        y=alt.Y('Value:Q', 
                title='Percentage',
                scale=alt.Scale(domain=[0, max(60, df['Value'].max() * 1.1)])),
        xOffset='Metric:N',
        color=alt.Color('Category:N',
                       scale=alt.Scale(domain=unique_cats['Category'].tolist(),
                                      range=unique_cats['Color'].tolist()),
                       legend=None),
        opacity=alt.condition(
            alt.datum.Metric == '% of Patients',
            alt.value(0.5),
            alt.value(1.0)
        ),
        tooltip=['Category', 'Metric', alt.Tooltip('Value:Q', format='.1f')]
    ).properties(
        width=500,
        height=350,
        title='Clinical Workload Attribution'
    )
    
    # Add value labels on bars
    text = chart.mark_text(
        dy=-5,
        fontSize=10
    ).encode(
        text='Label:N'
    )
    
    # Add a simple legend
    colors = get_mode_colors()
    legend_df = pd.DataFrame({
        'Metric': ['% of Patients', '% of Visits'],
        'y': [0, 1]
    })
    
    legend = alt.Chart(legend_df).mark_rect(
        width=15,
        height=15
    ).encode(
        y=alt.Y('y:O', axis=None),
        color=alt.value(colors.get('neutral', '#264653')),
        opacity=alt.condition(
            alt.datum.Metric == '% of Patients',
            alt.value(0.5),
            alt.value(1.0)
        )
    ).properties(width=20)
    
    legend_labels = alt.Chart(legend_df).mark_text(
        align='left',
        dx=20,
        fontSize=12
    ).encode(
        y=alt.Y('y:O', axis=None),
        text='Metric:N'
    ).properties(width=100)
    
    # Combine legend components with independent scales
    legend_combined = alt.hconcat(legend, legend_labels).resolve_scale(
        y='independent'
    )
    
    # Combine main chart with legend
    final_chart = alt.hconcat(
        (chart + text),
        legend_combined
    ).configure_axis(
        grid=False,
        labelFontSize=12,
        titleFontSize=14
    ).configure_view(
        strokeWidth=0
    ).configure_title(
        fontSize=16
    )
    
    return final_chart


def create_bubble_chart_altair(workload_data: Dict[str, Any], tufte_mode: bool = True) -> alt.Chart:
    """
    Create bubble chart using Altair - simpler and faster than Plotly.
    
    Shows relationship between patient percentage (x) and visit percentage (y),
    with bubble size representing workload intensity.
    """
    if not workload_data['summary_stats']:
        return alt.Chart(pd.DataFrame()).mark_text(
            text='No workload data available', size=16, color='gray'
        ).properties(width=500, height=500)
    
    # Prepare data
    records = []
    for category, stats in workload_data['summary_stats'].items():
        records.append({
            'Category': category,
            'Patient %': stats['patient_percentage'],
            'Visit %': stats['visit_percentage'],
            'Workload Intensity': stats['workload_intensity'],
            'Color': workload_data['category_definitions'].get(category, {}).get('color', '#999999'),
            'Patient Count': stats['patient_count'],
            'Visit Count': stats['visit_count']
        })
    
    df = pd.DataFrame(records)
    
    # Create color scale
    color_scale = alt.Scale(
        domain=df['Category'].tolist(),
        range=df['Color'].tolist()
    )
    
    # Create the bubble chart with better sizing
    # Scale bubble area proportional to workload intensity squared for better visual impact
    df['Bubble Size'] = df['Workload Intensity'] ** 2 * 1000
    
    bubbles = alt.Chart(df).mark_circle(opacity=0.8).encode(
        x=alt.X('Patient %:Q', 
                scale=alt.Scale(domain=[0, max(100, df['Patient %'].max() * 1.1)]),
                title='% of Patients'),
        y=alt.Y('Visit %:Q',
                scale=alt.Scale(domain=[0, max(100, df['Visit %'].max() * 1.1)]),
                title='% of Visits'),
        size=alt.Size('Bubble Size:Q',
                     scale=alt.Scale(range=[200, 5000]),
                     legend=None),  # We'll explain size in the text
        color=alt.Color('Category:N', scale=color_scale, legend=None),
        tooltip=[
            alt.Tooltip('Category:N', title='Category'),
            alt.Tooltip('Patient Count:Q', title='Patients'),
            alt.Tooltip('Patient %:Q', title='% of Patients', format='.1f'),
            alt.Tooltip('Visit Count:Q', title='Visits'),
            alt.Tooltip('Visit %:Q', title='% of Visits', format='.1f'),
            alt.Tooltip('Workload Intensity:Q', title='Efficiency', format='.1fx')
        ]
    )
    
    # Add text labels with dynamic positioning based on bubble size
    text = alt.Chart(df).mark_text(fontSize=12, fontWeight='bold').encode(
        x='Patient %:Q',
        y='Visit %:Q',
        text='Category:N',
        color=alt.value('#333333'),
        dy=alt.expr('-sqrt(datum["Bubble Size"]) / 40 - 10')  # Position above bubble
    )
    
    # Create diagonal reference line (1:1 ratio)
    max_val = max(df['Patient %'].max(), df['Visit %'].max())
    line_df = pd.DataFrame({
        'x': [0, max_val],
        'y': [0, max_val]
    })
    
    line = alt.Chart(line_df).mark_line(
        strokeDash=[5, 5],
        color='#264653',
        strokeWidth=2
    ).encode(
        x=alt.X('x:Q'),
        y=alt.Y('y:Q')
    )
    
    # Combine all elements
    chart = (line + bubbles + text).properties(
        width=500,
        height=500,
        title='Workload Impact Analysis'
    ).configure_axis(
        grid=True,
        gridOpacity=0.3,
        labelFontSize=12,
        titleFontSize=14
    ).configure_view(
        strokeWidth=0
    ).configure_title(
        fontSize=16
    )
    
    return chart


def get_workload_insight_summary(workload_data: Dict[str, Any]) -> str:
    """
    Generate a formatted summary of key workload insights.
    (Same as Plotly version - data processing is the same)
    
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