"""
APE: AMD Protocol Explorer

This application provides an interactive dashboard for exploring and visualizing
AMD treatment protocols using Discrete Event Simulation (DES) and Agent-Based Simulation (ABS),
including detailed modeling of treatment discontinuation patterns.
"""

import os
import sys
import streamlit as st

# Add the project root directory to sys.path to allow importing from the main project
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root_dir)
sys.path.append(os.getcwd())

# Import layout components
from streamlit_app.components.layout import (
    setup_page_config,
    display_sidebar_logo,
    create_navigation,
    create_debug_toggle,
    display_fixed_implementation_notice,
    display_footer
)

# Import page modules (these would be implemented in separate files)
# In the actual implementation, these would be imported from their respective modules
def display_dashboard():
    """Display the dashboard page."""
    # This would be implemented in streamlit_app/pages/dashboard.py
    from streamlit_app.components.layout import display_logo_and_title
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
        st.subheader("Latest Simulation Results")
        # Actual implementation would display simulation results
        st.info("Simulation results would be displayed here.")
    else:
        st.warning("No simulation results available. Please run a simulation to view results.")

def display_run_simulation():
    """Display the run simulation page."""
    # This would be implemented in streamlit_app/pages/run_simulation.py
    from streamlit_app.components.layout import display_logo_and_title
    display_logo_and_title("Run AMD Treatment Simulation")
    st.info("Run Simulation page would be implemented here.")

def display_staggered_simulation():
    """Display the staggered simulation page."""
    # This would be implemented in streamlit_app/pages/staggered_simulation_page.py
    from streamlit_app.components.layout import display_logo_and_title
    display_logo_and_title("Staggered Patient Enrollment Simulation")
    st.info("Staggered Simulation page would be implemented here.")

def display_patient_explorer_page():
    """Display the patient explorer page."""
    # This would be implemented in streamlit_app/pages/patient_explorer_page.py
    from streamlit_app.components.layout import display_logo_and_title
    display_logo_and_title("Patient Explorer")
    st.info("Patient Explorer page would be implemented here.")

def display_reports_page():
    """Display the reports page."""
    # This would be implemented in streamlit_app/pages/reports_page.py
    from streamlit_app.components.layout import display_logo_and_title
    display_logo_and_title("Generate Reports")
    st.info("Reports page would be implemented here.")

def display_about_page():
    """Display the about page."""
    # This would be implemented in streamlit_app/pages/about_page.py
    from streamlit_app.components.layout import display_logo_and_title
    display_logo_and_title("About APE: AMD Protocol Explorer")
    st.info("About page would be implemented here.")

def main():
    """Main function to run the Streamlit app."""
    # Set page configuration
    setup_page_config()
    
    # Add puppeteer support if available
    try:
        from streamlit_app.puppeteer_helpers import add_puppeteer_support
        add_puppeteer_support()
    except Exception:
        # Silently handle errors to avoid breaking the app
        pass
    
    # Sidebar components
    display_sidebar_logo()
    st.sidebar.markdown("Interactive dashboard for exploring AMD treatment protocols")
    display_fixed_implementation_notice()
    
    # Navigation
    page = create_navigation()
    
    # Debug mode toggle
    debug_mode = create_debug_toggle()
    
    # Set debug mode in the simulation runner module if available
    try:
        from streamlit_app.simulation_runner import DEBUG_MODE
        import streamlit_app.simulation_runner as sim_runner
        sim_runner.DEBUG_MODE = debug_mode
    except ImportError:
        pass
    
    # Route to the appropriate page based on navigation
    if page == "Dashboard":
        display_dashboard()
    elif page == "Run Simulation":
        display_run_simulation()
    elif page == "Staggered Simulation":
        display_staggered_simulation()
    elif page == "Patient Explorer":
        display_patient_explorer_page()
    elif page == "Reports":
        display_reports_page()
    elif page == "About":
        display_about_page()
    
    # Footer
    display_footer()

if __name__ == "__main__":
    main()