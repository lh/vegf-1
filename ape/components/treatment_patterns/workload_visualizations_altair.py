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
    
    # Create color mappings for each category
    category_colors = {}
    for category in sorted_stats:
        cat_name = category[0]
        category_colors[cat_name] = category_definitions.get(cat_name, {}).get('color', '#cccccc')
    
    for category, stats in sorted_stats:
        base_color = category_colors[category]
        
        # Patient percentage record (lighter shade)
        data_records.append({
            'Category': category,
            'Metric': '% of Patients',
            'Value': stats['patient_percentage'],
            'SortOrder': sorted_stats.index((category, stats)),
            'Label': f"{stats['patient_percentage']:.1f}%" if stats['patient_percentage'] < 1 else f"{stats['patient_percentage']:.0f}%",
            'CategoryColor': base_color,
            'IsPatient': True
        })
        
        # Visit percentage record (darker shade)
        data_records.append({
            'Category': category,
            'Metric': '% of Visits',
            'Value': stats['visit_percentage'],
            'SortOrder': sorted_stats.index((category, stats)),
            'Label': f"{stats['visit_percentage']:.1f}%" if stats['visit_percentage'] < 1 else f"{stats['visit_percentage']:.0f}%",
            'CategoryColor': base_color,
            'IsPatient': False
        })
    
    df = pd.DataFrame(data_records)
    
    # Create the grouped bar chart with semantic colors
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
                scale=alt.Scale(domain=[0, max(df['Value'].max() * 1.15, 10)])),
        xOffset=alt.XOffset('Metric:N', title=None),
        color=alt.Color('CategoryColor:N',
                       scale=None,  # Use exact colors from data
                       legend=None),  # We'll create a custom legend
        opacity=alt.condition(
            alt.datum.IsPatient,
            alt.value(0.5),  # Light for patients
            alt.value(1.0)   # Full opacity for visits
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
    
    # Get colors from the system
    colors = get_mode_colors()
    
    # Create manual legend data for metric types
    legend_data = pd.DataFrame([
        {'label': '% of Patients', 'order': 0},
        {'label': '% of Visits', 'order': 1}
    ])
    
    # Simple legend showing opacity difference using neutral color
    legend = alt.Chart(legend_data).mark_square(size=150).encode(
        y=alt.Y('label:N', axis=None, sort=alt.SortField(field='order')),
        color=alt.value(colors.get('neutral', '#264653')),
        opacity=alt.condition(
            alt.datum.label == '% of Patients',
            alt.value(0.5),
            alt.value(1.0)
        )
    ).properties(
        width=20
    )
    
    legend_text = alt.Chart(legend_data).mark_text(
        align='left',
        baseline='middle',
        dx=10,
        fontSize=12
    ).encode(
        y=alt.Y('label:N', axis=None, sort=alt.SortField(field='order')),
        text='label:N'
    ).properties(
        width=120
    )
    
    # Combine bars and text
    main_chart = (bars + text).properties(
        width=500,  # Narrower width
        height=350,
        title=alt.TitleParams(
            text='Clinical Workload Attribution',
            fontSize=TUFTE_FONT_SIZES['title'],
            anchor='middle'
        )
    )
    
    # Combine main chart with legend
    chart = alt.hconcat(
        main_chart,
        (legend + legend_text).properties(width=150)
    ).configure_view(
        strokeWidth=0
    ).configure_axis(
        domainWidth=1,
        domainColor=TUFTE_COLORS['neutral'],
        tickWidth=1,
        tickColor=TUFTE_COLORS['neutral'],
        labelColor=TUFTE_COLORS['neutral'],
        titleColor=TUFTE_COLORS['neutral']
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