"""Debug version of APE to find deployment issues."""

import streamlit as st
import sys
import traceback

st.set_page_config(page_title="APE Debug", page_icon="🐛")
st.title("🐛 APE Debug Mode")

# Show Python version
st.write(f"Python version: {sys.version}")

# Test imports step by step
st.header("Testing Imports")

# Test basic imports
try:
    import pandas as pd
    import numpy as np
    st.success("✅ Basic imports OK")
except Exception as e:
    st.error(f"❌ Basic import failed: {e}")
    st.stop()

# Test streamlit-carbon-button
try:
    from streamlit_carbon_button import carbon_button
    st.success("✅ streamlit-carbon-button imported")
except Exception as e:
    st.error(f"❌ streamlit-carbon-button import failed: {e}")
    st.write("Full traceback:")
    st.code(traceback.format_exc())

# Test our wrapper
try:
    from ape.utils.carbon_button_helpers import navigation_button
    st.success("✅ carbon_button_helpers imported")
except Exception as e:
    st.error(f"❌ carbon_button_helpers import failed: {e}")
    st.write("Full traceback:")
    st.code(traceback.format_exc())

# If we get here, imports are OK
st.header("Import Test Complete")
st.success("All imports successful! The issue might be in the main app logic.")

# Test running the actual app
if st.button("Try to load APE.py"):
    try:
        # Import the main app components
        st.write("Attempting to load APE components...")
        
        # Test session state initialization
        if 'simulation_results' not in st.session_state:
            st.session_state.simulation_results = None
        if 'current_protocol' not in st.session_state:
            st.session_state.current_protocol = None
        if 'audit_trail' not in st.session_state:
            st.session_state.audit_trail = None
            
        st.success("✅ Session state initialized")
        
        # Try to create a button
        if navigation_button("Test Button", key="test", icon="home"):
            st.write("Button clicked!")
            
    except Exception as e:
        st.error(f"❌ Error in main app: {e}")
        st.write("Full traceback:")
        st.code(traceback.format_exc())