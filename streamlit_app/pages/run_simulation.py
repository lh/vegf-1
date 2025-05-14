"""
Run Simulation page for the APE Streamlit application.

This module handles configuring and running AMD treatment simulations.
"""

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

from streamlit_app.components.layout import display_logo_and_title
from streamlit_app.utils.session_state import (
    get_simulation_parameters,
    set_simulation_parameters,
    set_simulation_results,
    set_simulation_running,
    get_debug_mode
)

# Import simulation_runner functions conditionally to handle missing dependencies
try:
    from streamlit_app.simulation_runner import (
        run_simulation, 
        get_ui_parameters,
        generate_va_over_time_plot,
        generate_discontinuation_plot,
        save_simulation_results
    )
except ImportError:
    # Define fallback functions
    def run_simulation(params):
        st.error("Simulation module failed to load correctly.")
        st.info("This may be due to missing dependencies or incorrect import paths.")
        return {"error": "simulation_module_failed"}
    
    def get_ui_parameters():
        return {}
    
    def generate_va_over_time_plot(results):
        fig, ax = plt.subplots()
        ax.text(0.5, 0.5, "Simulation module not available", ha='center', va='center')
        return fig
    
    def generate_discontinuation_plot(results):
        fig, ax = plt.subplots()
        ax.text(0.5, 0.5, "Simulation module not available", ha='center', va='center')
        return fig
    
    def save_simulation_results(results, filename=None):
        return None

# Import retreatment_panel conditionally
try:
    from streamlit_app.retreatment_panel import display_retreatment_panel
except ImportError:
    def display_retreatment_panel(results):
        st.warning("Retreatment panel module not available.")

# Import SimulationConfig conditionally
try:
    from simulation.config import SimulationConfig
except ImportError:
    SimulationConfig = None


def display_simulation_configuration():
    """Display the simulation configuration options.
    
    Returns
    -------
    bool
        True if all required components are available, False otherwise
    """
    st.subheader("Simulation Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Add a marker for Puppeteer
        st.markdown('<div data-test-id="simulation-type-select-marker"></div>', unsafe_allow_html=True)
        simulation_type = st.selectbox(
            "Simulation Type",
            ["ABS", "DES"],
            help="Agent-Based Simulation (ABS) or Discrete Event Simulation (DES)",
            key="simulation_type_select"
        )
        
        duration_years = st.slider(
            "Simulation Duration (years)",
            min_value=1,
            max_value=10,
            value=5,
            help="Duration of the simulation in years",
            key="duration_years_slider"
        )
        
        population_size = st.slider(
            "Population Size",
            min_value=100,
            max_value=10000,
            value=1000,
            step=100,
            help="Number of patients in the simulation",
            key="population_size_slider"
        )
    
    with col2:
        st.subheader("Discontinuation Parameters")
        
        enable_clinician_variation = st.checkbox(
            "Enable Clinician Variation",
            value=True,
            help="Include variation in clinician adherence to protocol",
            key="enable_clinician_variation_checkbox"
        )
        
        planned_discontinue_prob = st.slider(
            "Planned Discontinuation Probability",
            min_value=0.0,
            max_value=1.0,
            value=0.2,
            step=0.05,
            help="Probability of planned discontinuation when criteria are met",
            key="planned_discontinue_prob_slider"
        )
        
        admin_discontinue_prob = st.slider(
            "Administrative Discontinuation Annual Probability",
            min_value=0.0,
            max_value=0.5,
            value=0.05,
            step=0.01,
            help="Annual probability of random administrative discontinuation",
            key="admin_discontinue_prob_slider"
        )
        
        premature_discontinue_prob = st.slider(
            "Premature Discontinuation Probability Factor",
            min_value=0.0,
            max_value=5.0,
            value=2.0,
            step=0.1,
            help="Probability factor for premature discontinuations (clinician-dependent)",
            key="premature_discontinue_prob_slider"
        )
    
    # Add a marker div for the expander
    st.markdown('<div data-test-id="advanced-options-marker"></div>', unsafe_allow_html=True)

    # Advanced options in an expander
    with st.expander("Advanced Options"):
        col1, col2 = st.columns(2)
        
        with col1:
            recurrence_risk_multiplier = st.slider(
                "Recurrence Risk Multiplier",
                min_value=0.5,
                max_value=2.0,
                value=1.0,
                step=0.1,
                help="Multiplier for disease recurrence rates",
                key="recurrence_risk_multiplier_slider"
            )
            
            consecutive_stable_visits = st.slider(
                "Consecutive Stable Visits Required",
                min_value=1,
                max_value=5,
                value=3,
                step=1,
                help="Number of consecutive stable visits required for discontinuation",
                key="consecutive_stable_visits_slider"
            )
        
        with col2:
            monitoring_schedule = st.multiselect(
                "Monitoring Schedule (weeks after discontinuation)",
                options=[4, 8, 12, 16, 24, 36, 48, 52],
                default=[12, 24, 36],
                help="Weeks after discontinuation for follow-up visits",
                key="monitoring_schedule_multiselect"
            )
            
            no_monitoring_for_admin = st.checkbox(
                "No Monitoring for Administrative Discontinuation",
                value=True,
                help="Don't schedule monitoring visits for administrative discontinuations",
                key="no_monitoring_for_admin_checkbox"
            )
    
    # Check if SimulationConfig is available
    simulation_can_run = True
    if SimulationConfig is None:
        st.error("Required simulation modules are not available.")
        st.info("This may be due to missing dependencies or incorrect import paths.")
        simulation_can_run = False
    
    return simulation_can_run


def display_run_simulation():
    """Display the run simulation page."""
    display_logo_and_title("Run AMD Treatment Simulation")
    
    # Display configuration options
    simulation_can_run = display_simulation_configuration()
    
    # Add a marker element for Puppeteer to locate the button
    st.markdown('<div data-test-id="run-simulation-btn-marker"></div>', unsafe_allow_html=True)
    
    # Run simulation button
    if st.button("Run Simulation", type="primary", key="run_simulation_button", help="Run the simulation with current parameters"):
        # Save all parameters to session state
        params = {
            "simulation_type": st.session_state["simulation_type_select"],
            "duration_years": st.session_state["duration_years_slider"],
            "population_size": st.session_state["population_size_slider"],
            "enable_clinician_variation": st.session_state["enable_clinician_variation_checkbox"],
            "planned_discontinue_prob": st.session_state["planned_discontinue_prob_slider"],
            "admin_discontinue_prob": st.session_state["admin_discontinue_prob_slider"],
            "premature_discontinue_prob": st.session_state["premature_discontinue_prob_slider"],
            "consecutive_stable_visits": st.session_state["consecutive_stable_visits_slider"],
            "monitoring_schedule": st.session_state["monitoring_schedule_multiselect"],
            "no_monitoring_for_admin": st.session_state["no_monitoring_for_admin_checkbox"],
            "recurrence_risk_multiplier": st.session_state["recurrence_risk_multiplier_slider"]
        }
        
        # Save parameters to session state
        set_simulation_parameters(params)
        
        # Get parameters from UI
        ui_params = get_ui_parameters()
        
        # Initialize results
        results = None
        
        # Run the simulation if possible, otherwise use sample data
        if simulation_can_run:
            with st.spinner(f"Running {params['simulation_type']} simulation with {params['population_size']} patients over {params['duration_years']} years..."):
                set_simulation_running(True)
                
                try:
                    # Run simulation
                    results = run_simulation(ui_params)
                    
                    # Check if there was an error or if simulation failed
                    if "error" in results or results.get("failed", False):
                        st.error(f"Simulation failed: {results.get('error', 'Unknown error')}")
                        # Keep the results but mark them as failed for display
                        results["failed"] = True
                    else:
                        # Save results to file
                        results_path = save_simulation_results(results)
                        if results_path:
                            st.session_state["simulation_results_path"] = results_path
                        
                        # Show success message
                        debug_mode = get_debug_mode()
                        if debug_mode and "runtime_seconds" in results:
                            st.success(f"Simulation complete in {results['runtime_seconds']:.2f} seconds!")
                        else:
                            st.success("Simulation complete!")
                except Exception as e:
                    st.error(f"Error running simulation: {str(e)}")
                    # Create a minimal results object
                    results = {
                        "simulation_type": params["simulation_type"],
                        "population_size": params["population_size"],
                        "duration_years": params["duration_years"],
                        "enable_clinician_variation": params["enable_clinician_variation"],
                        "planned_discontinue_prob": params["planned_discontinue_prob"],
                        "admin_discontinue_prob": params["admin_discontinue_prob"],
                        "error": str(e),
                        "failed": True
                    }
                
                set_simulation_running(False)
        
        # Save results in session state
        set_simulation_results(results)
        
        # Display results
        display_simulation_results(results)


def display_simulation_results(results):
    """Display simulation results.
    
    Parameters
    ----------
    results : dict
        Simulation results to display
    """
    st.subheader("Simulation Results")
    
    # Check if these are sample results
    if results.get("is_sample", False):
        st.warning("⚠️ **Sample Data**: These are simulated results using sample data, not actual simulation outputs.")
        st.info("The actual simulation module couldn't be loaded. This is likely because you're viewing the UI without having the full simulation codebase installed.")
    
    # Check if simulation failed
    if results.get("failed", False):
        st.error("Simulation failed to complete. No results to display.")

        # Show error details if available
        if "error" in results:
            st.markdown('<div data-test-id="error-details-marker"></div>', unsafe_allow_html=True)
            with st.expander("Error Details"):
                st.write(results["error"])

        # Provide suggestions for troubleshooting
        st.info("""
        **Troubleshooting suggestions:**
        - Try reducing the population size
        - Try a different simulation type (ABS or DES)
        - Check the debug information section for more details
        """)
        
        return
    
    # Get debug mode
    debug_mode = get_debug_mode()
    
    # Show debug information about visualization issues if debug mode is enabled
    if debug_mode and "va_extraction_stats" in results:
        va_stats = results["va_extraction_stats"]
        st.markdown('<div data-test-id="va-debug-marker"></div>', unsafe_allow_html=True)
        with st.expander("Visual Acuity Data Debug Information", expanded=True):
            st.markdown("### Visual Acuity Extraction Statistics")
            col1, col2 = st.columns(2)

            with col1:
                st.metric("Total Patients", va_stats.get("total_patients", 0))
                st.metric("Patients With Acuity Data", va_stats.get("patients_with_acuity", 0))

            with col2:
                st.metric("Total VA Datapoints", va_stats.get("total_va_datapoints", 0))

                # Calculate extraction success rate
                if va_stats.get("total_patients", 0) > 0:
                    success_rate = va_stats.get("patients_with_acuity", 0) / va_stats.get("total_patients", 0) * 100
                    st.metric("Extraction Success Rate", f"{success_rate:.1f}%")
    
    # Only display metrics if simulation succeeded
    # Display metrics
    col1, col2, col3 = st.columns(3)
    
    # Calculate metrics
    total_patients = results["population_size"]
    discontinued_patients = results.get("total_discontinuations", 0)
    discontinued_percent = (discontinued_patients / total_patients * 100) if total_patients > 0 else 0
    
    # Get recurrence data with more details
    recurrence_data = results.get("recurrences", {})
    
    # Use simulation stats for retreatments if available
    if "raw_discontinuation_stats" in results and "unique_patient_retreatments" in results["raw_discontinuation_stats"]:
        # We have direct stats from simulation
        unique_recurrence_count = results["raw_discontinuation_stats"]["unique_patient_retreatments"]
        # If we also have total retreatments, use that
        if "retreatments" in results["raw_discontinuation_stats"]:
            recurrence_count = results["raw_discontinuation_stats"]["retreatments"]
        else:
            # Otherwise use the unique count or fall back to recurrence_data
            recurrence_count = recurrence_data.get("total", unique_recurrence_count)
    else:
        # Fall back to recurrence_data
        recurrence_count = recurrence_data.get("total", 0)
        unique_recurrence_count = recurrence_data.get("unique_count", recurrence_count)
        
    # Calculate rate based on unique counts whenever possible
    recurrence_rate = (unique_recurrence_count / discontinued_patients * 100) if discontinued_patients > 0 else 0
    
    # Display metrics in columns
    mean_va_final = 0
    if "mean_va_data" in results and results["mean_va_data"]:
        mean_va_final = results["mean_va_data"][-1]["visual_acuity"]
    
    with col1:
        st.metric("Patients Discontinued", f"{discontinued_percent:.1f}%", f"{discontinued_patients} patients")
    
    with col2:
        # Show unique patient count if available, otherwise total
        recurrence_detail = f"{unique_recurrence_count} patients" if unique_recurrence_count != recurrence_count else f"{recurrence_count} recurrences"
        st.metric("Recurrence Rate", f"{recurrence_rate:.1f}%", recurrence_detail)
    
    with col3:
        st.metric("Mean Injections", f"{results.get('mean_injections', 0):.1f}", f"{results.get('total_injections', 0)} total")
    
    # Display discontinuation types
    st.subheader("Discontinuation Types")
    
    # Prepare to display discontinuation data
    if "discontinuation_counts" in results:
        disc_counts = results["discontinuation_counts"]
        total = sum(disc_counts.values())
        
        # Create dataframe for display
        data = []
        for disc_type, count in disc_counts.items():
            percentage = (count / total * 100) if total > 0 else 0
            data.append({
                "Type": disc_type,
                "Count": count,
                "Percentage": f"{percentage:.1f}%",
                "Mean Time to Recurrence (weeks)": "-"  # Replace with actual data if available
            })
        
        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True)
    else:
        st.warning("No discontinuation data available in simulation results. Check simulation configuration.")
    
    # Show discontinuation and retreatment analysis
    if "discontinuation_counts" in results:
        st.subheader("Discontinuation and Retreatment Analysis")
        figs = generate_discontinuation_plot(results)

        # Display the discontinuation chart
        if isinstance(figs, list) and len(figs) > 0:
            # Show the enhanced chart with full width
            with st.container():
                st.pyplot(figs[0])
                st.caption("Discontinuation Reasons by Retreatment Status")
        else:
            # Fallback in case figs is not a list (should never happen with updated code)
            st.pyplot(figs)

        # Show retreatment analysis
        display_retreatment_panel(results)
    
    # Show visual acuity over time
    st.subheader("Visual Acuity Over Time")
    fig = generate_va_over_time_plot(results)
    st.pyplot(fig)


if __name__ == "__main__":
    # This allows the page to be run directly for testing
    import sys
    import os
    
    # Add parent directory to path so imports work
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # Set up basic Streamlit configuration
    st.set_page_config(page_title="Run Simulation Test", layout="wide")
    
    # Display the run simulation page
    display_run_simulation()