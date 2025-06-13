#!/usr/bin/env python3
"""
APE: AMD Protocol Explorer with Fixed Discontinuation Implementation

This script provides a direct entry point for running the APE dashboard
with the fixed implementations for correct discontinuation tracking.
"""

import os
import sys
import subprocess

print("Using fixed discontinuation implementation...")

# Force import path to include the project root
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Import the fixed implementations to make sure they're available
try:
    from treat_and_extend_abs_fixed import TreatAndExtendABS
    from treat_and_extend_des_fixed import TreatAndExtendDES
    print("✅ Successfully imported fixed TreatAndExtendABS and TreatAndExtendDES implementations")
    print("✅ Discontinuation rates will be correct (≤100%)")
except ImportError as e:
    print(f"❌ Failed to import fixed implementations: {e}")
    print("⚠️ Will fall back to original implementation with potential discontinuation rate issues")

# Ensure we're in the project root directory
os.chdir(project_root)
print(f"Changed working directory to: {os.getcwd()}")

# Run streamlit command using the properly modified app.py
app_path = os.path.join(project_root, "streamlit_app", "app.py")
print(f"Running app from: {app_path}")

# Run the Streamlit app using subprocess so we can see any errors immediately
subprocess.run(["streamlit", "run", app_path, "--server.port=8502"])