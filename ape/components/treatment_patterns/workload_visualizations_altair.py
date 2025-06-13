"""Clinical Workload Visualizations using Altair - Faster alternative to Plotly.

This module provides Altair-based visualizations that are 2-3x faster than Plotly
while maintaining visual quality and interactivity.
"""

import altair as alt
import pandas as pd
from typing import Dict, Any
import streamlit as st

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
    Create dual bar chart using Altair - 2-3x faster than Plotly version.
    
    Args:
        workload_data: Output from calculate_clinical_workload_attribution
        tufte_mode: Whether to use clean Tufte styling (ignored for consistency)
        
    Returns:
        Altair chart object
    """
    if not workload_data['summary_stats']:
        # Return empty chart with message
        return alt.Chart(pd.DataFrame()).mark_text(
            size=16, 
            color='gray',
            text='No workload data available'
        ).properties(
            width=800,
            height=500
        )
    
    # Prepare data for Altair
    data_records = []
    
    # Sort by workload intensity
    sorted_stats = sorted(
        workload_data['summary_stats'].items(),
        key=lambda x: x[1]['workload_intensity'],
        reverse=True
    )
    
    category_definitions = workload_data['category_definitions']
    
    for category, stats in sorted_stats:
        # Patient percentage record
        data_records.append({
            'Category': category,
            'Metric': '% of Patients',
            'Value': stats['patient_percentage'],
            'Color': category_definitions.get(category, {}).get('color', '#cccccc'),
            'SortOrder': sorted_stats.index((category, stats)),  # Maintain sort order
            'Label': f"{stats['patient_percentage']:.1f}%" if stats['patient_percentage'] < 1 else f"{stats['patient_percentage']:.0f}%"
        })
        
        # Visit percentage record
        data_records.append({
            'Category': category,
            'Metric': '% of Visits',
            'Value': stats['visit_percentage'],
            'Color': category_definitions.get(category, {}).get('color', '#cccccc'),
            'SortOrder': sorted_stats.index((category, stats)),
            'Label': f"{stats['visit_percentage']:.1f}%" if stats['visit_percentage'] < 1 else f"{stats['visit_percentage']:.0f}%"
        })
    
    df = pd.DataFrame(data_records)
    
    # Create the grouped bar chart with better positioning
    base = alt.Chart(df).encode(
        x=alt.X('Category:N', 
                sort=alt.SortField(field='SortOrder', order='ascending'),
                title='Treatment Intensity Category',
                axis=alt.Axis(
                    labelAngle=0,
                    labelFontSize=TUFTE_FONT_SIZES['tick'],
                    titleFontSize=TUFTE_FONT_SIZES['label'],
                    titlePadding=10
                )),
        y=alt.Y('Value:Q', 
                title='Percentage',
                axis=alt.Axis(
                    labelFontSize=TUFTE_FONT_SIZES['tick'],
                    titleFontSize=TUFTE_FONT_SIZES['label'],
                    grid=False,
                    titlePadding=10
                ),
                scale=alt.Scale(domain=[0, max(df['Value'].max() * 1.15, 10)])),  # Add space for labels
        xOffset=alt.XOffset('Metric:N', title=None),
        color=alt.Color('Metric:N', 
                       scale=alt.Scale(
                           domain=['% of Patients', '% of Visits'],
                           range=['#8ab4d6', '#2c7fb8']  # Light blue for patients, dark blue for visits
                       ),
                       legend=alt.Legend(
                           title=None,
                           orient='top',
                           labelFontSize=TUFTE_FONT_SIZES['tick'],
                           symbolSize=100,
                           direction='horizontal',
                           anchor='middle',
                           padding=10
                       )),
        opacity=alt.condition(
            alt.datum.Metric == '% of Patients',
            alt.value(0.6),
            alt.value(1.0)
        ),
        tooltip=[
            alt.Tooltip('Category:N', title='Category'),
            alt.Tooltip('Metric:N', title='Metric'),
            alt.Tooltip('Value:Q', title='Value', format='.1f')
        ]
    )
    
    # Create bars
    bars = base.mark_bar(size=30)
    
    # Add text labels on top of bars
    text = base.mark_text(
        align='center',
        baseline='bottom',
        dy=-5,
        fontSize=10
    ).encode(
        text='Label:N'
    )
    
    # Combine bars and text
    chart = (bars + text).properties(
        width=700,
        height=400,
        padding={'left': 20, 'right': 20, 'top': 40, 'bottom': 20}
    ).configure_view(
        strokeWidth=0  # Remove border
    ).configure_axis(
        domainWidth=1,
        domainColor=TUFTE_COLORS['neutral'],
        tickWidth=1,
        tickColor=TUFTE_COLORS['neutral'],
        labelColor=TUFTE_COLORS['neutral'],
        titleColor=TUFTE_COLORS['neutral']
    ).configure_legend(
        strokeColor='white',
        fillColor='white',
        padding=10
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