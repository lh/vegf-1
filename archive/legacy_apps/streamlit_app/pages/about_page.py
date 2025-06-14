"""
About page for the APE Streamlit application.

This module displays information about the application, its features,
and acknowledgments.
"""

import streamlit as st
from streamlit_app.components.layout import display_logo_and_title

# Import acknowledgments text if available
try:
    from streamlit_app.acknowledgments import ACKNOWLEDGMENT_TEXT
except ImportError:
    ACKNOWLEDGMENT_TEXT = """
    ## Acknowledgments
    
    This application was developed with the support of many contributors.
    Specific acknowledgments to be added.
    """


def display_about_page():
    """Display the about page with information about the application."""
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
    
    - Multiple discontinuation types (protocol-based, administrative, not renewed, premature)
    - Type-specific monitoring schedules
    - Time-dependent recurrence probabilities based on clinical data
    - Clinician variation in protocol adherence and treatment decisions
    """)
    
    # Display acknowledgments
    st.markdown(ACKNOWLEDGMENT_TEXT)
    
    # Display technical information about the application
    with st.expander("Technical Information"):
        st.markdown("""
        ### Technology Stack
        
        - **Frontend**: Streamlit
        - **Data Processing**: Pandas, NumPy
        - **Visualization**: Matplotlib, R/ggplot2
        - **Simulation**: Custom DES and ABS engines
        - **Report Generation**: Quarto
        
        ### Architecture
        
        The application follows a modular architecture:
        
        - **Pages**: Separate page components for different parts of the application
        - **Components**: Reusable UI components with consistent styling
        - **Models**: Structured data models for simulation parameters and results
        - **Visualization**: Progressive enhancement approach with both matplotlib and R
        - **Utils**: Shared utilities for state management, error handling, etc.
        
        ### High Performance Visualization
        
        The application uses a hybrid approach to visualization:
        
        1. Immediate display of matplotlib visualizations for responsive UI
        2. Background generation of high-quality R/ggplot2 visualizations
        3. Progressive replacement of matplotlib with R visualizations when ready
        4. Persistent caching to avoid regeneration of visualizations
        
        This ensures a responsive user experience while still providing publication-quality
        visualizations for reports and analysis.
        """)
    
    # Contact information
    st.subheader("Contact")
    st.markdown("""
    For questions or feedback about this dashboard, please contact:
    
    [Your Contact Information]
    """)


if __name__ == "__main__":
    # This allows the page to be run directly for testing
    import sys
    import os
    
    # Add parent directory to path so imports work
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # Set up basic Streamlit configuration
    st.set_page_config(page_title="About Test", layout="wide")
    
    # Display the about page
    display_about_page()