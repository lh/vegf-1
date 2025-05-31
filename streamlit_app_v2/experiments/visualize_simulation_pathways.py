#!/usr/bin/env python3
"""
Visualize patient pathways from actual simulation results.

This script loads real simulation data and creates Sankey diagrams showing
patient journeys through treatment states.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path
import json
from collections import defaultdict
import sys
from datetime import datetime

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
    "Monitoring": "#ffd700",
    "Retreatment": "#ff9500",
    
    # Gap-based states
    "Off Treatment (Gap)": "#ffc0cb",
    "Treatment Gap": "#ffb6c1", 
    "Extended Interval": "#ffd700",
    
    # Discontinuation states
    "Discontinued": "#ff6b6b",
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


def extract_patient_transitions(results):
    """Extract state transitions from actual simulation results."""
    transitions = []
    DAYS_PER_MONTH = 365.25 / 12
    
    # Check if this is a ParquetResults object
    if hasattr(results, 'iterate_patients'):
        # Use the ParquetResults iterator
        for patient_batch in results.iterate_patients(batch_size=100):
            for patient in patient_batch:
                process_patient_transitions(patient, transitions, DAYS_PER_MONTH)
    else:
        # Try to handle as a dict-based format
        if hasattr(results, 'raw_results'):
            patient_data = results.raw_results.get('patient_histories', {})
        else:
            patient_data = results.get('patient_histories', {})
            
        for patient_id, patient in patient_data.items():
            if isinstance(patient, dict):
                patient['patient_id'] = patient_id
            process_patient_transitions(patient, transitions, DAYS_PER_MONTH)
    
    return pd.DataFrame(transitions)


def process_patient_transitions(patient, transitions, DAYS_PER_MONTH):
    """Process transitions for a single patient."""
    # Get patient ID
    if isinstance(patient, dict):
        patient_id = patient.get('patient_id')
        visits = patient.get('visits', [])
        discontinued = patient.get('discontinued', False)
        discontinuation_time = patient.get('discontinuation_time')
    else:
        patient_id = getattr(patient, 'patient_id', None)
        visits = getattr(patient, 'visits', [])
        discontinued = getattr(patient, 'discontinued', False)
        discontinuation_time = getattr(patient, 'discontinuation_time', None)
    
    if not patient_id:
        return
        
    if len(visits) < 2:
        # Still process if only one visit (initial state)
        if len(visits) == 1:
            transitions.append({
                'patient_id': patient_id,
                'from_state': 'Initial',
                'to_state': 'Active',
                'from_time_days': 0,
                'to_time_days': 0,
                'from_time': 0,
                'to_time': 0,
                'duration_days': 0,
                'duration': 0
            })
        return
    
    # Track state changes
    prev_state = "Initial"
    prev_time_days = 0
    
    for i, visit in enumerate(visits):
        # Extract time
        if hasattr(visit, 'time_days'):
            time_days = visit.time_days
        elif isinstance(visit, dict):
            time_days = visit.get('time_days', visit.get('day', visit.get('visit_day', i * 30)))
        else:
            time_days = i * 30
        
        # Determine current state based on visit data
        current_state = determine_patient_state(visit, visits, i)
        
        # Record transition if state changed
        if current_state != prev_state:
            transitions.append({
                'patient_id': patient_id,
                'from_state': prev_state,
                'to_state': current_state,
                'from_time_days': prev_time_days,
                'to_time_days': time_days,
                'from_time': prev_time_days / DAYS_PER_MONTH,
                'to_time': time_days / DAYS_PER_MONTH,
                'duration_days': time_days - prev_time_days,
                'duration': (time_days - prev_time_days) / DAYS_PER_MONTH
            })
            prev_state = current_state
            prev_time_days = time_days
    
    # Add final state if discontinued
    if discontinued and discontinuation_time is not None:
        # Find the discontinuation reason from the last visit
        discontinuation_reason = "unknown"
        for visit in reversed(visits):
            if isinstance(visit, dict):
                reason = visit.get('discontinuation_reason')
            else:
                reason = getattr(visit, 'discontinuation_reason', None)
            if reason:
                discontinuation_reason = reason
                break
        
        final_state = f"Discontinued ({discontinuation_reason})"
        if final_state != prev_state:
            transitions.append({
                'patient_id': patient_id,
                'from_state': prev_state,
                'to_state': final_state,
                'from_time_days': prev_time_days,
                'to_time_days': discontinuation_time * DAYS_PER_MONTH if discontinuation_time else prev_time_days,
                'from_time': prev_time_days / DAYS_PER_MONTH,
                'to_time': discontinuation_time if discontinuation_time else prev_time_days / DAYS_PER_MONTH,
                'duration_days': 0,
                'duration': 0
            })
    elif prev_state != "Completed":
        # Add completion state
        transitions.append({
            'patient_id': patient_id,
            'from_state': prev_state,
            'to_state': "Completed",
            'from_time_days': prev_time_days,
            'to_time_days': time_days,
            'from_time': prev_time_days / DAYS_PER_MONTH,
            'to_time': time_days / DAYS_PER_MONTH,
            'duration_days': 0,
            'duration': 0
        })


def determine_patient_state(visit, all_visits, visit_index):
    """Determine patient state from visit data."""
    # Check for discontinuation
    if hasattr(visit, 'discontinuation_reason') and visit.discontinuation_reason:
        return f"Discontinued ({visit.discontinuation_reason})"
    elif isinstance(visit, dict) and visit.get('discontinuation_reason'):
        return f"Discontinued ({visit['discontinuation_reason']})"
    
    # Check monitoring status
    if hasattr(visit, 'monitoring_only') and visit.monitoring_only:
        return "Monitoring"
    elif isinstance(visit, dict) and visit.get('monitoring_only'):
        return "Monitoring"
    
    # Check treatment interval
    if hasattr(visit, 'interval_days'):
        interval = visit.interval_days
    elif isinstance(visit, dict):
        interval = visit.get('interval_days', visit.get('current_interval_days', 28))
    else:
        interval = 28
    
    # Categorize by interval
    if interval >= 112:  # 16 weeks
        return "Stable (Max Interval)"
    elif interval >= 84:  # 12 weeks
        return "Stable"
    else:
        return "Active"


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
    st.set_page_config(page_title="Patient Pathway Visualization", layout="wide")
    
    st.title("🔀 Patient Pathway Visualization")
    st.markdown("Visualizing actual patient journeys from simulation results")
    
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
            
            # Extract transitions
            with st.spinner("Extracting patient transitions..."):
                transitions_df = extract_patient_transitions(results)
            
            if len(transitions_df) == 0:
                st.error("No transitions found in simulation data")
                st.info("Debug info:")
                st.write(f"Results type: {type(results)}")
                st.write(f"Has iterate_patients: {hasattr(results, 'iterate_patients')}")
                if hasattr(results, 'metadata'):
                    st.write(f"Metadata: {results.metadata}")
                st.stop()
                
            st.success(f"Loaded {len(transitions_df)} transitions")
            
            # Show transition summary
            st.subheader("Transition Summary")
            unique_states = set(transitions_df['from_state'].unique()) | set(transitions_df['to_state'].unique())
            st.metric("Unique States", len(unique_states))
            
            # Count discontinuations
            disc_count = len(transitions_df[transitions_df['to_state'].str.contains('Discontinued')])
            st.metric("Discontinuations", disc_count)
            
        except Exception as e:
            st.error(f"Error loading simulation: {str(e)}")
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
        
        fig1 = create_patient_flow_sankey(transitions_df)
        st.plotly_chart(fig1, use_container_width=True)
        
    with tab2:
        st.subheader("Discontinuation Pathways")
        st.markdown("""
        This visualization focuses on which states lead to different types of
        discontinuation, helping identify critical decision points in the treatment journey.
        """)
        
        fig2 = create_discontinuation_analysis(transitions_df)
        st.plotly_chart(fig2, use_container_width=True)
        
    with tab3:
        st.subheader("Transition Statistics")
        
        # Most common transitions
        st.markdown("### Most Common Transitions")
        top_transitions = transitions_df.groupby(['from_state', 'to_state']).size()\
            .reset_index(name='count').sort_values('count', ascending=False).head(10)
        
        st.dataframe(top_transitions, use_container_width=True)
        
        # State duration analysis
        st.markdown("### Average Time in Each State")
        state_durations = transitions_df.groupby('from_state')['duration'].agg(['mean', 'median', 'count'])\
            .round(1).sort_values('mean', ascending=False)
        
        st.dataframe(state_durations, use_container_width=True)
        
        # Discontinuation breakdown
        disc_transitions = transitions_df[transitions_df['to_state'].str.contains('Discontinued')]
        if len(disc_transitions) > 0:
            st.markdown("### Discontinuation Types")
            disc_types = disc_transitions['to_state'].value_counts()
            st.bar_chart(disc_types)


if __name__ == "__main__":
    main()