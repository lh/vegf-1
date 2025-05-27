"""
Run Simulation - Execute simulations with selected protocols.
"""

import streamlit as st
import sys
from pathlib import Path
from datetime import datetime
import pandas as pd
import time

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from simulation_v2.protocols.protocol_spec import ProtocolSpecification
from core.simulation_adapter import MemoryAwareSimulationRunner
from core.monitoring.memory import MemoryMonitor

st.set_page_config(
    page_title="Run Simulation", 
    page_icon="🚀", 
    layout="wide",
    initial_sidebar_state="expanded"  # Show sidebar for memory monitoring
)

# Add parent for utils import
sys.path.append(str(Path(__file__).parent.parent))
from utils.button_styling import style_navigation_buttons

# Apply our button styling
style_navigation_buttons()

# Show memory usage in sidebar
monitor = MemoryMonitor()
monitor.display_in_sidebar()


# Top navigation
col1, col2, col3 = st.columns([1, 6, 1])
with col1:
    if st.button("🦍 Home", key="top_home"):
        st.switch_page("APE.py")
with col2:
    st.title("🚀 Run Simulation")
    st.markdown("Execute simulations using V2 engine with complete parameter tracking.")

# Check if protocol is loaded
if not st.session_state.get('current_protocol'):
    st.warning("⚠️ No protocol loaded. Please select a protocol in the Protocol Manager first.")
    
    # Add navigation button to Protocol Manager
    if st.button("📋 Go to Protocol Manager", use_container_width=True):
        st.switch_page("pages/1_Protocol_Manager.py")
    st.stop()

# Display current protocol
protocol_info = st.session_state.current_protocol
st.success(f"✅ Using Protocol: {protocol_info['name']} v{protocol_info['version']}")

# Simulation parameters
st.header("Simulation Parameters")

col1, col2, col3 = st.columns(3)

with col1:
    engine_type = st.selectbox(
        "Simulation Engine",
        ["abs", "des"],
        format_func=lambda x: {"abs": "Agent-Based (ABS)", "des": "Discrete Event (DES)"}[x]
    )
    
    n_patients = st.number_input(
        "Number of Patients",
        min_value=10,
        max_value=10000,
        value=100,
        step=10,
        help="Number of patients to simulate"
    )

with col2:
    duration_years = st.number_input(
        "Duration (years)",
        min_value=0.5,
        max_value=10.0,
        value=2.0,
        step=0.5,
        help="Simulation duration in years"
    )
    
    seed = st.number_input(
        "Random Seed",
        min_value=0,
        max_value=999999,
        value=42,
        help="Random seed for reproducibility"
    )

with col3:
    st.markdown("**Estimated Runtime**")
    # Simple runtime estimate
    estimated_seconds = (n_patients * duration_years) / 1000
    if estimated_seconds < 1:
        st.info(f"< 1 second")
    elif estimated_seconds < 60:
        st.info(f"~{estimated_seconds:.0f} seconds")
    else:
        st.info(f"~{estimated_seconds/60:.1f} minutes")
    
    st.markdown("**Total Visits**")
    visits_per_year = 365 / 42  # Rough estimate (6-week average)
    total_visits = int(n_patients * duration_years * visits_per_year)
    st.info(f"~{total_visits:,} visits")

# Action buttons in single line with dynamic proportional sizing
st.markdown("---")

# Dynamic layout based on whether we have results
if st.session_state.get('simulation_results'):
    # After simulation: emphasize View Analysis
    col1, col2, col3, col4 = st.columns([1, 3, 1, 1])
else:
    # Before simulation: emphasize Run Simulation
    col1, col2, col3, col4 = st.columns([3, 1, 1, 1])

with col1:
    # Run Simulation - changes size based on state
    run_clicked = st.button("🎯 **Run Simulation**", use_container_width=True, key="run_sim_main")

with col2:
    # View Analysis - changes size and emphasis based on state
    if st.session_state.get('simulation_results'):
        # Make it more prominent after simulation
        if st.button("📊 **View Analysis**", use_container_width=True, key="view_analysis_action"):
            st.switch_page("pages/3_Analysis_Overview.py")
    else:
        # Empty space before simulation
        st.empty()

with col3:
    # Change Protocol
    if st.button("📋 Change Protocol", use_container_width=True, key="change_protocol"):
        st.switch_page("pages/1_Protocol_Manager.py")

with col4:
    # Home
    if st.button("🦍 Home", use_container_width=True, key="home_action"):
        st.switch_page("APE.py")

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
        
        st.session_state.audit_trail = runner.audit_log
        
        progress_bar.progress(100, text="Simulation complete!")
        
        # Display results summary
        st.success(f"✅ Simulation completed in {runtime:.1f} seconds")
        
        # Results metrics
        st.header("Results Summary")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Total Injections",
                f"{results.get_total_injections():,}",
                f"{results.get_total_injections()/n_patients:.1f} per patient"
            )
            
        with col2:
            mean_vision, std_vision = results.get_final_vision_stats()
            st.metric(
                "Mean Final Vision",
                f"{mean_vision:.1f} letters",
                f"{mean_vision - spec.baseline_vision_mean:+.1f} from baseline"
            )
            
        with col3:
            st.metric(
                "Vision Std Dev",
                f"{std_vision:.1f} letters"
            )
            
        with col4:
            st.metric(
                "Discontinuation Rate",
                f"{results.get_discontinuation_rate():.1%}"
            )
        
        # Storage information
        st.subheader("Storage Information")
        
        storage_col1, storage_col2, storage_col3 = st.columns(3)
        
        with storage_col1:
            storage_icon = "💾" if results.metadata.storage_type == "memory" else "📁"
            st.info(f"{storage_icon} **Storage Type**: {results.metadata.storage_type.title()}")
            
        with storage_col2:
            st.info(f"💽 **Memory Usage**: {results.get_memory_usage_mb():.1f} MB")
            
        with storage_col3:
            patient_years = n_patients * duration_years
            st.info(f"📊 **Scale**: {patient_years:,} patient-years")
        
        # Patient-level summary
        st.subheader("Patient Summary Statistics")
        
        # Calculate patient stats using iterator for memory efficiency
        patient_stats = []
        total_processed = 0
        max_patients_for_stats = 1000  # Limit for display
        
        # Process in batches to avoid memory issues
        for patient_batch in results.iterate_patients(batch_size=100):
            for patient_data in patient_batch:
                # Extract data from dict format
                patient_id = patient_data.get('patient_id', f'patient_{total_processed}')
                visits = patient_data.get('visits', [])
                
                # Get baseline and final vision
                if visits:
                    baseline_vision = visits[0].get('vision', 70)
                    final_vision = visits[-1].get('vision', 70)
                else:
                    baseline_vision = 70
                    final_vision = 70
                
                patient_stats.append({
                    'Patient ID': patient_id,
                    'Baseline Vision': baseline_vision,
                    'Final Vision': final_vision,
                    'Vision Change': final_vision - baseline_vision,
                    'Visits': len(visits),
                    'Injections': patient_data.get('total_injections', 0),
                    'Discontinued': '✓' if patient_data.get('discontinued', False) else ''
                })
                
                total_processed += 1
                if total_processed >= max_patients_for_stats:
                    break
                    
            if total_processed >= max_patients_for_stats:
                break
            
        stats_df = pd.DataFrame(patient_stats)
        
        # Summary statistics
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Vision Changes**")
            vision_summary = stats_df['Vision Change'].describe()
            st.dataframe(vision_summary)
            
        with col2:
            st.markdown("**Injection Count Distribution**")
            injection_summary = stats_df['Injections'].describe()
            st.dataframe(injection_summary)
        
        # Sample of patients
        st.markdown("**Sample Patient Data** (first 10)")
        st.dataframe(
            stats_df.head(10),
            use_container_width=True,
            hide_index=True
        )
        
        # Next steps
        st.info("💡 **Success!** Simulation complete. Updating interface...")
        
        # Force a rerun to update the dynamic layout
        time.sleep(1.5)  # Brief pause to show success message
        st.rerun()
        
    except Exception as e:
        progress_bar.empty()
        st.error(f"❌ Simulation failed: {str(e)}")
        st.exception(e)

