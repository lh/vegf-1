"""
APE: AMD Protocol Explorer

This application provides an interactive dashboard for exploring and visualizing
AMD treatment protocols using Discrete Event Simulation (DES) and Agent-Based Simulation (ABS),
including detailed modeling of treatment discontinuation patterns.
"""

import os
import sys
import json
import subprocess
import platform
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import tempfile
from pathlib import Path

# Import Puppeteer helpers
try:
    from streamlit_app.puppeteer_helpers import add_puppeteer_support, selectable_radio, selectable_button, selectable_selectbox
except ImportError:
    # Fallback functions if puppeteer_helpers is not available
    def add_puppeteer_support():
        pass
    def selectable_radio(label, options, **kwargs):
        return st.radio(label, options, **kwargs)
    def selectable_button(label, **kwargs):
        return st.button(label, **kwargs)
    def selectable_selectbox(label, options, **kwargs):
        return st.selectbox(label, options, **kwargs)

# Add the project root directory to sys.path to allow importing from the main project
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root_dir)

# Add the current working directory as well for when running directly
sys.path.append(os.getcwd())

# Debug variables to show later
debug_info = {
    "root_dir": root_dir,
    "cwd": os.getcwd(),
    "sys_path": sys.path
}

# Import project modules
try:
    from simulation.config import SimulationConfig
except ImportError:
    # Handle missing imports gracefully
    SimulationConfig = None

# Import local modules
from streamlit_app.acknowledgments import ACKNOWLEDGMENT_TEXT
from streamlit_app.quarto_utils import get_quarto, render_quarto_report
from streamlit_app.patient_explorer import display_patient_explorer
from streamlit_app.retreatment_panel import display_retreatment_panel

try:
    from streamlit_app.amd_protocol_explorer import run_enhanced_discontinuation_dashboard
except ImportError:
    # Define a fallback function if the import fails
    def run_enhanced_discontinuation_dashboard(config_path=None):
        st.warning("Dashboard module failed to load correctly.")
        st.info("This may be due to missing dependencies or incorrect import paths.")

try:
    from streamlit_app.simulation_runner import (
        run_simulation, 
        get_ui_parameters,
        generate_va_over_time_plot,
        generate_discontinuation_plot,
        save_simulation_results,
        load_simulation_results
    )
except ImportError:
    # Define fallback functions if the imports fail
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
    
    def load_simulation_results(filepath):
        return {}


def display_logo_and_title(title, logo_width=100, column_ratio=[1, 4]):
    """Display the APE logo and title in columns.
    
    Parameters
    ----------
    title : str
        The title to display
    logo_width : int, optional
        Width of the logo image, by default 100
    column_ratio : list, optional
        Ratio for the columns [logo_col, title_col], by default [1, 4]
    """
    # Create columns for logo and title
    col1, col2 = st.columns(column_ratio)
    
    # Try to display logo in the first column
    try:
        # Try SVG first, then fall back to JPG if SVG not found
        svg_logo_path = os.path.join(os.path.dirname(__file__), "assets", "ape_logo.svg")
        jpg_logo_path = os.path.join(os.path.dirname(__file__), "assets", "ape_logo.jpg")
        
        if os.path.exists(svg_logo_path):
            col1.image(svg_logo_path, width=logo_width)
        elif os.path.exists(jpg_logo_path):
            col1.image(jpg_logo_path, width=logo_width)
    except Exception:
        pass
    
    # Display title in the second column
    col2.title(title)


# Determine favicon to use
favicon = "🦧"  # Default emoji fallback
try:
    svg_logo_path = os.path.join(os.path.dirname(__file__), "assets", "ape_logo.svg")
    if os.path.exists(svg_logo_path):
        favicon = svg_logo_path
except Exception:
    pass

# Set page configuration
st.set_page_config(
    page_title="APE: AMD Protocol Explorer",
    page_icon=favicon,
    layout="wide",
    initial_sidebar_state="expanded",
)

# Now add puppeteer support
try:
    add_puppeteer_support()
except Exception as e:
    # Silently handle errors to avoid breaking the app
    pass

# --- Sidebar ---
# Display logo image (if available) with fallback to text
try:
    # Try SVG first, then fall back to JPG if SVG not found
    svg_logo_path = os.path.join(os.path.dirname(__file__), "assets", "ape_logo.svg")
    jpg_logo_path = os.path.join(os.path.dirname(__file__), "assets", "ape_logo.jpg")
    
    if os.path.exists(svg_logo_path):
        st.sidebar.image(svg_logo_path, width=150)
    elif os.path.exists(jpg_logo_path):
        st.sidebar.image(jpg_logo_path, width=150)
    else:
        st.sidebar.title("APE: AMD Protocol Explorer")
except Exception:
    st.sidebar.title("APE: AMD Protocol Explorer")

st.sidebar.markdown("Interactive dashboard for exploring AMD treatment protocols")

# Show a notice about fixed implementation if applicable
try:
    from streamlit_app.simulation_runner import USING_FIXED_IMPLEMENTATION
    if USING_FIXED_IMPLEMENTATION:
        st.sidebar.success("""
        ### Using Fixed Discontinuation Implementation
        
        This app is using the fixed discontinuation implementation that properly tracks 
        unique patient discontinuations and prevents double-counting.
        
        The discontinuation rates shown will be accurate (≤100%).
        """)
except ImportError:
    pass

# Navigation - use regular radio for now since we encountered issues
page = st.sidebar.radio(
    "Navigate to",
    ["Dashboard", "Run Simulation", "Patient Explorer", "Reports", "About"],
    key="navigation",
    format_func=lambda x: f"{x}",  # For better screen reader support
    index=0,
    help="Select an application section to navigate to"
)

# Add a marker element to make navigation accessible for Puppeteer
st.sidebar.markdown('<div data-test-id="main-navigation-marker"></div>', unsafe_allow_html=True)

# Add a debug mode toggle in the sidebar (off by default)
debug_mode = st.sidebar.checkbox(
    "🛠️ Debug Mode", 
    value=False, 
    help="Show detailed diagnostic information",
    key="debug_mode_toggle"  # Added unique key
)

# Set debug mode in the simulation runner module
try:
    from streamlit_app.simulation_runner import DEBUG_MODE
    import streamlit_app.simulation_runner as sim_runner
    sim_runner.DEBUG_MODE = debug_mode
except ImportError:
    pass

# --- Main Content ---
if page == "Dashboard":
    display_logo_and_title("APE: AMD Protocol Explorer")
    st.markdown("""
    Welcome to APE: AMD Protocol Explorer. This interactive tool allows you
    to explore and visualize AMD treatment protocols through Discrete Event Simulation (DES)
    and Agent-Based Simulation (ABS), including detailed modeling of discontinuation patterns.
    
    Use the sidebar to navigate between different sections of the dashboard.
    """)
    
    # Advanced settings in an expander
    with st.expander("Advanced Settings"):
        st.write("To customize simulation parameters in detail, navigate to the 'Run Simulation' tab.")
    
    # Check if we have simulation results to display
    if "simulation_results" in st.session_state:
        results = st.session_state["simulation_results"]
        st.subheader("Latest Simulation Results")
        
        # Check if these are sample results
        if results.get("is_sample", False):
            st.warning("⚠️ **Sample Data**: These are simulated results using sample data, not actual simulation outputs.")
            st.info("The actual simulation module couldn't be loaded. This is likely because you're viewing the UI without having the full simulation codebase installed.")
            st.markdown("You can still explore the UI functionality with this sample data.")
        
        # Display metrics
        col1, col2, col3 = st.columns(3)
        
        # Calculate metrics
        total_patients = results["population_size"]
        discontinued_patients = results.get("total_discontinuations", 0)
        discontinued_percent = (discontinued_patients / total_patients * 100) if total_patients > 0 else 0
        
        # Get recurrence data with more details - WITH EMERGENCY DEBUG 
        recurrence_data = results.get("recurrences", {})
        # Force using sim stats for retreatments if available from raw_discontinuation_stats
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
        
        # Recurrence data has been calculated and is ready for display
        
        with col1:
            st.metric("Patients Discontinued", f"{discontinued_percent:.1f}%", f"{discontinued_patients} patients")
        
        with col2:
            # Show unique patient count if available, otherwise total
            recurrence_detail = f"{unique_recurrence_count} patients" if unique_recurrence_count != recurrence_count else f"{recurrence_count} recurrences"
            st.metric("Recurrence Rate", f"{recurrence_rate:.1f}%", recurrence_detail)
        
        with col3:
            st.metric("Mean Injections", f"{results.get('mean_injections', 0):.1f}", f"{results.get('total_injections', 0)} total")
        
        # Show visual acuity over time
        st.subheader("Visual Acuity Over Time")
        fig = generate_va_over_time_plot(results)
        st.pyplot(fig)
        
        # Show discontinuation plot if data available
        if "discontinuation_counts" in results:
            st.subheader("Discontinuation and Retreatment Analysis")
            figs = generate_discontinuation_plot(results)
            # Handle the case where generate_discontinuation_plot returns a list of figures
            if isinstance(figs, list):
                for fig in figs:
                    st.pyplot(fig)
            else:
                st.pyplot(figs)
            
            # Show retreatment analysis after discontinuation plot
            display_retreatment_panel(results)
    else:
        # Display instructions instead of sample visualization
        if debug_mode:
            st.info("No simulation results available. Please run a simulation in the 'Run Simulation' tab to view results here.")
        else:
            st.warning("No simulation results available. Please run a simulation to view results.")

elif page == "Run Simulation":
    display_logo_and_title("Run AMD Treatment Simulation")
    
    # Configuration options
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
            key="duration_years_slider"  # Added unique key
        )
        
        population_size = st.slider(
            "Population Size",
            min_value=100,
            max_value=10000,
            value=1000,
            step=100,
            help="Number of patients in the simulation",
            key="population_size_slider"  # Added unique key
        )
    
    with col2:
        st.subheader("Discontinuation Parameters")
        
        enable_clinician_variation = st.checkbox(
            "Enable Clinician Variation",
            value=True,
            help="Include variation in clinician adherence to protocol",
            key="enable_clinician_variation_checkbox"  # Added unique key
        )
        
        planned_discontinue_prob = st.slider(
            "Planned Discontinuation Probability",
            min_value=0.0,
            max_value=1.0,
            value=0.2,
            step=0.05,
            help="Probability of planned discontinuation when criteria are met",
            key="planned_discontinue_prob_slider"  # Added unique key
        )
        
        admin_discontinue_prob = st.slider(
            "Administrative Discontinuation Annual Probability",
            min_value=0.0,
            max_value=0.5,
            value=0.05,
            step=0.01,
            help="Annual probability of random administrative discontinuation",
            key="admin_discontinue_prob_slider"  # Added unique key
        )
        
        premature_discontinue_prob = st.slider(
            "Premature Discontinuation Probability Factor",
            min_value=0.0,
            max_value=5.0,
            value=2.0,
            step=0.1,
            help="Probability factor for premature discontinuations (clinician-dependent)",
            key="premature_discontinue_prob_slider"  # Added unique key
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
                key="recurrence_risk_multiplier_slider"  # Added unique key
            )
            
            consecutive_stable_visits = st.slider(
                "Consecutive Stable Visits Required",
                min_value=1,
                max_value=5,
                value=3,
                step=1,
                help="Number of consecutive stable visits required for discontinuation",
                key="consecutive_stable_visits_slider"  # Added unique key
            )
        
        with col2:
            monitoring_schedule = st.multiselect(
                "Monitoring Schedule (weeks after discontinuation)",
                options=[4, 8, 12, 16, 24, 36, 48, 52],
                default=[12, 24, 36],
                help="Weeks after discontinuation for follow-up visits",
                key="monitoring_schedule_multiselect"  # Added unique key
            )
            
            no_monitoring_for_admin = st.checkbox(
                "No Monitoring for Administrative Discontinuation",
                value=True,
                help="Don't schedule monitoring visits for administrative discontinuations",
                key="no_monitoring_for_admin_checkbox"  # Added unique key
            )
    
    # Store UI parameters in session state
    # Add a marker element for Puppeteer to locate the button
    st.markdown('<div data-test-id="run-simulation-btn-marker"></div>', unsafe_allow_html=True)
    if st.button("Run Simulation", type="primary", key="run_simulation_button", help="Run the simulation with current parameters"):
        # Check if SimulationConfig is available
        simulation_can_run = True
        if SimulationConfig is None:
            st.error("Cannot run simulation: required simulation modules are not available.")
            st.info("This may be due to missing dependencies or incorrect import paths.")
            simulation_can_run = False
        
        # Save all parameters to session state
        st.session_state["simulation_type"] = simulation_type
        st.session_state["duration_years"] = duration_years
        st.session_state["population_size"] = population_size
        st.session_state["enable_clinician_variation"] = enable_clinician_variation
        st.session_state["planned_discontinue_prob"] = planned_discontinue_prob
        st.session_state["admin_discontinue_prob"] = admin_discontinue_prob
        st.session_state["premature_discontinue_prob"] = premature_discontinue_prob
        st.session_state["consecutive_stable_visits"] = consecutive_stable_visits
        st.session_state["monitoring_schedule"] = monitoring_schedule
        st.session_state["no_monitoring_for_admin"] = no_monitoring_for_admin
        st.session_state["recurrence_risk_multiplier"] = recurrence_risk_multiplier
        
        # Get parameters from session state
        params = get_ui_parameters()
        
        # Initialize results
        results = None
        
        # Run the simulation if possible, otherwise use sample data
        if simulation_can_run:
            with st.spinner(f"Running {simulation_type} simulation with {population_size} patients over {duration_years} years..."):
                st.session_state["simulation_running"] = True
                
                try:
                    # Run simulation
                    results = run_simulation(params)
                    
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
                        
                        # Store patient histories in session state if available
                        if "patient_histories" in results:
                            st.session_state["patient_histories"] = results["patient_histories"]
                        
                        # Show success message
                        if debug_mode and "runtime_seconds" in results:
                            st.success(f"Simulation complete in {results['runtime_seconds']:.2f} seconds!")
                        else:
                            st.success("Simulation complete!")
                except Exception as e:
                    st.error(f"Error running simulation: {str(e)}")
                    # Create a minimal results object
                    results = {
                        "simulation_type": simulation_type,
                        "population_size": population_size,
                        "duration_years": duration_years,
                        "enable_clinician_variation": enable_clinician_variation,
                        "planned_discontinue_prob": planned_discontinue_prob,
                        "admin_discontinue_prob": admin_discontinue_prob,
                        "error": str(e),
                        "failed": True
                    }
        
        # Save results in session state
        st.session_state["simulation_results"] = results
        st.session_state["simulation_complete"] = True
        st.session_state["simulation_running"] = False
        
        # Show results
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

                # Show patient structure info if available
                if "patient_structure_info" in results:
                    st.markdown("### Patient Structure Analysis")
                    for info in results["patient_structure_info"]:
                        st.text(info)

                # Show failures if any
                if va_stats.get("extraction_failures"):
                    st.markdown("### Extraction Failures")
                    st.write(f"Failed to extract acuity data from {len(va_stats['extraction_failures'])} patients.")

                    # First failure details as sample
                    first_failure = list(va_stats["extraction_failures"].items())[0] if va_stats["extraction_failures"] else None
                    if first_failure:
                        st.markdown("#### Sample Patient Structure:")
                        st.json(first_failure[1])

                # Show VA data summary if available
                if "va_data_summary" in results:
                    st.markdown("### VA Data Summary")
                    st.json(results["va_data_summary"])

                # Option to sample a patient record to help diagnose format issues
                if "patient_histories" in st.session_state and st.session_state.get("patient_histories"):
                    st.markdown("### Sample Patient Record")

                    # Get patient histories from session state
                    patient_histories = st.session_state["patient_histories"]

                    # Get first patient ID
                    first_patient_id = next(iter(patient_histories))

                    # Show the first visit record to help debug extraction issues
                    patient_record = patient_histories[first_patient_id]

                    if isinstance(patient_record, list) and len(patient_record) > 0:
                        # For list-type records, show first few visits
                        max_visits = min(3, len(patient_record))
                        st.markdown(f"**First {max_visits} visits of patient {first_patient_id}:**")

                        for i, visit in enumerate(patient_record[:max_visits]):
                            st.markdown(f"**Visit {i+1}:**")
                            st.json(visit)
        
        else:
            # Only display metrics if simulation succeeded
            # Display metrics
            col1, col2, col3 = st.columns(3)
            
            # Calculate metrics
            total_patients = results["population_size"]
            discontinued_patients = results.get("total_discontinuations", 0)
            discontinued_percent = (discontinued_patients / total_patients * 100) if total_patients > 0 else 0
            
            # Get recurrence data with more details - WITH EMERGENCY DEBUG 
            recurrence_data = results.get("recurrences", {})
            # Force using sim stats for retreatments if available from raw_discontinuation_stats
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
            
            # Recurrence data has been calculated and is ready for display
            
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
                
                # Process discontinuation counts data
                
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
                
                # Removed redundant interactive bar chart (GRAPHIC G)
                
                # We'll show the discontinuation plot in the "Discontinuation and Retreatment Analysis" section below
                # rather than displaying it twice
            else:
                st.warning("No discontinuation data available in simulation results. Check simulation configuration.")
            
            # Show discontinuation and retreatment analysis
            if "discontinuation_counts" in results:
                st.subheader("Discontinuation and Retreatment Analysis")
                figs = generate_discontinuation_plot(results)
                # Display the discontinuation plot (now just a single figure)
                if isinstance(figs, list):
                    for fig in figs:
                        st.pyplot(fig)
                else:
                    st.pyplot(figs)
                
                # Show retreatment analysis only once
                display_retreatment_panel(results)
            
            # Show visual acuity over time
            st.subheader("Visual Acuity Over Time")
            fig = generate_va_over_time_plot(results)
            st.pyplot(fig)

elif page == "Patient Explorer":
    display_logo_and_title("Patient Explorer")
    
    # Check if we have simulation results to display
    if "simulation_results" in st.session_state and "patient_histories" in st.session_state:
        results = st.session_state["simulation_results"]
        patient_histories = st.session_state["patient_histories"]
        
        # Display the patient explorer
        display_patient_explorer(patient_histories, results)
    else:
        st.warning("No simulation data available. Please run a simulation first.")
        st.markdown("""
        The Patient Explorer allows you to:
        
        - Select individual patients from simulation results
        - View their complete treatment journey
        - Analyze visual acuity changes over time
        - Examine treatment phases and decisions
        - Review detailed visit history
        
        Run a simulation in the 'Run Simulation' tab to explore patient data.
        """)

elif page == "Reports":
    display_logo_and_title("Generate Reports")
    
    # Ensure Quarto is available
    quarto_path = get_quarto()
    
    if not quarto_path:
        st.error("Quarto is not available. Reports cannot be generated.")
    else:
        st.success(f"Quarto is available at: {quarto_path}")
        
        st.subheader("Generate Simulation Report")
        st.markdown("""
        Generate a comprehensive report of the simulation results. The report will include
        detailed statistics, visualizations, and analysis of the enhanced discontinuation model.
        """)
        
        # Report options
        report_format = st.radio(
            "Report Format",
            ["HTML", "PDF", "Word"],
            horizontal=True,
            help="Select the output format for the report",
            key="report_format_radio"  # Added unique key
        )
        
        include_code = st.checkbox(
            "Include Code",
            value=False,
            help="Include the code used to generate the visualizations in the report",
            key="include_code_checkbox"  # Added unique key
        )
        
        include_appendix = st.checkbox(
            "Include Appendix",
            value=True,
            help="Include additional details and methodology in an appendix",
            key="include_appendix_checkbox"  # Added unique key
        )
        
        # Generate report button
        if st.button("Generate Report", type="primary", key="generate_report_button", help="Generate a detailed report of simulation results"):
            if "simulation_complete" not in st.session_state or not st.session_state["simulation_complete"]:
                st.warning("Please run a simulation first before generating a report.")
            else:
                with st.spinner("Generating report..."):
                    # TODO: Actually generate the report using Quarto
                    # This is a placeholder
                    try:
                        # Create temporary directory for report
                        with tempfile.TemporaryDirectory() as tmp_dir:
                            # Use actual simulation results if available, otherwise use sample data
                            if "simulation_results" in st.session_state:
                                data = st.session_state["simulation_results"]
                                # Check if these are sample results
                                if data.get("is_sample", False):
                                    st.warning("⚠️ **Sample Data**: This report will use sample data, not actual simulation outputs.")
                                    st.info("The actual simulation module couldn't be loaded. The report will still be generated but with simulated data.")
                            else:
                                st.warning("Using sample data. Run a simulation first for more accurate reports.")
                                # Sample data for testing
                                data = {
                                    "simulation_type": "ABS",
                                    "population_size": 1000,
                                    "duration_years": 5,
                                    "planned_discontinue_prob": 0.2,
                                    "admin_discontinue_prob": 0.05,
                                    "enable_clinician_variation": True,
                                    "discontinuation_counts": {
                                        "Planned": 250,
                                        "Administrative": 120,
                                        "Time-based": 180,
                                        "Premature": 80
                                    }
                                }
                            
                            data_path = os.path.join(tmp_dir, "simulation_results.json")
                            with open(data_path, 'w') as f:
                                json.dump(data, f)
                            
                            # Define paths
                            qmd_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reports", "simulation_report.qmd")
                            output_format = report_format.lower()
                            
                            # Render report
                            report_path = render_quarto_report(
                                quarto_path,
                                qmd_path,
                                tmp_dir,
                                data_path,
                                output_format,
                                include_code=include_code,
                                include_appendix=include_appendix
                            )
                            
                            # Show success and provide download button
                            if report_path and os.path.exists(report_path):
                                st.success("Report generated successfully!")
                                
                                # Read the report file
                                with open(report_path, "rb") as f:
                                    report_data = f.read()
                                
                                # Create a download button
                                file_extension = output_format if output_format != "html" else "html"
                                st.download_button(
                                    label=f"Download {report_format} Report",
                                    data=report_data,
                                    file_name=f"enhanced_discontinuation_report.{file_extension}",
                                    mime=f"application/{file_extension}",
                                    key="download_report_button"  # Added unique key
                                )
                            else:
                                st.error("Failed to generate report.")
                    except Exception as e:
                        st.error(f"Error generating report: {str(e)}")

elif page == "About":
    display_logo_and_title("About APE: AMD Protocol Explorer")
    
    st.markdown("""
    APE: AMD Protocol Explorer provides an interactive interface for exploring AMD treatment protocols
    through simulation. The tool incorporates both Discrete Event Simulation (DES) and Agent-Based Simulation (ABS)
    approaches, with detailed modeling of discontinuation patterns, clinician variation, and time-dependent
    recurrence probabilities based on clinical data.
    
    ### Features
    
    - **Interactive Visualization**: Explore simulation results through interactive charts and tables
    - **Customizable Simulations**: Configure simulation parameters to test different scenarios
    - **Detailed Reports**: Generate comprehensive reports with Quarto integration
    - **Model Validation**: Compare simulation results with clinical data
    
    ### Implementation Details
    
    APE includes a sophisticated model of treatment discontinuation and recurrence in AMD treatment.
    The simulations use both DES and ABS approaches to provide comprehensive insights.
    Key components include:
    
    - Multiple discontinuation types (protocol-based, administrative, not renewed, premature)
    - Type-specific monitoring schedules
    - Time-dependent recurrence probabilities based on clinical data
    - Clinician variation in protocol adherence and treatment decisions
    """)
    
    # Display acknowledgments
    st.markdown(ACKNOWLEDGMENT_TEXT)
    
    # Contact information
    st.subheader("Contact")
    st.markdown("""
    For questions or feedback about this dashboard, please contact:
    
    [Your Contact Information]
    """)


# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("© 2025 APE: AMD Protocol Explorer")