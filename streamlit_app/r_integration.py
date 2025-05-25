"""
R integration module for Streamlit visualizations.

This module provides functions to create high-quality visualizations using R
from within a Python/Streamlit application.
"""

import os
import subprocess
import pandas as pd
import tempfile
from pathlib import Path
import streamlit as st
import uuid  # For generating unique filenames

def create_enrollment_visualization(enrollment_dates, width=8, height=5):
    """
    Create beautiful enrollment visualization using R's ggplot2.
    
    Parameters
    ----------
    enrollment_dates : dict
        Dictionary mapping patient IDs to enrollment dates
    width : float, optional
        Width of the output plot in inches, by default 8
    height : float, optional
        Height of the output plot in inches, by default 5
    
    Returns
    -------
    str
        Path to the generated visualization image
    """
    # Check if R is installed
    try:
        # Check R availability silently
        subprocess.run(
            ["Rscript", "--version"], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE
        )
    except (subprocess.SubprocessError, FileNotFoundError):
        st.warning("R is not available. Using fallback visualization.")
        return None
    
    # Create temporary CSV file for enrollment data
    with tempfile.NamedTemporaryFile(suffix='.csv', mode='w', delete=False) as tmp_data:
        # Convert enrollment dates to DataFrame
        data = []
        for patient_id, date in enrollment_dates.items():
            data.append({
                'patient_id': patient_id,
                'enrollment_date': date
            })
        
        # Write to CSV
        pd.DataFrame(data).to_csv(tmp_data.name, index=False)
        data_file = tmp_data.name
    
    # Create unique output file path to prevent overwriting/caching issues
    unique_id = uuid.uuid4().hex[:8]
    output_file = os.path.join(tempfile.gettempdir(), f"enrollment_viz_{unique_id}.png")
    
    # Get R script path
    r_script_path = Path(__file__).parent / "r_visualization.R"
    
    # Run R script with detailed logging
    try:
        print("Attempting to run R visualization...")
        print(f"R script path: {r_script_path}")
        print(f"Data file: {data_file}")
        print(f"Output file: {output_file}")

        # First verify R is working
        r_check = subprocess.run(
            ["Rscript", "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        print(f"R version check: {r_check.stdout} {r_check.stderr}")

        # Check if required packages are installed
        packages_check = subprocess.run(
            ["Rscript", "-e", "installed.packages()[,1]"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        print(f"Installed R packages: {packages_check.stdout}")

        # Now try to run our script
        result = subprocess.run(
            [
                "Rscript",
                str(r_script_path),
                data_file,
                output_file,
                str(width),
                str(height)
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=30  # Timeout after 30 seconds
        )

        # Log the full output
        print(f"R stdout: {result.stdout}")
        print(f"R stderr: {result.stderr}")
        print(f"R return code: {result.returncode}")
        print(f"Output file exists: {os.path.exists(output_file)}")

        # Check if the visualization was successful
        if result.returncode == 0 and os.path.exists(output_file):
            print("R visualization successful!")
            # Clean up temporary data file
            try:
                os.unlink(data_file)
            except Exception as e:
                print(f"Error removing temp file: {e}")

            return output_file
        else:
            # Log error
            print(f"R visualization failed: {result.stderr}")

            # Clean up temporary files
            try:
                os.unlink(data_file)
            except Exception:
                pass

            return None
    except Exception as e:
        print(f"Failed to run R visualization: {e}")
        
        # Clean up temporary files
        try:
            os.unlink(data_file)
        except Exception:
            pass
            
        return None