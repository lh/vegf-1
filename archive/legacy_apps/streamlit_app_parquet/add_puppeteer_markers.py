"""
Add Missing Puppeteer Markers

This script adds Puppeteer marker elements to the Streamlit app to make it easier for
Puppeteer automation to find and interact with key UI elements. Run this script as part of
the setup process to ensure all UI elements have consistent markers.
"""

import streamlit as st

def add_navigation_markers():
    """
    Add markers for navigation elements in the sidebar.
    This should be called after creating the navigation radio buttons.
    """
    st.sidebar.markdown('<div data-test-id="main-navigation-marker"></div>', unsafe_allow_html=True)
    
def add_simulation_form_markers():
    """
    Add markers for the simulation form elements.
    This should be called in the Run Simulation page.
    """
    # Simulation type selector
    st.markdown('<div data-test-id="simulation-type-select-marker"></div>', unsafe_allow_html=True)
    
    # Advanced options marker
    st.markdown('<div data-test-id="advanced-options-marker"></div>', unsafe_allow_html=True)
    
    # Run simulation button marker
    st.markdown('<div data-test-id="run-simulation-btn-marker"></div>', unsafe_allow_html=True)
    
def add_patient_explorer_markers():
    """
    Add markers for the patient explorer elements.
    This should be called in the Patient Explorer page.
    """
    # Patient selector
    st.markdown('<div data-test-id="patient-selector-marker"></div>', unsafe_allow_html=True)
    
    # Patient list
    st.markdown('<div data-test-id="patient-list-marker"></div>', unsafe_allow_html=True)

def add_patient_expander_marker(index):
    """
    Add a marker for a patient expander element.
    
    Parameters
    ----------
    index : int
        The index of the patient (0-based)
    """
    st.markdown(f'<div data-test-id="patient-expander-{index}-marker"></div>', unsafe_allow_html=True)

def add_retreatment_markers():
    """
    Add markers for the retreatment panel elements.
    """
    # Retreatment panel
    st.markdown('<div data-test-id="retreatment-panel-marker"></div>', unsafe_allow_html=True)
    
    # Retreatment statistics summary expander
    st.markdown('<div data-test-id="retreatment-summary-marker"></div>', unsafe_allow_html=True)
    
    # Retreatment by type expander
    st.markdown('<div data-test-id="retreatment-by-type-marker"></div>', unsafe_allow_html=True)

def add_report_markers():
    """
    Add markers for the report generation elements.
    """
    # Report format selector
    st.markdown('<div data-test-id="report-format-marker"></div>', unsafe_allow_html=True)
    
    # Generate report button
    st.markdown('<div data-test-id="generate-report-btn-marker"></div>', unsafe_allow_html=True)

def add_debug_mode_marker():
    """
    Add marker for the debug mode toggle.
    """
    st.sidebar.markdown('<div data-test-id="debug-mode-toggle-marker"></div>', unsafe_allow_html=True)

# Usage example:
if __name__ == "__main__":
    st.title("Puppeteer Marker Test")
    st.write("This script tests adding Puppeteer markers to the Streamlit app.")
    
    # Add some example markers
    add_navigation_markers()
    add_simulation_form_markers()
    add_patient_explorer_markers()
    
    # Example of adding patient expander markers
    for i in range(3):
        add_patient_expander_marker(i)
        with st.expander(f"Patient {i+1}"):
            st.write(f"Details for patient {i+1}")
    
    add_retreatment_markers()
    add_report_markers()
    
    st.success("All markers added successfully!")