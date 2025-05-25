"""
Fixed Streamlit app launcher with correct discontinuation handling.

This script launches the Streamlit app with the fixed discontinuation implementations
that properly track unique patient discontinuations and prevent double-counting.
"""

import os
import sys
import streamlit as st

# Add the project root directory to sys.path
root_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(root_dir)

# Apply monkey patching to use fixed implementations
from streamlit_app.monkey_patch import apply_all_patches

# Apply the patches
patches_applied = apply_all_patches()

# Import the Streamlit app
from streamlit_app.app import app

# Display a notice to the user about the fixed implementation
st.sidebar.success("""
### Using Fixed Discontinuation Implementation

This app is using the fixed discontinuation implementation that properly tracks 
unique patient discontinuations and prevents double-counting.

The discontinuation rates shown will be accurate (≤100%).
""")

if not patches_applied:
    st.sidebar.warning("""
    ⚠️ Warning: The fixed implementation may not have been properly loaded.
    
    Discontinuation rates may still show inaccurate values (>100%).
    Please check the logs for details.
    """)

# Run the app
if __name__ == "__main__":
    app()