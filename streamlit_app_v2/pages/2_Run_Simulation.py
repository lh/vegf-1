"""
Run Simulation - Execute simulations with selected protocols.
"""

import streamlit as st
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from simulation_v2.protocols.protocol_spec import ProtocolSpecification
from core.simulation_adapter import MemoryAwareSimulationRunner
from core.monitoring.memory import MemoryMonitor

st.set_page_config(
    page_title="Run Simulation", 
    page_icon="🦍", 
    layout="wide",
    initial_sidebar_state="expanded"  # Show sidebar for memory monitoring
)

# Add parent for utils import
sys.path.append(str(Path(__file__).parent.parent))
from utils.carbon_button_helpers import (
    top_navigation_home_button, ape_button,
    navigation_button
)

# Show memory usage in sidebar
monitor = MemoryMonitor()
monitor.display_in_sidebar()


# Top navigation
col1, col2, col3 = st.columns([1, 6, 1])
with col1:
    if top_navigation_home_button():
        st.switch_page("APE.py")
with col2:
    st.title("Run Simulation")
    st.markdown("Execute simulations using V2 engine with complete parameter tracking.")

# Check if protocol is loaded
if not st.session_state.get('current_protocol'):
    # Just show the navigation button - it's self-explanatory
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if navigation_button("Go to Protocol Manager", key="nav_protocol_missing", 
                           full_width=True, is_primary_action=True):
            st.switch_page("pages/1_Protocol_Manager.py")
    st.stop()

# Display current protocol (subtle)
protocol_info = st.session_state.current_protocol
st.caption(f"Protocol: **{protocol_info['name']}** v{protocol_info['version']}")

# Simulation parameters
st.header("Simulation Parameters")

# Preset buttons first
st.markdown("**Quick Presets**")
preset_col1, preset_col2, preset_col3, preset_col4 = st.columns(4)

with preset_col1:
    if ape_button("Small", key="preset_small", full_width=True, 
                 help_text="100 patients, 1 year"):
        st.session_state.preset_patients = 100
        st.session_state.preset_duration = 1.0
        st.rerun()

with preset_col2:
    if ape_button("Medium", key="preset_medium", full_width=True,
                 help_text="500 patients, 2 years"):
        st.session_state.preset_patients = 500
        st.session_state.preset_duration = 2.0
        st.rerun()

with preset_col3:
    if ape_button("Large", key="preset_large", full_width=True,
                 help_text="2000 patients, 5 years"):
        st.session_state.preset_patients = 2000
        st.session_state.preset_duration = 5.0
        st.rerun()

with preset_col4:
    if ape_button("Extra Large", key="preset_xl", full_width=True,
                 help_text="10000 patients, 10 years"):
        st.session_state.preset_patients = 10000
        st.session_state.preset_duration = 10.0
        st.rerun()

# More compact parameter inputs
col1, col2, col3, col4 = st.columns([1.5, 1, 1, 1.5])

with col1:
    engine_type = st.selectbox(
        "Engine",
        ["abs", "des"],
        format_func=lambda x: {"abs": "Agent-Based", "des": "Discrete Event"}[x]
    )

with col2:
    # Use preset values if available
    default_patients = st.session_state.get('preset_patients', 100)
    n_patients = st.number_input(
        "Patients",
        min_value=10,
        max_value=50000,
        value=default_patients,
        step=10
    )

with col3:
    # Use preset values if available
    default_duration = st.session_state.get('preset_duration', 2.0)
    duration_years = st.number_input(
        "Years",
        min_value=0.5,
        max_value=20.0,
        value=default_duration,
        step=0.5
    )

with col4:
    seed = st.number_input(
        "Random Seed",
        min_value=0,
        max_value=999999,
        value=42
    )

# Runtime estimate as a simple line
estimated_seconds = (n_patients * duration_years) / 1000
if estimated_seconds < 1:
    runtime_text = "short"
elif estimated_seconds < 60:
    runtime_text = f"~{estimated_seconds:.0f} seconds"
else:
    runtime_text = f"~{estimated_seconds/60:.1f} minutes"

visits_per_year = 365 / 42  # Rough estimate (6-week average)
total_visits = int(n_patients * duration_years * visits_per_year)

st.caption(f"Estimated runtime: {runtime_text} • Total visits: ~{total_visits:,}")

# Action buttons in single line with dynamic proportional sizing
st.markdown("---")

# Create a container for the buttons so we can update them
button_container = st.container()

with button_container:
    # Dynamic layout based on whether we have results
    if st.session_state.get('simulation_results'):
        # After simulation: emphasize View Analysis
        col1, col2, col3 = st.columns([1, 2, 1])
    else:
        # Before simulation: emphasize Run Simulation
        col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        # Run Simulation - changes size based on state
        run_clicked = ape_button("Run Simulation", key="run_sim_main", 
                                icon="play", full_width=True, is_primary_action=True)

    with col2:
        # View Analysis - always show but disable if no results
        has_results = st.session_state.get('simulation_results') is not None
        if ape_button("View Analysis", key="view_analysis_action", 
                     icon="chart", full_width=True, 
                     is_primary_action=has_results,
                     disabled=not has_results):
            if has_results:
                st.switch_page("pages/3_Analysis_Overview.py")

    with col3:
        # Change Protocol
        if ape_button("Protocol", key="change_protocol", 
                     full_width=True):
            st.switch_page("pages/1_Protocol_Manager.py")

if run_clicked:
    # Create progress indicators
    progress_bar = st.progress(0, text="Initializing simulation...")
    status_text = st.empty()
    
    try:
        # Load protocol spec
        progress_bar.progress(10, text="Loading protocol specification...")
        spec = ProtocolSpecification.from_yaml(Path(protocol_info['path']))
        
        # Create memory-aware runner
        progress_bar.progress(20, text="Creating memory-aware simulation runner...")
        runner = MemoryAwareSimulationRunner(spec)
        
        # Check memory before starting
        monitor = MemoryMonitor()
        suggestion = monitor.suggest_memory_optimization(n_patients, duration_years)
        if suggestion:
            with st.expander("⚠️ Memory Notice", expanded=True):
                st.warning(suggestion)
        
        # Run simulation
        progress_bar.progress(30, text=f"Running {engine_type.upper()} simulation...")
        start_time = datetime.now()
        
        # Run with memory-aware storage
        results = runner.run(
            engine_type=engine_type,
            n_patients=n_patients,
            duration_years=duration_years,
            seed=seed,
            force_parquet=False,
            show_progress=False  # We have our own progress bar
        )
        
        end_time = datetime.now()
        runtime = (end_time - start_time).total_seconds()
        
        progress_bar.progress(90, text="Processing results...")
        
        # Store memory-aware results in session state
        st.session_state.simulation_results = {
            'results': results,  # This is now a SimulationResults object
            'protocol': protocol_info,
            'parameters': {
                'engine': engine_type,
                'n_patients': n_patients,
                'duration_years': duration_years,
                'seed': seed
            },
            'runtime': runtime,
            'timestamp': datetime.now().isoformat(),
            'storage_type': results.metadata.storage_type,
            'memory_usage_mb': results.get_memory_usage_mb()
        }
        
        progress_bar.progress(100, text="Simulation complete!")
        
        # Simple success message
        st.success(f"✅ Simulation completed in {runtime:.1f} seconds")
        
        # Direct to analysis
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if ape_button("View Analysis", key="continue_analysis", 
                         icon="chart", is_primary_action=True, full_width=True):
                st.switch_page("pages/3_Analysis_Overview.py")
        
    except Exception as e:
        progress_bar.empty()
        st.error(f"❌ Simulation failed: {str(e)}")
        st.exception(e)

