#!/usr/bin/env python3
"""
APE: AMD Protocol Explorer main runner

This script provides a simpler entry point for running the APE dashboard
with correct imports for simulation modules.
"""

import os
import sys
import subprocess

# Get the absolute path to the project root directory
project_root = os.path.dirname(os.path.abspath(__file__))

# Ensure we're in the project root directory
os.chdir(project_root)
print(f"Changed working directory to: {os.getcwd()}")

# Run streamlit command
app_path = os.path.join(project_root, "streamlit_app", "app.py")
print(f"Running app from: {app_path}")

# Run the Streamlit app using subprocess so we can see any errors immediately
subprocess.run(["streamlit", "run", app_path, "--server.port=8502"])