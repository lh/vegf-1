#!/usr/bin/env python3
"""
Setup Streamlit App Environment

This script sets up the required directories and files for the Streamlit app.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def main():
    print("Setting up APE: AMD Protocol Explorer Streamlit environment...")
    
    # Get the project root directory
    project_root = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_root)
    print(f"Working directory: {os.getcwd()}")
    
    # Create required directories if they don't exist
    dirs_to_create = [
        "streamlit_app",
        "streamlit_app/assets",
        "streamlit_app/reports",
        ".streamlit",
        "output/simulation_results"
    ]
    
    for dir_path in dirs_to_create:
        os.makedirs(dir_path, exist_ok=True)
        print(f"Created directory: {dir_path}")
    
    # Install requirements
    print("Installing Streamlit requirements...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "streamlit_requirements.txt"], check=True)
        print("Successfully installed Streamlit requirements")
    except subprocess.CalledProcessError as e:
        print(f"Error installing requirements: {e}")
        print("You may need to install them manually with: pip install -r streamlit_requirements.txt")
    
    # Check if Streamlit is installed
    try:
        subprocess.run(["streamlit", "--version"], check=True, capture_output=True)
        print("Streamlit is installed and ready to use")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Streamlit installation could not be verified")
        print("Make sure it's installed with: pip install streamlit")
    
    # Print next steps
    print("\nSetup complete! To run the APE dashboard:")
    print("1. Run: python run_ape.py")
    print("2. Or use: streamlit run streamlit_app/app.py")
    print("\nThe dashboard will be available at http://localhost:8502")

if __name__ == "__main__":
    main()