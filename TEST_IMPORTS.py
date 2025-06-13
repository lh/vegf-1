"""Test all import strategies for deployment debugging."""

import streamlit as st
import sys
import os

st.set_page_config(page_title="Import Test", page_icon="🔍")
st.title("🔍 Import Strategy Test")

# Show environment info
st.header("Environment Info")
st.write(f"Python version: {sys.version}")
st.write(f"Current directory: {os.getcwd()}")
st.write(f"__file__ location: {__file__ if '__file__' in globals() else 'Not available'}")

# Test direct import
st.header("Test 1: Direct Import")
try:
    from streamlit_carbon_button import carbon_button, CarbonIcons
    st.success("✅ Direct import of streamlit-carbon-button succeeded")
except ImportError as e:
    st.error(f"❌ Direct import failed: {e}")

# Test our wrapper with fallback
st.header("Test 2: Wrapper with Fallback")
try:
    from ape.utils.carbon_button_helpers import ape_button, navigation_button, CARBON_AVAILABLE
    st.success(f"✅ Wrapper import succeeded (CARBON_AVAILABLE={CARBON_AVAILABLE})")
    
    # Try to use the button
    if st.button("Test Standard Button", key="std_test"):
        st.write("Standard button clicked!")
        
    if navigation_button("Test Navigation", key="nav_test"):
        st.write("Navigation button clicked!")
        
except Exception as e:
    st.error(f"❌ Wrapper import failed: {e}")
    import traceback
    st.code(traceback.format_exc())

# Test local fallback directly
st.header("Test 3: Local Fallback Only")
try:
    from ape.utils.carbon_button_local import carbon_button as local_carbon_button, CarbonIcons as LocalCarbonIcons
    st.success("✅ Local fallback import succeeded")
    
    if local_carbon_button("Test Local Button", key="local_test", icon=LocalCarbonIcons.HOME):
        st.write("Local button clicked!")
        
except Exception as e:
    st.error(f"❌ Local fallback import failed: {e}")
    import traceback
    st.code(traceback.format_exc())

st.success("🎉 Import tests complete!")