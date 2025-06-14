"""
Experiments page for testing new visualization concepts.

This page allows exploration of different Sankey diagram layouts,
particularly focusing on meaningful positioning where discontinuations
curve downward and continuations flow horizontally.
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from pathlib import Path

from ape.components.treatment_patterns import extract_treatment_patterns_vectorized
from ape.components.treatment_patterns.pattern_analyzer_enhanced import extract_treatment_patterns_with_terminals
from ape.core.results.factory import ResultsFactory
from ape.utils.visualization_modes import get_mode_colors
from ape.utils.export_config import get_export_config, render_export_settings

# Page configuration
st.set_page_config(
    page_title="APE - Experiments",
    page_icon="🧪",
    layout="wide"
)

st.title("🧪 Visualization Experiments")
st.markdown("""
This page is for experimenting with different visualization approaches, 
particularly Sankey diagram layouts that use meaningful positioning.
""")

# Sidebar controls
st.sidebar.header("Experiment Controls")

experiment_type = st.sidebar.selectbox(
    "Select Experiment",
    [
        "Source-Colored Enhanced (Iterative)",
        "Source-Colored with Terminal Status Colors",
        "Meaningful Curves - Basic",
        "Meaningful Curves - Time-Based",
        "Stacked Outcomes View",
        "Hybrid Position/Color",
        "Custom Layout Builder"
    ]
)

# Add export settings to sidebar
render_export_settings("sidebar")

# Load simulation data
@st.cache_data
def load_latest_simulation():
    """Load the most recent simulation results."""
    sim_dir = Path("simulation_results")
    if not sim_dir.exists():
        return None
    
    # Find latest simulation
    sims = sorted(sim_dir.glob("*/metadata.json"))
    if not sims:
        return None
    
    latest_sim = sims[-1].parent
    return str(latest_sim)

# Get simulation data
sim_path = load_latest_simulation()
if not sim_path:
    st.error("No simulation data found. Please run a simulation first.")
    st.stop()

results = ResultsFactory.load_results(sim_path)

# Display simulation info
metadata = results.metadata
st.caption(f"**Simulation:** {metadata.protocol_name} • {metadata.n_patients} patients • {metadata.duration_years} years • {metadata.sim_id}")

# Try to use enhanced version with terminals, fall back to basic if needed
try:
    transitions_df, visits_df = extract_treatment_patterns_with_terminals(results)
    st.success("Using enhanced data with terminal states")
except:
    transitions_df, visits_df = extract_treatment_patterns_vectorized(results)
    st.info("Using basic transition data (no terminal states)")

# Calculate some statistics for positioning
flow_counts = transitions_df.groupby(['from_state', 'to_state']).size().reset_index(name='count')
total_patients = transitions_df['patient_id'].nunique()

st.info(f"Loaded simulation with {total_patients:,} patients and {len(flow_counts):,} unique transitions")

# Helper functions for experiments
def categorize_state(state):
    """Categorize states for positioning logic."""
    if 'No Further Visits' in state:
        return 'discontinued'
    elif 'Still in' in state:
        return 'active_end'
    elif 'Gap' in state:
        return 'gap'
    elif 'Initial' in state or 'Pre-Treatment' in state:
        return 'early'
    elif 'Intensive' in state or 'Regular' in state or 'Extended' in state or 'Maximum' in state:
        return 'active'
    elif 'Restarted' in state:
        return 'restart'
    else:
        return 'other'

def extract_time_from_state(state):
    """Extract year from terminal state names."""
    if 'Year' in state:
        try:
            year = int(state.split('Year ')[-1].split(')')[0])
            return year
        except:
            return 10
    return None

# Experiment implementations
if experiment_type == "Source-Colored Enhanced (Iterative)":
    st.header("Source-Colored Enhanced (Iterative)")
    st.markdown("""
    **Concept**: 
    - Start with the successful source-colored Sankey
    - Iteratively improve by removing elements that don't add meaning
    - First iteration: Remove Pre-Treatment node (adds no information)
    """)
    
    # Import necessary functions
    from ape.components.treatment_patterns.sankey_builder import get_treatment_state_colors
    
    # Filter out Pre-Treatment transitions
    filtered_df = transitions_df[
        (transitions_df['from_state'] != 'Pre-Treatment') & 
        (transitions_df['to_state'] != 'Pre-Treatment')
    ].copy()
    
    # Get colors from central system
    treatment_colors = get_treatment_state_colors()
    
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
    
    # Try to position terminal nodes to align with parent tops
    # First, we need to use fixed positioning
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
            label=ordered_states,
            color=[treatment_colors.get(state, "#cccccc") for state in ordered_states],
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
        textfont=dict(size=12, color='#333333', family='Arial')
    )])
    
    fig.update_layout(
        title=dict(
            text="Treatment Pattern Flow - Source-Colored (Pre-Treatment Removed)",
            font=dict(size=16)
        ),
        font=dict(size=12),
        height=600,
        margin=dict(l=10, r=150, t=40, b=40)  # Extra right margin for terminal nodes
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Show statistics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Transitions", f"{len(filtered_df):,}")
    with col2:
        st.metric("Unique Paths", len(flow_counts))
    with col3:
        removed_count = len(transitions_df) - len(filtered_df)
        st.metric("Pre-Treatment Transitions Removed", f"{removed_count:,}")
    
    with st.expander("🔄 Next Iterations to Consider"):
        st.markdown("""
        **Potential improvements for further iterations:**
        
        1. **Merge similar gap states**: Combine "Extended Gap" and "Long Gap" into a single "Prolonged Gap" category
        2. **Simplify terminal nodes**: Group "Still in X" nodes by treatment intensity level
        3. **Add time-based positioning**: Position nodes horizontally based on typical timing
        4. **Highlight critical paths**: Make the most common patient journeys more prominent
        5. **Remove rare transitions**: Hide flows representing < 0.5% of patients
        
        Each iteration should simplify while preserving clinical meaning.
        """)
    
    with st.expander("⚠️ Technical Note on Node Alignment"):
        st.markdown("""
        **Plotly Sankey Limitations:**
        
        While we've attempted to align terminal nodes with their parent nodes using fixed positioning, 
        Plotly's Sankey implementation has constraints:
        
        1. **Automatic Layout Override**: Even with `arrangement='fixed'`, Plotly may adjust positions to avoid overlaps
        2. **Node Size Considerations**: Node heights vary based on flow volume, making precise top-edge alignment difficult
        3. **Link Routing**: The algorithm prioritizes smooth flow paths over exact node positioning
        
        **Alternative Approaches:**
        - Use D3.js for full control over positioning
        - Create a custom SVG-based visualization
        - Post-process the Plotly output with JavaScript
        
        The current implementation attempts to position nodes logically, but exact alignment 
        as shown in your mockup may require a different visualization library.
        """)

# Experiment 1.5: Source-Colored with Terminal Status Colors
elif experiment_type == "Source-Colored with Terminal Status Colors":
    st.header("Source-Colored with Terminal Status Colors")
    st.markdown("""
    **Concept**: 
    - Based on the successful iterative source-colored version
    - Terminal nodes colored by their status (continuing = green, discontinued = red)
    - Maintains the visually appealing descending intensity layout
    """)
    
    # Import necessary functions
    from ape.components.treatment_patterns.sankey_builder import get_treatment_state_colors
    
    # Filter out Pre-Treatment transitions
    filtered_df = transitions_df[
        (transitions_df['from_state'] != 'Pre-Treatment') & 
        (transitions_df['to_state'] != 'Pre-Treatment')
    ].copy()
    
    # Get colors from central system
    treatment_colors = get_treatment_state_colors()
    
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
        title=dict(
            text="Treatment Pattern Flow - Terminal Status Colors (Green=Continuing, Red=Discontinued)",
            font=dict(size=16)
        ),
        font=dict(size=12),
        height=600,
        margin=dict(l=10, r=150, t=40, b=40),  # Extra right margin for terminal nodes
        annotations=[
            dict(
                text="Status at End<br>of Simulation",
                xref="paper",
                yref="paper",
                x=0.95,
                y=1.05,
                xanchor="center",
                yanchor="bottom",
                showarrow=False,
                font=dict(size=14, color="black", family="Arial"),
                align="center"
            )
        ]
    )
    
    # Use centralized export configuration
    config = get_export_config(
        filename='treatment_pattern_sankey',
        width=1400,
        height=800
    )
    
    # Display the chart
    st.plotly_chart(fig, use_container_width=True, config=config)
    
    # Show statistics with color coding
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Transitions", f"{len(filtered_df):,}")
    with col2:
        continuing = len([s for s in ordered_states if 'Still in' in s])
        st.metric("🟢 Continuing States", continuing)
    with col3:
        discontinued = 1 if 'No Further Visits' in ordered_states else 0
        st.metric("🔴 Discontinued State", discontinued)
    with col4:
        st.metric("Unique Paths", len(flow_counts))
    
    with st.expander("🎨 Color Meanings"):
        st.markdown("""
        **Terminal Node Colors:**
        - 🟢 **Green**: Patients still in treatment at end of simulation
        - 🔴 **Red**: Patients who discontinued treatment
        
        **Flow Colors:**
        - Flows inherit the color of their source state
        - Opacity indicates volume (darker = more patients)
        
        This combination shows both the treatment journey (via flow colors) 
        and the final outcome (via terminal node colors).
        """)
    
    # Add legend for abbreviations
    st.markdown("---")
    st.markdown("**Legend:**")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        **Treatment States:**
        - Initial = Initial Treatment
        - Intensive = Monthly visits
        - Regular = 6-8 week visits
        - Extended = 12+ week visits
        - Maximum = 16 week visits
        """)
    
    with col2:
        st.markdown("""
        **Other States:**
        - Restarted = Restarted After Gap
        - Irregular = Irregular Pattern
        - Discontinued = No Further Treatment
        """)
    
    with col3:
        st.markdown("""
        **Terminal States:**
        - 🟢 = Continuing treatment
        - 🔴 = Discontinued treatment
        - Right column shows status at simulation end
        """)
    
    with st.expander("📊 Understanding the Sankey Diagram"):
        st.markdown("""
        **Why are there gaps to the left of some nodes?**
        
        In a Sankey diagram, the width of each node represents the **total number of patients** 
        who pass through that state at any point during the simulation.
        
        The "gap" you see to the left occurs because:
        - Some patients remain in that state at the end of the simulation (they flow to the green terminal nodes)
        - The node width = incoming flows + patients who stay
        - This creates a visual gap showing patients "dwelling" in that state
        
        For example, if 1000 patients reach "Regular" treatment:
        - 600 might progress to "Extended"
        - 300 might remain in "Regular" at simulation end
        - 100 might discontinue
        - The node width shows all 1000, but incoming flows might only show 800
        
        This is a feature of Sankey diagrams - they show both flow and accumulation.
        """)
    
    # Show current export format
    export_format = st.session_state.get('export_format', 'png').upper()
    st.info(f"""
    💡 **Export**: Currently set to {export_format} format. Use the Export Settings in the sidebar 
    to change format. Click the 📷 camera icon on any chart to download.
    """)

# Experiment 2: Basic Meaningful Curves
elif experiment_type == "Meaningful Curves - Basic":
    st.header("Meaningful Curves - Basic Layout")
    st.markdown("""
    **Concept**: 
    - Active treatments flow horizontally in the middle band
    - Discontinuations curve downward to bottom right
    - Gaps positioned lower to suggest problems
    """)
    
    # Position nodes based on categories
    all_states = list(set(flow_counts['from_state']) | set(flow_counts['to_state']))
    node_map = {state: i for i, state in enumerate(all_states)}
    
    # Calculate positions
    positions = {}
    colors = get_mode_colors()
    
    # Y-position bands
    y_bands = {
        'early': 0.5,
        'active': 0.5,      # Middle band for active treatment
        'gap': 0.7,         # Lower for gaps
        'restart': 0.6,     # Slightly lower
        'discontinued': 0.9, # Bottom for discontinuations
        'active_end': 0.1,   # Top for still active
        'other': 0.5
    }
    
    # X-position progression
    x_progression = {
        'Pre-Treatment': 0.01,
        'Initial Treatment': 0.15,
        'Intensive (Monthly)': 0.25,
        'Regular (6-8 weeks)': 0.35,
        'Extended (12+ weeks)': 0.45,
        'Maximum Extension (16 weeks)': 0.55,
        'Treatment Gap (3-6 months)': 0.65,
        'Extended Gap (6-12 months)': 0.70,
        'Long Gap (12+ months)': 0.75,
        'Restarted After Gap': 0.40,
        'Irregular Pattern': 0.60,
        'No Further Visits': 0.95
    }
    
    x_positions = []
    y_positions = []
    node_colors = []
    
    for state in all_states:
        category = categorize_state(state)
        
        # X position
        if state in x_progression:
            x = x_progression[state]
        elif 'Still in' in state:
            x = 0.90  # Active at end
        elif 'No Further Visits' in state:
            x = 0.95  # Discontinued
        else:
            x = 0.5
        
        # Y position
        y = y_bands.get(category, 0.5)
        
        x_positions.append(x)
        y_positions.append(y)
        
        # Colors
        if category == 'discontinued':
            node_colors.append('#ff6b6b')  # Red for discontinued
        elif category == 'active_end':
            node_colors.append('#51cf66')  # Green for still active
        elif category == 'gap':
            node_colors.append('#ffd43b')  # Yellow for gaps
        else:
            node_colors.append('#4c6ef5')  # Blue for active treatment
    
    # Create Sankey
    fig = go.Figure(data=[go.Sankey(
        arrangement='fixed',
        node=dict(
            pad=30,
            thickness=20,
            label=all_states,
            color=node_colors,
            x=x_positions,
            y=y_positions,
            line=dict(color="black", width=0.5),
            hovertemplate='%{label}<br>%{value} patients<extra></extra>'
        ),
        link=dict(
            source=[node_map[row['from_state']] for _, row in flow_counts.iterrows()],
            target=[node_map[row['to_state']] for _, row in flow_counts.iterrows()],
            value=[row['count'] for _, row in flow_counts.iterrows()],
            color='rgba(150,150,150,0.3)'
        )
    )])
    
    fig.update_layout(
        title="Treatment Flow with Meaningful Positioning",
        height=700,
        margin=dict(l=10, r=10, t=40, b=40),
        annotations=[
            dict(
                text="Active Treatment Band →",
                x=0.5, y=0.5,
                xref="paper", yref="paper",
                showarrow=False,
                font=dict(size=14, color="gray"),
                opacity=0.3
            ),
            dict(
                text="Discontinuations ↓",
                x=0.95, y=0.9,
                xref="paper", yref="paper",
                showarrow=False,
                font=dict(size=12, color="red"),
                opacity=0.5
            ),
            dict(
                text="Still Active ↑",
                x=0.90, y=0.1,
                xref="paper", yref="paper",
                showarrow=False,
                font=dict(size=12, color="green"),
                opacity=0.5
            )
        ]
    )
    
    st.plotly_chart(fig, use_container_width=True)

# Experiment 2: Time-Based Layout
elif experiment_type == "Meaningful Curves - Time-Based":
    st.header("Time-Based Discontinuation Layout")
    st.markdown("""
    **Concept**: 
    - Discontinuations positioned by time (early exits left, late exits right)
    - Creates a visual "survival" curve effect
    - Still-active patients stack at top right
    """)
    
    all_states = list(set(flow_counts['from_state']) | set(flow_counts['to_state']))
    node_map = {state: i for i, state in enumerate(all_states)}
    
    x_positions = []
    y_positions = []
    node_colors = []
    node_labels = []
    
    for state in all_states:
        category = categorize_state(state)
        year = extract_time_from_state(state)
        
        # X position based on time
        if year is not None:
            # Terminal states positioned by year
            x = 0.6 + (year / 10 * 0.35)  # Spread from 0.6 to 0.95
        elif 'Pre-Treatment' in state:
            x = 0.05
        elif 'Initial' in state:
            x = 0.15
        elif 'Intensive' in state:
            x = 0.25
        elif 'Regular' in state:
            x = 0.35
        elif 'Extended' in state:
            x = 0.45
        elif 'Maximum' in state:
            x = 0.50
        else:
            x = 0.4  # Default middle position
        
        # Y position based on outcome type
        if 'No Further' in state:
            y = 0.85  # Bottom for discontinuations
        elif 'Still in' in state:
            # Stack active patients at different heights
            if 'Initial' in state:
                y = 0.15
            elif 'Intensive' in state:
                y = 0.20
            elif 'Regular' in state:
                y = 0.25
            elif 'Extended' in state:
                y = 0.30
            else:
                y = 0.35
        elif 'Gap' in state:
            y = 0.65  # Gaps in lower-middle area
        else:
            y = 0.5  # Active treatment in middle
        
        x_positions.append(x)
        y_positions.append(y)
        
        # Color by category
        if 'No Further' in state:
            node_colors.append('#e74c3c')  # Red
        elif 'Still in' in state:
            node_colors.append('#27ae60')  # Green
        elif 'Gap' in state:
            node_colors.append('#f39c12')  # Orange
        else:
            node_colors.append('#3498db')  # Blue
        
        # Simplify labels for terminal nodes
        if year is not None:
            if 'Still in' in state:
                label = f"Active Y{year}"
            else:
                label = f"Stopped Y{year}"
            node_labels.append(label)
        else:
            node_labels.append(state)
    
    fig = go.Figure(data=[go.Sankey(
        arrangement='fixed',
        node=dict(
            pad=25,
            thickness=20,
            label=node_labels,
            color=node_colors,
            x=x_positions,
            y=y_positions,
            line=dict(color="darkgray", width=0.5),
            hovertemplate='%{label}<br>%{value} patients<extra></extra>'
        ),
        link=dict(
            source=[node_map[row['from_state']] for _, row in flow_counts.iterrows()],
            target=[node_map[row['to_state']] for _, row in flow_counts.iterrows()],
            value=[row['count'] for _, row in flow_counts.iterrows()],
            color='rgba(150,150,150,0.2)'
        )
    )])
    
    fig.update_layout(
        title="Time-Based Treatment Outcomes",
        height=700,
        margin=dict(l=10, r=10, t=40, b=40),
        annotations=[
            dict(
                text="← Early in Study",
                x=0.2, y=1.05,
                xref="paper", yref="paper",
                showarrow=False,
                font=dict(size=11, color="gray")
            ),
            dict(
                text="Late in Study →",
                x=0.8, y=1.05,
                xref="paper", yref="paper",
                showarrow=False,
                font=dict(size=11, color="gray")
            ),
            dict(
                text="Still Active",
                x=0.02, y=0.25,
                xref="paper", yref="paper",
                showarrow=False,
                font=dict(size=11, color="green"),
                textangle=-90
            ),
            dict(
                text="Discontinued",
                x=0.02, y=0.85,
                xref="paper", yref="paper",
                showarrow=False,
                font=dict(size=11, color="red"),
                textangle=-90
            )
        ]
    )
    
    st.plotly_chart(fig, use_container_width=True)

# Experiment 3: Stacked Outcomes
elif experiment_type == "Stacked Outcomes View":
    st.header("Stacked Outcomes Visualization")
    st.markdown("""
    **Concept**: 
    - End states align vertically on the right
    - Creates a stacked bar effect showing final outcomes
    - Visual proportion of outcomes is immediately apparent
    """)
    
    # Calculate outcome proportions
    final_states = transitions_df[transitions_df['to_state'].str.contains('Still in|No Further')].copy()
    outcome_counts = final_states['to_state'].value_counts()
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Sankey with aligned outcomes
        all_states = list(set(flow_counts['from_state']) | set(flow_counts['to_state']))
        node_map = {state: i for i, state in enumerate(all_states)}
        
        # Position outcome nodes in a stack
        outcome_states = [s for s in all_states if 'Still in' in s or 'No Further' in s]
        other_states = [s for s in all_states if s not in outcome_states]
        
        x_positions = []
        y_positions = []
        node_colors = []
        
        # Position non-outcome states normally
        for state in all_states:
            if state in outcome_states:
                x = 0.95  # All outcomes at right edge
                # Stack them vertically
                if 'No Further' in state:
                    y = 0.8
                else:
                    # Distribute "Still in" states
                    idx = outcome_states.index(state)
                    y = 0.1 + (idx * 0.6 / len([s for s in outcome_states if 'Still in' in s]))
            else:
                # Normal positioning for other states
                x = 0.1 + (other_states.index(state) * 0.7 / len(other_states))
                y = 0.5
            
            x_positions.append(x)
            y_positions.append(y)
            
            # Colors
            if 'No Further' in state:
                node_colors.append('#ff6b6b')
            elif 'Still in' in state:
                node_colors.append('#51cf66')
            else:
                node_colors.append('#4c6ef5')
        
        fig = go.Figure(data=[go.Sankey(
            arrangement='fixed',
            node=dict(
                pad=20,
                thickness=30,
                label=all_states,
                color=node_colors,
                x=x_positions,
                y=y_positions,
                line=dict(color="black", width=1)
            ),
            link=dict(
                source=[node_map[row['from_state']] for _, row in flow_counts.iterrows()],
                target=[node_map[row['to_state']] for _, row in flow_counts.iterrows()],
                value=[row['count'] for _, row in flow_counts.iterrows()],
                color='rgba(150,150,150,0.3)'
            )
        )])
        
        fig.update_layout(
            title="Stacked Outcomes View",
            height=600,
            margin=dict(l=10, r=150, t=40, b=40)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Outcome Summary")
        for state, count in outcome_counts.items():
            pct = count / total_patients * 100
            if 'No Further' in state:
                st.metric(
                    "Discontinued",
                    f"{count:,}",
                    f"{pct:.1f}%",
                    delta_color="inverse"
                )
            else:
                st.metric(
                    "Still Active",
                    f"{count:,}",
                    f"{pct:.1f}%"
                )

# Experiment 4: Hybrid Position/Color
elif experiment_type == "Hybrid Position/Color":
    st.header("Hybrid Position & Color Encoding")
    st.markdown("""
    **Concept**: 
    - Position AND color both encode the same information (redundant encoding)
    - Vertical position: Higher = better outcomes, Lower = worse outcomes
    - Color intensity: Green = positive, Yellow = caution, Red = negative
    - Flow opacity: Thicker/darker = more patients
    """)
    
    all_states = list(set(flow_counts['from_state']) | set(flow_counts['to_state']))
    node_map = {state: i for i, state in enumerate(all_states)}
    
    # Calculate node importance (total flow through node)
    node_importance = {}
    for state in all_states:
        inflow = flow_counts[flow_counts['to_state'] == state]['count'].sum()
        outflow = flow_counts[flow_counts['from_state'] == state]['count'].sum()
        node_importance[state] = inflow + outflow
    
    max_importance = max(node_importance.values()) if node_importance else 1
    
    x_positions = []
    y_positions = []
    node_colors = []
    
    # Define color gradient based on outcome quality
    def get_outcome_color(state, category):
        """Get color based on outcome quality."""
        if 'Still in' in state:
            if 'Intensive' in state or 'Regular' in state:
                return '#00a86b'  # Jade green - best outcome
            elif 'Extended' in state:
                return '#50c878'  # Emerald green - good outcome
            else:
                return '#90ee90'  # Light green - okay outcome
        elif 'No Further' in state:
            return '#dc143c'  # Crimson - worst outcome
        elif 'Gap' in state:
            if 'Long Gap' in state:
                return '#ff6347'  # Tomato red
            elif 'Extended Gap' in state:
                return '#ff8c00'  # Dark orange
            else:
                return '#ffa500'  # Orange
        elif 'Restarted' in state:
            return '#dda0dd'  # Plum - mixed outcome
        elif category == 'active':
            return '#4169e1'  # Royal blue - active treatment
        else:
            return '#808080'  # Gray - neutral
    
    # Define Y position based on outcome quality (0=worst, 1=best)
    def get_outcome_position(state, category):
        """Get Y position based on outcome quality."""
        if 'Still in' in state:
            if 'Intensive' in state or 'Regular' in state:
                return 0.9  # Top - best outcomes
            elif 'Extended' in state:
                return 0.8
            else:
                return 0.7
        elif 'No Further' in state:
            return 0.1  # Bottom - worst outcome
        elif 'Gap' in state:
            if 'Long Gap' in state:
                return 0.2
            elif 'Extended Gap' in state:
                return 0.3
            else:
                return 0.4
        elif 'Restarted' in state:
            return 0.5
        elif category == 'active':
            return 0.6  # Active treatment in upper-middle
        elif category == 'early':
            return 0.5  # Starting position in middle
        else:
            return 0.5
    
    # Define X progression
    x_progression = {
        'Pre-Treatment': 0.05,
        'Initial Treatment': 0.15,
        'Intensive (Monthly)': 0.25,
        'Regular (6-8 weeks)': 0.35,
        'Extended (12+ weeks)': 0.45,
        'Maximum Extension (16 weeks)': 0.55,
        'Treatment Gap (3-6 months)': 0.5,
        'Extended Gap (6-12 months)': 0.55,
        'Long Gap (12+ months)': 0.6,
        'Restarted After Gap': 0.4,
        'Irregular Pattern': 0.5,
    }
    
    for state in all_states:
        category = categorize_state(state)
        
        # X position
        if state in x_progression:
            x = x_progression[state]
        elif 'Still in' in state or 'No Further' in state:
            x = 0.9  # All outcomes on right
        else:
            x = 0.5
        
        # Y position based on outcome quality
        y = get_outcome_position(state, category)
        
        # Color based on outcome quality
        color = get_outcome_color(state, category)
        
        x_positions.append(x)
        y_positions.append(y)
        node_colors.append(color)
    
    # Create link colors based on destination outcome
    link_colors = []
    for _, row in flow_counts.iterrows():
        to_category = categorize_state(row['to_state'])
        to_color = get_outcome_color(row['to_state'], to_category)
        
        # Convert hex to rgba with opacity based on flow volume
        if to_color.startswith('#'):
            hex_color = to_color.lstrip('#')
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            opacity = 0.2 + (row['count'] / flow_counts['count'].max() * 0.4)
            link_colors.append(f'rgba({r}, {g}, {b}, {opacity})')
        else:
            link_colors.append(to_color)
    
    fig = go.Figure(data=[go.Sankey(
        arrangement='fixed',
        node=dict(
            pad=30,
            thickness=20,  # Fixed thickness (Plotly limitation)
            label=all_states,
            color=node_colors,
            x=x_positions,
            y=y_positions,
            line=dict(
                color=['black' if imp > max_importance * 0.5 else 'gray' 
                       for imp in [node_importance.get(s, 0) for s in all_states]],
                width=[2 if imp > max_importance * 0.5 else 1 
                       for imp in [node_importance.get(s, 0) for s in all_states]]
            ),
            hovertemplate='%{label}<br>%{value} patients<br>Quality Score: %{customdata:.1f}<extra></extra>',
            customdata=[get_outcome_position(s, categorize_state(s)) for s in all_states]
        ),
        link=dict(
            source=[node_map[row['from_state']] for _, row in flow_counts.iterrows()],
            target=[node_map[row['to_state']] for _, row in flow_counts.iterrows()],
            value=[row['count'] for _, row in flow_counts.iterrows()],
            color=link_colors,
            hovertemplate='%{source.label} → %{target.label}<br>%{value} patients<extra></extra>'
        )
    )])
    
    fig.update_layout(
        title="Hybrid Encoding: Position + Color = Outcome Quality",
        height=800,
        margin=dict(l=60, r=60, t=60, b=60),
        annotations=[
            # Outcome quality scale on left
            dict(
                text="Best Outcomes",
                x=-0.05, y=0.9,
                xref="paper", yref="paper",
                showarrow=False,
                font=dict(size=12, color="green"),
                textangle=-90
            ),
            dict(
                text="Worst Outcomes",
                x=-0.05, y=0.1,
                xref="paper", yref="paper",
                showarrow=False,
                font=dict(size=12, color="red"),
                textangle=-90
            ),
            # Color legend
            dict(
                text="Color: Green=Good, Yellow=Caution, Red=Poor",
                x=0.5, y=-0.08,
                xref="paper", yref="paper",
                showarrow=False,
                font=dict(size=11, color="gray"),
                xanchor='center'
            ),
            dict(
                text="Position: Higher=Better, Lower=Worse",
                x=0.5, y=-0.05,
                xref="paper", yref="paper",
                showarrow=False,
                font=dict(size=11, color="gray"),
                xanchor='center'
            )
        ]
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Add explanation
    with st.expander("🎨 Understanding the Hybrid Encoding"):
        st.markdown("""
        ### Why Redundant Encoding Works
        
        This visualization uses **redundant encoding** - both position AND color convey the same information about outcome quality:
        
        **Vertical Position:**
        - 🔝 **Top** = Best outcomes (patients still in active, effective treatment)
        - 🔄 **Middle** = Mixed outcomes (gaps, restarts, irregular patterns)
        - 🔻 **Bottom** = Worst outcomes (treatment discontinuation)
        
        **Color Coding:**
        - 🟢 **Green** = Positive outcomes (active treatment)
        - 🟡 **Yellow/Orange** = Caution (treatment gaps)
        - 🔴 **Red** = Negative outcomes (discontinuation)
        
        **Benefits:**
        1. **Accessibility**: Color-blind users can rely on position
        2. **Clarity**: The message is reinforced through multiple channels
        3. **Intuitive**: Both metaphors (up=good, green=go) are culturally familiar
        4. **Memorable**: Redundant encoding improves recall
        
        **Additional Visual Elements:**
        - **Node size**: Larger = more patients flow through this state
        - **Link opacity**: Darker = more patients taking this path
        - **Border emphasis**: Thick black borders on important nodes
        """)

# Experiment 5: Custom Layout Builder
elif experiment_type == "Custom Layout Builder":
    st.header("Interactive Layout Builder")
    st.markdown("🚧 **Coming Soon**: Drag-and-drop interface to design custom Sankey layouts")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("Layout Controls")
        
        # Y-position sliders for each category
        st.markdown("### Vertical Positioning")
        active_y = st.slider("Active Treatment", 0.0, 1.0, 0.5, 0.05)
        gap_y = st.slider("Treatment Gaps", 0.0, 1.0, 0.7, 0.05)
        discontinued_y = st.slider("Discontinued", 0.0, 1.0, 0.9, 0.05)
        still_active_y = st.slider("Still Active", 0.0, 1.0, 0.1, 0.05)
        
        st.markdown("### Visual Options")
        show_annotations = st.checkbox("Show Annotations", True)
        link_style = st.radio("Link Style", ["Gradient", "Uniform", "By Volume"])
        
    with col2:
        st.info("Custom layout builder will allow interactive positioning of nodes to create the ideal visualization for your data.")

# Additional experiments can be added here...

# Show insights
with st.expander("💡 Insights from Experiments"):
    st.markdown("""
    ### Key Findings:
    
    1. **Meaningful Positioning**: 
       - Downward curves naturally suggest "falling off" treatment
       - Horizontal flows imply continuation
       - Upward curves could show improvement
    
    2. **Visual Hierarchy**:
       - Position reinforces meaning (top=good, bottom=problematic)
       - Color provides secondary information
       - Flow thickness shows volume
    
    3. **Practical Considerations**:
       - Too many nodes can still create clutter
       - May need to aggregate minor flows
       - Terminal nodes benefit from time-based positioning
    
    4. **Next Steps**:
       - Test with different data sizes
       - Get user feedback on readability
       - Consider animation possibilities
    """)

# Code examples
with st.expander("🔧 Implementation Notes"):
    st.code("""
    # Key positioning strategy
    y_bands = {
        'active': 0.5,      # Middle band
        'gap': 0.7,         # Lower (problematic)
        'discontinued': 0.9, # Bottom (exit)
        'active_end': 0.1,   # Top (success)
    }
    
    # Use fixed arrangement for control
    go.Sankey(arrangement='fixed', ...)
    
    # Position nodes explicitly
    node=dict(
        x=[...],  # 0-1 normalized
        y=[...],  # 0-1 normalized
    )
    """, language='python')