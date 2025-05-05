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

# Add the parent directory to sys.path to allow importing from the main project
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import project modules
from simulation.config import SimulationConfig
from streamlit_app.acknowledgments import ACKNOWLEDGMENT_TEXT
from streamlit_app.amd_protocol_explorer import run_enhanced_discontinuation_dashboard
from streamlit_app.quarto_utils import get_quarto, render_quarto_report


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
        logo_path = os.path.join(os.path.dirname(__file__), "assets", "ape_logo.jpg")
        if os.path.exists(logo_path):
            col1.image(logo_path, width=logo_width)
    except Exception:
        pass
    
    # Display title in the second column
    col2.title(title)


# Set page configuration
st.set_page_config(
    page_title="APE: AMD Protocol Explorer",
    page_icon="🦧",  # Fallback emoji if image doesn't load
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Sidebar ---
# Display logo image (if available) with fallback to text
try:
    logo_path = os.path.join(os.path.dirname(__file__), "assets", "ape_logo.jpg")
    if os.path.exists(logo_path):
        st.sidebar.image(logo_path, width=150)
    else:
        st.sidebar.title("APE: AMD Protocol Explorer")
except Exception:
    st.sidebar.title("APE: AMD Protocol Explorer")

st.sidebar.markdown("Interactive dashboard for exploring AMD treatment protocols")

# Navigation
page = st.sidebar.radio(
    "Navigate to",
    ["Dashboard", "Run Simulation", "Reports", "About"]
)

# --- Main Content ---
if page == "Dashboard":
    display_logo_and_title("APE: AMD Protocol Explorer")
    st.markdown("""
    Welcome to APE: AMD Protocol Explorer. This interactive tool allows you
    to explore and visualize AMD treatment protocols through Discrete Event Simulation (DES)
    and Agent-Based Simulation (ABS), including detailed modeling of discontinuation patterns.
    
    Use the sidebar to navigate between different sections of the dashboard.
    """)
    
    # Display some sample visualizations or statistics
    st.subheader("Sample Visualization")
    
    # TODO: Replace with actual visualization from simulation results
    # This is a placeholder that will be updated with actual visualizations
    fig, ax = plt.subplots(figsize=(10, 6))
    x = np.linspace(0, 10, 100)
    y1 = np.sin(x)
    y2 = np.cos(x)
    ax.plot(x, y1, label="Treatment A")
    ax.plot(x, y2, label="Treatment B")
    ax.set_xlabel("Time (years)")
    ax.set_ylabel("Visual Acuity")
    ax.set_title("Sample Treatment Comparison")
    ax.legend()
    st.pyplot(fig)

elif page == "Run Simulation":
    display_logo_and_title("Run AMD Treatment Simulation")
    
    # Configuration options
    st.subheader("Simulation Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        simulation_type = st.selectbox(
            "Simulation Type",
            ["ABS", "DES"],
            help="Agent-Based Simulation (ABS) or Discrete Event Simulation (DES)"
        )
        
        duration_years = st.slider(
            "Simulation Duration (years)",
            min_value=1,
            max_value=10,
            value=5,
            help="Duration of the simulation in years"
        )
        
        population_size = st.slider(
            "Population Size",
            min_value=100,
            max_value=10000,
            value=1000,
            step=100,
            help="Number of patients in the simulation"
        )
    
    with col2:
        st.subheader("Discontinuation Parameters")
        
        enable_clinician_variation = st.checkbox(
            "Enable Clinician Variation",
            value=True,
            help="Include variation in clinician adherence to protocol"
        )
        
        planned_discontinue_prob = st.slider(
            "Planned Discontinuation Probability",
            min_value=0.0,
            max_value=1.0,
            value=0.2,
            step=0.05,
            help="Probability of planned discontinuation when criteria are met"
        )
        
        admin_discontinue_prob = st.slider(
            "Administrative Discontinuation Annual Probability",
            min_value=0.0,
            max_value=0.5,
            value=0.05,
            step=0.01,
            help="Annual probability of random administrative discontinuation"
        )
    
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
                help="Multiplier for disease recurrence rates"
            )
            
            consecutive_stable_visits = st.slider(
                "Consecutive Stable Visits Required",
                min_value=1,
                max_value=5,
                value=3,
                step=1,
                help="Number of consecutive stable visits required for discontinuation"
            )
        
        with col2:
            monitoring_schedule = st.multiselect(
                "Monitoring Schedule (weeks after discontinuation)",
                options=[4, 8, 12, 16, 24, 36, 48, 52],
                default=[12, 24, 36],
                help="Weeks after discontinuation for follow-up visits"
            )
            
            no_monitoring_for_admin = st.checkbox(
                "No Monitoring for Administrative Discontinuation",
                value=True,
                help="Don't schedule monitoring visits for administrative discontinuations"
            )
    
    # Run simulation button
    if st.button("Run Simulation", type="primary"):
        with st.spinner("Running simulation..."):
            st.session_state["simulation_running"] = True
            # TODO: Actually run the simulation with the selected parameters
            # This is a placeholder
            import time
            time.sleep(3)  # Simulate computation time
            st.session_state["simulation_complete"] = True
            st.success("Simulation complete!")
        
            # Show some results
            st.subheader("Simulation Results")
            
            # These are placeholder metrics and visualizations
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Patients Discontinued", f"{42}%", "5%")
            with col2:
                st.metric("Recurrence Rate", f"{23}%", "-2%")
            with col3:
                st.metric("Vision Preserved", f"{76}%", "8%")
            
            # Display a placeholder results table
            st.subheader("Discontinuation Types")
            df = pd.DataFrame({
                "Type": ["Planned", "Administrative", "Time-based", "Premature"],
                "Count": [250, 120, 180, 80],
                "Percentage": ["40%", "19%", "29%", "12%"],
                "Mean Time to Recurrence (weeks)": [48.2, 32.5, 40.1, 24.8]
            })
            st.dataframe(df, use_container_width=True)
            
            # Charts placeholder
            st.subheader("Visual Acuity Over Time")
            # This will be replaced with actual simulation results
            fig, ax = plt.subplots(figsize=(10, 6))
            x = np.linspace(0, duration_years, 100)
            y = 80 - 3 * x + 2 * np.sin(x)
            ax.plot(x, y)
            ax.set_xlabel("Time (years)")
            ax.set_ylabel("Visual Acuity (letters)")
            ax.set_title("Mean Visual Acuity Over Time")
            st.pyplot(fig)

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
            help="Select the output format for the report"
        )
        
        include_code = st.checkbox(
            "Include Code",
            value=False,
            help="Include the code used to generate the visualizations in the report"
        )
        
        include_appendix = st.checkbox(
            "Include Appendix",
            value=True,
            help="Include additional details and methodology in an appendix"
        )
        
        # Generate report button
        if st.button("Generate Report", type="primary"):
            if "simulation_complete" not in st.session_state or not st.session_state["simulation_complete"]:
                st.warning("Please run a simulation first before generating a report.")
            else:
                with st.spinner("Generating report..."):
                    # TODO: Actually generate the report using Quarto
                    # This is a placeholder
                    try:
                        # Create temporary directory for report
                        with tempfile.TemporaryDirectory() as tmp_dir:
                            # Create a temporary data file that would normally contain simulation results
                            data = {
                                "simulation_type": "ABS",
                                "population_size": 1000,
                                "duration_years": 5,
                                "planned_discontinue_prob": 0.2,
                                "admin_discontinue_prob": 0.05,
                                "enable_clinician_variation": True,
                                "results": {
                                    "discontinuation_counts": {
                                        "Planned": 250,
                                        "Administrative": 120,
                                        "Time-based": 180,
                                        "Premature": 80
                                    }
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
                                    mime=f"application/{file_extension}"
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
    
    - Multiple discontinuation types (protocol-based, administrative, time-based, premature)
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