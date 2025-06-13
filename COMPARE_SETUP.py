"""Compare our setup with carbon-button-demo."""

import streamlit as st

st.title("Setup Comparison")

st.header("Our App (VEGF-1)")
st.code("""
# requirements.txt includes:
streamlit>=1.28.0
pandas>=2.0.0
numpy>=1.24.0
matplotlib>=3.7.0
# ... and others

# Main app: APE.py
# Structure: pages/, ape/, assets/
""")

st.header("Working App (carbon-button-demo)")
st.code("""
# Uses briquette package (not streamlit-carbon-button)
# Simpler structure
# Main app: streamlit_app.py
""")

st.warning("""
Key difference: The working demo uses a different package name!
- Working: from briquette import carbon_button
- Our app: from streamlit_carbon_button import carbon_button
""")

# Show Python version
import sys
st.write(f"Current Python: {sys.version}")
st.info("Streamlit Cloud uses Python 3.13.3 (from logs)")
st.info("Local environment likely uses a different version")