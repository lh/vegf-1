"""
AMD Protocol Explorer V2 - Streamlit Interface

Clean implementation using V2 simulation engine with full protocol traceability.
"""

import streamlit as st
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

# Page configuration
st.set_page_config(
    page_title="AMD Protocol Explorer V2",
    page_icon="🦍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'simulation_results' not in st.session_state:
    st.session_state.simulation_results = None
if 'current_protocol' not in st.session_state:
    st.session_state.current_protocol = None
if 'audit_trail' not in st.session_state:
    st.session_state.audit_trail = None

# Main page with logo
col1, col2 = st.columns([1, 5])
with col1:
    logo_path = Path(__file__).parent / "assets" / "ape_logo.svg"
    if logo_path.exists():
        st.image(str(logo_path), width=100)
    else:
        st.markdown("🦍")  # Fallback emoji
with col2:
    st.title("AMD Protocol Explorer V2")

st.markdown("""
Welcome to the V2 simulation system with complete parameter traceability.

### Key Features
- **No Hidden Parameters**: Every parameter explicitly defined in protocol files
- **Full Audit Trail**: Complete tracking from parameter to result
- **Protocol Library**: Load and compare different treatment protocols
- **Reproducible Results**: Checksums ensure exact protocol versions

### Getting Started
1. Navigate to **Protocol Manager** to view available protocols
2. Go to **Run Simulation** to execute a protocol
3. View results in **Analysis** pages
""")

# Info columns
col1, col2, col3 = st.columns(3)

with col1:
    st.info("""
    **📋 Protocol Manager**
    
    Browse, view, and validate treatment protocols
    """)

with col2:
    st.info("""
    **🚀 Run Simulation**
    
    Execute simulations with selected protocols
    """)

with col3:
    st.info("""
    **📊 Analysis**
    
    Visualize and compare simulation results
    """)

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
st.caption("🦍 AMD Protocol Explorer V2 - Scientific simulation with complete traceability")