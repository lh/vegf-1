"""
Patient Explorer page for the APE Streamlit application.

This module displays detailed information about individual patients
from simulation results, allowing users to explore patient journeys,
treatments, and outcomes.
"""

import streamlit as st
import pandas as pd
from typing import Dict, Any, Optional, List

from streamlit_app_parquet.components.layout import display_logo_and_title
from streamlit_app_parquet.utils.session_state import (
    get_simulation_results,
    get_staggered_results,
    get_debug_mode
)

# Import display_patient_explorer conditionally
try:
    from streamlit_app_parquet.patient_explorer import display_patient_explorer
except ImportError:
    # Define a fallback function
    def display_patient_explorer(patient_histories, results):
        st.error("Patient explorer module failed to load.")
        st.info("This may be due to missing dependencies or incorrect import paths.")
        
        # Show basic information about patient histories
        if patient_histories:
            st.subheader("Patient Data Summary")
            st.write(f"Number of patients: {len(patient_histories)}")
            
            # Show first patient ID
            first_patient_id = list(patient_histories.keys())[0]
            st.write(f"Sample patient ID: {first_patient_id}")
            
            # Show summary of first patient
            first_patient = patient_histories[first_patient_id]
            if isinstance(first_patient, list):
                st.write(f"Number of visits: {len(first_patient)}")
                
                # Create a simple table of visits
                if len(first_patient) > 0:
                    st.subheader(f"Visits for Patient {first_patient_id}")
                    
                    # Create a dataframe for the visits
                    visits_df = pd.DataFrame(first_patient)
                    st.dataframe(visits_df)


def display_patient_explorer_page():
    """Display the patient explorer page with detailed patient information."""
    display_logo_and_title("Patient Explorer")
    
    # Check various sources of simulation data
    has_standard_simulation = "simulation_results" in st.session_state and "patient_histories" in st.session_state
    has_staggered_simulation = "staggered_results" in st.session_state and "patient_histories" in st.session_state.get("staggered_results", {})
    
    # If we have either type of simulation data, show the data selection options
    if has_standard_simulation or has_staggered_simulation:
        st.subheader("Select Simulation Data")
        
        # Create tabs for different simulation types
        tab_names = []
        if has_standard_simulation:
            tab_names.append("Standard Simulation")
        if has_staggered_simulation:
            tab_names.append("Staggered Simulation")
        
        tabs = st.tabs(tab_names)
        
        # Fill tabs with data
        tab_index = 0
        
        if has_standard_simulation:
            with tabs[tab_index]:
                results = get_simulation_results()
                patient_histories = st.session_state["patient_histories"]
                
                # Display information about this simulation
                st.markdown(f"""
                **Simulation Type**: {results.get('simulation_type', 'Unknown')}
                **Population Size**: {results.get('population_size', 0)} patients
                **Duration**: {results.get('duration_years', 0)} years
                """)
                
                # Display the patient explorer
                display_patient_explorer(patient_histories, results)
            tab_index += 1
        
        if has_staggered_simulation:
            with tabs[tab_index]:
                staggered_results = get_staggered_results()
                patient_histories = staggered_results.get("patient_histories", {})
                
                # Display information about this simulation
                st.markdown(f"""
                **Simulation Type**: Staggered ABS
                **Population Size**: {staggered_results.get('population_size', 0)} patients
                **Duration**: {staggered_results.get('duration_years', 0)} years
                **Arrival Rate**: {staggered_results.get('arrival_rate', 0)} patients/week
                """)
                
                # Additional staggered enrollment info
                enrollment_dates = staggered_results.get("enrollment_dates", {})
                if enrollment_dates:
                    enrollment_dates_list = list(enrollment_dates.values())
                    dates_df = pd.DataFrame({"enrollment_date": enrollment_dates_list})
                    dates_df["enrollment_date"] = pd.to_datetime(dates_df["enrollment_date"])
                    
                    # Get min and max enrollment dates
                    min_date = dates_df["enrollment_date"].min()
                    max_date = dates_df["enrollment_date"].max()
                    
                    # Display enrollment period
                    st.markdown(f"""
                    **Enrollment Period**: {min_date.strftime('%Y-%m-%d')} to {max_date.strftime('%Y-%m-%d')}
                    """)
                
                # Display the patient explorer
                st.markdown("### Patient Data")
                display_patient_explorer(patient_histories, staggered_results)
    else:
        st.warning("No simulation data available. Please run a simulation first.")
        st.markdown("""
        The Patient Explorer allows you to:
        
        - Select individual patients from simulation results
        - View their complete treatment journey
        - Analyze visual acuity changes over time
        - Examine treatment phases and decisions
        - Review detailed visit history
        
        Run a simulation in the 'Run Simulation' or 'Staggered Simulation' tab to explore patient data.
        """)


if __name__ == "__main__":
    # This allows the page to be run directly for testing
    import sys
    import os
    
    # Add parent directory to path so imports work
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # Set up basic Streamlit configuration
    st.set_page_config(page_title="Patient Explorer Test", layout="wide")
    
    # Display the patient explorer page
    display_patient_explorer_page()