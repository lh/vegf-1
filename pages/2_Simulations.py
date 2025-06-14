"""
Simulations - Run new simulations and manage existing ones.
"""

import streamlit as st
from pathlib import Path
from datetime import datetime

from simulation_v2.protocols.protocol_spec import ProtocolSpecification
from ape.core.simulation_runner import SimulationRunner
from ape.core.monitoring.memory import MemoryMonitor
from ape.core.results.factory import ResultsFactory
from ape.utils.state_helpers import (
    add_simulation_to_registry, save_protocol_spec,
    set_active_simulation, list_simulation_summaries,
    get_active_simulation
)
from ape.utils.environment import should_check_memory_limits, is_streamlit_cloud
from ape.utils.startup_redirect import handle_page_startup

st.set_page_config(
    page_title="Simulations", 
    page_icon="🦍", 
    layout="wide",
    initial_sidebar_state="expanded"  # Show sidebar for memory monitoring
)

# Check for startup redirect
handle_page_startup("simulations")

# Add parent for utils import
from ape.utils.carbon_button_helpers import (
    top_navigation_home_button, ape_button,
    navigation_button
)

# Import our new component modules
from ape.components.simulation_io import create_export_package, handle_import, render_manage_section
from ape.components.simulation_ui import (
    render_preset_buttons, render_parameter_inputs, render_runtime_estimate,
    render_control_buttons, render_recent_simulations, clear_preset_values
)
from ape.components.simulation_ui_v2 import (
    render_enhanced_parameter_inputs, render_preset_buttons_v2,
    calculate_runtime_estimate_v2
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

# Use v2 UI components for Phase 4 implementation
use_v2_ui = True  # Feature flag - set to True to enable new recruitment modes

if use_v2_ui:
    # V2: Enhanced UI with recruitment modes
    render_preset_buttons_v2()
    
    # Get all parameters including recruitment mode
    engine_type, recruitment_params, seed = render_enhanced_parameter_inputs()
    
    # Extract values for compatibility with rest of code
    if recruitment_params['mode'] == 'Fixed Total':
        n_patients = recruitment_params['n_patients']
        duration_years = recruitment_params['duration_years']
    else:
        # For constant rate mode, use expected total
        n_patients = recruitment_params.get('expected_total', 1000)
        duration_years = recruitment_params['duration_years']
    
    # Runtime estimate using v2 calculator
    runtime_estimate = calculate_runtime_estimate_v2(recruitment_params)
    st.caption(f"Estimated runtime: {runtime_estimate}")
else:
    # V1: Original UI (kept for fallback)
    render_preset_buttons()
    engine_type, n_patients, duration_years, seed = render_parameter_inputs()
    render_runtime_estimate(n_patients, duration_years)

# Section 4: Action buttons (Control Panel)
st.markdown("---")

# Control buttons
has_results = st.session_state.get('current_sim_id') is not None
run_clicked, view_analysis_clicked, protocol_clicked, manage_clicked = render_control_buttons(has_results)

# Handle button clicks
if view_analysis_clicked and has_results:
    st.switch_page("pages/3_Analysis.py")

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
    
    # Store parameters for the simulation run
    if use_v2_ui:
        st.session_state.recruitment_params = recruitment_params
    else:
        # Convert old-style parameters to recruitment params format
        st.session_state.recruitment_params = {
            'mode': 'Fixed Total',
            'n_patients': n_patients,
            'duration_years': duration_years,
            'engine_type': engine_type,
            'seed': seed
        }
    
    st.rerun()

# Check if we should be running a simulation (after rerun)
if st.session_state.get('simulation_running', False):
    # Create progress indicators
    progress_bar = st.progress(0, text="Initializing simulation...")
    status_text = st.empty()
    
    # Retrieve recruitment parameters
    recruitment_params = st.session_state.get('recruitment_params', {
        'mode': 'Fixed Total',
        'n_patients': n_patients,
        'duration_years': duration_years,
        'engine_type': engine_type,
        'seed': seed
    })
    
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
        
        # Extract values for the run
        if recruitment_params['mode'] == 'Fixed Total':
            # Fixed Total Mode
            results = runner.run(
                engine_type=recruitment_params['engine_type'],
                n_patients=recruitment_params['n_patients'],
                duration_years=recruitment_params['duration_years'],
                seed=recruitment_params['seed'],
                show_progress=False,  # We have our own progress bar
                recruitment_mode="Fixed Total"
            )
        else:
            # Constant Rate Mode - use expected total as n_patients for now
            # TODO: Update V2 engine to support true constant rate mode
            expected_total = recruitment_params.get('expected_total', 1000)
            results = runner.run(
                engine_type=recruitment_params['engine_type'],
                n_patients=expected_total,  # Use expected total
                duration_years=recruitment_params['duration_years'],
                seed=recruitment_params['seed'],
                show_progress=False,  # We have our own progress bar
                recruitment_mode="Constant Rate",
                patient_arrival_rate=recruitment_params['recruitment_rate']
            )
        
        end_time = datetime.now()
        runtime = (end_time - start_time).total_seconds()
        
        progress_bar.progress(90, text="Processing results...")
        
        # Pre-compute treatment patterns for better UI performance
        from ape.components.treatment_patterns.precompute import precompute_treatment_patterns
        progress_bar.progress(92, text="Pre-computing visualizations...")
        precompute_treatment_patterns(results, show_progress=False)
        
        progress_bar.progress(95, text="Saving results...")
        
        # Build simulation data
        simulation_data = {
            'results': results,  # This is now a SimulationResults object
            'protocol': protocol_info,
            'parameters': {
                'engine': recruitment_params['engine_type'],
                'n_patients': recruitment_params.get('n_patients', 0),
                'duration_years': recruitment_params['duration_years'],
                'seed': recruitment_params['seed'],
                'recruitment_mode': recruitment_params['mode'],
                'recruitment_rate': recruitment_params.get('recruitment_rate'),
                'rate_unit': recruitment_params.get('rate_unit'),
                'expected_total': recruitment_params.get('expected_total')
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