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
from core.simulation_runner import SimulationRunner
from core.monitoring.memory import MemoryMonitor
from utils.state_helpers import (
    add_simulation_to_registry, save_protocol_spec,
    set_active_simulation, list_simulation_summaries,
    get_active_simulation
)
from utils.environment import should_check_memory_limits, is_streamlit_cloud

st.set_page_config(
    page_title="Simulations", 
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

# Memory limit toggle in sidebar (only show if running locally)
with st.sidebar:
    st.markdown("### ⚙️ Settings")
    
    # Only show toggle if running locally
    if not is_streamlit_cloud():
        st.session_state['check_memory_limits'] = st.checkbox(
            "Check memory limits",
            value=st.session_state.get('check_memory_limits', False),
            help="Enable memory limit checking (automatically enabled on Streamlit Cloud)"
        )
    else:
        # Always check on Streamlit Cloud
        st.session_state['check_memory_limits'] = True
        st.info("📊 Memory limits enforced (Streamlit Cloud)")
    
    # Debug info in expander
    with st.expander("Environment Info", expanded=False):
        st.text(f"Environment: {'☁️ Cloud' if is_streamlit_cloud() else '💻 Local'}")
        st.text(f"Memory checking: {'✅ On' if st.session_state.get('check_memory_limits', should_check_memory_limits()) else '❌ Off'}")

# Top navigation
col1, col2, col3 = st.columns([1, 6, 1])
with col1:
    if top_navigation_home_button():
        st.switch_page("APE.py")
with col2:
    st.title("Simulations")
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

# Show saved simulations selector if any exist
saved_simulations = list_simulation_summaries()
if saved_simulations:
    st.markdown("---")
    st.subheader("Saved Simulations")
    
    # Create a table-like display
    cols = st.columns([3, 2, 2, 2, 2])
    cols[0].markdown("**Protocol**")
    cols[1].markdown("**Patients**")
    cols[2].markdown("**Duration**")
    cols[3].markdown("**Engine**")
    cols[4].markdown("**Actions**")
    
    for sim in saved_simulations[:5]:  # Show max 5
        cols = st.columns([3, 2, 2, 2, 2])
        cols[0].text(sim['protocol_name'])
        cols[1].text(f"{sim['n_patients']:,}")
        cols[2].text(f"{sim['duration_years']} years")
        cols[3].text(sim['engine'].upper())
        
        # View button
        if cols[4].button("View", key=f"view_{sim['sim_id']}", use_container_width=True):
            set_active_simulation(sim['sim_id'])
            st.switch_page("pages/3_Analysis_Overview.py")
    
    st.markdown("---")

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
        
        # Create simulation runner
        progress_bar.progress(20, text="Creating simulation runner...")
        runner = SimulationRunner(spec)
        
        # Check memory feasibility (optional)
        if st.session_state.get('check_memory_limits', True):
            monitor = MemoryMonitor()
            is_feasible, warning = monitor.check_simulation_feasibility(n_patients, duration_years)
            if warning:
                with st.expander("💾 Memory Check", expanded=not is_feasible):
                    if is_feasible:
                        st.warning(warning)
                    else:
                        st.error(warning)
                        if not st.checkbox("Run anyway (may cause errors)"):
                            st.stop()
        
        # Run simulation
        progress_bar.progress(30, text=f"Running {engine_type.upper()} simulation...")
        start_time = datetime.now()
        
        # Run simulation (always saves to Parquet)
        results = runner.run(
            engine_type=engine_type,
            n_patients=n_patients,
            duration_years=duration_years,
            seed=seed,
            show_progress=False  # We have our own progress bar
        )
        
        end_time = datetime.now()
        runtime = (end_time - start_time).total_seconds()
        
        progress_bar.progress(90, text="Processing results...")
        
        # Build simulation data
        simulation_data = {
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
            'memory_usage_mb': results.get_memory_usage_mb(),
            'audit_trail': runner.audit_log  # Add audit trail to simulation data
        }
        
        # Save protocol YAML content
        save_protocol_spec(simulation_data, Path(protocol_info['path']))
        
        # Add to registry with simulation ID
        sim_id = results.metadata.sim_id
        add_simulation_to_registry(sim_id, simulation_data)
        
        # Set as active simulation
        set_active_simulation(sim_id)
        
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

