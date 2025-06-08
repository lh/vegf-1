"""
Simulations - Run new simulations and manage existing ones.
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
from core.results.factory import ResultsFactory
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

# Import our new component modules
from components.simulation_io import create_export_package, handle_import, render_manage_section
from components.simulation_ui import (
    render_preset_buttons, render_parameter_inputs, render_runtime_estimate,
    render_control_buttons, render_recent_simulations, clear_preset_values
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
with col3:
    # Display ape logo - closed eyes if simulation is running
    if st.session_state.get('simulation_running', False):
        st.image("assets/closed_eyes_ape.svg", width=80)
    else:
        st.image("assets/ape_logo.svg", width=80)

# Check if protocol is loaded first
if not st.session_state.get('current_protocol'):
    st.header("New")
    st.info("Select a protocol first to run a simulation.")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if navigation_button("Go to Protocol Manager", key="nav_protocol_missing", 
                           full_width=True, is_primary_action=True):
            st.switch_page("pages/1_Protocol_Manager.py")
    st.stop()

# Section 3: Run New Simulation
st.header("New")

# Display current protocol (subtle)
protocol_info = st.session_state.current_protocol
st.caption(f"Protocol: **{protocol_info['name']}** v{protocol_info['version']}")

# Simulation parameters
st.subheader("Simulation Parameters")

# Preset buttons
render_preset_buttons()

# Parameter inputs
engine_type, n_patients, duration_years, seed = render_parameter_inputs()

# Runtime estimate
render_runtime_estimate(n_patients, duration_years)

# Section 4: Action buttons (Control Panel)
st.markdown("---")

# Control buttons
has_results = st.session_state.get('current_sim_id') is not None
run_clicked, view_analysis_clicked, protocol_clicked, manage_clicked = render_control_buttons(has_results)

# Handle button clicks
if view_analysis_clicked and has_results:
    st.switch_page("pages/3_Analysis_Overview.py")

if protocol_clicked:
    st.switch_page("pages/1_Protocol_Manager.py")

if manage_clicked:
    st.session_state.show_manage = not st.session_state.get('show_manage', False)

# Show manage panel if toggled
if st.session_state.get('show_manage', False):
    # Make the manage section 1/4 width by using columns
    manage_cols = st.columns([3, 1])  # 3:1 ratio gives us the rightmost quarter
    with manage_cols[1]:
        render_manage_section()

# Handle Run Simulation click
if run_clicked:
    # Set simulation running state to show closed eyes ape
    st.session_state.simulation_running = True
    st.rerun()

# Check if we should be running a simulation (after rerun)
if st.session_state.get('simulation_running', False):
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
        
        # Clear preset values after successful simulation
        clear_preset_values()
        
        progress_bar.progress(100, text="Simulation complete!")
        
        # Clear simulation running state
        st.session_state.simulation_running = False
        
        # Simple success message
        st.success(f"Simulation completed in {runtime:.1f} seconds")
        
        # Reload to show in recent simulations
        st.rerun()
        
    except Exception as e:
        progress_bar.empty()
        # Clear simulation running state on error
        st.session_state.simulation_running = False
        st.error(f"Simulation failed: {str(e)}")
        st.exception(e)

# Section 1: Recent Simulations List
st.markdown("---")
render_recent_simulations()