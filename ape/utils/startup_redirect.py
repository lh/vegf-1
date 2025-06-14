"""Handle startup redirection to ensure we always start at the home page.

This module provides utilities to detect if we're in a fresh session
and redirect to the home page if needed.
"""

import streamlit as st
from typing import Optional


def ensure_home_page_on_startup():
    """
    Ensure that we're on the home page when the app starts or restarts.
    
    This helps recover from crashes where Streamlit remembers the last page.
    """
    # Check if this is a new session
    if 'startup_complete' not in st.session_state:
        # Mark that we've handled startup
        st.session_state.startup_complete = True
        
        # For pages other than home, redirect to home on startup
        # This should be called from individual pages
        return True  # Indicates redirect needed
    return False  # No redirect needed


def handle_page_startup(page_name: str):
    """
    Handle startup for individual pages.
    
    Args:
        page_name: Name of the current page
        
    Returns:
        bool: True if page should redirect to home
    """
    # If we haven't completed startup and we're not on the home page
    if 'startup_complete' not in st.session_state and page_name != 'home':
        # Initialize session state first
        initialize_session_state()
        # Then redirect to home
        st.switch_page("APE.py")
        return True
    return False


def initialize_session_state():
    """Initialize all required session state variables."""
    # Core simulation state
    if 'simulation_results' not in st.session_state:
        st.session_state.simulation_results = None
    if 'current_protocol' not in st.session_state:
        st.session_state.current_protocol = None
    if 'audit_trail' not in st.session_state:
        st.session_state.audit_trail = None
    
    # Track active simulation
    if 'active_simulation_id' not in st.session_state:
        st.session_state.active_simulation_id = None
    if 'active_simulation_name' not in st.session_state:
        st.session_state.active_simulation_name = None
    
    # Startup tracking
    if 'startup_complete' not in st.session_state:
        st.session_state.startup_complete = False


def check_deployment_recovery():
    """
    Check if we're recovering from a deployment crash/restart.
    
    Returns:
        bool: True if this appears to be a recovery scenario
    """
    # Multiple indicators of a fresh start
    fresh_start_indicators = [
        'startup_complete' not in st.session_state,
        st.session_state.get('simulation_results') is None,
        st.session_state.get('current_protocol') is None,
    ]
    
    # If most indicators suggest fresh start, we're likely recovering
    return sum(fresh_start_indicators) >= 2


def force_home_redirect():
    """Force redirect to home page using Streamlit's navigation."""
    # Use a meta refresh as a fallback method
    st.markdown(
        """
        <meta http-equiv="refresh" content="0; url=/">
        <script>window.location.href = '/';</script>
        """,
        unsafe_allow_html=True
    )
    st.stop()