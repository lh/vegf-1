"""
Demonstration of advanced Sankey customization options.

This script shows various ways to enhance the appearance and functionality
of Sankey diagrams for treatment pattern visualization.
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from components.treatment_patterns import extract_treatment_patterns_vectorized
from core.results.factory import ResultsFactory


def create_basic_sankey(transitions_df):
    """Create a basic Sankey for comparison."""
    flow_counts = transitions_df.groupby(['from_state', 'to_state']).size().reset_index(name='count')
    
    # Create nodes
    all_states = list(set(flow_counts['from_state']) | set(flow_counts['to_state']))
    node_map = {state: i for i, state in enumerate(all_states)}
    
    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            label=all_states,
            color="blue"
        ),
        link=dict(
            source=[node_map[row['from_state']] for _, row in flow_counts.iterrows()],
            target=[node_map[row['to_state']] for _, row in flow_counts.iterrows()],
            value=[row['count'] for _, row in flow_counts.iterrows()]
        )
    )])
    
    fig.update_layout(title="Basic Sankey", height=400)
    return fig


def create_custom_positioned_sankey(transitions_df):
    """Create Sankey with custom node positions."""
    flow_counts = transitions_df.groupby(['from_state', 'to_state']).size().reset_index(name='count')
    
    # Define node positions based on treatment progression
    position_map = {
        # Early treatment (left side)
        'Pre-Treatment': (0.01, 0.5),
        'Initial Treatment': (0.15, 0.3),
        'Intensive (Monthly)': (0.3, 0.2),
        
        # Stable treatment (middle)
        'Regular (6-8 weeks)': (0.5, 0.3),
        'Extended (12+ weeks)': (0.5, 0.5),
        'Maximum Extension (16 weeks)': (0.5, 0.7),
        
        # Gaps and issues (right side, lower)
        'Treatment Gap (3-6 months)': (0.7, 0.8),
        'Extended Gap (6-12 months)': (0.85, 0.85),
        'Long Gap (12+ months)': (0.99, 0.9),
        
        # Special states
        'Restarted After Gap': (0.4, 0.8),
        'Irregular Pattern': (0.6, 0.9),
        'No Further Visits': (0.99, 0.5)
    }
    
    # Create nodes with positions
    all_states = list(set(flow_counts['from_state']) | set(flow_counts['to_state']))
    node_map = {state: i for i, state in enumerate(all_states)}
    
    x_pos = []
    y_pos = []
    colors = []
    
    for state in all_states:
        if state in position_map:
            x, y = position_map[state]
            x_pos.append(x)
            y_pos.append(y)
        else:
            # Default position for unknown states
            x_pos.append(0.5)
            y_pos.append(0.5)
        
        # Color based on state type
        if 'Gap' in state:
            colors.append('#ff9999')
        elif 'Initial' in state or 'Intensive' in state:
            colors.append('#99ccff')
        elif 'Regular' in state or 'Extended' in state or 'Maximum' in state:
            colors.append('#99ff99')
        else:
            colors.append('#cccccc')
    
    fig = go.Figure(data=[go.Sankey(
        arrangement='fixed',  # Use our custom positions
        node=dict(
            pad=20,
            thickness=15,
            label=all_states,
            color=colors,
            x=x_pos,
            y=y_pos,
            hovertemplate='%{label}<br>%{value} total transitions<extra></extra>'
        ),
        link=dict(
            source=[node_map[row['from_state']] for _, row in flow_counts.iterrows()],
            target=[node_map[row['to_state']] for _, row in flow_counts.iterrows()],
            value=[row['count'] for _, row in flow_counts.iterrows()],
            color='rgba(150,150,150,0.3)'
        )
    )])
    
    fig.update_layout(
        title="Custom Positioned Sankey (Treatment Progression Left→Right)",
        height=600,
        font=dict(size=10)
    )
    return fig


def create_interactive_filtered_sankey(transitions_df, min_flow_percent=1.0):
    """Create Sankey with interactive flow filtering."""
    flow_counts = transitions_df.groupby(['from_state', 'to_state']).size().reset_index(name='count')
    total_flow = flow_counts['count'].sum()
    
    # Filter flows
    min_count = total_flow * (min_flow_percent / 100)
    filtered_flows = flow_counts[flow_counts['count'] >= min_count]
    
    # Create nodes
    all_states = list(set(filtered_flows['from_state']) | set(filtered_flows['to_state']))
    node_map = {state: i for i, state in enumerate(all_states)}
    
    # Calculate percentages for hover text
    flow_percentages = [(count / total_flow * 100) for count in filtered_flows['count']]
    
    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=30,
            thickness=20,
            label=all_states,
            color=['#1f77b4' if i % 2 == 0 else '#ff7f0e' for i in range(len(all_states))],
            line=dict(color="black", width=0.5)
        ),
        link=dict(
            source=[node_map[row['from_state']] for _, row in filtered_flows.iterrows()],
            target=[node_map[row['to_state']] for _, row in filtered_flows.iterrows()],
            value=[row['count'] for _, row in filtered_flows.iterrows()],
            customdata=flow_percentages,
            hovertemplate='%{source.label} → %{target.label}<br>' +
                         '%{value} patients (%{customdata:.1f}%)<extra></extra>',
            color=['rgba(31,119,180,0.4)' if p > 5 else 'rgba(255,127,14,0.4)' 
                   for p in flow_percentages]
        ),
        textfont=dict(size=11, family='Arial')
    )])
    
    fig.update_layout(
        title=f"Filtered Sankey (showing flows ≥ {min_flow_percent}% of total)",
        height=500,
        margin=dict(l=10, r=10, t=40, b=10)
    )
    return fig


def create_styled_gradient_sankey(transitions_df):
    """Create Sankey with gradient colors and enhanced styling."""
    flow_counts = transitions_df.groupby(['from_state', 'to_state']).size().reset_index(name='count')
    
    # Create nodes
    all_states = list(set(flow_counts['from_state']) | set(flow_counts['to_state']))
    node_map = {state: i for i, state in enumerate(all_states)}
    
    # Create gradient colors for links based on flow volume
    max_flow = flow_counts['count'].max()
    link_colors = []
    for count in flow_counts['count']:
        # Create gradient from light blue to dark red based on flow volume
        ratio = count / max_flow
        r = int(255 * ratio)
        b = int(255 * (1 - ratio))
        opacity = 0.3 + 0.5 * ratio  # More opaque for larger flows
        link_colors.append(f'rgba({r}, 100, {b}, {opacity})')
    
    # Node colors with gradient based on total flow through node
    node_flows = {}
    for state in all_states:
        outflow = flow_counts[flow_counts['from_state'] == state]['count'].sum()
        inflow = flow_counts[flow_counts['to_state'] == state]['count'].sum()
        node_flows[state] = outflow + inflow
    
    max_node_flow = max(node_flows.values())
    node_colors = []
    for state in all_states:
        ratio = node_flows[state] / max_node_flow
        # Gradient from light green to dark purple
        r = int(100 + 155 * (1 - ratio))
        g = int(255 * (1 - ratio))
        b = int(100 + 155 * ratio)
        node_colors.append(f'rgb({r}, {g}, {b})')
    
    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=35,
            thickness=25,
            label=[f"{state}<br>({node_flows[state]} total)" for state in all_states],
            color=node_colors,
            line=dict(
                color=['black' if node_flows[state] > max_node_flow * 0.5 else 'gray' 
                       for state in all_states],
                width=[2 if node_flows[state] > max_node_flow * 0.5 else 1 
                       for state in all_states]
            ),
            hovertemplate='<b>%{label}</b><extra></extra>'
        ),
        link=dict(
            source=[node_map[row['from_state']] for _, row in flow_counts.iterrows()],
            target=[node_map[row['to_state']] for _, row in flow_counts.iterrows()],
            value=[row['count'] for _, row in flow_counts.iterrows()],
            color=link_colors,
            hovertemplate='%{source.label} → %{target.label}<br>%{value} patients<extra></extra>'
        ),
        textfont=dict(size=10, color='white', family='Arial Black')
    )])
    
    fig.update_layout(
        title=dict(
            text="Gradient-Styled Sankey (Volume-Based Colors)",
            font=dict(size=18, color='#333')
        ),
        height=600,
        paper_bgcolor='#f5f5f5',
        plot_bgcolor='white',
        margin=dict(l=20, r=20, t=50, b=20)
    )
    return fig


def create_vertical_sankey(transitions_df):
    """Create vertical-oriented Sankey diagram."""
    flow_counts = transitions_df.groupby(['from_state', 'to_state']).size().reset_index(name='count')
    
    # Create nodes
    all_states = list(set(flow_counts['from_state']) | set(flow_counts['to_state']))
    node_map = {state: i for i, state in enumerate(all_states)}
    
    fig = go.Figure(data=[go.Sankey(
        orientation='v',  # Vertical orientation
        node=dict(
            pad=40,
            thickness=30,
            label=all_states,
            color='lightblue',
            line=dict(color="darkblue", width=2)
        ),
        link=dict(
            source=[node_map[row['from_state']] for _, row in flow_counts.iterrows()],
            target=[node_map[row['to_state']] for _, row in flow_counts.iterrows()],
            value=[row['count'] for _, row in flow_counts.iterrows()],
            color='rgba(0,0,255,0.2)'
        ),
        textfont=dict(size=12, color='darkblue')
    )])
    
    fig.update_layout(
        title="Vertical Sankey Layout",
        height=800,  # Taller for vertical layout
        width=600    # Narrower for vertical layout
    )
    return fig


def main():
    st.set_page_config(page_title="Sankey Customization Demo", layout="wide")
    
    st.title("🎨 Sankey Diagram Customization Showcase")
    st.markdown("""
    This demo shows various customization options for Sankey diagrams.
    Each example demonstrates different styling and layout possibilities.
    """)
    
    # Load sample data
    @st.cache_data
    def load_sample_data():
        # Try to load an existing simulation
        sim_dir = Path("simulation_results")
        if sim_dir.exists():
            sims = sorted(sim_dir.glob("*/metadata.json"))
            if sims:
                latest_sim = sims[-1].parent
                results = ResultsFactory.create_from_path(str(latest_sim))
                transitions_df, _ = extract_treatment_patterns_vectorized(results)
                return transitions_df
        
        # If no simulation exists, create sample data
        st.warning("No simulation data found. Using sample data.")
        return create_sample_transitions()
    
    def create_sample_transitions():
        """Create sample transition data for demo."""
        data = []
        states = [
            'Initial Treatment', 'Intensive (Monthly)', 'Regular (6-8 weeks)',
            'Extended (12+ weeks)', 'Treatment Gap (3-6 months)', 'No Further Visits'
        ]
        
        # Create realistic transitions
        transitions = [
            ('Initial Treatment', 'Intensive (Monthly)', 500),
            ('Intensive (Monthly)', 'Regular (6-8 weeks)', 400),
            ('Regular (6-8 weeks)', 'Extended (12+ weeks)', 300),
            ('Extended (12+ weeks)', 'Treatment Gap (3-6 months)', 100),
            ('Treatment Gap (3-6 months)', 'No Further Visits', 50),
            ('Regular (6-8 weeks)', 'Treatment Gap (3-6 months)', 80),
            ('Intensive (Monthly)', 'Treatment Gap (3-6 months)', 60),
        ]
        
        for from_state, to_state, count in transitions:
            for _ in range(count):
                data.append({
                    'patient_id': np.random.randint(1, 1000),
                    'from_state': from_state,
                    'to_state': to_state
                })
        
        return pd.DataFrame(data)
    
    transitions_df = load_sample_data()
    
    # Sidebar controls
    st.sidebar.header("Customization Options")
    
    demo_type = st.sidebar.selectbox(
        "Select Demo",
        ["Basic", "Custom Positions", "Interactive Filtering", 
         "Gradient Styling", "Vertical Layout", "All Demos"]
    )
    
    if demo_type == "Interactive Filtering":
        min_flow = st.sidebar.slider(
            "Minimum Flow % to Display",
            min_value=0.1,
            max_value=10.0,
            value=1.0,
            step=0.1
        )
    
    # Display selected demo(s)
    if demo_type == "All Demos":
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("1. Basic Sankey")
            fig1 = create_basic_sankey(transitions_df)
            st.plotly_chart(fig1, use_container_width=True)
            
            st.subheader("3. Interactive Filtering")
            fig3 = create_interactive_filtered_sankey(transitions_df, 1.0)
            st.plotly_chart(fig3, use_container_width=True)
            
        with col2:
            st.subheader("2. Custom Positioned")
            fig2 = create_custom_positioned_sankey(transitions_df)
            st.plotly_chart(fig2, use_container_width=True)
            
            st.subheader("4. Gradient Styling")
            fig4 = create_styled_gradient_sankey(transitions_df)
            st.plotly_chart(fig4, use_container_width=True)
        
        st.subheader("5. Vertical Layout")
        fig5 = create_vertical_sankey(transitions_df)
        st.plotly_chart(fig5, use_container_width=True)
        
    else:
        # Single demo
        if demo_type == "Basic":
            fig = create_basic_sankey(transitions_df)
        elif demo_type == "Custom Positions":
            fig = create_custom_positioned_sankey(transitions_df)
        elif demo_type == "Interactive Filtering":
            fig = create_interactive_filtered_sankey(transitions_df, min_flow)
        elif demo_type == "Gradient Styling":
            fig = create_styled_gradient_sankey(transitions_df)
        elif demo_type == "Vertical Layout":
            fig = create_vertical_sankey(transitions_df)
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Show customization code
    with st.expander("View Customization Code"):
        st.markdown("""
        ### Key Customization Parameters
        
        ```python
        # Node customization
        node=dict(
            pad=40,              # Space between nodes
            thickness=25,        # Node rectangle width
            x=[...],            # Custom x positions (0-1)
            y=[...],            # Custom y positions (0-1)
            color=[...],        # List of colors
            line=dict(
                color=[...],    # Border colors
                width=[...]     # Border widths
            ),
            hovertemplate='...' # Custom hover text
        )
        
        # Link customization
        link=dict(
            color=[...],        # Individual link colors
            customdata=[...],   # Extra data for hover
            hovertemplate='...' # Custom hover format
        )
        
        # Layout options
        arrangement='snap'      # or 'fixed', 'perpendicular'
        orientation='h'         # or 'v' for vertical
        ```
        """)
    
    # Additional tips
    st.info("""
    💡 **Tips for Sankey Customization:**
    - Use opacity in colors to show flow volume
    - Position important nodes strategically
    - Filter small flows for clarity
    - Use hover templates for detailed information
    - Consider vertical layout for time-based flows
    """)


if __name__ == "__main__":
    main()