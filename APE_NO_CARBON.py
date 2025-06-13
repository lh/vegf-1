"""
AMD Protocol Explorer V2 - WITHOUT Carbon Buttons
Testing if deployment works without streamlit-carbon-button
"""

import streamlit as st
from pathlib import Path

# Page configuration MUST be first
st.set_page_config(
    page_title="APE V2 (No Carbon)",
    page_icon="🦍",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize session state
if 'simulation_results' not in st.session_state:
    st.session_state.simulation_results = None
if 'current_protocol' not in st.session_state:
    st.session_state.current_protocol = None
if 'audit_trail' not in st.session_state:
    st.session_state.audit_trail = None

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
    st.title("AMD Protocol Explorer (No Carbon Test)")
    st.markdown("Testing deployment without Carbon buttons.")

# Navigation section using standard Streamlit buttons
st.header("🧭 Navigation")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🏥 Protocol Manager", key="protocol_nav", use_container_width=True):
        st.switch_page("pages/1_Protocol_Manager.py")
        
with col2:
    if st.button("🏃 Run Simulation", key="run_nav", use_container_width=True):
        st.switch_page("pages/2_Run_Simulation.py")
        
with col3:
    if st.button("📊 Analysis Overview", key="analysis_nav", use_container_width=True):
        st.switch_page("pages/3_Analysis_Overview.py")

# Info sections
st.markdown("---")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    ### 🚀 Getting Started
    
    1. **Define Protocol** - Set up your treatment protocol parameters
    2. **Run Simulation** - Execute simulations with complete traceability  
    3. **Analyze Results** - Explore outcomes with interactive visualizations
    
    ### 📋 Key Features
    
    - **Complete parameter traceability** - Every value tracked from source
    - **Scientific rigor** - No synthetic data, only real simulation results
    - **Interactive analysis** - Explore your data from multiple perspectives
    """)

with col2:
    st.markdown("""
    ### 📊 Available Analyses
    
    - **Patient Trajectories** - Follow individual patient journeys
    - **Outcome Distributions** - Statistical analysis of endpoints
    - **Economic Analysis** - Cost-effectiveness evaluations
    - **Sensitivity Analysis** - Parameter impact assessment
    
    ### 🔬 Scientific Integrity
    
    This tool maintains complete scientific integrity:
    - All data comes from actual simulations
    - No synthetic or smoothed data
    - Full audit trail for every parameter
    """)

# Footer
st.markdown("---")
st.caption("APE V2 - AMD Protocol Explorer | Built with Streamlit")

# Success indicator
st.success("✅ If you see this, the app is running without Carbon buttons!")