#!/usr/bin/env python
"""
Direct R visualization test.

This script tests the R visualization script directly without depending on
the streamlit_app module.
"""

import os
import sys
import subprocess
import tempfile
import pandas as pd
import time

def main():
    """Test R visualization directly."""
    print("=== Direct R Visualization Test ===")
    print(f"Testing at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Python version: {sys.version}")
    print(f"Working directory: {os.getcwd()}")
    print("==================================\n")
    
    # Check if R is available
    try:
        r_version = subprocess.run(
            ["Rscript", "--version"],
            capture_output=True,
            text=True
        )
        print(f"R version: {r_version.stderr.strip()}")
    except Exception as e:
        print(f"Error checking R installation: {e}")
        return
    
    # Find the R script
    r_script_path = os.path.join(os.getcwd(), "streamlit_app", "r_scripts", "visualization.R")
    if not os.path.exists(r_script_path):
        print(f"R script not found at: {r_script_path}")
        return
    
    print(f"Found R script at: {r_script_path}")
    
    # Create test data
    temp_dir = tempfile.mkdtemp()
    csv_path = os.path.join(temp_dir, "test_enrollment.csv")
    output_path = os.path.join(temp_dir, "test_visualization.png")
    
    # Generate sample data
    dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='D')
    patient_ids = range(1, len(dates) + 1)
    df = pd.DataFrame({
        'patient_id': patient_ids,
        'enrollment_date': dates
    })
    df.to_csv(csv_path, index=False)
    
    print(f"Created test data at: {csv_path}")
    print(f"Will save output to: {output_path}")
    
    # Run R script directly
    cmd = [
        "Rscript", r_script_path,
        f"--data={csv_path}",
        f"--output={output_path}",
        "--type=enrollment",
        "--width=10",
        "--height=5",
        "--dpi=120",
        "--theme=tufte"
    ]
    
    print(f"\nRunning command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False
        )
        
        print(f"\nCommand completed with return code: {result.returncode}")
        print(f"\n=== STDOUT ===\n{result.stdout}")
        print(f"\n=== STDERR ===\n{result.stderr}")
        
        if os.path.exists(output_path):
            file_size = os.path.getsize(output_path)
            print(f"\nOutput file created at: {output_path}")
            print(f"File size: {file_size} bytes")
            
            if file_size > 1000:
                print("Test PASSED: Visualization created successfully ✅")
            else:
                print("Test FAILED: Output file is too small or empty ❌")
        else:
            print(f"\nTest FAILED: Output file not created ❌")
    except Exception as e:
        print(f"\nError running R script: {e}")
    
    print(f"\nTest completed. Look for the output file at: {output_path}")
    print(f"If successful, you should be able to open this file to view the visualization.")

if __name__ == "__main__":
    main()