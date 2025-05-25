"""
Patched entry point for the Streamlit app to use the fixed discontinuation implementations.

This script monkey-patches the imports in the simulation_runner.py module
to use the fixed versions of the ABS and DES implementations.
"""

import os
import sys
import importlib.util
import streamlit as st

# Add the project root directory to sys.path
root_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(root_dir)

# Import the Streamlit app module
from streamlit_app.app import app

# Define a monkey patch to use the fixed implementations
def patch_imports():
    """
    Monkey patch the imports in the simulation_runner.py module to use the fixed
    implementations of the treat-and-extend protocol.
    """
    import streamlit_app.simulation_runner as sr
    import treat_and_extend_abs_fixed
    import treat_and_extend_des_fixed
    
    # Replace the original classes with the fixed ones
    sr.TreatAndExtendABS = treat_and_extend_abs_fixed.TreatAndExtendABS
    sr.TreatAndExtendDES = treat_and_extend_des_fixed.TreatAndExtendDES
    
    print("Successfully patched Streamlit app to use fixed discontinuation implementations.")

# Patch the imports
patch_imports()

# Display a notice to the user
st.sidebar.success("""
### Using Fixed Discontinuation Implementation

This app is using the fixed discontinuation implementation that properly tracks 
unique patient discontinuations and prevents double-counting.

The discontinuation rates shown will be accurate (≤100%).
""")

# Run the app
if __name__ == "__main__":
    app()