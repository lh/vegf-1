"""
Staggered Simulation page for the APE Streamlit application.

This module handles the staggered patient enrollment simulation where patients
enter the study over time following a Poisson process, which better represents
real-world clinical studies.
"""

import os
import datetime
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import time
from typing import Dict, Any, Optional

from streamlit_app.components.layout import display_logo_and_title
from streamlit_app.utils.session_state import get_debug_mode
from streamlit_app.components.visualizations.r_integration import render_enrollment_visualization

# Import staggered simulation components conditionally to handle missing dependencies
try:
    from streamlit_app.staggered_simulation import (
        run_staggered_simulation,
        display_staggered_enrollment_controls,
        create_dual_timeframe_visualizations,
        add_staggered_parameters
    )
except ImportError:
    # Define fallback functions
    def run_staggered_simulation(params):
        """Fallback for run_staggered_simulation."""
        st.error("Staggered simulation module failed to load correctly.")
        st.info("This may be due to missing dependencies or incorrect import paths.")
        return {"error": "staggered_simulation_module_failed"}
    
    def display_staggered_enrollment_controls():
        """Fallback for display_staggered_enrollment_controls."""
        st.warning("Staggered enrollment controls not available.")
    
    def create_dual_timeframe_visualizations(results, output_dir):
        """Fallback for create_dual_timeframe_visualizations."""
        os.makedirs(output_dir, exist_ok=True)
        return {}
    
    def add_staggered_parameters(params):
        """Fallback for add_staggered_parameters."""
        return params


def display_staggered_simulation():
    """Display the staggered simulation page with enrollment patterns."""
    display_logo_and_title("Staggered Patient Enrollment Simulation")

    st.markdown("""
    This simulation models realistic patient enrollment patterns where patients enter
    the study over time following a Poisson process. This approach better represents
    real-world clinical studies and enables dual timeframe analysis (calendar time vs. patient time).

    See `STAGGERED_ENROLLMENT.md` for detailed documentation on this feature.
    """)

    # Configuration options
    st.subheader("Simulation Configuration")

    col1, col2 = st.columns(2)

    with col1:
        # Use only ABS for staggered simulation
        simulation_type = "ABS"
        st.info("Staggered enrollment is only available for Agent-Based Simulation (ABS)")

        duration_years = st.slider(
            "Simulation Duration (years)",
            min_value=1,
            max_value=10,
            value=2,
            help="Duration of the simulation in years",
            key="staggered_duration_years_slider"
        )

        population_size = st.slider(
            "Target Population Size",
            min_value=100,
            max_value=2000,
            value=500,
            step=100,
            help="Target number of patients to enroll (actual number depends on arrival rate and duration)",
            key="staggered_population_size_slider"
        )

        # Patient arrival rate (per week)
        arrival_rate = st.slider(
            "Patient Arrival Rate (per week)",
            min_value=1.0,
            max_value=20.0,
            value=10.0,
            step=0.5,
            help="Average number of new patients per week (Poisson distribution parameter)",
            key="arrival_rate_slider"
        )

    with col2:
        # Explanation of staggered enrollment
        st.markdown("### Staggered Enrollment Benefits")
        st.markdown("""
        - **Time-Dependent Analysis**: Track outcomes by calendar time and patient time
        - **Realistic Resource Utilization**: See realistic patterns of clinic visits
        - **Cohort Comparisons**: Compare patients who joined at different times
        - **Capacity Planning**: Better model impact on clinic resources
        """)

        # Show expected enrollment
        expected_patients = int(arrival_rate * duration_years * 52)
        st.markdown(f"### Expected Enrollment: ~{expected_patients} patients")
        st.markdown(f"Based on arrival rate of {arrival_rate} patients/week over {duration_years} years")

        # Basic discontinuation settings
        enable_clinician_variation = st.checkbox(
            "Enable Clinician Variation",
            value=True,
            help="Include variation in clinician adherence to protocol",
            key="staggered_enable_clinician_checkbox"
        )

        # Only show R visualization toggle in debug mode
        if get_debug_mode():
            st.markdown("### Debug Options")
            enable_r_visualization = st.checkbox(
                "Enable R Visualization",
                value=True,
                help="Use R for high-quality visualizations if available (debug option)",
                key="enable_r_visualization_checkbox"
            )

    # Run staggered simulation button
    if st.button("Run Staggered Simulation", type="primary", key="run_staggered_button"):
        # Check if StaggeredABS is available
        staggered_can_run = True
        try:
            from simulation.staggered_abs import StaggeredABS
        except ImportError:
            st.error("Cannot run staggered simulation: required modules are not available.")
            st.info("This may be due to missing dependencies or incorrect import paths.")
            staggered_can_run = False

        # Save all parameters to session state
        st.session_state["staggered_simulation_type"] = simulation_type
        st.session_state["staggered_duration_years"] = duration_years
        st.session_state["staggered_population_size"] = population_size
        st.session_state["staggered_arrival_rate"] = arrival_rate
        st.session_state["staggered_enable_clinician_variation"] = enable_clinician_variation

        # Get parameters from session state
        params = {
            "simulation_type": "ABS",  # Always ABS for staggered
            "duration_years": duration_years,
            "population_size": population_size,
            "arrival_rate": arrival_rate,
            "enable_clinician_variation": enable_clinician_variation,
            "staggered_enrollment": True
        }

        # Run the staggered simulation if possible
        if staggered_can_run:
            with st.spinner(f"Running staggered enrollment simulation with ~{expected_patients} patients over {duration_years} years..."):
                # Run simulation
                staggered_results = run_staggered_simulation(params)

                # Check if there was an error or if simulation failed
                if "error" in staggered_results or staggered_results.get("failed", False):
                    st.error(f"Simulation failed: {staggered_results.get('error', 'Unknown error')}")

                    # Show error details if available
                    if "traceback" in staggered_results:
                        with st.expander("Show error details"):
                            st.code(staggered_results["traceback"])
                else:
                    # Store patient histories in session state
                    st.session_state["staggered_results"] = staggered_results

                    # Show success message
                    st.success(f"Staggered simulation completed with {staggered_results.get('population_size', 0)} patients!")

                    # Display basic metrics
                    col1, col2, col3 = st.columns(3)

                    # Extract basic metrics
                    actual_patients = staggered_results.get('population_size', 0)
                    total_visits = staggered_results.get('total_visits', 0)
                    mean_visits = staggered_results.get('mean_visits', 0)

                    with col1:
                        st.metric("Total Patients", actual_patients)

                    with col2:
                        st.metric("Total Visits", total_visits)

                    with col3:
                        st.metric("Avg Visits per Patient", f"{mean_visits:.1f}")

                    # Show enrollment distribution
                    st.subheader("Patient Enrollment Distribution")
                    enrollment_dates = staggered_results.get('enrollment_dates', {})

                    # Convert enrollment dates to pandas DataFrame
                    enrollments = []
                    for patient_id, date in enrollment_dates.items():
                        # Convert date to datetime if it's not already
                        if isinstance(date, str):
                            try:
                                date = datetime.datetime.strptime(date, "%Y-%m-%d %H:%M:%S.%f")
                            except ValueError:
                                # Try alternative formats
                                try:
                                    date = datetime.datetime.strptime(date, "%Y-%m-%d %H:%M:%S")
                                except ValueError:
                                    date = datetime.datetime.now()  # Fallback
                        enrollments.append({
                            'patient_id': patient_id,
                            'enrollment_date': date
                        })

                    if enrollments:
                        # Show patient enrollment with visualization
                        enroll_df = pd.DataFrame(enrollments)
                        enroll_df['enrollment_date'] = pd.to_datetime(enroll_df['enrollment_date'])

                        # Calculate simple statistics
                        total_patients = len(enroll_df)
                        start_date = enroll_df['enrollment_date'].min().strftime('%Y-%m-%d')
                        end_date = enroll_df['enrollment_date'].max().strftime('%Y-%m-%d')

                        # Display stats in a cleaner format
                        st.markdown(f"""
                        ### Patient Enrollment

                        - **Total Patients:** {total_patients}
                        - **First Enrollment:** {start_date}
                        - **Last Enrollment:** {end_date}
                        """)

                        # Get debug mode and R visualization setting
                        debug_mode = get_debug_mode()
                        # Use R by default unless explicitly disabled in debug mode
                        use_r = True
                        if debug_mode:
                            use_r = st.session_state.get("enable_r_visualization_checkbox", True)

                        # Use our improved visualization approach that shows matplotlib first
                        # then replaces with R visualization when available
                        try:
                            # If debug mode is on, add more detailed information about R visualization
                            if debug_mode:
                                from streamlit_app.components.visualizations.common import is_r_available, get_r_script_path, check_r_packages, ensure_r_script_exists
                                import tempfile
                                import subprocess

                                r_available = is_r_available()
                                r_script_path = get_r_script_path()
                                r_packages = check_r_packages() if r_available else False
                                r_script_exists = os.path.exists(r_script_path)
                                temp_dir = tempfile.gettempdir()

                                # Create a more detailed debug panel
                                with st.expander("Visualization Debug Information", expanded=True):
                                    st.markdown("### R Environment")
                                    st.markdown(f"- **R Visualization Enabled:** {use_r}")
                                    st.markdown(f"- **R Available:** {r_available}")
                                    st.markdown(f"- **R Packages Installed:** {r_packages}")
                                    st.markdown(f"- **R Script Path:** {r_script_path}")
                                    st.markdown(f"- **R Script Exists:** {r_script_exists}")
                                    st.markdown(f"- **Temp Directory:** {temp_dir}")

                                    # Try to get R version
                                    if r_available:
                                        try:
                                            r_version = subprocess.run(
                                                ["Rscript", "--version"],
                                                capture_output=True,
                                                text=True
                                            )
                                            st.markdown(f"- **R Version:** {r_version.stderr.strip()}")
                                        except Exception as e:
                                            st.markdown(f"- **R Version Error:** {str(e)}")

                                    # Check if we need to create the R script
                                    if not r_script_exists:
                                        st.warning("R script does not exist. Attempting to create it...")
                                        if ensure_r_script_exists():
                                            st.success("R script created successfully!")
                                        else:
                                            st.error("Failed to create R script")

                                    # Show R package installation info if needed
                                    if r_available and not r_packages:
                                        st.warning("Missing required R packages. Please install manually or check console output.")
                                        st.code("install.packages(c('ggplot2', 'optparse', 'lubridate', 'scales', 'dplyr', 'tidyr'))")

                                # Show a clear message about what's happening
                                st.info("Starting visualization process - please wait for progressive enhancement...")

                            # Use direct matplotlib visualization instead of complex R integration
                            st.markdown("### Patient Enrollment Visualization")

                            # Create a Tufte-styled visualization for patient enrollment
                            import matplotlib.pyplot as plt
                            import numpy as np

                            try:
                                # Ensure enrollment_date is datetime
                                if not pd.api.types.is_datetime64_any_dtype(enroll_df['enrollment_date']):
                                    enroll_df['enrollment_date'] = pd.to_datetime(enroll_df['enrollment_date'])

                                # Use our Tufte style library for consistent visualization
                                from streamlit_app.utils.tufte_style import create_tufte_enrollment_chart

                                # Create visualization using our reusable function with matching styling
                                fig, ax = create_tufte_enrollment_chart(
                                    enroll_df,
                                    title='Patient Enrollment Over Time',
                                    add_trend=False,  # No trend line to match other visualizations
                                    figsize=(10, 5)
                                )

                                # Display the plot
                                st.pyplot(fig)

                            except Exception as e:
                                if debug_mode:
                                    st.error(f"Error creating visualization: {e}")
                                    import traceback
                                    st.code(traceback.format_exc())

                                # Create a simple fallback visualization without showing an error message
                                try:
                                    # Group by month
                                    enroll_df['month'] = enroll_df['enrollment_date'].dt.strftime('%Y-%m')
                                    monthly_counts = enroll_df.groupby('month').size()

                                    # Create a simple figure with Tufte-inspired styling
                                    from streamlit_app.utils.tufte_style import set_tufte_style, style_axis

                                    # Apply Tufte style
                                    set_tufte_style()

                                    # Create a figure
                                    fig, ax = plt.subplots(figsize=(10, 5))

                                    # Plot bars with lighter blue to match other visualizations
                                    ax.bar(range(len(monthly_counts)), monthly_counts.values,
                                           color='#a8c4e5', alpha=0.3)

                                    # Style axis
                                    style_axis(ax)

                                    # Add labels
                                    ax.set_xticks(range(len(monthly_counts)))
                                    ax.set_xticklabels(monthly_counts.index, rotation=45, ha='right')
                                    ax.set_title('Patient Enrollment Over Time', fontsize=14)
                                    ax.set_ylabel('Number of Patients', fontsize=10)

                                    plt.tight_layout()
                                    st.pyplot(fig)

                                except Exception as fallback_error:
                                    if debug_mode:
                                        st.error(f"Fallback visualization also failed: {fallback_error}")
                                    # As a last resort, use the original function
                                    render_enrollment_visualization(enroll_df, use_r=use_r)

                            # Add additional debug information
                            if debug_mode:
                                import tempfile
                                import glob
                                import time

                                # Let the R visualization process have time to complete
                                time.sleep(1)  # Small delay to let background thread finish

                                # Show any PNG files created in temp directory
                                temp_dir = tempfile.gettempdir()
                                png_files = glob.glob(f"{temp_dir}/*.png")

                                # Check specifically for enrollment visualization files
                                enrollment_pngs = [f for f in png_files if "enrollment" in f.lower()]

                                with st.expander("Generated Image Files", expanded=True):
                                    if enrollment_pngs:
                                        st.success(f"Found {len(enrollment_pngs)} enrollment PNG files in temp directory.")
                                        for i, png_file in enumerate(enrollment_pngs[:3]):  # Show up to 3
                                            file_size = os.path.getsize(png_file)
                                            st.text(f"Enrollment PNG {i+1}: {png_file} ({file_size} bytes)")
                                            # If in debug mode and file exists, show it directly
                                            if os.path.exists(png_file) and file_size > 100:
                                                st.image(png_file, caption=f"Debug view of generated file {i+1}")
                                    else:
                                        st.warning(f"No enrollment PNG files found in temp directory.")

                                    # Show all PNG files as well
                                    if len(png_files) > 0:
                                        st.info(f"Found {len(png_files)} total PNG files in temp directory.")
                        except Exception as e:
                            # If there's an error with the improved visualization, fall back to simple matplotlib plot
                            if get_debug_mode():
                                st.error(f"Error in improved visualization: {e}")
                                # Show traceback for debugging
                                import traceback
                                st.code(traceback.format_exc())

                            # Group by month
                            enroll_df['month'] = enroll_df['enrollment_date'].dt.strftime('%Y-%m')
                            monthly_counts = enroll_df['month'].value_counts().sort_index()

                            # Create a small figure
                            fig, ax = plt.subplots(figsize=(8, 4), dpi=80)

                            # Simple bar chart
                            ax.bar(range(len(monthly_counts)), monthly_counts.values, color='#4682B4')

                            # Clean up the appearance
                            ax.spines['top'].set_visible(False)
                            ax.spines['right'].set_visible(False)

                            # Set labels and title
                            ax.set_title('Patient Enrollment by Month', fontsize=12)
                            ax.set_ylabel('Patients')

                            # X-axis labels
                            ax.set_xticks(range(len(monthly_counts)))
                            ax.set_xticklabels(monthly_counts.index, rotation=45, ha='right')

                            plt.tight_layout()
                            st.pyplot(fig)
                            plt.close(fig)
                            if get_debug_mode():
                                st.info(f"Visualization error: {e}")

                    # Create dual timeframe visualizations
                    st.subheader("Dual Timeframe Analysis")

                    # Create output directory for visualizations
                    output_dir = "output/staggered_comparison"
                    os.makedirs(output_dir, exist_ok=True)

                    # Generate visualizations
                    viz_paths = create_dual_timeframe_visualizations(staggered_results, output_dir)

                    # Display the dual timeframe visualization
                    if "dual_timeframe" in viz_paths:
                        st.markdown("#### Visual Acuity by Calendar Time vs. Patient Time")
                        st.markdown("""
                        **Left Panel**: Mean visual acuity by calendar time (months since simulation start)
                        **Right Panel**: Mean visual acuity by patient time (weeks since individual enrollment)
                        """)
                        st.image(viz_paths["dual_timeframe"])

                    # Display calendar time visualization
                    if "calendar_time" in viz_paths:
                        st.markdown("#### Mean Visual Acuity by Calendar Time")
                        st.markdown("""
                        This Tufte-inspired visualization shows the mean visual acuity across all patients
                        by calendar date. Key features:

                        - **Date-based analysis**: Shows real-world timeline of the study
                        - **Trend detection**: Helps identify overall visual acuity patterns
                        - **Context aware**: Subtle visual elements maintain focus on the data
                        - **Clear interpretation**: Reduced visual noise for clinical decision-making

                        Note: Calendar time analysis is affected by the "dilution effect" where newer
                        patients entering the study can mask treatment effects in longer-term patients.
                        """)
                        st.image(viz_paths["calendar_time"])

                    # Display patient time visualization
                    if "patient_time" in viz_paths:
                        st.markdown("#### Mean Visual Acuity by Patient Time (Weeks Since Enrollment)")
                        st.markdown("""
                        This Tufte-inspired visualization shows the mean visual acuity trajectory aligned by patient time,
                        with sample size indicated by bar height. Key features:

                        - **Clear data presentation**: Primary focus on the visual acuity trend
                        - **Sample size context**: Subtle background bars show patient counts at each timepoint
                        - **Trend line**: Smoothed trend helps identify the overall pattern
                        - **Baseline reference**: Horizontal reference line shows initial acuity for comparison
                        - **Reduced chart junk**: Minimal non-data ink for clearer interpretation

                        This approach eliminates the dilution effect seen in calendar time analysis when new
                        patients continually enter the study at different timepoints.
                        """)
                        st.image(viz_paths["patient_time"])

                    # Show a sample of patient data
                    st.subheader("Patient Data Sample")

                    # Get patient histories
                    patient_histories = staggered_results.get('patient_histories', {})

                    if patient_histories:
                        # Get a sample patient
                        first_patient_id = list(patient_histories.keys())[0]
                        first_patient_visits = patient_histories[first_patient_id]

                        # Show enrollment date
                        enrollment_date = enrollment_dates.get(first_patient_id, "Unknown")
                        st.markdown(f"**Patient {first_patient_id}** enrolled on: {enrollment_date}")

                        # Create table of visits
                        if first_patient_visits:
                            # Create DataFrame of visits
                            visits_data = []
                            for i, visit in enumerate(first_patient_visits):
                                visit_data = {
                                    'Visit #': i+1,
                                    'Date': visit.get('date', 'Unknown'),
                                    'Vision': visit.get('vision', 'Unknown')
                                }
                                # Add actions if available
                                if 'actions' in visit:
                                    actions = visit['actions']
                                    if isinstance(actions, list):
                                        visit_data['Actions'] = ', '.join(actions)
                                    else:
                                        visit_data['Actions'] = str(actions)
                                else:
                                    visit_data['Actions'] = 'None recorded'

                                visits_data.append(visit_data)

                            # Create and display table
                            visits_df = pd.DataFrame(visits_data)
                            st.table(visits_df)


if __name__ == "__main__":
    # This allows the page to be run directly for testing
    import sys
    import os
    
    # Add parent directory to path so imports work
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # Set up basic Streamlit configuration
    st.set_page_config(page_title="Staggered Simulation Test", layout="wide")
    
    # Display the staggered simulation page
    display_staggered_simulation()