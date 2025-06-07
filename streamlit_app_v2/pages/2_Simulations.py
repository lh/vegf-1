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
from core.simulation_adapter import MemoryAwareSimulationRunner
from core.monitoring.memory import MemoryMonitor
from core.results.factory import ResultsFactory

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

# Import export/import components
from components.export import render_export_section
from components.import_component import render_import_section

# Show memory usage in sidebar
monitor = MemoryMonitor()
monitor.display_in_sidebar()

# Top navigation
col1, col2, col3 = st.columns([1, 6, 1])
with col1:
    if top_navigation_home_button():
        st.switch_page("APE.py")
with col2:
    st.title("Simulations")
    st.markdown("Run new simulations and manage existing ones.")

# Recent Simulations List
st.header("Recent Simulations")

# Get list of simulations from results directory
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
                                    st.session_state.current_sim_id = sim['id']
                                    st.rerun()
        else:
            st.info("No recent simulations found. Run a simulation below to get started.")
    else:
        st.info("No recent simulations found. Run a simulation below to get started.")
else:
    st.info("No simulations directory found. Run your first simulation below!")

# Manage section with export/import
if st.session_state.get('current_sim_id'):
    st.markdown("---")
    
    # Manage button with floppy disk icon
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if 'show_manage' not in st.session_state:
            st.session_state.show_manage = False
            
        if ape_button(
            "💾 Manage" if not st.session_state.show_manage else "💾 Manage ✓",
            key="manage_simulations",
            full_width=True,
            icon="save"  # This would be the Carbon save icon
        ):
            st.session_state.show_manage = not st.session_state.show_manage
            st.rerun()
    
    # Show manage section if toggled
    if st.session_state.show_manage:
        with st.container():
            st.markdown("### 📦 Simulation Management")
            
            tab1, tab2 = st.tabs(["📤 Export", "📥 Import"])
            
            with tab1:
                # Export current simulation
                render_export_section()
            
            with tab2:
                # Import simulation package
                render_import_section()

# Divider
st.markdown("---")

# Check if protocol is loaded
if not st.session_state.get('current_protocol'):
    st.header("Run New Simulation")
    st.info("Select a protocol first to run a simulation.")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if navigation_button("Go to Protocol Manager", key="nav_protocol_missing", 
                           full_width=True, is_primary_action=True):
            st.switch_page("pages/1_Protocol_Manager.py")
    st.stop()

# Run New Simulation section
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

# Action buttons in single line
st.markdown("---")

col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    # Run Simulation button
    run_clicked = ape_button("▶️ Run Simulation", key="run_sim_main", 
                            full_width=True, is_primary_action=True)

with col2:
    # View Analysis - always show but disable if no results  
    has_results = st.session_state.get('current_sim_id') is not None
    if ape_button("📊 View Analysis", key="view_analysis_action", 
                 full_width=True, 
                 disabled=not has_results):
        if has_results:
            st.switch_page("pages/3_Analysis_Overview.py")

with col3:
    # Change Protocol
    if ape_button("📋 Protocol", key="change_protocol", 
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
        
        # Store results and set current simulation
        st.session_state.current_sim_id = results.metadata.sim_id
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
        
        st.session_state.audit_trail = runner.audit_log
        
        progress_bar.progress(100, text="Simulation complete!")
        
        # Simple success message
        st.success(f"✅ Simulation completed in {runtime:.1f} seconds")
        
        # Reload to show in recent simulations
        st.rerun()
        
    except Exception as e:
        progress_bar.empty()
        st.error(f"❌ Simulation failed: {str(e)}")
        st.exception(e)