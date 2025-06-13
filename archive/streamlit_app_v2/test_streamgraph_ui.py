#!/usr/bin/env python3
"""
Test streamgraph in actual Streamlit UI to verify wedge shape.
"""

import streamlit as st
import sys
from pathlib import Path

# Add parent to path
sys.path.append(str(Path(__file__).parent))
sys.path.append(str(Path(__file__).parent.parent))

from simulation_v2.protocols.protocol_spec import ProtocolSpecification
from core.simulation_runner import SimulationRunner
from visualizations.streamgraph_treatment_states import create_treatment_state_streamgraph

st.set_page_config(page_title="Streamgraph Test", layout="wide")

st.title("Streamgraph Wedge Shape Test")

# Run simulation
if st.button("Run Test Simulation"):
    with st.spinner("Running simulation..."):
        protocol_path = Path("protocols/eylea.yaml")
        protocol_spec = ProtocolSpecification.from_yaml(protocol_path)
        
        runner = SimulationRunner(protocol_spec)
        results = runner.run(
            engine_type='abs',
            n_patients=100,
            duration_years=2.0,
            seed=456,
            show_progress=True
        )
        
        st.session_state.test_results = results
        st.success(f"Simulation complete! Saved to {results.data_path}")

# Show streamgraph
if 'test_results' in st.session_state:
    results = st.session_state.test_results
    
    st.header("Treatment State Streamgraph")
    
    # Test different views
    col1, col2 = st.columns(2)
    with col1:
        time_resolution = st.selectbox("Time Resolution", ["week", "month", "quarter"], index=1)
    with col2:
        normalize = st.checkbox("Show as Percentage", value=False)
    
    # Create streamgraph
    fig = create_treatment_state_streamgraph(
        results,
        time_resolution=time_resolution,
        normalize=normalize,
        height=600
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Show enrollment stats
    st.header("Enrollment Statistics")
    patients_df = results.get_patients_df()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Patients", len(patients_df))
    with col2:
        st.metric("Enrollment Period (days)", 
                  f"{patients_df['enrollment_time_days'].min():.0f} - {patients_df['enrollment_time_days'].max():.0f}")
    with col3:
        st.metric("Average Enrollment Rate", 
                  f"{len(patients_df) / (patients_df['enrollment_time_days'].max() / 30.44):.1f} patients/month")
    
else:
    st.info("Click 'Run Test Simulation' to generate data")