"""Test without accessing any submodules."""

import streamlit as st

st.title("No Submodules Test")
st.write("Testing if submodules are causing deployment issues")

# Don't access any files from submodule directories
st.write("This app does not access:")
st.write("- aflibercept_2mg_data/")
st.write("- eylea_high_dose_data/")  
st.write("- vegf_literature_data/")

st.success("If you see this, the issue might be with submodule access!")