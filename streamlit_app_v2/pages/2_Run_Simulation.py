"""
Run Simulation - Execute simulations with selected protocols.
"""

import streamlit as st
import sys
from pathlib import Path
from datetime import datetime
import pandas as pd

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from simulation_v2.protocols.protocol_spec import ProtocolSpecification
from simulation_v2.core.simulation_runner import SimulationRunner

st.set_page_config(page_title="Run Simulation", page_icon="🚀", layout="wide")

st.title("🚀 Run Simulation")
st.markdown("Execute simulations using V2 engine with complete parameter tracking.")

# Check if protocol is loaded
if not st.session_state.get('current_protocol'):
    st.warning("⚠️ No protocol loaded. Please select a protocol in the Protocol Manager first.")
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

# Run simulation button
st.markdown("---")

if st.button("🎯 Run Simulation", type="primary", use_container_width=True):
    # Create progress indicators
    progress_bar = st.progress(0, text="Initializing simulation...")
    status_text = st.empty()
    
    try:
        # Load protocol spec
        progress_bar.progress(10, text="Loading protocol specification...")
        spec = ProtocolSpecification.from_yaml(Path(protocol_info['path']))
        
        # Create runner
        progress_bar.progress(20, text="Creating simulation runner...")
        runner = SimulationRunner(spec)
        
        # Run simulation
        progress_bar.progress(30, text=f"Running {engine_type.upper()} simulation...")
        start_time = datetime.now()
        
        with st.spinner(f"Simulating {n_patients} patients over {duration_years} years..."):
            results = runner.run(
                engine_type=engine_type,
                n_patients=n_patients,
                duration_years=duration_years,
                seed=seed
            )
        
        end_time = datetime.now()
        runtime = (end_time - start_time).total_seconds()
        
        progress_bar.progress(90, text="Processing results...")
        
        # Store results in session state
        st.session_state.simulation_results = {
            'results': results,
            'protocol': protocol_info,
            'parameters': {
                'engine': engine_type,
                'n_patients': n_patients,
                'duration_years': duration_years,
                'seed': seed
            },
            'runtime': runtime,
            'timestamp': datetime.now().isoformat()
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
                f"{results.total_injections:,}",
                f"{results.total_injections/n_patients:.1f} per patient"
            )
            
        with col2:
            st.metric(
                "Mean Final Vision",
                f"{results.mean_final_vision:.1f} letters",
                f"{results.mean_final_vision - spec.baseline_vision_mean:+.1f} from baseline"
            )
            
        with col3:
            st.metric(
                "Vision Std Dev",
                f"{results.final_vision_std:.1f} letters"
            )
            
        with col4:
            st.metric(
                "Discontinuation Rate",
                f"{results.discontinuation_rate:.1%}"
            )
        
        # Patient-level summary
        st.subheader("Patient Summary Statistics")
        
        # Calculate patient stats
        patient_stats = []
        for pid, patient in results.patient_histories.items():
            patient_stats.append({
                'Patient ID': pid,
                'Baseline Vision': patient.baseline_vision,
                'Final Vision': patient.current_vision,
                'Vision Change': patient.current_vision - patient.baseline_vision,
                'Visits': len(patient.visit_history),
                'Injections': patient.injection_count,
                'Discontinued': '✓' if patient.is_discontinued else ''
            })
            
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
        st.info("💡 **Next Steps:** Navigate to the Analysis pages to visualize results in detail.")
        
    except Exception as e:
        progress_bar.empty()
        st.error(f"❌ Simulation failed: {str(e)}")
        st.exception(e)

# Previous results
if st.session_state.get('simulation_results'):
    st.markdown("---")
    st.subheader("Previous Results")
    
    prev_results = st.session_state.simulation_results
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.info(f"**Protocol:** {prev_results['protocol']['name']}")
    with col2:
        st.info(f"**Patients:** {prev_results['parameters']['n_patients']}")
    with col3:
        st.info(f"**Timestamp:** {prev_results['timestamp'][:19]}")
        
    if st.button("🗑️ Clear Previous Results"):
        st.session_state.simulation_results = None
        st.session_state.audit_trail = None
        st.rerun()