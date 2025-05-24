"""
Test Streamlit app for the improved streamgraph implementation.

This script loads simulation results and displays the patient state streamgraph
using the improved implementation.
"""

import streamlit as st
import json
import glob
import os
from pathlib import Path
import pandas as pd
import sys

# Import our improved streamgraph implementation
from streamgraph_improved import (
    create_streamlit_visualization,
    analyze_time_formats
)

def find_simulation_files():
    """Find available simulation result files."""
    # Look in common locations
    locations = [
        "../output/simulation_results/*.json",
        "../*.json",
    ]
    
    # Collect all potential files
    all_files = []
    for pattern in locations:
        files = glob.glob(pattern)
        all_files.extend(files)
    
    # Filter to keep only files larger than 100KB (likely to contain patient data)
    data_files = []
    for file_path in all_files:
        try:
            size = os.path.getsize(file_path)
            if size > 100000:  # Larger than 100KB
                # Get a nicer display name
                display_name = Path(file_path).name
                data_files.append((file_path, display_name, size))
        except Exception:
            # Skip files we can't access
            continue
    
    # Sort by size (largest first)
    data_files.sort(key=lambda x: x[2], reverse=True)
    
    return data_files

def load_data(file_path):
    """Load simulation results from file."""
    try:
        with open(file_path, "r") as f:
            data = json.load(f)
        return data
    except Exception as e:
        st.error(f"Error loading file: {e}")
        return None

def main():
    st.set_page_config(
        page_title="Patient State Streamgraph",
        page_icon="📊",
        layout="wide"
    )
    
    st.title("Patient State Streamgraph Visualization")
    st.write("""
    This app demonstrates the improved patient state streamgraph visualization.
    It properly tracks patient transitions between active, discontinued, and 
    retreated states over time.
    """)
    
    # Find available data files
    data_files = find_simulation_files()
    
    if not data_files:
        st.warning("No simulation data files found. Please run a simulation first.")
        st.stop()
    
    # File selection
    st.sidebar.header("Data Selection")
    
    file_options = [(path, name) for path, name, _ in data_files[:20]]  # Limit to first 20
    default_index = 0
    
    selected_path, selected_name = st.sidebar.selectbox(
        "Select Simulation Results",
        options=file_options,
        format_func=lambda x: x[1],
        index=default_index
    )
    
    # Load data
    with st.spinner("Loading simulation data..."):
        data = load_data(selected_path)
    
    if data is None:
        st.error("Failed to load data. Please select another file.")
        st.stop()
    
    # Debugging options
    show_data = st.sidebar.checkbox("Show Data Tables", value=False)
    show_time_analysis = st.sidebar.checkbox("Debug Time Formats", value=False)
    
    # Display data summary
    st.header("Dataset Summary")
    
    patient_count = len(data.get("patient_histories", {}))
    duration_years = data.get("duration_years", 5)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Patients", patient_count)
    with col2:
        st.metric("Duration (years)", duration_years)
    with col3:
        disc_counts = data.get("discontinuation_counts", {})
        total_disc = sum(disc_counts.values()) if disc_counts else 0
        st.metric("Total Discontinuations", total_disc)
    
    # Display time format analysis if requested
    if show_time_analysis:
        analyze_time_formats(data)
    
    # Create and display visualization
    st.header("Patient State Streamgraph")
    create_streamlit_visualization(data, show_data=show_data)
    
    # Add explanation
    with st.expander("About This Visualization"):
        st.markdown("""
        ### Understanding the Patient State Streamgraph
        
        This visualization shows how patients move between different treatment states over time:
        
        - **Active (Never Discontinued)**: Patients who have been continuously on treatment
        - **Active (Retreated from X)**: Patients who were discontinued for reason X, but later returned to treatment
        - **Discontinued (X)**: Patients who have stopped treatment for reason X
        
        The streamgraph ensures that the total patient count remains constant across all time points, following 
        the conservation principle for scientific visualization. The colors follow a traffic light scheme:
        
        - **Green shades**: Active treatment states
        - **Amber**: Planned discontinuation
        - **Red shades**: Other discontinuation types
        
        The black dotted line represents the total population.
        """)

if __name__ == "__main__":
    main()