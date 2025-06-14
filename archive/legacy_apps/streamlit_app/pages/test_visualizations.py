"""
Test Visualizations Page

This page is for testing and debugging visualizations without running simulations.
It loads saved simulation results from files.
"""

import os
import sys
import json
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# Add parent directory to path so we can import from project root
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Import visualization tools
from streamgraph_patient_states import create_streamgraph
from components.layout import display_logo_and_title


def find_simulation_results():
    """Find available simulation result files."""
    result_files = []
    
    # Check output directory for simulation results
    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                             "output", "simulation_results")
    
    if os.path.exists(output_dir):
        # List all json files
        for file in sorted(os.listdir(output_dir), reverse=True):
            if file.endswith(".json") and file.startswith("ape_simulation_"):
                result_files.append(os.path.join(output_dir, file))
    
    return result_files


def load_simulation_results(file_path):
    """Load simulation results from a file."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Error loading simulation results: {e}")
        return None


def display_test_visualizations():
    """Display the test visualizations page."""
    display_logo_and_title("Test Visualizations")
    
    st.write("""
    This page is for testing and debugging visualizations without running simulations.
    It loads saved simulation results from files.
    """)
    
    # Find available simulation results
    result_files = find_simulation_results()
    
    if not result_files:
        st.warning("No simulation result files found. Please run a simulation first.")
        return
    
    # Let user select a result file
    selected_file = st.selectbox(
        "Select simulation results to visualize",
        result_files,
        format_func=lambda x: os.path.basename(x)
    )
    
    # Load the selected results
    results = load_simulation_results(selected_file)
    
    if not results:
        return
    
    # Display basic simulation info
    st.subheader("Simulation Information")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Simulation Type", results.get("simulation_type", "Unknown"))
    with col2:
        st.metric("Population Size", results.get("population_size", 0))
    with col3:
        st.metric("Duration (years)", results.get("duration_years", 0))
    
    # Test different visualizations
    st.subheader("Available Visualizations")
    
    # Visualization selection
    viz_options = [
        "Patient States Streamgraph",
        "Discontinuation Types",
        "Visual Acuity Over Time"
    ]
    
    selected_viz = st.radio("Select visualization to test", viz_options)
    
    # Display the selected visualization
    if selected_viz == "Patient States Streamgraph":
        st.subheader("Patient States Streamgraph")
        
        with st.spinner("Generating streamgraph..."):
            try:
                # Check if patient_histories data is available
                if "patient_histories" not in results or not results["patient_histories"]:
                    if "patient_data" in results:
                        # Use patient_data instead
                        results["patient_histories"] = results["patient_data"]
                        st.info("Using 'patient_data' instead of 'patient_histories'")
                
                # Create the streamgraph
                fig = create_streamgraph(results)
                st.pyplot(fig)
                
                # Display counts at key time points
                if st.checkbox("Show patient counts at selected time points"):
                    # Get time points
                    duration_months = int(results.get("duration_years", 5) * 12)
                    time_points = [0, duration_months // 4, duration_months // 2, 
                                  (duration_months * 3) // 4, duration_months]
                    
                    # Import what we need
                    from streamgraph_patient_states import (
                        extract_patient_states, 
                        aggregate_states_by_month,
                        PATIENT_STATES
                    )
                    
                    # Extract and aggregate patient states
                    patient_histories = results.get("patient_histories", {})
                    patient_states_df = extract_patient_states(patient_histories)
                    monthly_counts = aggregate_states_by_month(patient_states_df, duration_months)
                    
                    # Prepare data for display
                    count_data = []
                    for month in time_points:
                        month_data = monthly_counts[monthly_counts['time_months'] == month]
                        for _, row in month_data.iterrows():
                            if row['count'] > 0:  # Only include non-zero states
                                count_data.append({
                                    "Time (months)": month,
                                    "State": row['state'],
                                    "Count": row['count']
                                })
                    
                    # Convert to dataframe and display
                    count_df = pd.DataFrame(count_data)
                    count_df = count_df.pivot(index='State', columns='Time (months)', values='Count').fillna(0)
                    st.dataframe(count_df)
            
            except Exception as e:
                st.error(f"Error generating streamgraph: {e}")
                st.exception(e)
    
    elif selected_viz == "Discontinuation Types":
        st.subheader("Discontinuation Types")
        
        # If available, use the discontinuation visualization
        try:
            from discontinuation_chart import generate_enhanced_discontinuation_plot
            
            fig = generate_enhanced_discontinuation_plot(results)
            st.pyplot(fig)
            
            # Show raw data
            if st.checkbox("Show raw discontinuation data"):
                disc_counts = results.get("discontinuation_counts", {})
                st.json(disc_counts)
        except Exception as e:
            st.error(f"Error generating discontinuation visualization: {e}")
            st.exception(e)
    
    elif selected_viz == "Visual Acuity Over Time":
        st.subheader("Visual Acuity Over Time")
        
        # If available, use the VA visualization
        try:
            from simulation_runner import generate_va_over_time_plot
            
            fig = generate_va_over_time_plot(results)
            st.pyplot(fig)
            
            # Show raw data
            if st.checkbox("Show raw VA data"):
                va_data = results.get("mean_va_data", [])
                va_df = pd.DataFrame(va_data)
                st.dataframe(va_df)
        except Exception as e:
            st.error(f"Error generating VA visualization: {e}")
            st.exception(e)


if __name__ == "__main__":
    display_test_visualizations()