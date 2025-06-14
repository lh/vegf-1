"""
Dashboard page for the APE Streamlit application.

This module displays the main dashboard with simulation results and visualizations.
"""

import streamlit as st
import pandas as pd

from streamlit_app.components.layout import display_logo_and_title
from streamlit_app.utils.session_state import get_simulation_results, get_debug_mode

# Import simulation_runner functions conditionally to handle missing dependencies
try:
    from streamlit_app.simulation_runner import (
        generate_va_over_time_plot,
        generate_discontinuation_plot
    )
except ImportError:
    # Define fallback functions
    def generate_va_over_time_plot(results):
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots()
        ax.text(0.5, 0.5, "Simulation module not available", ha='center', va='center')
        return fig
    
    def generate_discontinuation_plot(results):
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots()
        ax.text(0.5, 0.5, "Simulation module not available", ha='center', va='center')
        return fig

# Import retreatment_panel conditionally
try:
    from streamlit_app.retreatment_panel import display_retreatment_panel
except ImportError:
    def display_retreatment_panel(results):
        st.warning("Retreatment panel module not available.")


def display_dashboard():
    """Display the dashboard page with simulation results."""
    display_logo_and_title("APE: AMD Protocol Explorer")
    
    # Introduction
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
    results = get_simulation_results()
    debug_mode = get_debug_mode()
    
    if results:
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
        
        # Get recurrence data with details
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


if __name__ == "__main__":
    # This allows the page to be run directly for testing
    import sys
    import os
    
    # Add parent directory to path so imports work
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # Set up basic Streamlit configuration
    st.set_page_config(page_title="Dashboard Test", layout="wide")
    
    # Display the dashboard
    display_dashboard()