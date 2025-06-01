"""
Enhanced Sankey builder that includes special handling for terminal "Still in Treatment" nodes.
"""

import plotly.graph_objects as go
from typing import Dict, List
import pandas as pd

from .pattern_analyzer import get_treatment_state_colors
from .pattern_analyzer_enhanced import get_terminal_node_colors


def add_terminal_node_styling(nodes: List[Dict], node_map: Dict[str, int]):
    """
    Add special styling for terminal nodes.
    
    Modifies nodes list in place to add distinct styling for "Still in" nodes.
    """
    terminal_colors = get_terminal_node_colors()
    treatment_colors = get_treatment_state_colors()
    
    for i, node in enumerate(nodes):
        if 'Still in' in node['label']:
            # Extract the base state name for color mapping
            for base_state in treatment_colors:
                if base_state in node['label']:
                    # Use a lighter, semi-transparent version
                    base_color = treatment_colors[base_state]
                    if base_color.startswith('#'):
                        # Convert hex to rgba with transparency
                        hex_color = base_color.lstrip('#')
                        r = int(hex_color[0:2], 16)
                        g = int(hex_color[2:4], 16)
                        b = int(hex_color[4:6], 16)
                        node['color'] = f'rgba({r}, {g}, {b}, 0.4)'
                    break
            
            # Add a special marker to identify terminal nodes
            node['is_terminal'] = True


def create_enhanced_sankey_with_terminals(transitions_df):
    """
    Create Sankey diagram with terminal state nodes for patients still in treatment.
    
    This version includes special handling and styling for terminal nodes.
    """
    # Get colors from central system
    treatment_colors = get_treatment_state_colors()
    
    # Aggregate transitions
    flow_counts = transitions_df.groupby(['from_state', 'to_state']).size().reset_index(name='count')
    
    # Don't filter out terminal flows
    min_flow_size = max(1, len(transitions_df) * 0.001)
    is_terminal = flow_counts['to_state'].str.contains('Still in')
    flow_counts = flow_counts[(flow_counts['count'] >= min_flow_size) | is_terminal]
    
    # Create nodes with special ordering
    nodes = []
    node_map = {}
    
    # Define preferred order - regular states first, then terminal states
    regular_state_order = [
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
    
    # Add regular nodes first
    for state in regular_state_order:
        if state in flow_counts['from_state'].values or state in flow_counts['to_state'].values:
            node_map[state] = len(nodes)
            nodes.append({
                'label': state,
                'color': treatment_colors.get(state, "#cccccc"),
                'is_terminal': False
            })
    
    # Add terminal nodes at the end
    terminal_states = sorted([s for s in set(flow_counts['to_state']) if 'Still in' in s])
    for state in terminal_states:
        node_map[state] = len(nodes)
        nodes.append({
            'label': state,
            'color': "#cccccc",  # Will be updated by add_terminal_node_styling
            'is_terminal': True
        })
    
    # Apply special terminal node styling
    add_terminal_node_styling(nodes, node_map)
    
    # Create link colors based on source state
    link_colors = []
    for _, row in flow_counts.iterrows():
        source_color = treatment_colors.get(row['from_state'], "#cccccc")
        
        # Make terminal flows more transparent
        if 'Still in' in row['to_state']:
            opacity = 0.3
        else:
            # Regular flow opacity based on strength
            max_count = flow_counts[~flow_counts['to_state'].str.contains('Still in')]['count'].max()
            opacity = 0.3 + (0.5 * row['count'] / max_count)
        
        # Convert color to rgba
        if source_color.startswith('#'):
            hex_color = source_color.lstrip('#')
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            link_colors.append(f'rgba({r}, {g}, {b}, {opacity})')
        else:
            link_colors.append(source_color)
    
    # Create Sankey with custom node shapes for terminals
    fig = go.Figure(data=[go.Sankey(
        arrangement='snap',
        node=dict(
            pad=40,  # Increased padding to reduce cramping
            thickness=20,
            line=dict(
                color=[
                    "rgba(0,0,0,0.3)" if node.get('is_terminal') else "black"
                    for node in nodes
                ],
                width=[
                    2 if node.get('is_terminal') else 1
                    for node in nodes
                ]
            ),
            label=[n['label'] for n in nodes],
            color=[n['color'] for n in nodes],
            # Add hover text to explain terminal nodes
            hovertemplate=[
                'Active patients at simulation end<br>%{value} patients<extra></extra>' 
                if n.get('is_terminal') 
                else '%{label}<br>%{value} transitions<extra></extra>'
                for n in nodes
            ]
        ),
        link=dict(
            source=[node_map[row['from_state']] for _, row in flow_counts.iterrows()],
            target=[node_map[row['to_state']] for _, row in flow_counts.iterrows()],
            value=[row['count'] for _, row in flow_counts.iterrows()],
            color=link_colors,
            hovertemplate='%{source.label} → %{target.label}<br>Count: %{value}<extra></extra>'
        ),
        textfont=dict(
            size=11,  # Slightly smaller for less cramping
            color='#333333',
            family='Arial'
        )
    )])
    
    fig.update_layout(
        title=dict(
            text="Treatment Pattern Flow (Source-Coloured) with Active Patients at End",
            font=dict(size=16)
        ),
        font=dict(size=12),
        height=800,  # Taller to give more space
        margin=dict(l=10, r=150, t=40, b=50),  # More right margin for terminal nodes
        annotations=[
            {
                'text': 'Dashed boxes show patients still in treatment at simulation end',
                'showarrow': False,
                'xref': 'paper', 'yref': 'paper',
                'x': 0.5, 'y': -0.05,
                'xanchor': 'center', 'yanchor': 'top',
                'font': {'size': 11, 'color': 'gray', 'style': 'italic'}
            }
        ]
    )
    
    return fig


def create_enhanced_sankey_with_terminals_destination_colored(transitions_df):
    """
    Create Sankey diagram with terminal nodes and destination-based coloring.
    """
    # Get colors from central system
    treatment_colors = get_treatment_state_colors()
    
    # Aggregate transitions
    flow_counts = transitions_df.groupby(['from_state', 'to_state']).size().reset_index(name='count')
    
    # Don't filter out terminal flows
    min_flow_size = max(1, len(transitions_df) * 0.001)
    is_terminal = flow_counts['to_state'].str.contains('Still in')
    flow_counts = flow_counts[(flow_counts['count'] >= min_flow_size) | is_terminal]
    
    # Create nodes with special ordering
    nodes = []
    node_map = {}
    
    # Define preferred order - regular states first, then terminal states
    regular_state_order = [
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
    
    # Add regular nodes first
    for state in regular_state_order:
        if state in flow_counts['from_state'].values or state in flow_counts['to_state'].values:
            node_map[state] = len(nodes)
            nodes.append({
                'label': state,
                'color': treatment_colors.get(state, "#cccccc"),
                'is_terminal': False
            })
    
    # Add terminal nodes at the end
    terminal_states = sorted([s for s in set(flow_counts['to_state']) if 'Still in' in s])
    for state in terminal_states:
        node_map[state] = len(nodes)
        nodes.append({
            'label': state,
            'color': "#cccccc",  # Will be updated by add_terminal_node_styling
            'is_terminal': True
        })
    
    # Apply special terminal node styling
    add_terminal_node_styling(nodes, node_map)
    
    # Create colors based on destination state
    def get_transition_color(from_state, to_state):
        """Determine colour based on destination state."""
        # Special handling for terminal states
        if 'Still in' in to_state:
            # Extract base state for coloring
            for base_state in treatment_colors:
                if base_state in to_state:
                    base_color = treatment_colors[base_state]
                    if base_color.startswith('#'):
                        hex_color = base_color.lstrip('#')
                        r = int(hex_color[0:2], 16)
                        g = int(hex_color[2:4], 16)
                        b = int(hex_color[4:6], 16)
                        return f'rgba({r}, {g}, {b}, 0.3)'
                    return base_color
            return 'rgba(100, 100, 100, 0.3)'
        
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
    
    # Apply destination-based colors
    link_colors = [get_transition_color(row['from_state'], row['to_state']) 
                   for _, row in flow_counts.iterrows()]
    
    # Create Sankey with custom node shapes for terminals
    fig = go.Figure(data=[go.Sankey(
        arrangement='snap',
        node=dict(
            pad=40,  # Increased padding to reduce cramping
            thickness=20,
            line=dict(
                color=[
                    "rgba(0,0,0,0.3)" if node.get('is_terminal') else "black"
                    for node in nodes
                ],
                width=[
                    2 if node.get('is_terminal') else 1
                    for node in nodes
                ]
            ),
            label=[n['label'] for n in nodes],
            color=[n['color'] for n in nodes],
            # Add hover text to explain terminal nodes
            hovertemplate=[
                'Active patients at simulation end<br>%{value} patients<extra></extra>' 
                if n.get('is_terminal') 
                else '%{label}<br>%{value} transitions<extra></extra>'
                for n in nodes
            ]
        ),
        link=dict(
            source=[node_map[row['from_state']] for _, row in flow_counts.iterrows()],
            target=[node_map[row['to_state']] for _, row in flow_counts.iterrows()],
            value=[row['count'] for _, row in flow_counts.iterrows()],
            color=link_colors,
            hovertemplate='%{source.label} → %{target.label}<br>Count: %{value}<extra></extra>'
        ),
        textfont=dict(
            size=11,  # Slightly smaller for less cramping
            color='#333333',
            family='Arial'
        )
    )])
    
    fig.update_layout(
        title=dict(
            text="Treatment Pattern Flow (Destination-Coloured) with Active Patients at End",
            font=dict(size=16)
        ),
        font=dict(size=12),
        height=800,  # Taller to give more space
        margin=dict(l=10, r=150, t=40, b=50),  # More right margin for terminal nodes
        annotations=[
            {
                'text': 'Dashed boxes show patients still in treatment at simulation end',
                'showarrow': False,
                'xref': 'paper', 'yref': 'paper',
                'x': 0.5, 'y': -0.05,
                'xanchor': 'center', 'yanchor': 'top',
                'font': {'size': 11, 'color': 'gray', 'style': 'italic'}
            }
        ]
    )
    
    return fig