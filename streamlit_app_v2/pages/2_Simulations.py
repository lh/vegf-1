"""
Simulations - Run new simulations and manage existing ones.
"""

import streamlit as st
import sys
from pathlib import Path
from datetime import datetime
import json

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
from utils.simulation_loader import load_simulation_results

# Import simulation package manager
from utils.simulation_package import SimulationPackageManager, SecurityError, PackageValidationError
from core.storage.registry import SimulationRegistry


@st.cache_data
def create_export_package(sim_id: str) -> bytes:
    """Create export package for a simulation"""
    try:
        # Load simulation results
        results_path = ResultsFactory.DEFAULT_RESULTS_DIR / sim_id
        results = ResultsFactory.load_results(results_path)
        
        # Create package
        manager = SimulationPackageManager()
        package_data = manager.create_package(results)
        
        return package_data
    except Exception as e:
        st.error(f"Failed to create package: {str(e)}")
        return b""


def handle_import(uploaded_file):
    """Handle simulation package import"""
    try:
        with st.spinner("Importing simulation..."):
            # Read package data
            package_data = uploaded_file.read()
            
            # Import the package
            manager = SimulationPackageManager()
            imported_results = manager.import_package(package_data)
            
            # Get the sim_id from imported results
            sim_id = imported_results.metadata.sim_id
            
            # Register with simulation registry
            registry = SimulationRegistry(ResultsFactory.DEFAULT_RESULTS_DIR)
            
            # Calculate size
            import os
            sim_path = ResultsFactory.DEFAULT_RESULTS_DIR / sim_id
            size_mb = 0
            if sim_path.exists():
                for file in sim_path.rglob('*'):
                    if file.is_file():
                        size_mb += file.stat().st_size / (1024 * 1024)
            
            # Convert metadata to dict
            metadata_dict = imported_results.metadata.to_dict()
            registry.register_simulation(sim_id, metadata_dict, size_mb)
            
            # Load the imported simulation
            if load_simulation_results(sim_id):
                # Mark as imported
                if 'imported_simulations' not in st.session_state:
                    st.session_state.imported_simulations = set()
                st.session_state.imported_simulations.add(sim_id)
                
                st.success("Simulation imported successfully!")
                st.rerun()
            else:
                st.error("Failed to load imported simulation")
                
    except SecurityError as e:
        st.error(f"Security Error: {str(e)}")
    except PackageValidationError as e:
        st.error(f"Package Error: {str(e)}")
    except Exception as e:
        st.error(f"Import failed: {str(e)}")


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
    st.markdown("Run new simulations and manage existing ones.")

# Check if protocol is loaded first
if not st.session_state.get('current_protocol'):
    st.header("Run New Simulation")
    st.info("Select a protocol first to run a simulation.")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if navigation_button("Go to Protocol Manager", key="nav_protocol_missing", 
                           full_width=True, is_primary_action=True):
            st.switch_page("pages/1_Protocol_Manager.py")
    st.stop()

# Section 3: Run New Simulation
st.header("Run New Simulation")

# Display current protocol (subtle)
protocol_info = st.session_state.current_protocol
st.caption(f"Protocol: **{protocol_info['name']}** v{protocol_info['version']}")

# Simulation parameters
st.subheader("Simulation Parameters")

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
    # Use current simulation parameters if loaded, otherwise use simple values
    if ('simulation_results' in st.session_state and 
        st.session_state.simulation_results is not None and 
        'parameters' in st.session_state.simulation_results):
        engine_value = st.session_state.simulation_results['parameters']['engine']
        engine_index = 0 if engine_value == "abs" else 1
    else:
        engine_index = 0  # Start with ABS
    
    engine_type = st.selectbox(
        "Engine",
        ["abs", "des"],
        format_func=lambda x: {"abs": "Agent-Based", "des": "Discrete Event"}[x],
        index=engine_index
    )

with col2:
    # Check for preset from buttons FIRST, then fall back to current simulation
    if 'preset_patients' in st.session_state:
        patients_value = st.session_state.preset_patients
    elif ('simulation_results' in st.session_state and 
          st.session_state.simulation_results is not None and 
          'parameters' in st.session_state.simulation_results):
        patients_value = st.session_state.simulation_results['parameters']['n_patients']
    else:
        patients_value = 100
    
    # Force update the widget by changing its key when preset is used
    widget_key = "n_patients_input"
    if 'preset_patients' in st.session_state:
        widget_key = f"n_patients_input_{st.session_state.preset_patients}"
    
    n_patients = st.number_input(
        "Patients",
        min_value=10,
        max_value=50000,
        value=patients_value,
        step=10,
        key=widget_key
    )

with col3:
    # Check for preset from buttons FIRST, then fall back to current simulation
    if 'preset_duration' in st.session_state:
        duration_value = st.session_state.preset_duration
    elif ('simulation_results' in st.session_state and 
          st.session_state.simulation_results is not None and 
          'parameters' in st.session_state.simulation_results):
        duration_value = st.session_state.simulation_results['parameters']['duration_years']
    else:
        duration_value = 2.0
    
    # Force update the widget by changing its key when preset is used
    widget_key = "duration_years_input"
    if 'preset_duration' in st.session_state:
        widget_key = f"duration_years_input_{st.session_state.preset_duration}"
    
    duration_years = st.number_input(
        "Years",
        min_value=0.5,
        max_value=20.0,
        value=duration_value,
        step=0.5,
        key=widget_key
    )

with col4:
    # Use current simulation seed if loaded
    if ('simulation_results' in st.session_state and 
        st.session_state.simulation_results is not None and 
        'parameters' in st.session_state.simulation_results):
        seed_value = st.session_state.simulation_results['parameters']['seed']
    else:
        seed_value = 42
    
    seed = st.number_input(
        "Random Seed",
        min_value=0,
        max_value=999999,
        value=seed_value
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

# Section 4: Action buttons (Control Panel)
st.markdown("---")

col1, col2, col3, col4 = st.columns([1, 1, 1, 1])

with col1:
    # Run Simulation button with play icon
    run_clicked = ape_button("Run Simulation", key="run_sim_main", 
                            full_width=True, is_primary_action=True, icon="play")

with col2:
    # View Analysis - always show but disable if no results  
    has_results = st.session_state.get('current_sim_id') is not None
    if ape_button("View Analysis", key="view_analysis_action", 
                 full_width=True, 
                 disabled=not has_results,
                 icon="chart"):
        if has_results:
            st.switch_page("pages/3_Analysis_Overview.py")

with col3:
    # Change Protocol
    if ape_button("Protocol", key="change_protocol", 
                 full_width=True,
                 icon="document"):
        st.switch_page("pages/1_Protocol_Manager.py")

with col4:
    # Manage button
    has_any_simulations = False
    if ResultsFactory.DEFAULT_RESULTS_DIR.exists():
        sim_dirs = list(ResultsFactory.DEFAULT_RESULTS_DIR.iterdir())
        has_any_simulations = any(d.is_dir() for d in sim_dirs)
    
    show_manage = has_any_simulations or st.session_state.get('current_sim_id')
    
    if show_manage:
        if ape_button("Manage", key="manage_btn", 
                     full_width=True,
                     icon="save"):
            st.session_state.show_manage = not st.session_state.get('show_manage', False)

# Show manage panel if toggled
if st.session_state.get('show_manage', False):
    # Make the manage section 1/4 width by using columns
    manage_cols = st.columns([3, 1])  # 3:1 ratio gives us the rightmost quarter
    with manage_cols[1]:
        # Upload section first
        uploaded_file = st.file_uploader(
            "",
            type=['zip'],
            label_visibility="collapsed",
            help="Upload a simulation package (.zip)"
        )
        
        if uploaded_file is not None:
            handle_import(uploaded_file)
        
        # Download section - only show if simulation is selected
        if st.session_state.get('current_sim_id'):
            sim_id = st.session_state.get('current_sim_id')
            # Check if simulation exists
            results_path = ResultsFactory.DEFAULT_RESULTS_DIR / sim_id
            if results_path.exists():
                # Show info about current simulation
                st.markdown(f"<small style='color: #666;'>Current: {sim_id[:20]}...</small>", unsafe_allow_html=True)
                
                # Carbon-styled download button
                package_data = create_export_package(sim_id)
                if package_data:
                    st.download_button(
                        label="Download",
                        data=package_data,
                        file_name=f"APE_{sim_id}.zip",
                        mime="application/zip",
                        use_container_width=True,
                        help="Download simulation as portable package"
                    )

# Handle Run Simulation click
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
        
        # Clear preset values after successful simulation
        if 'preset_patients' in st.session_state:
            del st.session_state.preset_patients
        if 'preset_duration' in st.session_state:
            del st.session_state.preset_duration
        
        progress_bar.progress(100, text="Simulation complete!")
        
        # Simple success message
        st.success(f"Simulation completed in {runtime:.1f} seconds")
        
        # Reload to show in recent simulations
        st.rerun()
        
    except Exception as e:
        progress_bar.empty()
        st.error(f"Simulation failed: {str(e)}")
        st.exception(e)

# Section 1: Recent Simulations List
st.markdown("---")
st.header("Recent Simulations")

results_dir = ResultsFactory.DEFAULT_RESULTS_DIR
if results_dir.exists():
    sim_dirs = sorted([d for d in results_dir.iterdir() if d.is_dir()], 
                     key=lambda x: x.name, reverse=True)[:10]  # Show last 10
    
    if sim_dirs:
        # Create a list of simulations with metadata
        simulations = []
        for sim_dir in sim_dirs:
            try:
                # Load metadata
                metadata_path = sim_dir / "metadata.json"
                if metadata_path.exists():
                    with open(metadata_path) as f:
                        metadata = json.load(f)
                    
                    # Extract key info
                    sim_info = {
                        'id': sim_dir.name,
                        'timestamp': metadata.get('created_date', 'Unknown'),
                        'patients': metadata.get('n_patients', 0),
                        'duration': metadata.get('duration_years', 0),
                        'protocol': metadata.get('protocol_name', 'Unknown'),
                        'is_imported': sim_dir.name.startswith('imported_')
                    }
                    simulations.append(sim_info)
            except:
                continue
        
        if simulations:
            # Display as cards
            for i in range(0, len(simulations), 3):
                cols = st.columns(3)
                for j, col in enumerate(cols):
                    if i + j < len(simulations):
                        sim = simulations[i + j]
                        with col:
                            # Card styling
                            is_selected = st.session_state.get('current_sim_id') == sim['id']
                            is_imported = sim['is_imported'] or sim['id'] in st.session_state.get('imported_simulations', set())
                            
                            # Create card with conditional styling
                            card_style = "border: 2px solid #0F62FE;" if is_selected else "border: 1px solid #ddd;"
                            if is_imported:
                                card_style += " background-color: #f0f7ff;"
                            
                            with st.container():
                                st.markdown(f"""
                                <div style="padding: 1rem; {card_style} border-radius: 8px; margin-bottom: 1rem;">
                                    <h5 style="margin: 0 0 0.5rem 0;">{sim['protocol']}</h5>
                                    <p style="margin: 0; font-size: 0.9rem; color: #666;">
                                        {sim['patients']:,} patients • {sim['duration']} years
                                    </p>
                                    <p style="margin: 0; font-size: 0.8rem; color: #999;">
                                        {sim['timestamp'][:19]}
                                    </p>
                                    {f'<span style="background: #0F62FE; color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.8rem;">IMPORTED</span>' if is_imported else ''}
                                </div>
                                """, unsafe_allow_html=True)
                                
                                if ape_button(
                                    "Select" if not is_selected else "Selected ✓",
                                    key=f"select_{sim['id']}",
                                    full_width=True,
                                    is_primary_action=not is_selected
                                ):
                                    # Use the unified loader to set both current_sim_id AND load results
                                    if load_simulation_results(sim['id']):
                                        st.rerun()
                                    else:
                                        st.error(f"Failed to load simulation {sim['id']}")
        else:
            st.info("No recent simulations found. Run a simulation above to get started.")
    else:
        st.info("No recent simulations found. Run a simulation above to get started.")
else:
    st.info("No simulations directory found. Run your first simulation above!")