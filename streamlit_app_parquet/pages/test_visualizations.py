"""
Test Visualizations Page

This page is for testing and debugging visualizations without running simulations.
It loads saved simulation results from Parquet files.
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
from streamgraph_parquet import create_streamgraph_from_parquet
from components.layout import display_logo_and_title


def find_simulation_results():
    """Find available simulation result files (Parquet format)."""
    result_files = []
    
    # Check parquet output directory
    parquet_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                              "output", "parquet_results")
    
    if os.path.exists(parquet_dir):
        # Get unique simulation runs by metadata files
        metadata_files = {}
        for file in sorted(os.listdir(parquet_dir), reverse=True):
            if file.endswith("_metadata.parquet"):
                # Extract the base name (everything before _metadata.parquet)
                base_name = file.replace("_metadata.parquet", "")
                # Check if all three files exist
                visits_file = os.path.join(parquet_dir, f"{base_name}_visits.parquet")
                stats_file = os.path.join(parquet_dir, f"{base_name}_stats.parquet")
                metadata_file = os.path.join(parquet_dir, file)
                
                if os.path.exists(visits_file) and os.path.exists(stats_file):
                    metadata_files[base_name] = {
                        "visits": visits_file,
                        "stats": stats_file,
                        "metadata": metadata_file
                    }
        
        result_files = list(metadata_files.items())
    
    return result_files


def load_simulation_results(file_info):
    """Load simulation results from Parquet files."""
    try:
        # Load all three Parquet files
        visits_df = pd.read_parquet(file_info["visits"])
        stats_df = pd.read_parquet(file_info["stats"])
        metadata_df = pd.read_parquet(file_info["metadata"])
        
        # Extract simulation parameters from metadata
        sim_params = metadata_df.to_dict(orient="records")[0] if len(metadata_df) > 0 else {}
        
        # Return in expected format - include the DataFrames directly
        return {
            "simulation_parameters": sim_params,
            "visits_df": visits_df,
            "stats_df": stats_df,
            "metadata_df": metadata_df,
            # For backwards compatibility with visualization functions
            "simulation_type": sim_params.get("simulation_type"),
            "population_size": sim_params.get("population_size"),
            "duration_years": sim_params.get("duration_years"),
        }
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
        format_func=lambda x: x[0]  # Display the base name
    )
    
    # Load the selected results
    results = load_simulation_results(selected_file[1])  # Pass the file info dict
    
    if not results:
        return
    
    # Display basic simulation info
    st.subheader("Simulation Information")
    
    sim_params = results.get("simulation_parameters", {})
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Simulation Type", sim_params.get("simulation_type", "Unknown"))
    with col2:
        # Check both 'population_size' and 'patients' for backwards compatibility
        pop_size = sim_params.get("population_size", sim_params.get("patients", 0))
        st.metric("Population Size", pop_size)
    with col3:
        st.metric("Duration (years)", sim_params.get("duration_years", 0))
    
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
                # Create the streamgraph using visits DataFrame
                if "visits_df" in results:
                    fig = create_streamgraph_from_parquet(results)
                    st.pyplot(fig)
                else:
                    st.error("No visits data found in results")
                
            except Exception as e:
                st.error(f"Error generating streamgraph: {e}")
                st.exception(e)
    
    elif selected_viz == "Discontinuation Types":
        st.subheader("Discontinuation Types")
        
        try:
            # Check if we have discontinuation data in visits_df
            if "visits_df" in results:
                visits_df = results["visits_df"]
                
                # Count discontinuation types
                disc_counts = visits_df[visits_df['is_discontinuation'] == True]['discontinuation_type'].value_counts()
                
                # Create a simple bar chart
                fig, ax = plt.subplots(figsize=(10, 6))
                disc_counts.plot(kind='bar', ax=ax)
                ax.set_title("Discontinuation Types")
                ax.set_xlabel("Type")
                ax.set_ylabel("Count")
                plt.xticks(rotation=45, ha='right')
                plt.tight_layout()
                
                st.pyplot(fig)
                
                # Show raw data
                if st.checkbox("Show raw discontinuation data"):
                    st.dataframe(disc_counts.to_frame("count"))
            else:
                st.error("No visits data found")
                
        except Exception as e:
            st.error(f"Error generating discontinuation visualization: {e}")
            st.exception(e)
    
    elif selected_viz == "Visual Acuity Over Time":
        st.subheader("Visual Acuity Over Time")
        
        try:
            # Process VA data from the visits DataFrame
            if "visits_df" in results:
                visits_df = results["visits_df"]
                
                # Convert date to time if needed
                if 'time' not in visits_df.columns and 'date' in visits_df.columns:
                    visits_df = visits_df.copy()
                    visits_df['date'] = pd.to_datetime(visits_df['date'])
                    min_date = visits_df['date'].min()
                    visits_df['time'] = (visits_df['date'] - min_date).dt.days / 30.44
                    results["visits_df"] = visits_df  # Update in results
                
                # Process VA data to create mean_va_data
                if 'vision' in visits_df.columns and 'time' in visits_df.columns:
                    # Filter non-null vision data
                    va_df = visits_df[visits_df['vision'].notna()].copy()
                    
                    if len(va_df) > 0:
                        # Round time to months
                        va_df["time_month"] = va_df["time"].round().astype(int)
                        
                        # Group by month
                        grouped = va_df.groupby("time_month")
                        mean_va_by_month = grouped["vision"].mean()
                        std_va_by_month = grouped["vision"].std()
                        count_by_month = grouped["vision"].count()
                        
                        # Calculate SEM
                        std_error = std_va_by_month / (count_by_month.clip(lower=1).apply(lambda x: x ** 0.5))
                        
                        # Create mean_va_data
                        mean_va_data = pd.DataFrame({
                            "time": mean_va_by_month.index,
                            "visual_acuity": mean_va_by_month.values,
                            "sample_size": count_by_month.values,
                            "std_dev": std_va_by_month.values,
                            "std_error": std_error.values
                        }).to_dict(orient="records")
                        
                        # Add to results for the plot function
                        results["mean_va_data"] = mean_va_data
                        
                        st.info(f"Processed {len(va_df)} vision measurements across {len(mean_va_data)} months")
                
                # Now generate the plot
                from simulation_runner import generate_va_over_time_plot
                fig = generate_va_over_time_plot(results)
                st.pyplot(fig)
                
                # Show some stats
                if 'vision' in visits_df.columns:
                    va_stats = visits_df['vision'].describe()
                    st.write("Visual Acuity Statistics:")
                    st.dataframe(va_stats.to_frame())
            else:
                st.error("No visits data found")
                
        except Exception as e:
            st.error(f"Error generating VA visualization: {e}")
            st.exception(e)


if __name__ == "__main__":
    display_test_visualizations()