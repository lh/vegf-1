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
    from streamlit_app_parquet.simulation_runner import (
        run_simulation, 
        get_ui_parameters,
        generate_va_over_time_plot
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
    
    
    # Removed JSON save function - Parquet only!

# Import retreatment_panel conditionally
try:
    from streamlit_app_parquet.retreatment_panel import display_retreatment_panel
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
                        # Results are already saved as Parquet in simulation_runner
                        if "parquet_base_path" in results:
                            st.session_state["simulation_results_path"] = results["parquet_base_path"]
                        
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
    
    # Patient State Visualisation
    st.subheader("Patient State Visualisation")
    
    # Create tabs for different views
    current_tab, cumulative_tab = st.tabs(["Current State View", "Cumulative View"])
    
    with current_tab:
        st.write("**Where patients are right now at each time point**")
        
        # Try to create current state visualization
        try:
            # Import and use our current state streamgraph
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            
            # PARQUET ONLY - No JSON fallback!
            # Debug: Show what's in results
            if get_debug_mode():
                st.write("Debug: Results keys:", list(results.keys()))
                if "parquet_base_path" in results:
                    st.write("Debug: Parquet path:", results["parquet_base_path"])
            
            # Check in the results passed to this function
            if "visits_df" not in results:
                st.error("❌ Parquet data not available. This version requires Parquet pipeline.")
                if "parquet_base_path" in results:
                    st.info(f"Parquet files were saved to: {results['parquet_base_path']}")
                    st.info("But DataFrames were not loaded into results.")
                st.stop()
                
            # Get Parquet data directly from results
            visits_df = results["visits_df"]
            metadata_df = results["metadata_df"]
            stats_df = results["stats_df"]
            
            if get_debug_mode():
                st.info("✅ Using Parquet pipeline data")
                st.write(f"Visits shape: {visits_df.shape}")
                st.write(f"Enrichment columns: {[col for col in visits_df.columns if col.startswith(('is_', 'has_'))]}")
            
            # Import visualization functions that use enrichment flags
            from create_current_state_streamgraph_fixed import (
                prepare_current_state_data, 
                create_current_state_streamgraph
            )
            
            # Prepare data for current state visualization
            state_counts_df, state_categories = prepare_current_state_data(visits_df, metadata_df)
            
            # Create the streamgraph
            fig = create_current_state_streamgraph(
                state_counts_df,
                state_categories,
                metadata_df,
                stats_df
            )
            
            # Display the visualization
            st.plotly_chart(fig, use_container_width=True)
            
        except ImportError as e:
            st.error(f"Import error: {e}")
            st.info("Debugging: Check that all required modules are accessible")
            if get_debug_mode():
                import traceback
                st.code(traceback.format_exc())
        except Exception as e:
            st.error(f"Could not create current state visualization: {str(e)}")
            if get_debug_mode():
                import traceback
                st.code(traceback.format_exc())
    
    with cumulative_tab:
        st.write("**What patients have ever experienced**")
        
        # Try to create cumulative state visualization
        try:
            # PARQUET ONLY - No JSON fallback!
            # Check in the results passed to this function
            if "visits_df" not in results:
                st.error("❌ Parquet data not available. This version requires Parquet pipeline.")
                st.stop()
                
            # Get Parquet data directly from results
            visits_df = results["visits_df"]
            metadata_df = results["metadata_df"]
            stats_df = results["stats_df"]
            
            # Import visualization functions that use enrichment flags
            from create_patient_state_streamgraph_cumulative_fixed import (
                prepare_cumulative_state_data, 
                create_cumulative_streamgraph
            )
            
            # Prepare data for cumulative visualization
            state_counts_df, state_categories = prepare_cumulative_state_data(visits_df, metadata_df)
            
            # Create the streamgraph
            fig = create_cumulative_streamgraph(
                state_counts_df,
                state_categories,
                metadata_df,
                stats_df
            )
            
            # Display the visualization
            st.plotly_chart(fig, use_container_width=True)
            
            # Add interpretation guide
            with st.expander("📊 Understanding the Cumulative View"):
                st.markdown("""
                This view shows what patients have **ever experienced** during the simulation:
                
                - **Active (never discontinued)**: Patients who remained on treatment throughout
                - **Retreated**: Patients who discontinued but returned to treatment at least once
                - **Discontinued categories**: Shows the reason for discontinuation
                  - *Planned*: Achieved stable remission (good outcome)
                  - *Administrative*: System/booking failures
                  - *Duration*: Treatment course complete
                  - *Premature*: Stopped too early
                  - *Poor outcome*: Stopped due to vision loss
                
                **Key Insight**: Once a patient is retreated, they remain in the "Retreated" category 
                even if currently active, showing their treatment journey included interruption.
                """)
                
        except ImportError as e:
            st.error(f"Import error: {e}")
            st.info("Debugging: Check that all required modules are accessible")
            if get_debug_mode():
                import traceback
                st.code(traceback.format_exc())
        except Exception as e:
            st.error(f"Could not create cumulative visualization: {str(e)}")
            if get_debug_mode():
                import traceback
                st.code(traceback.format_exc())
    
    # Add expandable clinical glossary
    with st.expander("📖 Clinical State Definitions"):
        st.markdown("""
        ### Current State View
        Shows where patients are **right now** at each time point - better for operational planning.
        
        | **State** | **Clinical Meaning** | **Duration** |
        |-----------|---------------------|--------------|
        | **Active** | Currently receiving regular injections | Ongoing |
        | **Recommencing treatment** | Previously discontinued, now restarting (loading phase) | Transient (1-3 months) |
        | **Untreated - remission** | Stable patients who reached maximum intervals | Long-term |
        | **Not booked** | Administrative issues preventing treatment | Variable |
        | **Not renewed** | Course complete, clinician chose not to continue | Long-term |
        | **Discontinued without reason** | Clinician decision without clear documentation | Variable |
        
        ### Cumulative View  
        Shows what patients have **ever experienced** - better for outcome analysis.
        
        | **State** | **Clinical Meaning** |
        |-----------|---------------------|
        | **Active** | Never discontinued |
        | **Retreated** | Has experienced at least one treatment restart |
        | **Discontinued planned** | Has been discontinued due to stable remission |
        | **Discontinued administrative** | Has experienced administrative barriers |
        | **Discontinued duration** | Has completed treatment course without renewal |
        
        ### Key Insight
        **Why "Recommencing treatment" oscillates:** This represents patients currently in the retreatment process - a transient state lasting 1-3 months before returning to active treatment.
        """)
    
    # Show retreatment analysis
    if "discontinuation_counts" in results:
        display_retreatment_panel(results)
    
    # Show visual acuity over time
    st.subheader("Visual Acuity Over Time")
    
    # Show thumbnail previews
    st.write("**Quick Comparison**")
    thumb_col1, thumb_col2 = st.columns([1, 1])
    
    with thumb_col1:
        from streamlit_app_parquet.simulation_runner import generate_va_over_time_thumbnail
        thumb_fig1 = generate_va_over_time_thumbnail(results)
        st.pyplot(thumb_fig1)
        st.caption("Mean + 95% CI", unsafe_allow_html=True)
    
    with thumb_col2:
        from streamlit_app_parquet.simulation_runner import generate_va_distribution_thumbnail
        try:
            thumb_fig2 = generate_va_distribution_thumbnail(results)
            st.pyplot(thumb_fig2)
            st.caption("Patient Distribution", unsafe_allow_html=True)
        except ValueError:
            # This should never happen in production since we control data generation
            st.error("Patient data missing - simulation error")
    
    # Add some spacing
    st.write("")
    
    # Show full plots stacked
    st.write("**Mean Visual Acuity with Confidence Intervals**")
    fig1 = generate_va_over_time_plot(results)
    st.pyplot(fig1)
    
    # Show distribution plot
    st.write("**Distribution of Visual Acuity**")
    from streamlit_app_parquet.simulation_runner import generate_va_distribution_plot
    try:
        fig2 = generate_va_distribution_plot(results)
        st.pyplot(fig2)
    except ValueError as e:
        # This should never happen in production since we control data generation
        st.error(f"Cannot generate distribution plot: {e}")
        if st.session_state.get("debug_mode", False):
            st.exception(e)


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