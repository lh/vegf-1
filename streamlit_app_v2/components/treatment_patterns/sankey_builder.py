"""Sankey diagram builders for treatment patterns."""

import plotly.graph_objects as go
import pandas as pd
from .pattern_analyzer import TREATMENT_STATE_COLORS


def create_treatment_pattern_sankey(transitions_df):
    """Create Sankey diagram of treatment patterns."""
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
    
    # Create Sankey
    fig = go.Figure(data=[go.Sankey(
        arrangement='snap',
        node=dict(
            pad=30,
            thickness=20,
            line=dict(color="black", width=1),
            label=[n['label'] for n in nodes],
            color=[n['color'] for n in nodes],
            # Ensure clean text rendering
            hoverlabel=dict(font=dict(color='black'))
        ),
        link=dict(
            source=[node_map[row['from_state']] for _, row in flow_counts.iterrows()],
            target=[node_map[row['to_state']] for _, row in flow_counts.iterrows()],
            value=[row['count'] for _, row in flow_counts.iterrows()],
            color="rgba(100, 100, 100, 0.2)"
        ),
        textfont=dict(size=12, color='#333333', family='Arial')
    )])
    
    fig.update_layout(
        title=dict(
            text="Treatment Pattern Transitions (Based on Visit Intervals Only)",
            font=dict(size=16)
        ),
        font=dict(size=12),
        height=600,
        margin=dict(l=10, r=10, t=40, b=30),
        annotations=[{
            'text': 'This visualization uses ONLY treatment timing data - no disease state information',
            'showarrow': False,
            'xref': 'paper', 'yref': 'paper',
            'x': 0.5, 'y': -0.05,
            'xanchor': 'center', 'yanchor': 'top',
            'font': {'size': 11, 'color': 'gray'}
        }]
    )
    
    return fig


def create_enhanced_sankey_with_colored_streams(transitions_df):
    """
    Create Sankey diagram with source-colored streams.
    Each flow inherits the color of its source state.
    """
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
    
    # Calculate total flow for opacity scaling
    total_flow = flow_counts['count'].sum()
    
    # Create link colors based on source state
    link_colors = []
    for _, row in flow_counts.iterrows():
        source_color = TREATMENT_STATE_COLORS.get(row['from_state'], "#cccccc")
        # Convert hex to rgba with opacity based on flow volume
        opacity = min(0.8, max(0.2, row['count'] / total_flow * 20))
        
        # Convert hex to RGB
        hex_color = source_color.lstrip('#')
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        
        link_colors.append(f'rgba({r}, {g}, {b}, {opacity})')
    
    # Create Sankey
    fig = go.Figure(data=[go.Sankey(
        arrangement='snap',
        node=dict(
            pad=30,
            thickness=20,
            line=dict(color="black", width=1),
            label=[n['label'] for n in nodes],
            color=[n['color'] for n in nodes],
            # Ensure clean text rendering
            hoverlabel=dict(font=dict(color='black'))
        ),
        link=dict(
            source=[node_map[row['from_state']] for _, row in flow_counts.iterrows()],
            target=[node_map[row['to_state']] for _, row in flow_counts.iterrows()],
            value=[row['count'] for _, row in flow_counts.iterrows()],
            color=link_colors,
            hovertemplate='%{source.label} → %{target.label}<br>Count: %{value}<extra></extra>'
        ),
        textfont=dict(size=12, color='#333333', family='Arial')
    )])
    
    fig.update_layout(
        title=dict(
            text="Treatment Pattern Flow (Source-Colored Streams)",
            font=dict(size=16)
        ),
        font=dict(size=12),
        height=600,
        margin=dict(l=10, r=10, t=40, b=30),
        # No annotations needed - colors are self-explanatory from source nodes
    )
    
    return fig


def create_gradient_sankey(transitions_df):
    """
    Create Sankey diagram with semantically colored gradients.
    Colors represent the type of transition (improving, stable, worsening).
    """
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
    
    # Create semantic colors for transitions
    def get_transition_color(from_state, to_state):
        """Determine color based on transition type."""
        # Moving to intensive treatment
        if 'Intensive' in to_state or 'Initial' in to_state:
            return 'rgba(74, 144, 226, 0.5)'  # Blue - starting/intensifying
        
        # Regular/extended treatment (stable)
        elif 'Regular' in to_state or 'Extended' in to_state:
            return 'rgba(127, 186, 0, 0.5)'  # Green - stable/extending
        
        # Moving to gaps
        elif 'Gap' in to_state and 'Gap' not in from_state:
            return 'rgba(255, 215, 0, 0.5)'  # Yellow - developing gap
        
        # Within gaps or worsening gaps
        elif 'Gap' in to_state and 'Gap' in from_state:
            if '12+' in to_state:
                return 'rgba(255, 99, 71, 0.5)'  # Red - long gap
            else:
                return 'rgba(255, 149, 0, 0.5)'  # Orange - continuing gap
        
        # Restarting after gap
        elif 'Restarted' in to_state:
            return 'rgba(255, 20, 147, 0.5)'  # Pink - restart
        
        # Discontinuation
        elif 'No Further' in to_state:
            return 'rgba(153, 153, 153, 0.5)'  # Gray - stopped
        
        else:
            return 'rgba(100, 100, 100, 0.3)'  # Default gray
    
    # Apply semantic colors
    link_colors = [get_transition_color(row['from_state'], row['to_state']) 
                   for _, row in flow_counts.iterrows()]
    
    # Create Sankey
    fig = go.Figure(data=[go.Sankey(
        arrangement='snap',
        node=dict(
            pad=30,
            thickness=20,
            line=dict(color="black", width=1),
            label=[n['label'] for n in nodes],
            color=[n['color'] for n in nodes],
            # Ensure clean text rendering
            hoverlabel=dict(font=dict(color='black'))
        ),
        link=dict(
            source=[node_map[row['from_state']] for _, row in flow_counts.iterrows()],
            target=[node_map[row['to_state']] for _, row in flow_counts.iterrows()],
            value=[row['count'] for _, row in flow_counts.iterrows()],
            color=link_colors,
            hovertemplate='%{source.label} → %{target.label}<br>Count: %{value}<extra></extra>'
        ),
        textfont=dict(size=12, color='#333333', family='Arial')
    )])
    
    # Add colour legend
    color_legend_text = """
    <b>Flow Colours:</b><br>
    🔵 Blue: Starting/intensifying treatment<br>
    🟢 Green: Stable/extending treatment<br>
    🟡 Yellow: Developing treatment gap<br>
    🟠 Orange: Continuing gap<br>
    🔴 Red: Long gap (12+ months)<br>
    🩷 Pink: Restarting after gap<br>
    ⚫ Grey: Discontinuation
    """
    
    fig.update_layout(
        title=dict(
            text="Treatment Pattern Flow (Semantically Coloured)",
            font=dict(size=16)
        ),
        font=dict(size=12),
        height=600,
        margin=dict(l=10, r=10, t=40, b=100),  # Space for legend below
        annotations=[
            {
                'text': 'Flow colours indicate the type of transition (improving, stable, or developing gaps)',
                'showarrow': False,
                'xref': 'paper', 'yref': 'paper',
                'x': 0.5, 'y': -0.05,
                'xanchor': 'center', 'yanchor': 'top',
                'font': {'size': 11, 'color': 'gray'}
            },
            {
                'text': color_legend_text,
                'showarrow': False,
                'xref': 'paper', 'yref': 'paper',
                'x': 0.5, 'y': -0.15,  # Moved below the chart
                'xanchor': 'center', 'yanchor': 'top',
                'font': {'size': 10},
                'align': 'left'
            }
        ]
    )
    
    return fig