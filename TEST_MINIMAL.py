"""Minimal test app to diagnose Streamlit Cloud deployment issues."""

import streamlit as st

st.set_page_config(page_title="Test Deployment", page_icon="🧪")

st.title("🧪 Minimal Deployment Test")
st.write("If you see this, basic Streamlit is working!")

# Test imports one by one
st.header("Testing Imports")

# Test standard libraries
try:
    import pandas as pd
    import numpy as np
    st.success("✅ pandas and numpy imported successfully")
except Exception as e:
    st.error(f"❌ Failed to import pandas/numpy: {e}")

# Test visualization libraries
try:
    import matplotlib.pyplot as plt
    import seaborn as sns
    import plotly.graph_objects as go
    st.success("✅ Visualization libraries imported successfully")
except Exception as e:
    st.error(f"❌ Failed to import visualization libraries: {e}")

# Test other requirements
try:
    import yaml
    import pyarrow
    st.success("✅ yaml and pyarrow imported successfully")
except Exception as e:
    st.error(f"❌ Failed to import yaml/pyarrow: {e}")

# Test problematic imports
st.header("Testing Potentially Problematic Imports")

try:
    from streamlit_carbon_button import carbon_button
    st.success("✅ streamlit-carbon-button imported successfully")
except Exception as e:
    st.error(f"❌ Failed to import streamlit-carbon-button: {e}")
    st.warning("This is likely causing the deployment failure!")

# Test app-specific imports
st.header("Testing App Imports")

try:
    import sys
    st.write(f"Python version: {sys.version}")
    st.write(f"Python path: {sys.executable}")
    st.write(f"Working directory: {os.getcwd()}")
except:
    pass

# List files in directory
import os
st.header("Files in Root Directory")
files = os.listdir(".")
st.write(files[:20])  # First 20 files

# Check if key directories exist
st.header("Directory Check")
for dir_name in ["pages", "ape", "assets", "protocols"]:
    if os.path.exists(dir_name):
        st.success(f"✅ {dir_name}/ exists")
    else:
        st.error(f"❌ {dir_name}/ not found")

st.success("🎉 Test complete! If you see this, the app can run.")