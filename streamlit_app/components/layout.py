"""
Layout components for the APE Streamlit application.

This module contains components for the application layout including:
- Logo and title display
- Sidebar navigation
- Footer
"""

import os
import streamlit as st
from pathlib import Path

def display_logo_and_title(title, logo_width=100, column_ratio=[1, 4]):
    """Display the APE logo and title in columns.
    
    Parameters
    ----------
    title : str
        The title to display
    logo_width : int, optional
        Width of the logo image, by default 100
    column_ratio : list, optional
        Ratio for the columns [logo_col, title_col], by default [1, 4]
    """
    # Create columns for logo and title
    col1, col2 = st.columns(column_ratio)
    
    # Try to display logo in the first column
    try:
        # Try SVG first, then fall back to JPG if SVG not found
        svg_logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "ape_logo.svg")
        jpg_logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "ape_logo.jpg")
        
        if os.path.exists(svg_logo_path):
            col1.image(svg_logo_path, width=logo_width)
        elif os.path.exists(jpg_logo_path):
            col1.image(jpg_logo_path, width=logo_width)
    except Exception:
        pass
    
    # Display title in the second column
    col2.title(title)

def get_favicon():
    """Get the path to the favicon or default emoji.
    
    Returns
    -------
    str
        Path to the favicon SVG or emoji fallback
    """
    favicon = "🦧"  # Default emoji fallback
    try:
        svg_logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "ape_logo.svg")
        if os.path.exists(svg_logo_path):
            favicon = svg_logo_path
    except Exception:
        pass
    
    return favicon

def display_sidebar_logo():
    """Display the logo in the sidebar with fallback to text.
    
    Returns
    -------
    bool
        True if logo was displayed, False if fallback to text
    """
    try:
        # Try SVG first, then fall back to JPG if SVG not found
        svg_logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "ape_logo.svg")
        jpg_logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "ape_logo.jpg")
        
        if os.path.exists(svg_logo_path):
            st.sidebar.image(svg_logo_path, width=150)
            return True
        elif os.path.exists(jpg_logo_path):
            st.sidebar.image(jpg_logo_path, width=150)
            return True
        else:
            st.sidebar.title("APE: AMD Protocol Explorer")
            return False
    except Exception:
        st.sidebar.title("APE: AMD Protocol Explorer")
        return False

def create_navigation():
    """Create the sidebar navigation.
    
    Returns
    -------
    str
        The selected page
    """
    page = st.sidebar.radio(
        "Navigate to",
        ["Dashboard", "Run Simulation", "Staggered Simulation", "Patient Explorer", "Reports", "About"],
        key="navigation",
        format_func=lambda x: f"{x}",  # For better screen reader support
        index=0,
        help="Select an application section to navigate to"
    )
    
    # Add a marker element to make navigation accessible for Puppeteer
    st.sidebar.markdown('<div data-test-id="main-navigation-marker"></div>', unsafe_allow_html=True)
    
    return page

def create_debug_toggle():
    """Create the debug mode toggle in the sidebar.
    
    Returns
    -------
    bool
        True if debug mode is enabled, False otherwise
    """
    debug_mode = st.sidebar.checkbox(
        "🛠️ Debug Mode", 
        value=False, 
        help="Show detailed diagnostic information",
        key="debug_mode_toggle"
    )
    
    return debug_mode

def display_footer():
    """Display the application footer in the sidebar."""
    st.sidebar.markdown("---")
    st.sidebar.markdown("© 2025 APE: AMD Protocol Explorer")

def setup_page_config():
    """Set up the Streamlit page configuration."""
    favicon = get_favicon()
    st.set_page_config(
        page_title="APE: AMD Protocol Explorer",
        page_icon=favicon,
        layout="wide",
        initial_sidebar_state="expanded",
    )

def display_fixed_implementation_notice():
    """Display a notice about fixed implementation if applicable."""
    try:
        from streamlit_app.simulation_runner import USING_FIXED_IMPLEMENTATION
        if USING_FIXED_IMPLEMENTATION:
            st.sidebar.success("""
            ### Using Fixed Discontinuation Implementation
            
            This app is using the fixed discontinuation implementation that properly tracks 
            unique patient discontinuations and prevents double-counting.
            
            The discontinuation rates shown will be accurate (≤100%).
            """)
    except ImportError:
        pass