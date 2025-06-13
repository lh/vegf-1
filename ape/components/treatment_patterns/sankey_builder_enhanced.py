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
    # Import mode colors for terminal status
    from ape.utils.visualization_modes import get_mode_colors
    
    # Get colors from central system
    treatment_colors = get_treatment_state_colors()
    
    # Filter out Pre-Treatment transitions (as requested by user)
    filtered_df = transitions_df[
        (transitions_df['from_state'] != 'Pre-Treatment') & 
        (transitions_df['to_state'] != 'Pre-Treatment')
    ].copy()
    
    # Aggregate transitions
    flow_counts = filtered_df.groupby(['from_state', 'to_state']).size().reset_index(name='count')
    
    # Filter out small flows (but keep all terminal flows)
    min_flow_size = max(1, len(filtered_df) * 0.001)
    is_terminal = flow_counts['to_state'].str.contains('Still in|No Further')
    flow_counts = flow_counts[(flow_counts['count'] >= min_flow_size) | is_terminal]
    
    # Create nodes
    all_states = list(set(flow_counts['from_state']) | set(flow_counts['to_state']))
    # Exclude Pre-Treatment from nodes entirely
    all_states = [s for s in all_states if s != 'Pre-Treatment']
    
    # Sort nodes in logical order
    state_order = [
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
    
    # Add terminal states at the end
    terminal_states = [s for s in all_states if 'Still in' in s and s not in state_order]
    state_order.extend(sorted(terminal_states))
    
    # Add any remaining states
    for state in all_states:
        if state not in state_order:
            state_order.append(state)
    
    # Filter to only states that exist
    ordered_states = [s for s in state_order if s in all_states]
    node_map = {state: i for i, state in enumerate(ordered_states)}
    
    # Calculate total flow for opacity scaling
    total_flow = flow_counts['count'].sum()
    
    # Create link colors based on source state
    link_colors = []
    for _, row in flow_counts.iterrows():
        source_color = treatment_colors.get(row['from_state'], "#cccccc")
        # Convert hex to rgba with opacity based on flow volume
        opacity = min(0.8, max(0.2, row['count'] / total_flow * 20))
        
        # Convert hex to RGB
        hex_color = source_color.lstrip('#')
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        
        link_colors.append(f'rgba({r}, {g}, {b}, {opacity})')
    
    # Create shorter labels for display
    label_mapping = {
        'Initial Treatment': 'Initial',
        'Intensive (Monthly)': 'Intensive',
        'Regular (6-8 weeks)': 'Regular',
        'Extended (12+ weeks)': 'Extended',
        'Maximum Extension (16 weeks)': 'Maximum',
        'Treatment Gap (3-6 months)': 'Gap (3-6m)',
        'Extended Gap (6-12 months)': 'Gap (6-12m)',
        'Long Gap (12+ months)': 'Gap (12m+)',
        'Restarted After Gap': 'Restarted',
        'Irregular Pattern': 'Irregular',
        'No Further Visits': 'Discontinued'
    }
    
    # Process terminal state labels - remove "(Year X)"
    display_labels = []
    for state in ordered_states:
        if 'Still in' in state:
            # Remove the (Year X) part and "Still in" prefix
            base_state = state.split(' (Year')[0]
            # Extract just the treatment state
            if 'Still in Initial' in base_state:
                display_labels.append('Initial')
            elif 'Still in Intensive' in base_state:
                display_labels.append('Intensive')
            elif 'Still in Regular' in base_state:
                display_labels.append('Regular')
            elif 'Still in Extended' in base_state and 'Maximum' not in base_state:
                display_labels.append('Extended')
            elif 'Still in Maximum' in base_state:
                display_labels.append('Maximum')
            else:
                display_labels.append(base_state.replace('Still in ', ''))
        else:
            # Use shortened label if available
            display_labels.append(label_mapping.get(state, state))
    
    # Get colors from central system
    mode_colors = get_mode_colors()
    
    # Create node colors - override terminal node colors
    node_colors = []
    for state in ordered_states:
        if 'Still in' in state:
            # Green for continuing treatment
            node_colors.append(mode_colors.get('terminal_active', '#27ae60'))
        elif 'No Further Visits' in state:
            # Red for discontinued
            node_colors.append(mode_colors.get('terminal_discontinued', '#e74c3c'))
        else:
            # Use standard colors for non-terminal nodes
            node_colors.append(treatment_colors.get(state, "#cccccc"))
    
    # Try to position terminal nodes to align with parent tops
    x_positions = []
    y_positions = []
    
    # Define x positions for each state type
    x_mapping = {
        'Initial Treatment': 0.0,
        'Intensive (Monthly)': 0.2,
        'Regular (6-8 weeks)': 0.4,
        'Extended (12+ weeks)': 0.6,
        'Maximum Extension (16 weeks)': 0.75,
        'No Further Visits': 0.95,
    }
    
    # For terminal "Still in" states, position them at x=0.95
    for state in ordered_states:
        if 'Still in' in state:
            x_positions.append(0.95)
            # Extract parent state from terminal state name
            if 'Intensive' in state:
                y_positions.append(0.3)  # Align with Intensive
            elif 'Regular' in state:
                y_positions.append(0.4)  # Align with Regular
            elif 'Extended' in state and 'Maximum' not in state:
                y_positions.append(0.5)  # Align with Extended
            elif 'Maximum' in state:
                y_positions.append(0.6)  # Align with Maximum
            elif 'Initial' in state:
                y_positions.append(0.2)  # Align with Initial
            else:
                y_positions.append(0.5)  # Default middle
        else:
            # Non-terminal states
            x_positions.append(x_mapping.get(state, 0.5))
            if state == 'Initial Treatment':
                y_positions.append(0.2)
            elif state == 'Intensive (Monthly)':
                y_positions.append(0.3)
            elif state == 'Regular (6-8 weeks)':
                y_positions.append(0.4)
            elif state == 'Extended (12+ weeks)':
                y_positions.append(0.5)
            elif state == 'Maximum Extension (16 weeks)':
                y_positions.append(0.6)
            elif state == 'No Further Visits':
                y_positions.append(0.8)
            else:
                y_positions.append(0.5)
    
    # Create Sankey with fixed positioning
    fig = go.Figure(data=[go.Sankey(
        arrangement='fixed',  # Use fixed arrangement to respect our positions
        node=dict(
            pad=40,
            thickness=20,
            line=dict(color="black", width=1),
            label=display_labels,  # Use shortened labels
            color=node_colors,  # Using our custom colors with terminal overrides
            x=x_positions,
            y=y_positions,
            hoverlabel=dict(font=dict(color='black'))
        ),
        link=dict(
            source=[node_map[row['from_state']] for _, row in flow_counts.iterrows()],
            target=[node_map[row['to_state']] for _, row in flow_counts.iterrows()],
            value=[row['count'] for _, row in flow_counts.iterrows()],
            color=link_colors,
            hovertemplate='%{source.label} → %{target.label}<br>%{value} patients<extra></extra>'
        ),
        textfont=dict(size=14, color='#333333', family='Arial')  # Increased font size
    )])
    
    fig.update_layout(
        title=None,  # Remove title since it's redundant with the section header
        font=dict(size=12),
        height=600,
        margin=dict(l=10, r=150, t=10, b=40),  # Reduced top margin since no title
        showlegend=False
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