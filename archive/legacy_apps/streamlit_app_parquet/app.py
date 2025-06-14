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

# This version is ALWAYS Parquet!

# Determine favicon to use (this needs to be before set_page_config)
favicon = "🦧"  # Default emoji fallback
try:
    svg_logo_path = os.path.join(os.path.dirname(__file__), "assets", "ape_logo.svg")
    if os.path.exists(svg_logo_path):
        favicon = svg_logo_path
except Exception:
    pass

# Set page configuration - must be first Streamlit command
st.set_page_config(
    page_title="APE: AMD Protocol Explorer",
    page_icon=favicon,
    layout="wide",
    initial_sidebar_state="expanded",
)

# CRITICAL: Check if we're running from the correct working directory
expected_files = ["protocols", "simulation", "README.md"]
missing_files = [f for f in expected_files if not Path(f).exists()]

if missing_files:
    st.error(f"""
    ❌ **Wrong working directory detected!**
    
    Missing: {', '.join(missing_files)}
    
    **Please run from project root:**
    ```bash
    cd /path/to/your/project/
    streamlit run streamlit_app/app.py
    ```
    
    **Current working directory:** `{os.getcwd()}`
    """)
    st.stop()

# Import Puppeteer helpers
try:
    from streamlit_app_parquet.puppeteer_helpers import add_puppeteer_support, selectable_radio, selectable_button, selectable_selectbox
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
from streamlit_app_parquet.acknowledgments import ACKNOWLEDGMENT_TEXT
from streamlit_app_parquet.quarto_utils import get_quarto, render_quarto_report
from streamlit_app_parquet.patient_explorer import display_patient_explorer
from streamlit_app_parquet.retreatment_panel import display_retreatment_panel
# Note: Staggered simulation is now handled by Streamlit's multi-page app feature
# from streamlit_app_parquet.pages.staggered_simulation_page import run_staggered_simulation_page

try:
    from streamlit_app_parquet.amd_protocol_explorer import run_enhanced_discontinuation_dashboard
except ImportError:
    # Define a fallback function if the import fails
    def run_enhanced_discontinuation_dashboard(config_path=None):
        st.warning("Dashboard module failed to load correctly.")
        st.info("This may be due to missing dependencies or incorrect import paths.")

try:
    from streamlit_app_parquet.simulation_runner import (
        run_simulation, 
        get_ui_parameters,
        generate_va_over_time_plot,
        generate_discontinuation_plot
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
    
    # Removed JSON save/load - Parquet only!


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

# Show that this is the Parquet version
st.sidebar.success("""
### 🚀 Parquet-Enhanced Version

This version provides:
- Full discontinuation categorization
- Retreatment tracking  
- Enhanced state flags
- Rich patient state visualization
""")

# Show a notice about fixed implementation if applicable
try:
    from streamlit_app_parquet.simulation_runner import USING_FIXED_IMPLEMENTATION
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
    ["Dashboard", "Run Simulation", "Calendar-Time Analysis", "Patient Explorer", "Reports", "About"],
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
    from streamlit_app_parquet.simulation_runner import DEBUG_MODE
    import streamlit_app_parquet.simulation_runner as sim_runner
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
            # Calculate average VA change
            va_change = results.get("va_change", {})
            mean_va_change = va_change.get("mean", 0)
            st.metric("Mean VA Change", f"{mean_va_change:+.1f} letters", "From baseline")
        
        # Display visualization tabs
        st.subheader("Visualizations")
        tab1, tab2, tab3 = st.tabs(["Patient States", "VA Over Time", "Retreatment Analysis"])
        
        with tab1:
            if "streamgraph" in results:
                st.pyplot(results["streamgraph"])
            else:
                st.info("No patient state visualization available for this simulation.")
        
        with tab2:
            if "va_plot" in results:
                st.pyplot(results["va_plot"])
            else:
                st.info("No visual acuity data available for this simulation.")
        
        with tab3:
            # Display retreatment panel
            display_retreatment_panel(results)
    else:
        st.info("No simulation results available. Run a simulation to see results here.")
        
        # Show a sample image of what the dashboard will look like
        try:
            sample_img_path = os.path.join(os.path.dirname(__file__), "assets", "sample_dashboard.png")
            if os.path.exists(sample_img_path):
                st.image(sample_img_path, caption="Sample Dashboard Visualization")
        except Exception:
            pass

elif page == "Run Simulation":
    display_logo_and_title("Run Simulation")
    
    st.markdown("""
    This page allows you to run new simulations with custom parameters.
    Configure your simulation settings below and click 'Run Simulation' to start.
    """)
    
    # Create expandable section for simulation settings
    with st.expander("Simulation Settings", expanded=True):
        # Get parameters from UI
        params = get_ui_parameters()
        
        # Create columns for a more compact layout
        col1, col2 = st.columns(2)
        
        with col1:
            # Core simulation parameters
            st.subheader("Simulation Parameters")
            
            # Simulation type (ABS or DES)
            params["simulation_type"] = selectable_radio(
                "Simulation Type",
                ["ABS", "DES"],
                help="Agent-Based Simulation (ABS) or Discrete Event Simulation (DES)",
                horizontal=True,
                key="sim_type"
            )
            
            # Population size
            params["population_size"] = st.slider(
                "Population Size",
                min_value=10,
                max_value=1000,
                value=100,
                step=10,
                help="Number of patients to simulate"
            )
            
            # Simulation duration
            params["duration_years"] = st.slider(
                "Simulation Duration (years)",
                min_value=1,
                max_value=10,
                value=5,
                step=1,
                help="Duration of simulation in years"
            )
            
            if debug_mode:
                # Advanced debug option to enable fixed implementation
                params["use_fixed_implementation"] = st.checkbox(
                    "Use Fixed Implementation", 
                    value=True,
                    help="Use the fixed implementation for discontinuation tracking"
                )
        
        with col2:
            # Protocol parameters
            st.subheader("Protocol Parameters")
            
            # Protocol selection
            protocol_options = ["Treat and Extend", "Fixed", "PRN", "Hybrid"]
            params["protocol"] = selectable_selectbox(
                "Treatment Protocol",
                protocol_options,
                help="Select the treatment protocol to simulate",
                key="protocol"
            )
            
            # Discontinuation probability
            params["discontinuation_probability"] = st.slider(
                "Discontinuation Probability",
                min_value=0.0,
                max_value=1.0,
                value=0.2,
                step=0.05,
                help="Probability of discontinuation when criteria are met"
            )
            
            # Administrative discontinuation rate
            params["administrative_discontinuation_rate"] = st.slider(
                "Administrative Discontinuation Rate",
                min_value=0.0,
                max_value=0.5,
                value=0.05,
                step=0.01,
                help="Annual rate of random administrative discontinuations"
            )
    
    # Advanced options expander
    with st.expander("Advanced Options"):
        # Enhanced discontinuation options
        st.subheader("Enhanced Discontinuation Options")
        
        # Option to enable retreatment
        params["enable_retreatment"] = st.checkbox(
            "Enable Retreatment",
            value=True,
            help="Allow patients to return to treatment after discontinuation"
        )
        
        if params["enable_retreatment"]:
            # Retreatment probability by discontinuation type
            st.write("Retreatment Probability by Discontinuation Type")
            
            params["retreatment_probability"] = {}
            
            col1, col2 = st.columns(2)
            with col1:
                params["retreatment_probability"]["stable_max_interval"] = st.slider(
                    "Planned Discontinuation",
                    min_value=0.0,
                    max_value=1.0,
                    value=0.3,
                    step=0.05,
                    help="Probability of retreatment after planned discontinuation"
                )
                
                params["retreatment_probability"]["random_administrative"] = st.slider(
                    "Administrative Discontinuation",
                    min_value=0.0,
                    max_value=1.0,
                    value=0.5,
                    step=0.05,
                    help="Probability of retreatment after administrative discontinuation"
                )
            
            with col2:
                params["retreatment_probability"]["course_complete"] = st.slider(
                    "Course Complete",
                    min_value=0.0,
                    max_value=1.0,
                    value=0.2,
                    step=0.05,
                    help="Probability of retreatment after course completion"
                )
                
                params["retreatment_probability"]["premature"] = st.slider(
                    "Premature Discontinuation",
                    min_value=0.0,
                    max_value=1.0,
                    value=0.7,
                    step=0.05,
                    help="Probability of retreatment after premature discontinuation"
                )
    
    # Run simulation button
    if selectable_button("Run Simulation", key="run_sim_button", type="primary"):
        with st.spinner("Running simulation..."):
            try:
                results = run_simulation(params)
                
                # Store results in session state
                st.session_state["simulation_results"] = results
                st.session_state["simulation_params"] = params
                
                if "error" in results:
                    st.error(f"Simulation failed: {results['error']}")
                else:
                    st.success("Simulation completed successfully!")
                    
                    # Display key metrics
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        total_patients = results["population_size"]
                        discontinued_patients = results.get("total_discontinuations", 0)
                        discontinued_percent = (discontinued_patients / total_patients * 100) if total_patients > 0 else 0
                        st.metric("Patients Discontinued", f"{discontinued_percent:.1f}%", f"{discontinued_patients} patients")
                    
                    with col2:
                        recurrence_data = results.get("recurrences", {})
                        recurrence_count = recurrence_data.get("total", 0)
                        recurrence_rate = (recurrence_count / discontinued_patients * 100) if discontinued_patients > 0 else 0
                        st.metric("Recurrence Rate", f"{recurrence_rate:.1f}%", f"{recurrence_count} recurrences")
                    
                    with col3:
                        va_change = results.get("va_change", {})
                        mean_va_change = va_change.get("mean", 0)
                        st.metric("Mean VA Change", f"{mean_va_change:+.1f} letters", "From baseline")
                    
                    # Create tabs for different visualizations
                    tabs = st.tabs(["Patient States", "VA Over Time", "Retreatment Analysis"])
                    
                    with tabs[0]:
                        # Display streamgraph if available
                        if "streamgraph" in results:
                            st.pyplot(results["streamgraph"])
                        else:
                            streamgraph = generate_discontinuation_plot(results)
                            st.pyplot(streamgraph)
                    
                    with tabs[1]:
                        # Display VA plot
                        va_plot = generate_va_over_time_plot(results)
                        st.pyplot(va_plot)
                    
                    with tabs[2]:
                        # Display retreatment panel
                        display_retreatment_panel(results)
                    
                    # Results are automatically saved as Parquet
                    if "parquet_base_path" in results:
                        st.info(f"Results saved to: {results['parquet_base_path']}")
            
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
                st.exception(e)
    
    # Removed JSON loading - Parquet only!
    # Results are loaded directly from Parquet files when needed

elif page == "Calendar-Time Analysis":
    # This is now handled by Streamlit's multi-page app
    st.info("Please use the 📅 Calendar Time Analysis option in the sidebar.")

elif page == "Patient Explorer":
    display_logo_and_title("Patient Explorer")
    
    # Check if we have simulation results
    if "simulation_results" not in st.session_state:
        st.warning("No simulation results available. Run a simulation first.")
    else:
        # Display patient explorer
        display_patient_explorer(st.session_state["simulation_results"])

elif page == "Reports":
    display_logo_and_title("Reports")
    
    st.markdown("""
    Generate reports from simulation results with customizable formats and content.
    """)
    
    # Check if quarto is available
    quarto_path = get_quarto()
    
    if not quarto_path:
        st.warning("Quarto not found. Reports will have limited functionality.")
    else:
        st.success(f"Quarto is available at: {quarto_path}")
    
    # Check if we have simulation results
    if "simulation_results" not in st.session_state:
        st.warning("No simulation results available. Run a simulation first.")
    else:
        st.subheader("Generate Report")
        
        # Report options
        col1, col2 = st.columns(2)
        
        with col1:
            report_format = st.selectbox(
                "Report Format",
                ["HTML", "PDF", "Word", "Markdown"],
                index=0,
                help="Choose the format for the generated report"
            )
            
            include_code = st.checkbox(
                "Include Code",
                value=False,
                help="Include code snippets in the report"
            )
        
        with col2:
            include_appendix = st.checkbox(
                "Include Appendix",
                value=True,
                help="Include technical appendix with detailed methodology"
            )
            
            include_raw_data = st.checkbox(
                "Include Raw Data",
                value=False,
                help="Include raw data tables in the report"
            )
        
        # Generate report button
        if st.button("Generate Report", type="primary"):
            with st.spinner("Generating report..."):
                try:
                    # Get the path to the report template
                    template_path = os.path.join(os.path.dirname(__file__), "reports", "simulation_report.qmd")
                    
                    if not os.path.exists(template_path):
                        st.error(f"Report template not found at: {template_path}")
                    else:
                        # Create a temporary directory for the report
                        with tempfile.TemporaryDirectory() as tmp_dir:
                            # Save the results to a JSON file
                            results_path = os.path.join(tmp_dir, "results.json")
                            with open(results_path, "w") as f:
                                json.dump(st.session_state["simulation_results"], f)
                            
                            # Define the output format
                            fmt = report_format.lower()
                            if fmt == "word":
                                fmt = "docx"
                            
                            # Render the report
                            output_path = render_quarto_report(
                                quarto_path=quarto_path,
                                template_path=template_path,
                                output_dir=tmp_dir,
                                data_path=results_path,
                                format=fmt,
                                include_code=include_code,
                                include_appendix=include_appendix,
                                include_raw_data=include_raw_data
                            )
                            
                            if output_path and os.path.exists(output_path):
                                # Read the generated report
                                with open(output_path, "rb") as f:
                                    report_data = f.read()
                                
                                # Generate a download link
                                st.download_button(
                                    label=f"Download {report_format} Report",
                                    data=report_data,
                                    file_name=f"simulation_report.{fmt}",
                                    mime=f"application/{fmt}"
                                )
                                
                                st.success("Report generated successfully!")
                            else:
                                st.error("Failed to generate report.")
                
                except Exception as e:
                    st.error(f"Error generating report: {str(e)}")
                    if debug_mode:
                        st.exception(e)

elif page == "About":
    display_logo_and_title("About")
    
    st.markdown("""
    ## APE: AMD Protocol Explorer
    
    APE is a tool for exploring and visualizing Age-related Macular Degeneration (AMD) treatment protocols
    through simulation and data analysis. The tool allows researchers and clinicians to better understand
    the impact of different treatment strategies on visual outcomes for patients with AMD.
    
    ### Key Features
    
    - **Simulation**: Run both Discrete Event Simulation (DES) and Agent-Based Simulation (ABS) models
    - **Visualization**: Explore results through interactive visualizations
    - **Patient Explorer**: Examine individual patient journeys and outcomes
    - **Reporting**: Generate comprehensive reports of simulation results
    
    ### Enhanced Discontinuation Model
    
    This version includes a sophisticated model of treatment discontinuation and retreatment
    that accounts for multiple discontinuation types:
    
    - **Planned Discontinuation**: Clinician-initiated treatment cessation due to patient stability
    - **Administrative Discontinuation**: Random discontinuation for non-clinical reasons
    - **Course Completion**: Discontinuation after a fixed treatment duration
    - **Premature Discontinuation**: Patient-initiated treatment cessation
    
    The model also simulates retreatment after discontinuation with parameters specific to each
    discontinuation type.
    """)
    
    # Display acknowledgments
    st.subheader("Acknowledgments")
    st.markdown(ACKNOWLEDGMENT_TEXT)
    
    # Show debug info if debug mode is enabled
    if debug_mode:
        st.subheader("Debug Information")
        st.json(debug_info)

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("© 2025 AMD Protocol Explorer")