"""Absolute minimal test."""
import streamlit as st

st.write("If you see this, Streamlit works!")

# Test basic imports
try:
    import sys
    st.write(f"Python version: {sys.version}")
except Exception as e:
    st.error(f"sys import failed: {e}")

try:
    import os
    st.write(f"Working directory: {os.getcwd()}")
    st.write(f"Files in root: {os.listdir('.')[:10]}")
except Exception as e:
    st.error(f"os import failed: {e}")

# Check if our modules exist
try:
    import simulation_v2
    st.success("simulation_v2 module found")
except Exception as e:
    st.error(f"simulation_v2 not found: {e}")

try:
    import ape
    st.success("ape module found")
except Exception as e:
    st.error(f"ape not found: {e}")

st.balloons()