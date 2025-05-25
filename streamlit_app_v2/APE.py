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

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

# Import button styling fix
from utils.button_styling import style_navigation_buttons


# Initialize session state
if 'simulation_results' not in st.session_state:
    st.session_state.simulation_results = None
if 'current_protocol' not in st.session_state:
    st.session_state.current_protocol = None
if 'audit_trail' not in st.session_state:
    st.session_state.audit_trail = None

# Main page
st.title("AMD Protocol Explorer")

st.markdown("Welcome to the V2 simulation system with complete parameter traceability.")

# Two column layout for intro content
col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    ### Getting Started
    1. Navigate to **Protocol Manager** to view available protocols
    2. Go to **Run Simulation** to execute a protocol
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

# Apply button styling (includes red text fix!)
style_navigation_buttons()

# Navigation cards
col1, col2, col3 = st.columns(3)

with col1:
    if st.button(
        "📋 **Protocol Manager**\n\nBrowse, view, and validate treatment protocols",
        key="nav_protocol",
        use_container_width=True
    ):
        st.switch_page("pages/1_Protocol_Manager.py")

with col2:
    if st.button(
        "🚀 **Run Simulation**\n\nExecute simulations with selected protocols",
        key="nav_simulation",
        use_container_width=True
    ):
        st.switch_page("pages/2_Run_Simulation.py")

with col3:
    if st.button(
        "📊 **Analysis**\n\nVisualize and compare simulation results",
        key="nav_analysis",
        use_container_width=True
    ):
        st.switch_page("pages/3_Analysis_Overview.py")

# Current status
st.markdown("---")
st.subheader("Current Status")

col1, col2 = st.columns(2)

with col1:
    if st.session_state.current_protocol:
        st.success(f"✅ Protocol Loaded: {st.session_state.current_protocol['name']}")
    else:
        st.warning("⚠️ No protocol loaded")

with col2:
    if st.session_state.simulation_results:
        st.success("✅ Simulation results available")
    else:
        st.info("ℹ️ No simulation results yet")

# Footer
st.markdown("---")
st.caption("🦍 APE V2 - Scientific simulation with complete traceability")

# Add logo to sidebar (only on main page)
logo_path = Path(__file__).parent / "assets" / "ape_logo.svg"
if logo_path.exists():
    st.sidebar.image(str(logo_path), use_container_width=True)