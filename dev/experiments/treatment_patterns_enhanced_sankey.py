#!/usr/bin/env python3
"""
Enhanced Treatment Pattern Visualizations with Colored Sankey Streams.

This builds on the original treatment_patterns_visualization.py but adds
enhanced color coding to the Sankey diagram streams for better visibility.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from pathlib import Path
import json
from collections import defaultdict
import sys
from datetime import datetime
import time

# Add parent directories to path
sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent.parent.parent))

from core.results.factory import ResultsFactory

# Import the original functions
from treatment_patterns_visualization import (
    get_available_simulations,
    extract_treatment_patterns_vectorized,
    determine_treatment_state_vectorized,
    create_interval_distribution_chart,
    create_gap_analysis_chart,
    TREATMENT_STATE_COLORS
)


def create_enhanced_sankey_with_colored_streams(transitions_df):
    """Create Sankey diagram with colored streams based on source states."""
    # Aggregate transitions
    flow_counts = transitions_df.groupby(['from_state', 'to_state']).size().reset_index(name='count')
    
    # Filter out small flows
    min_flow_size = max(1, len(transitions_df) * 0.001)
    flow_counts = flow_counts[flow_counts['count'] >= min_flow_size]
    
    # Create nodes
    nodes = []
    node_map = {}
    
    # Define preferred order for nodes
    state_order = [
        'Pre-Treatment',
        'Initial Treatment',
        'Intensive (Monthly)',
        'Regular (6-8 weeks)',
        'Extended (12+ weeks)',
        'Maximum Extension (16 weeks)',
        'Treatment Gap (3-6 months)',
        'Extended Gap (6-12 months)',
        'Long Gap (12+ months)',
        'Restarted After Gap',
        'Irregular Pattern',
        'No Further Visits'
    ]
    
    # Add nodes in preferred order if they exist
    for state in state_order:
        if state in flow_counts['from_state'].values or state in flow_counts['to_state'].values:
            node_map[state] = len(nodes)
            nodes.append({
                'label': state,
                'color': TREATMENT_STATE_COLORS.get(state, "#cccccc")
            })
    
    # Add any missing states
    for _, row in flow_counts.iterrows():
        for state in [row['from_state'], row['to_state']]:
            if state not in node_map:
                node_map[state] = len(nodes)
                nodes.append({
                    'label': state,
                    'color': TREATMENT_STATE_COLORS.get(state, "#cccccc")
                })
    
    # Create link colors based on source state with transparency
    link_colors = []
    for _, row in flow_counts.iterrows():
        # Get source color and add transparency
        source_color = TREATMENT_STATE_COLORS.get(row['from_state'], "#cccccc")
        
        # Convert hex to rgba with transparency
        if source_color.startswith('#'):
            # Parse hex color
            hex_color = source_color.lstrip('#')
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            # Add transparency based on flow strength
            max_count = flow_counts['count'].max()
            opacity = 0.3 + (0.5 * row['count'] / max_count)  # Scale opacity 0.3-0.8
            link_colors.append(f'rgba({r},{g},{b},{opacity})')
        else:
            link_colors.append(source_color)
    
    # Create enhanced Sankey
    fig = go.Figure(data=[go.Sankey(
        arrangement='snap',
        node=dict(
            pad=25,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=[n['label'] for n in nodes],
            color=[n['color'] for n in nodes],
            # Add hover text showing patient counts at each node
            customdata=[
                flow_counts[
                    (flow_counts['from_state'] == n['label']) | 
                    (flow_counts['to_state'] == n['label'])
                ]['count'].sum() for n in nodes
            ],
            hovertemplate='%{label}<br>Total patients: %{customdata}<extra></extra>'
        ),
        link=dict(
            source=[node_map[row['from_state']] for _, row in flow_counts.iterrows()],
            target=[node_map[row['to_state']] for _, row in flow_counts.iterrows()],
            value=flow_counts['count'].tolist(),
            color=link_colors,
            # Add hover information
            customdata=[[row['from_state'], row['to_state'], row['count']] 
                       for _, row in flow_counts.iterrows()],
            hovertemplate='%{customdata[0]} → %{customdata[1]}<br>Patients: %{customdata[2]}<extra></extra>'
        )
    )])
    
    fig.update_layout(
        title={
            'text': "Enhanced Treatment Pattern Transitions (Colored by Source State)",
            'font': {'size': 20}
        },
        font=dict(size=12),
        height=700,
        margin=dict(l=50, r=50, t=100, b=50)
    )
    
    return fig


def create_gradient_sankey(transitions_df):
    """Create Sankey diagram with gradient-colored streams."""
    # Aggregate transitions
    flow_counts = transitions_df.groupby(['from_state', 'to_state']).size().reset_index(name='count')
    
    # Filter out small flows
    min_flow_size = max(1, len(transitions_df) * 0.001)
    flow_counts = flow_counts[flow_counts['count'] >= min_flow_size]
    
    # Create nodes
    nodes = []
    node_map = {}
    
    # Define preferred order for nodes
    state_order = [
        'Pre-Treatment',
        'Initial Treatment',
        'Intensive (Monthly)',
        'Regular (6-8 weeks)',
        'Extended (12+ weeks)',
        'Maximum Extension (16 weeks)',
        'Treatment Gap (3-6 months)',
        'Extended Gap (6-12 months)',
        'Long Gap (12+ months)',
        'Restarted After Gap',
        'Irregular Pattern',
        'No Further Visits'
    ]
    
    # Add nodes in preferred order if they exist
    for state in state_order:
        if state in flow_counts['from_state'].values or state in flow_counts['to_state'].values:
            node_map[state] = len(nodes)
            nodes.append({
                'label': state,
                'color': TREATMENT_STATE_COLORS.get(state, "#cccccc")
            })
    
    # Create link colors with special handling for different transition types
    link_colors = []
    for _, row in flow_counts.iterrows():
        from_state = row['from_state']
        to_state = row['to_state']
        
        # Special colors for specific transition types
        if 'Gap' in from_state and 'Restarted' in to_state:
            # Restart after gap - hopeful pink/purple
            color = 'rgba(255, 20, 147, 0.6)'  # Deep pink
        elif 'Gap' in to_state:
            # Moving to a gap - warning colors (orange/red)
            if 'Long Gap' in to_state:
                color = 'rgba(255, 99, 71, 0.7)'  # Tomato
            elif 'Extended Gap' in to_state:
                color = 'rgba(255, 149, 0, 0.6)'  # Orange
            else:
                color = 'rgba(255, 215, 0, 0.6)'  # Gold
        elif to_state == 'No Further Visits':
            # Discontinuation - gray
            color = 'rgba(128, 128, 128, 0.5)'
        elif 'Extension' in to_state or 'Extended' in to_state:
            # Treatment extension - darker greens
            color = 'rgba(92, 138, 0, 0.6)'
        elif 'Regular' in to_state:
            # Regular treatment - healthy green
            color = 'rgba(127, 186, 0, 0.6)'
        elif 'Intensive' in to_state:
            # Intensive treatment - blue
            color = 'rgba(74, 144, 226, 0.6)'
        else:
            # Default - light blue
            color = 'rgba(200, 200, 200, 0.5)'
        
        link_colors.append(color)
    
    # Create Sankey with semantic coloring
    fig = go.Figure(data=[go.Sankey(
        arrangement='snap',
        node=dict(
            pad=25,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=[n['label'] for n in nodes],
            color=[n['color'] for n in nodes]
        ),
        link=dict(
            source=[node_map[row['from_state']] for _, row in flow_counts.iterrows()],
            target=[node_map[row['to_state']] for _, row in flow_counts.iterrows()],
            value=flow_counts['count'].tolist(),
            color=link_colors,
            customdata=[[row['from_state'], row['to_state'], row['count']] 
                       for _, row in flow_counts.iterrows()],
            hovertemplate='%{customdata[0]} → %{customdata[1]}<br>Patients: %{customdata[2]}<extra></extra>'
        )
    )])
    
    fig.update_layout(
        title={
            'text': "Treatment Patterns with Semantic Flow Colors",
            'font': {'size': 20}
        },
        font=dict(size=12),
        height=700,
        margin=dict(l=50, r=50, t=100, b=50),
        annotations=[{
            'text': (
                '<b>Flow Color Legend:</b><br>' +
                '🔵 Blue: Intensive treatment | 🟢 Green: Regular/Extended treatment<br>' +
                '🟡 Yellow/Orange: Treatment gaps | 🔴 Red: Long gaps<br>' +
                '💜 Pink: Restart after gap | ⚫ Gray: No further visits'
            ),
            'showarrow': False,
            'xref': 'paper',
            'yref': 'paper',
            'x': 0.5,
            'y': -0.1,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': {'size': 11}
        }]
    )
    
    return fig


def main():
    """Main Streamlit app."""
    st.set_page_config(page_title="Enhanced Treatment Pattern Analysis", layout="wide")
    
    st.title("🎨 Enhanced Treatment Pattern Analysis with Colored Flows")
    st.markdown("""
    ### Sankey Diagrams with Enhanced Stream Visualization
    
    This page shows the same treatment pattern analysis but with **colored flow streams** 
    to better visualize patient journeys through different treatment states.
    """)
    
    # Sidebar
    with st.sidebar:
        st.header("Select Simulation")
        
        simulations = get_available_simulations()
        
        if not simulations:
            st.error("No simulation results found!")
            st.stop()
        
        sim_options = [f"{sim['id']} ({sim['patients']} patients, {sim['duration']}m)" 
                      for sim in simulations]
        selected_idx = st.selectbox(
            "Choose simulation",
            range(len(sim_options)),
            format_func=lambda x: sim_options[x]
        )
        
        selected_sim = simulations[selected_idx]
        
        st.subheader("Simulation Details")
        st.metric("Patients", f"{selected_sim['patients']:,}")
        st.metric("Duration", f"{selected_sim['duration']} months")
        
        # Color scheme selector
        st.subheader("Visualization Options")
        color_scheme = st.radio(
            "Color Scheme",
            ["Source-based (flows inherit source color)",
             "Semantic (flows colored by transition type)"],
            index=0
        )
        
        # Load simulation data
        try:
            results = ResultsFactory.load_results(selected_sim['path'])
            
            # Extract transitions and visits with intervals
            transitions_df, visits_df = extract_treatment_patterns_vectorized(results)
            
            if len(transitions_df) == 0:
                st.error("No transitions found")
                st.stop()
                
            st.success(f"Analyzed {len(transitions_df):,} treatment patterns")
            
        except Exception as e:
            st.error(f"Error: {str(e)}")
            import traceback
            st.code(traceback.format_exc())
            st.stop()
    
    # Show comparison
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📊 Enhanced Sankey Diagram")
        if "Source-based" in color_scheme:
            fig = create_enhanced_sankey_with_colored_streams(transitions_df)
            st.plotly_chart(fig, use_container_width=True)
            
            with st.expander("ℹ️ About source-based coloring"):
                st.markdown("""
                In this visualization:
                - Each **flow inherits the color of its source state**
                - Flow opacity indicates the number of patients (thicker = more patients)
                - This helps track where patients are coming FROM
                - Useful for seeing which states lead to gaps or discontinuation
                """)
        else:
            fig = create_gradient_sankey(transitions_df)
            st.plotly_chart(fig, use_container_width=True)
            
            with st.expander("ℹ️ About semantic coloring"):
                st.markdown("""
                In this visualization:
                - Flows are colored based on **what type of transition they represent**
                - 🔵 Blue flows: Moving to intensive treatment
                - 🟢 Green flows: Regular or extended treatment patterns  
                - 🟡🟠 Yellow/Orange flows: Treatment gaps developing
                - 🔴 Red flows: Long treatment gaps
                - 💜 Pink flows: Restarting after a gap
                - ⚫ Gray flows: Discontinuation
                """)
    
    with col2:
        st.subheader("📈 Flow Statistics")
        
        # Calculate flow statistics
        flow_stats = transitions_df.groupby(['from_state', 'to_state']).size().reset_index(name='count')
        flow_stats = flow_stats.sort_values('count', ascending=False).head(15)
        
        st.markdown("**Top 15 Most Common Transitions:**")
        for _, row in flow_stats.iterrows():
            pct = row['count'] / len(transitions_df) * 100
            st.markdown(f"• {row['from_state']} → {row['to_state']}: "
                       f"**{row['count']:,}** patients ({pct:.1f}%)")
        
        # Key insights
        st.markdown("---")
        st.subheader("🔍 Key Insights")
        
        # Calculate key metrics
        gap_transitions = transitions_df[transitions_df['to_state'].str.contains('Gap')]
        restart_transitions = transitions_df[transitions_df['to_state'] == 'Restarted After Gap']
        discontinuation_transitions = transitions_df[transitions_df['to_state'] == 'No Further Visits']
        
        col_a, col_b = st.columns(2)
        with col_a:
            st.metric("Patients with gaps", 
                     f"{len(gap_transitions):,}",
                     f"{len(gap_transitions)/len(transitions_df)*100:.1f}% of transitions")
        with col_b:
            restart_pct = (len(restart_transitions)/len(gap_transitions)*100 
                          if len(gap_transitions) > 0 else 0)
            st.metric("Patients restarting", 
                     f"{len(restart_transitions):,}",
                     f"{restart_pct:.1f}% of gaps" if len(gap_transitions) > 0 else "N/A")
        
        # Link back to original
        st.markdown("---")
        st.info("💡 **Tip:** Compare with the [original visualization](http://localhost:8512) "
               "to see the difference color coding makes!")


if __name__ == "__main__":
    main()