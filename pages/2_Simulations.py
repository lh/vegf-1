"""
Simulations - Run new simulations and manage existing ones.
"""

import streamlit as st
from pathlib import Path
from datetime import datetime
import time
import threading
import logging

# Suppress Streamlit thread context warnings
logging.getLogger('streamlit.runtime.scriptrunner_utils.script_run_context').setLevel(logging.ERROR)

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
    initial_sidebar_state="collapsed"  # Start with sidebar hidden
)

# Check for startup redirect
handle_page_startup("simulations")

# Add parent for utils import
from ape.utils.carbon_button_helpers import (
    ape_button,
    navigation_button
)

# Import UI components
from ape.components.ui.workflow_indicator import workflow_progress_indicator
from ape.components.ui.quick_start_box import quick_start_box

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

# Check if protocol is loaded first
if not st.session_state.get('current_protocol'):
    # Show workflow progress first
    workflow_progress_indicator("simulation")
    
    st.info("Select a protocol first to run a simulation.")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if navigation_button("Go to Protocol Manager", key="nav_protocol_missing", 
                           full_width=True, is_primary_action=True):
            st.switch_page("pages/1_Protocol_Manager.py")
    st.stop()

# Protocol is loaded, get info
protocol_info = st.session_state.current_protocol

# We'll define the actual run_simulation function later, but need a placeholder for now
# This will be updated after we have the recruitment parameters
if 'run_simulation_action' not in st.session_state:
    st.session_state.run_simulation_action = lambda: st.warning("Please wait for parameters to load...")

# Show workflow progress at the top with the action callback
has_results = st.session_state.get('current_sim_id') is not None
workflow_progress_indicator("simulation", on_current_action=st.session_state.run_simulation_action, has_results=has_results)

# Don't display protocol separately - it will be shown in the quick start box

# Show memory usage in sidebar
monitor = MemoryMonitor()
monitor.display_in_sidebar()

# Memory limit toggle in sidebar (only show if running locally)
with st.sidebar:
    st.markdown("### Settings")
    
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
        st.info("Memory limits enforced (Streamlit Cloud)")
    

# Initialize with default preset if this is the first time on the page
if 'preset_initialized' not in st.session_state:
    st.session_state.preset_initialized = True
    st.session_state.preset_patients = 500
    st.session_state.preset_duration = 3
    st.session_state.recruitment_mode = "Fixed Total"


# Define presets for Quick Start box
presets = {
    'small': {
        'label': 'Small',
        'description': 'Quick test run',
        'patients': 100,
        'duration': 2.0,
        'runtime': '< 1 second'
    },
    'default': {
        'label': 'Default',
        'description': 'Standard analysis',
        'patients': 500,
        'duration': 3.0,
        'runtime': '~3 seconds'
    },
    'large': {
        'label': 'Large',
        'description': 'Comprehensive study',
        'patients': 2000,
        'duration': 5.0,
        'runtime': '~10 seconds'
    },
    'rate': {
        'label': 'Rate',
        'description': 'Continuous recruitment',
        'patients': '80/month',
        'duration': 5.0,
        'runtime': '~10 seconds'
    }
}

# Create engine selector widget function
def engine_selector():
    """Engine selector without label"""
    engine_type = st.selectbox(
        "Engine",
        ["abs", "des"],
        format_func=lambda x: {"abs": "Agent-Based", "des": "Discrete Event"}[x],
        index=0,
        label_visibility="collapsed",
        help="Simulation engine: Agent-Based (ABS) or Discrete Event (DES)"
    )
    st.session_state.engine_type = engine_type
    return engine_type

# Show Quick Start box with protocol name as title and engine selector
selected_preset = quick_start_box(presets, default_preset='default', 
                                 title=f"{protocol_info['name']} v{protocol_info['version']}",
                                 engine_widget=engine_selector)

# Handle preset selection
if selected_preset:
    if selected_preset == 'rate':
        st.session_state.recruitment_rate = 80.0
        st.session_state.rate_unit = "per month"
        st.session_state.preset_duration = 5
        st.session_state.recruitment_mode = "Constant Rate"
    else:
        preset = presets[selected_preset]
        st.session_state.preset_patients = preset['patients']
        st.session_state.preset_duration = preset['duration']
        st.session_state.recruitment_mode = "Fixed Total"
    # No st.rerun() - let Streamlit handle it naturally!

# Get parameters - always need them for running simulation
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

# Define the simulation action callback
def run_simulation():
    # Set simulation running state to show closed eyes ape
    st.session_state.simulation_running = True
    
    # Store parameters for the simulation run
    st.session_state.recruitment_params = recruitment_params
    
    st.rerun()

# Update the callback in session state so the workflow button uses it
st.session_state.run_simulation_action = run_simulation

# Initialize runtime history if not present
if 'runtime_history' not in st.session_state:
    st.session_state.runtime_history = []

# Initialize last completion time if not present
if 'last_completion_time' not in st.session_state:
    st.session_state.last_completion_time = None

# Create progress area that's always visible
with st.container():
    progress_col, status_col = st.columns([4, 1])
    with progress_col:
        # Show full progress bar if we've completed a simulation
        if st.session_state.last_completion_time:
            progress_bar = st.progress(1.0)
        else:
            progress_bar = st.progress(0)
    with status_col:
        status_text = st.empty()
        if st.session_state.last_completion_time:
            status_text.caption(f"Completed in {st.session_state.last_completion_time:.1f}s")
        else:
            status_text.caption("")

def estimate_runtime(n_patients: int, duration_years: float, engine_type: str) -> float:
    """
    Estimate runtime based on historical data from this session.
    Returns estimated seconds.
    """
    # Calculate complexity score (patient-years)
    complexity = n_patients * duration_years
    
    # Check if we have any history
    if st.session_state.runtime_history:
        # Calculate average time per patient-year from history
        total_complexity = 0
        total_time = 0
        
        for entry in st.session_state.runtime_history:
            entry_complexity = entry['n_patients'] * entry['duration_years']
            # Give more weight to similar engine types
            weight = 2.0 if entry['engine_type'] == engine_type else 1.0
            total_complexity += entry_complexity * weight
            total_time += entry['runtime'] * weight
        
        if total_complexity > 0:
            time_per_complexity = total_time / total_complexity
            estimated_time = complexity * time_per_complexity
            
            # Add some padding for safety (10% extra)
            return estimated_time * 1.1
    
    # Default pessimistic estimate if no history
    # Rough estimate: 1 second per 1000 patient-years
    return max(2.0, (complexity / 1000) * 1.5)

def update_runtime_history(n_patients: int, duration_years: float, engine_type: str, runtime: float):
    """Update the runtime history with a new data point."""
    # Keep last 10 simulations
    st.session_state.runtime_history.append({
        'n_patients': n_patients,
        'duration_years': duration_years,
        'engine_type': engine_type,
        'runtime': runtime
    })
    
    # Keep only last 10 entries
    if len(st.session_state.runtime_history) > 10:
        st.session_state.runtime_history = st.session_state.runtime_history[-10:]

# Check if we should be running a simulation (after rerun)
if st.session_state.get('simulation_running', False):
    # Update progress bar that's already visible
    progress_bar.progress(0)
    status_text.caption("Initializing...")
    
    # Retrieve recruitment parameters
    recruitment_params = st.session_state.get('recruitment_params', {
        'mode': 'Fixed Total',
        'n_patients': n_patients,
        'duration_years': duration_years,
        'engine_type': engine_type,
        'seed': seed
    })
    
    # Get runtime estimate
    estimated_runtime = estimate_runtime(
        recruitment_params.get('n_patients', n_patients),
        recruitment_params['duration_years'],
        recruitment_params['engine_type']
    )
    
    # Variables for smooth progress
    simulation_complete = False
    actual_runtime = 0
    
    try:
        # Quick setup phase (0-10%)
        progress_bar.progress(2)
        status_text.caption("Loading protocol...")
        spec = ProtocolSpecification.from_yaml(Path(protocol_info['path']))
        
        progress_bar.progress(5)
        status_text.caption("Initializing...")
        runner = SimulationRunner(spec)
        
        # Check memory feasibility (optional)
        if st.session_state.get('check_memory_limits', True):
            monitor = MemoryMonitor()
            is_feasible, warning = monitor.check_simulation_feasibility(
                recruitment_params.get('n_patients', n_patients), 
                recruitment_params['duration_years']
            )
            if warning:
                with st.expander("Memory Check", expanded=not is_feasible):
                    if is_feasible:
                        st.warning(warning)
                    else:
                        st.error(warning)
                        if not st.checkbox("Run anyway (may cause errors)"):
                            st.stop()
        
        progress_bar.progress(10)
        status_text.caption(f"Running {recruitment_params['engine_type'].upper()}...")
        
        # Start smooth progress updater in a separate thread
        start_time = time.time()
        progress_stop_event = threading.Event()
        
        def update_progress():
            """Update progress bar smoothly based on estimated time."""
            import streamlit.runtime.scriptrunner as scriptrunner
            
            while not progress_stop_event.is_set() and not simulation_complete:
                # Double-check we still have context before any Streamlit operations
                ctx = scriptrunner.get_script_run_ctx()
                if ctx is None:
                    # No context - exit silently
                    return
                    
                try:
                    # Add the context to this thread
                    scriptrunner.add_script_run_ctx(threading.current_thread(), ctx)
                    
                    elapsed = time.time() - start_time
                    # Progress from 10% to 85% during simulation
                    progress = min(0.85, 0.10 + (elapsed / estimated_runtime) * 0.75)
                    progress_bar.progress(progress)
                    
                    # Update status text with time
                    if elapsed < 60:
                        status_text.caption(f"Running... {elapsed:.0f}s")
                    else:
                        status_text.caption(f"Running... {elapsed/60:.1f}m")
                except Exception:
                    # Any error including context issues - exit silently
                    return
                finally:
                    # Clean up context
                    try:
                        scriptrunner.add_script_run_ctx(threading.current_thread(), None)
                    except:
                        pass
                
                time.sleep(0.1)  # Update every 100ms
        
        # Start progress thread
        progress_thread = threading.Thread(target=update_progress)
        progress_thread.daemon = True
        progress_thread.start()
        
        # Run the actual simulation
        sim_start_time = datetime.now()
        
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
        
        # Stop the progress thread
        simulation_complete = True
        progress_stop_event.set()
        
        # Wait for thread to finish (with timeout to avoid hanging)
        progress_thread.join(timeout=1.0)
        
        sim_end_time = datetime.now()
        runtime = (sim_end_time - sim_start_time).total_seconds()
        
        # Update runtime history with actual time
        update_runtime_history(
            recruitment_params.get('n_patients', n_patients),
            recruitment_params['duration_years'],
            recruitment_params['engine_type'],
            runtime
        )
        
        # Now show actual progress for post-processing
        progress_bar.progress(85)
        status_text.caption("Processing results...")
        
        # Pre-compute treatment patterns for better UI performance
        from ape.components.treatment_patterns.precompute import precompute_treatment_patterns
        progress_bar.progress(90)
        status_text.caption("Preparing visualizations...")
        precompute_treatment_patterns(results, show_progress=False)
        
        progress_bar.progress(95)
        status_text.caption("Saving data...")
        
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
        
        progress_bar.progress(100)
        status_text.caption("Complete!")
        
        # Clear simulation running state
        st.session_state.simulation_running = False
        
        # Keep progress bar at 100% to show completion
        progress_bar.progress(100)
        status_text.caption(f"Completed in {runtime:.1f}s")
        
        # Store completion time for persistent display
        st.session_state.last_completion_time = runtime
        
        # Simple success message
        st.success(f"Simulation completed in {runtime:.1f} seconds")
        
        # Reload to show in recent simulations
        st.rerun()
        
    except Exception as e:
        # Stop progress thread if running
        if 'progress_stop_event' in locals():
            simulation_complete = True
            progress_stop_event.set()
            if 'progress_thread' in locals():
                progress_thread.join(timeout=1.0)
        
        # Show error in progress bar
        progress_bar.progress(0)
        status_text.caption("Failed")
        # Clear simulation running state on error
        st.session_state.simulation_running = False
        st.error(f"Simulation failed: {str(e)}")
        st.exception(e)

# Section 1: Recent Simulations List
st.markdown("---")
render_recent_simulations()