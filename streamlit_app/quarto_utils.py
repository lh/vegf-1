"""
Quarto Utilities Module

This module provides utilities for integrating Quarto with Streamlit, including
automatic installation of Quarto in Streamlit Cloud environments and rendering
Quarto reports.

Based on the implementation by Sammi Rosser in the Project_Toy_MECC repository
(https://github.com/Bergam0t/Project_Toy_MECC).
"""

import os
import sys
import platform
import subprocess
import streamlit as st
import tempfile
import shutil
from pathlib import Path


def get_quarto():
    """
    Check if Quarto is installed and available. If not, attempt to install it
    in the Streamlit Cloud environment.
    
    This function is adapted from the implementation by Sammi Rosser in the
    Project_Toy_MECC repository.
    
    Returns
    -------
    str or None
        Path to the Quarto executable if available, None otherwise
    """
    # First check if Quarto is already installed
    result = subprocess.run(
        ["which", "quarto"], 
        capture_output=True, 
        text=True
    )
    
    quarto_path = result.stdout.strip()
    
    if quarto_path:
        st.toast(f"Quarto found at {quarto_path}")
        return quarto_path
    
    # If not found, try to install it (primarily for Streamlit Cloud)
    st.info("Quarto not found. Attempting to install...")
    
    try:
        # Create temporary directory for installation
        temp_dir = tempfile.mkdtemp()
        
        # Set up platform-specific details
        system = platform.system().lower()
        
        # Currently only supporting Linux for Streamlit Cloud
        if system != "linux":
            st.warning(f"Automatic Quarto installation is only supported on Linux. Detected: {system}")
            return None
        
        # Download Quarto for Linux
        st.text("Downloading Quarto...")
        quarto_version = "1.5.14"
        quarto_url = f"https://github.com/quarto-dev/quarto-cli/releases/download/v{quarto_version}/quarto-{quarto_version}-linux-amd64.tar.gz"
        
        download_path = os.path.join(temp_dir, "quarto.tar.gz")
        subprocess.run(
            ["wget", quarto_url, "-O", download_path],
            check=True
        )
        
        # Extract the archive
        st.text("Extracting Quarto...")
        extract_dir = os.path.join(temp_dir, "quarto-extract")
        os.makedirs(extract_dir, exist_ok=True)
        
        subprocess.run(
            ["tar", "-xzf", download_path, "-C", extract_dir],
            check=True
        )
        
        # Find the quarto executable
        quarto_dir = os.path.join(extract_dir, f"quarto-{quarto_version}")
        quarto_bin = os.path.join(quarto_dir, "bin", "quarto")
        
        # Make executable
        os.chmod(quarto_bin, 0o755)
        
        # Add to PATH
        os.environ["PATH"] = f"{os.path.dirname(quarto_bin)}:{os.environ['PATH']}"
        
        # Verify installation
        result = subprocess.run(
            [quarto_bin, "--version"],
            capture_output=True,
            text=True
        )
        
        if "quarto" in result.stdout.lower():
            st.success(f"Quarto {quarto_version} installed successfully")
            return quarto_bin
        else:
            st.error("Quarto installation verification failed")
            return None
            
    except Exception as e:
        st.error(f"Failed to install Quarto: {str(e)}")
        return None


def render_quarto_report(quarto_path, qmd_template_path, output_dir, data_path, 
                         output_format='html', include_code=False, include_appendix=True):
    """
    Render a Quarto report from a template using simulation data.
    
    Parameters
    ----------
    quarto_path : str
        Path to the Quarto executable
    qmd_template_path : str
        Path to the Quarto template file (.qmd)
    output_dir : str
        Directory to save the rendered report
    data_path : str
        Path to the JSON data file with simulation results
    output_format : str, optional
        Output format ('html', 'pdf', 'docx'), by default 'html'
    include_code : bool, optional
        Whether to include code chunks in the output, by default False
    include_appendix : bool, optional
        Whether to include the appendix section, by default True
    
    Returns
    -------
    str or None
        Path to the rendered report if successful, None otherwise
    """
    try:
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Create a temporary directory for the template
        with tempfile.TemporaryDirectory() as temp_dir:
            # Copy the template to the temp directory
            temp_qmd_path = os.path.join(temp_dir, "report.qmd")
            shutil.copyfile(qmd_template_path, temp_qmd_path)
            
            # Set up command line arguments
            cmd = [
                quarto_path,
                "render",
                temp_qmd_path,
                "--to", output_format,
                "--output-dir", output_dir,
                "-M", f"dataPath={data_path}",
                "-M", f"includeCode={'true' if include_code else 'false'}",
                "-M", f"includeAppendix={'true' if include_appendix else 'false'}"
            ]
            
            # Run Quarto
            st.text("Rendering report with Quarto...")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                st.error(f"Error rendering report: {result.stderr}")
                return None
            
            # Determine the output file path
            output_filename = f"report.{output_format}"
            output_path = os.path.join(output_dir, output_filename)
            
            if os.path.exists(output_path):
                st.success("Report rendered successfully")
                return output_path
            else:
                st.error(f"Output file not found at {output_path}")
                return None
                
    except Exception as e:
        st.error(f"Failed to render report: {str(e)}")
        return None