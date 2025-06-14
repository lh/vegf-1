"""
AMD Protocol Explorer V2 - Streamlit Interface

Clean implementation using V2 simulation engine with full protocol traceability.
"""

import streamlit as st
import sys
from pathlib import Path

# Page configuration MUST be first
st.set_page_config(
    page_title="APE V2",
    page_icon="🦍",
    layout="wide",
    initial_sidebar_state="collapsed"  # Start with sidebar hidden
)

# Import startup redirect to handle crash recovery
from ape.utils.startup_redirect import initialize_session_state, check_deployment_recovery

# Initialize session state and check for crash recovery
initialize_session_state()

# Import Carbon button helpers
from ape.utils.carbon_button_helpers import navigation_button

# Main page with logo
logo_col, title_col = st.columns([1, 4])

with logo_col:
    # Display the ape logo
    logo_path = Path(__file__).parent / "assets" / "ape_logo.svg"
    if logo_path.exists():
        st.image(str(logo_path), width=150)
    else:
        st.markdown("🦍")  # Fallback emoji

with title_col:
    st.title("AMD Protocol Explorer")
    st.markdown("Welcome to the V2 simulation system with complete parameter traceability.")

# Two column layout for intro content
col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    ### Getting Started
    1. Navigate to **Protocol Manager** to view available protocols
    2. Go to **Simulations** to run or manage simulations
    3. View results in **Analysis** pages
    """)

with col2:
    st.markdown("""
    ### Key Features
    - **No Hidden Parameters**: Every parameter explicitly defined in protocol files
    - **Full Audit Trail**: Complete tracking from parameter to result
    - **Protocol Library**: Load and compare different treatment protocols
    - **Reproducible Results**: Checksums ensure exact protocol versions
    """)

# No longer need custom styling - Carbon buttons handle it

# Navigation cards
st.subheader("Navigation")
col1, col2, col3 = st.columns(3)

with col1:
    if navigation_button(
        "Protocol Manager",
        key="nav_protocol",
        help_text="Browse, view, and validate treatment protocols",
        full_width=True
    ):
        st.switch_page("pages/1_Protocol_Manager.py")

with col2:
    # Simulations button is always enabled (can manage existing ones)
    if navigation_button(
        "Simulations",
        key="nav_simulation",
        help_text="Run new simulations or manage existing ones",
        full_width=True
    ):
        st.switch_page("pages/2_Simulations.py")

with col3:
    # Disable Analysis if no simulation results are available
    analysis_disabled = st.session_state.simulation_results is None
    if navigation_button(
        "Analysis",
        key="nav_analysis",
        help_text="Visualize and compare simulation results",
        full_width=True,
        disabled=analysis_disabled,
        button_type="ghost" if analysis_disabled else "secondary"
    ):
        st.switch_page("pages/3_Analysis.py")

# Quick status line (optional - much more subtle)
if st.session_state.current_protocol or st.session_state.simulation_results:
    st.markdown("---")
    status_parts = []
    if st.session_state.current_protocol:
        status_parts.append(f"Protocol: **{st.session_state.current_protocol['name']}**")
    if st.session_state.simulation_results:
        status_parts.append("Results: **Available**")
    st.caption(" • ".join(status_parts))

# Footer
st.markdown("---")
st.caption("🦍 APE V2 - Scientific simulation with complete traceability")

# Logo is now displayed in the main page header