#!/usr/bin/env python3
"""
Fast vectorized version of patient pathway visualization.

Uses pandas operations instead of loops for better performance with large datasets.
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


# Color scheme for states
STATE_COLORS = {
    "Initial": "#e6f2ff",
    "Active": "#4a90e2", 
    "Stable": "#7fba00",
    "Stable (Max Interval)": "#5c8a00",
    "Highly Active": "#1a5490",  # Darker blue for highly active
    "Monitoring": "#ffd700",
    "Retreatment": "#ff9500",
    
    # Gap-based states
    "Off Treatment (Gap)": "#ffc0cb",
    "Treatment Gap": "#ffb6c1", 
    "Extended Interval": "#ffd700",
    
    # Discontinuation states - V2 categories
    "Discontinued": "#ff6b6b",
    "Discontinued (planned)": "#90ee90",  # Same as stable_max_interval
    "Discontinued (stable_max_interval)": "#90ee90",
    "Discontinued (system_discontinuation)": "#ff6b6b",
    "Discontinued (reauthorization_failure)": "#ff9999",
    "Discontinued (premature)": "#ffb366",
    "Discontinued (poor_response)": "#cc0000",
    "Discontinued (mortality)": "#333333",
    
    "Completed": "#b8b8b8"
}


def get_available_simulations():
    """Get list of available simulation results."""
    results_dir = Path(__file__).parent.parent / "simulation_results"
    simulations = []
    
    if results_dir.exists():
        for sim_dir in sorted(results_dir.iterdir(), reverse=True):
            if sim_dir.is_dir() and sim_dir.name.startswith("sim_"):
                metadata_file = sim_dir / "metadata.json"
                if metadata_file.exists():
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)
                    # Get duration in months
                    duration_years = metadata.get('duration_years', 0)
                    duration_months = int(duration_years * 12) if duration_years else metadata.get('simulation_months', 0)
                    
                    simulations.append({
                        'id': sim_dir.name,
                        'date': metadata.get('timestamp', metadata.get('simulation_date', 'Unknown')),
                        'patients': metadata.get('n_patients', 0),
                        'duration': duration_months,
                        'path': sim_dir
                    })
    
    return simulations


def extract_transitions_vectorized(results):
    """Extract patient transitions using vectorized operations."""
    DAYS_PER_MONTH = 365.25 / 12
    
    # For ParquetResults, use the efficient DataFrame methods
    if hasattr(results, 'get_visits_df'):
        st.info("Using vectorized extraction from Parquet data...")
        start_time = time.time()
        
        # Get all visits as DataFrame
        visits_df = results.get_visits_df()
        
        # Sort by patient and time
        visits_df = visits_df.sort_values(['patient_id', 'time_days'])
        
        # Add visit number for each patient
        visits_df['visit_num'] = visits_df.groupby('patient_id').cumcount()
        
        # Determine state for each visit
        visits_df['state'] = determine_states_vectorized(visits_df)
        
        # Create previous state column using shift
        visits_df['prev_state'] = visits_df.groupby('patient_id')['state'].shift(1)
        visits_df['prev_time_days'] = visits_df.groupby('patient_id')['time_days'].shift(1)
        
        # First visit for each patient starts from Initial
        first_visits = visits_df['visit_num'] == 0
        visits_df.loc[first_visits, 'prev_state'] = 'Initial'
        visits_df.loc[first_visits, 'prev_time_days'] = 0
        
        # Filter to only state changes
        state_changes = visits_df[visits_df['state'] != visits_df['prev_state']].copy()
        
        # Create transitions DataFrame
        transitions_df = pd.DataFrame({
            'patient_id': state_changes['patient_id'],
            'from_state': state_changes['prev_state'],
            'to_state': state_changes['state'],
            'from_time_days': state_changes['prev_time_days'],
            'to_time_days': state_changes['time_days'],
            'from_time': state_changes['prev_time_days'] / DAYS_PER_MONTH,
            'to_time': state_changes['time_days'] / DAYS_PER_MONTH,
            'duration_days': state_changes['time_days'] - state_changes['prev_time_days'],
            'duration': (state_changes['time_days'] - state_changes['prev_time_days']) / DAYS_PER_MONTH
        })
        
        # Add final transitions for completed/discontinued patients
        # Get last visit for each patient
        last_visits = visits_df.groupby('patient_id').last().reset_index()
        
        # Check if patient discontinued
        patients_df = pd.read_parquet(results.data_path / 'patients.parquet')
        
        # Check which columns are available
        patient_cols = ['patient_id', 'discontinued']
        if 'discontinuation_reason' in patients_df.columns:
            patient_cols.append('discontinuation_reason')
        elif 'discontinuation_type' in patients_df.columns:
            patient_cols.append('discontinuation_type')
            patients_df['discontinuation_reason'] = patients_df['discontinuation_type']
        else:
            # Create a default column
            patients_df['discontinuation_reason'] = 'unknown'
            patient_cols.append('discontinuation_reason')
        
        last_visits = last_visits.merge(
            patients_df[patient_cols], 
            on='patient_id', 
            how='left'
        )
        
        # Add final transitions - vectorized approach
        # Create final state column
        last_visits['final_state'] = 'Completed'
        
        # Set discontinued states
        disc_mask = last_visits['discontinued'] == True
        if 'discontinuation_reason' in last_visits.columns:
            last_visits.loc[disc_mask, 'final_state'] = last_visits.loc[disc_mask, 'discontinuation_reason'].apply(
                lambda x: f"Discontinued ({x})" if pd.notna(x) else "Discontinued"
            )
        else:
            last_visits.loc[disc_mask, 'final_state'] = 'Discontinued'
        
        # Only add transitions where final state differs from current state
        needs_final = last_visits[last_visits['final_state'] != last_visits['state']]
        
        if len(needs_final) > 0:
            final_transitions = pd.DataFrame({
                'patient_id': needs_final['patient_id'],
                'from_state': needs_final['state'],
                'to_state': needs_final['final_state'],
                'from_time_days': needs_final['time_days'],
                'to_time_days': needs_final['time_days'],
                'from_time': needs_final['time_days'] / DAYS_PER_MONTH,
                'to_time': needs_final['time_days'] / DAYS_PER_MONTH,
                'duration_days': 0,
                'duration': 0
            })
            
            transitions_df = pd.concat([transitions_df, final_transitions], ignore_index=True)
        
        elapsed = time.time() - start_time
        st.success(f"Extracted {len(transitions_df)} transitions in {elapsed:.1f} seconds")
        
        return transitions_df
        
    else:
        # Fallback to iterative approach for other formats
        st.warning("Using iterative extraction (slower)...")
        from visualize_simulation_pathways import extract_patient_transitions
        return extract_patient_transitions(results)


def determine_states_vectorized(visits_df):
    """Determine patient states using vectorized operations."""
    states = pd.Series('Active', index=visits_df.index)
    
    # Check disease states if available
    if 'disease_state' in visits_df.columns:
        # Map disease states to our state names
        # Handle both string and enum representations
        disease_state_map = {
            'NAIVE': 'Initial',
            'STABLE': 'Stable', 
            'ACTIVE': 'Active',
            'HIGHLY_ACTIVE': 'Highly Active',
            'DiseaseState.NAIVE': 'Initial',
            'DiseaseState.STABLE': 'Stable',
            'DiseaseState.ACTIVE': 'Active', 
            'DiseaseState.HIGHLY_ACTIVE': 'Highly Active'
        }
        
        # Convert disease states to string for mapping
        visits_df['disease_state_str'] = visits_df['disease_state'].astype(str)
        
        # Apply mapping
        for disease_state, state_name in disease_state_map.items():
            mask = visits_df['disease_state_str'] == disease_state
            states[mask] = state_name
    
    # Check for discontinuation visits
    if 'is_discontinuation_visit' in visits_df.columns:
        disc_mask = visits_df['is_discontinuation_visit'] == True
        if 'discontinuation_reason' in visits_df.columns:
            states[disc_mask] = visits_df.loc[disc_mask, 'discontinuation_reason'].apply(
                lambda x: f"Discontinued ({x})" if pd.notna(x) else "Discontinued"
            )
        else:
            states[disc_mask] = 'Discontinued'
    
    # Check for monitoring only
    if 'monitoring_only' in visits_df.columns:
        monitoring_mask = (visits_df['monitoring_only'] == True) & ~states.str.contains('Discontinued')
        states[monitoring_mask] = 'Monitoring'
    
    # Check retreatment
    if 'is_retreatment_visit' in visits_df.columns:
        retreat_mask = visits_df['is_retreatment_visit'] == True
        states[retreat_mask] = 'Retreatment'
    
    # Check interval-based states (override disease state if at max interval)
    if 'next_interval_days' in visits_df.columns:
        # Use next_interval_days instead of interval_days
        max_interval_mask = (visits_df['next_interval_days'] >= 112) & ~states.str.contains('Discontinued|Monitoring|Retreatment')
        states[max_interval_mask] = 'Stable (Max Interval)'
    elif 'interval_days' in visits_df.columns:
        # Fallback to interval_days
        max_interval_mask = (visits_df['interval_days'] >= 112) & ~states.str.contains('Discontinued|Monitoring|Retreatment')
        states[max_interval_mask] = 'Stable (Max Interval)'
    
    return states


def create_patient_flow_sankey(transitions_df):
    """Create a Sankey diagram showing patient state transitions."""
    # Aggregate transitions
    flow_counts = transitions_df.groupby(['from_state', 'to_state']).size().reset_index(name='count')
    
    # Filter out small flows for clarity
    min_flow_size = max(1, len(transitions_df) * 0.001)  # 0.1% threshold
    flow_counts = flow_counts[flow_counts['count'] >= min_flow_size]
    
    # Create nodes
    nodes = []
    node_map = {}
    
    for _, row in flow_counts.iterrows():
        for state in [row['from_state'], row['to_state']]:
            if state not in node_map:
                node_map[state] = len(nodes)
                nodes.append({
                    'label': state,
                    'color': STATE_COLORS.get(state, "#cccccc")
                })
    
    # Create Sankey
    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=30,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=[n['label'] for n in nodes],
            color=[n['color'] for n in nodes]
        ),
        link=dict(
            source=[node_map[row['from_state']] for _, row in flow_counts.iterrows()],
            target=[node_map[row['to_state']] for _, row in flow_counts.iterrows()],
            value=[row['count'] for _, row in flow_counts.iterrows()],
            color="rgba(100, 100, 100, 0.2)"
        ),
        textfont=dict(size=11, color='black', family='Arial')
    )])
    
    fig.update_layout(
        title=dict(
            text="Patient State Transitions",
            font=dict(size=16)
        ),
        font=dict(size=12),
        height=800,
        margin=dict(l=20, r=20, t=60, b=20)
    )
    
    return fig


def create_discontinuation_analysis(transitions_df):
    """Create visualization focused on discontinuation patterns."""
    # Find all discontinuation transitions
    disc_transitions = transitions_df[
        transitions_df['to_state'].str.contains('Discontinued')
    ].copy()
    
    if len(disc_transitions) == 0:
        fig = go.Figure()
        fig.add_annotation(
            text="No discontinuations found in this simulation",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16)
        )
        return fig
    
    # Group by discontinuation type
    disc_transitions['disc_type'] = disc_transitions['to_state'].str.extract(r'Discontinued \((.*?)\)')
    disc_summary = disc_transitions.groupby(['from_state', 'disc_type']).size().reset_index(name='count')
    
    # Create Sankey for discontinuation flows
    nodes = []
    node_map = {}
    
    # Add source states
    for state in disc_summary['from_state'].unique():
        node_map[state] = len(nodes)
        nodes.append({
            'label': state,
            'color': STATE_COLORS.get(state, "#cccccc")
        })
    
    # Add discontinuation types
    for disc_type in disc_summary['disc_type'].unique():
        label = f"Discontinued ({disc_type})"
        node_map[label] = len(nodes)
        nodes.append({
            'label': label,
            'color': STATE_COLORS.get(label, "#ff6b6b")
        })
    
    # Create flows
    flows = []
    for _, row in disc_summary.iterrows():
        flows.append({
            'source': node_map[row['from_state']],
            'target': node_map[f"Discontinued ({row['disc_type']})"],
            'value': row['count']
        })
    
    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=40,
            thickness=25,
            line=dict(color="black", width=0.5),
            label=[n['label'] for n in nodes],
            color=[n['color'] for n in nodes]
        ),
        link=dict(
            source=[f['source'] for f in flows],
            target=[f['target'] for f in flows],
            value=[f['value'] for f in flows],
            color="rgba(100, 100, 100, 0.2)"
        ),
        textfont=dict(size=11, color='black', family='Arial')
    )])
    
    fig.update_layout(
        title=dict(
            text="Pathways to Discontinuation",
            font=dict(size=16)
        ),
        font=dict(size=12),
        height=700,
        margin=dict(l=20, r=20, t=60, b=20)
    )
    
    return fig


def main():
    """Main Streamlit app."""
    st.set_page_config(page_title="Patient Pathway Visualization (Fast)", layout="wide")
    
    st.title("🚀 Fast Patient Pathway Visualization")
    st.markdown("Vectorized visualization of patient journeys from simulation results")
    
    # Sidebar
    with st.sidebar:
        st.header("Select Simulation")
        
        # Get available simulations
        simulations = get_available_simulations()
        
        if not simulations:
            st.error("No simulation results found!")
            st.info("Run a simulation first using the main Streamlit app")
            st.stop()
        
        # Select simulation
        sim_options = [f"{sim['id']} ({sim['patients']} patients, {sim['duration']}m)" 
                      for sim in simulations]
        selected_idx = st.selectbox(
            "Choose simulation",
            range(len(sim_options)),
            format_func=lambda x: sim_options[x]
        )
        
        selected_sim = simulations[selected_idx]
        
        # Show simulation details
        st.subheader("Simulation Details")
        st.metric("Simulation ID", selected_sim['id'])
        st.metric("Date", selected_sim['date'])
        st.metric("Patients", selected_sim['patients'])
        st.metric("Duration", f"{selected_sim['duration']} months")
        
        # Load simulation data
        try:
            results = ResultsFactory.load_results(selected_sim['path'])
            
            # Extract transitions using vectorized approach
            overall_start = time.time()
            transitions_df = extract_transitions_vectorized(results)
            
            if len(transitions_df) == 0:
                st.error("No transitions found in simulation data")
                st.stop()
                
            st.success(f"Loaded {len(transitions_df):,} transitions")
            
            # Show transition summary
            st.subheader("Transition Summary")
            unique_states = set(transitions_df['from_state'].unique()) | set(transitions_df['to_state'].unique())
            st.metric("Unique States", len(unique_states))
            
            # Count discontinuations
            disc_count = len(transitions_df[transitions_df['to_state'].str.contains('Discontinued')])
            st.metric("Discontinuations", f"{disc_count:,}")
            
            overall_elapsed = time.time() - overall_start
            st.info(f"Total processing time: {overall_elapsed:.1f}s")
            
        except Exception as e:
            st.error(f"Error loading simulation: {str(e)}")
            import traceback
            st.code(traceback.format_exc())
            st.stop()
    
    # Main content
    tab1, tab2, tab3 = st.tabs([
        "📊 Patient Flow Overview",
        "🎯 Discontinuation Analysis",
        "📈 Transition Statistics"
    ])
    
    with tab1:
        st.subheader("Overall Patient State Transitions")
        st.markdown("""
        This Sankey diagram shows how patients flow through different treatment states
        during the simulation. The width of the flows indicates the number of patients
        making each transition.
        """)
        
        with st.spinner("Creating Sankey diagram..."):
            start = time.time()
            fig1 = create_patient_flow_sankey(transitions_df)
            elapsed = time.time() - start
            st.info(f"Sankey created in {elapsed:.1f}s")
        
        st.plotly_chart(fig1, use_container_width=True)
        
    with tab2:
        st.subheader("Discontinuation Pathways")
        st.markdown("""
        This visualization focuses on which states lead to different types of
        discontinuation, helping identify critical decision points in the treatment journey.
        """)
        
        with st.spinner("Creating discontinuation analysis..."):
            fig2 = create_discontinuation_analysis(transitions_df)
        
        st.plotly_chart(fig2, use_container_width=True)
        
    with tab3:
        st.subheader("Transition Statistics")
        
        # Most common transitions
        st.markdown("### Most Common Transitions")
        top_transitions = transitions_df.groupby(['from_state', 'to_state']).size()\
            .reset_index(name='count').sort_values('count', ascending=False).head(10)
        
        st.dataframe(top_transitions, use_container_width=True)
        
        # State duration analysis - vectorized
        st.markdown("### Average Time in Each State")
        state_durations = transitions_df.groupby('from_state').agg({
            'duration': ['mean', 'median'],
            'patient_id': 'count'
        }).round(1)
        state_durations.columns = ['Mean (months)', 'Median (months)', 'Count']
        state_durations = state_durations.sort_values('Mean (months)', ascending=False)
        
        st.dataframe(state_durations, use_container_width=True)
        
        # Discontinuation breakdown
        disc_transitions = transitions_df[transitions_df['to_state'].str.contains('Discontinued')]
        if len(disc_transitions) > 0:
            st.markdown("### Discontinuation Types")
            disc_types = disc_transitions['to_state'].value_counts()
            st.bar_chart(disc_types)


if __name__ == "__main__":
    main()