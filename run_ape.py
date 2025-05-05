"""
APE: AMD Protocol Explorer main runner

This script provides a simpler entry point for running the APE dashboard
with correct imports for simulation modules.
"""

import os
import sys
import streamlit.web.cli as stcli

# Ensure we're in the right directory
if os.path.dirname(__file__) != '':
    os.chdir(os.path.dirname(__file__))

# Add current directory to Python path
sys.path.append(os.getcwd())

def run_streamlit():
    """Run the Streamlit app."""
    sys.argv = ["streamlit", "run", "streamlit_app/app.py", "--server.port=8502"]
    sys.exit(stcli.main())

if __name__ == "__main__":
    run_streamlit()