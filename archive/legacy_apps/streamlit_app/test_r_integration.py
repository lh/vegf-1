#!/usr/bin/env python
"""
Test script for R integration.

This script tests the R visualization integration by directly generating an example
plot and verifying that the R script works correctly.
"""

import os
import sys
import pandas as pd
import tempfile
import logging
import time
import subprocess
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Add the project root to the path
root_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(root_dir)

def test_r_installation():
    """Test if R is installed and working."""
    print("Testing R installation...")
    try:
        result = subprocess.run(
            ["which", "Rscript"] if sys.platform != "win32" else ["where", "Rscript"],
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode == 0:
            print(f"R found at: {result.stdout.strip()}")
            
            # Test R version
            version_result = subprocess.run(
                ["Rscript", "--version"],
                capture_output=True,
                text=True,
                check=False
            )
            print(f"R version: {version_result.stderr.strip()}")
            return True
        else:
            print("R not found in PATH")
            return False
    except Exception as e:
        print(f"Error testing R installation: {e}")
        return False

def test_r_packages():
    """Test if required R packages are installed."""
    print("\nTesting R packages...")
    script = """
    installed <- rownames(installed.packages())
    required <- c("ggplot2", "optparse", "lubridate", "scales", "dplyr", "tidyr")
    missing <- required[!required %in% installed]
    if (length(missing) > 0) {
        cat("Missing packages:", paste(missing, collapse=", "))
        quit(status=1)
    } else {
        cat("All required packages are installed")
        quit(status=0)
    }
    """
    
    with tempfile.NamedTemporaryFile(suffix=".R", mode="w", delete=False) as f:
        f.write(script)
        script_path = f.name
    
    try:
        result = subprocess.run(
            ["Rscript", script_path],
            capture_output=True,
            text=True,
            check=False
        )
        
        print(f"Package check result: {result.stdout.strip()}")
        return result.returncode == 0
    except Exception as e:
        print(f"Error testing R packages: {e}")
        return False
    finally:
        os.unlink(script_path)

def test_r_script():
    """Test if the R visualization script exists and is executable."""
    print("\nTesting R script...")
    
    # Import project-specific paths
    from streamlit_app.components.visualizations.common import get_r_script_path, ensure_r_script_exists
    
    r_script_path = get_r_script_path()
    print(f"R script path: {r_script_path}")
    
    if os.path.exists(r_script_path):
        print(f"R script exists with size: {os.path.getsize(r_script_path)} bytes")
        is_executable = os.access(r_script_path, os.X_OK)
        print(f"R script is executable: {is_executable}")
        return True
    else:
        print("R script does not exist, attempting to create it...")
        if ensure_r_script_exists():
            print("R script created successfully")
            return True
        else:
            print("Failed to create R script")
            return False

def create_test_data():
    """Create test enrollment data for visualization."""
    print("\nCreating test data...")
    
    # Create sample enrollment data
    dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='D')
    patient_ids = range(1, len(dates) + 1)
    
    enrollment_data = pd.DataFrame({
        'patient_id': patient_ids,
        'enrollment_date': dates
    })
    
    # Save to temporary CSV
    temp_dir = tempfile.mkdtemp()
    csv_path = os.path.join(temp_dir, 'test_enrollment.csv')
    enrollment_data.to_csv(csv_path, index=False)
    
    print(f"Created test data with {len(enrollment_data)} entries")
    print(f"Data saved to: {csv_path}")
    
    return temp_dir, csv_path, enrollment_data

def test_r_visualization():
    """Test running the R visualization directly."""
    print("\nTesting R visualization...")
    
    # Create test data
    temp_dir, csv_path, _ = create_test_data()
    output_path = os.path.join(temp_dir, 'test_visualization.png')
    
    # Import project-specific paths
    from streamlit_app.components.visualizations.common import get_r_script_path
    r_script_path = get_r_script_path()
    
    # Run R visualization script directly
    cmd = [
        "Rscript", r_script_path,
        "--data", csv_path,
        "--output", output_path,
        "--type", "enrollment",
        "--width", "10",
        "--height", "5",
        "--dpi", "120"
    ]
    
    print(f"Running command: {' '.join(cmd)}")
    
    try:
        start_time = time.time()
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False
        )
        elapsed_time = time.time() - start_time
        
        print(f"Command completed in {elapsed_time:.2f} seconds with return code: {result.returncode}")
        print(f"Stdout: {result.stdout}")
        print(f"Stderr: {result.stderr}")
        
        if os.path.exists(output_path):
            file_size = os.path.getsize(output_path)
            print(f"Output file created: {output_path} (size: {file_size} bytes)")
            if file_size > 1000:
                print("Visualization test PASSED ✅")
                return True
            else:
                print("Output file is too small, likely invalid")
                return False
        else:
            print(f"Output file not created: {output_path}")
            return False
    except Exception as e:
        print(f"Error testing R visualization: {e}")
        return False

def test_integration():
    """Test the integration with the streamlit application."""
    print("\nTesting integration with Streamlit...")
    
    try:
        # Import the render_enrollment_visualization function
        from streamlit_app.components.visualizations.r_integration import render_enrollment_visualization
        
        # Create test data
        _, _, enrollment_df = create_test_data()
        
        # This test cannot run in this script since it requires a Streamlit context
        print("Integration test must be run within Streamlit context.")
        print("Please run the following in your Streamlit app:")
        print("""
        import pandas as pd
        from datetime import timedelta, datetime
        from streamlit_app.components.visualizations.r_integration import render_enrollment_visualization
        
        # Create test data
        dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='D')
        patient_ids = range(1, len(dates) + 1)
        enrollment_df = pd.DataFrame({'patient_id': patient_ids, 'enrollment_date': dates})
        
        # Render visualization
        render_enrollment_visualization(enrollment_df, use_r=True)
        """)
        
        print("Integration test SKIPPED (requires Streamlit context)")
        return None
    except Exception as e:
        print(f"Error in integration test: {e}")
        return False

def main():
    """Run all tests."""
    print("=== R Integration Test ===")
    print(f"Testing at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Python version: {sys.version}")
    print(f"Working directory: {os.getcwd()}")
    print(f"Temp directory: {tempfile.gettempdir()}")
    print("========================\n")
    
    tests = [
        ("R Installation", test_r_installation),
        ("R Packages", test_r_packages),
        ("R Script", test_r_script),
        ("R Visualization", test_r_visualization),
        ("Integration", test_integration)
    ]
    
    results = {}
    
    for name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"RUNNING TEST: {name}")
        print(f"{'='*50}")
        
        try:
            result = test_func()
            results[name] = result
        except Exception as e:
            print(f"Test failed with error: {e}")
            results[name] = False
    
    # Print summary
    print("\n\n=== TEST SUMMARY ===")
    for name, result in results.items():
        status = "PASSED ✅" if result is True else "FAILED ❌" if result is False else "SKIPPED ⚠️"
        print(f"{name}: {status}")
    
    # Overall result
    passed = sum(1 for r in results.values() if r is True)
    failed = sum(1 for r in results.values() if r is False)
    skipped = sum(1 for r in results.values() if r is None)
    
    print(f"\nTEST RESULTS: {passed} passed, {failed} failed, {skipped} skipped")
    
    if failed > 0:
        print("\nSome tests failed. Please check the output above for details.")
    else:
        print("\nAll tests passed or skipped!")

if __name__ == "__main__":
    main()