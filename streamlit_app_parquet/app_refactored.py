"""
APE: AMD Protocol Explorer

This application provides an interactive dashboard for exploring and visualizing
AMD treatment protocols using Discrete Event Simulation (DES) and Agent-Based Simulation (ABS),
including detailed modeling of treatment discontinuation patterns.

This is the refactored version using a modular architecture.
"""

import os
import sys
import logging
import streamlit as st

# Configure detailed logging to both file and console
import tempfile

# Create log file in temp directory
log_file = os.path.join(tempfile.gettempdir(), 'streamlit_app.log')

logging.basicConfig(
    level=logging.DEBUG,  # Use DEBUG level for more detailed logging
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
logger.info(f"Log file located at: {log_file}")

# Add the project root directory to sys.path to allow importing from the main project
root_dir = os.path.dirname(os.path.abspath(__file__))
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

# Import page modules
from streamlit_app.pages.dashboard import display_dashboard
from streamlit_app.pages.run_simulation import display_run_simulation
from streamlit_app.pages.reports_page import display_reports_page
from streamlit_app.pages.about_page import display_about_page

# Import conditionally to handle missing modules gracefully
try:
    from streamlit_app.pages.staggered_simulation_page import display_staggered_simulation
except ImportError:
    def display_staggered_simulation():
        st.error("Staggered Simulation module could not be loaded.")
        st.info("This may be due to missing dependencies or incorrect import paths.")

try:
    from streamlit_app.pages.patient_explorer_page import display_patient_explorer_page
except ImportError:
    def display_patient_explorer_page():
        st.error("Patient Explorer module could not be loaded.")
        st.info("This may be due to missing dependencies or incorrect import paths.")


def main():
    """Main function to run the APE Streamlit application."""
    # Set up the page configuration
    setup_page_config()
    
    # Initialize session state for first-time users
    if "page" not in st.session_state:
        st.session_state["page"] = "Dashboard"
    
    # Add puppeteer support if available
    try:
        from streamlit_app.puppeteer_helpers import add_puppeteer_support
        add_puppeteer_support()
    except Exception as e:
        # Silently handle errors to avoid breaking the app
        logger.warning(f"Could not load puppeteer support: {str(e)}")
    
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
        logger.warning("Could not load simulation_runner module for debug mode setting")
    
    # Route to the appropriate page based on navigation selection
    try:
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
        else:
            # Fallback to dashboard if an unknown page is selected
            logger.warning(f"Unknown page selected: {page}")
            display_dashboard()
    except Exception as e:
        # Handle any errors in page display
        logger.error(f"Error displaying page {page}: {str(e)}", exc_info=True)
        st.error(f"An error occurred while displaying the {page} page.")
        
        # Show details in debug mode
        if debug_mode:
            st.exception(e)
        else:
            st.info("Enable debug mode in the sidebar for more information.")
    
    # Footer
    display_footer()


if __name__ == "__main__":
    main()