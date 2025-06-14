#!/usr/bin/env python3
"""
Quick script to test that the Streamlit app properly displays the thumbnails.
This will create a screenshot if possible or at least verify the HTML output.
"""

import subprocess
import time
import requests
import sys

def check_streamlit_app():
    """Check if the Streamlit app shows the thumbnails correctly."""
    
    print("Starting Streamlit app in test mode...")
    
    # Try to get the HTML content
    try:
        # Start the test UI
        proc = subprocess.Popen([
            sys.executable, "-m", "streamlit", "run", 
            "test_ui_integration.py", 
            "--server.port", "8509",
            "--server.headless", "true"
        ])
        
        # Give it time to start
        time.sleep(5)
        
        # Make a request to check if it's running
        response = requests.get("http://localhost:8509")
        
        if response.status_code == 200:
            print("✓ Streamlit app is running successfully")
            print("✓ Thumbnails should be visible at http://localhost:8509")
            
            # Check for key elements in the HTML
            html_content = response.text
            
            if "Quick Comparison" in html_content:
                print("✓ Found 'Quick Comparison' section")
            else:
                print("✗ Could not find 'Quick Comparison' section")
                
            if "Mean + 95% CI" in html_content:
                print("✓ Found mean plot caption")
            else:
                print("✗ Could not find mean plot caption")
                
            if "Patient Distribution" in html_content:
                print("✓ Found distribution plot caption")
            else:
                print("✗ Could not find distribution plot caption")
                
        else:
            print(f"✗ Failed to connect to Streamlit app: {response.status_code}")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Clean up
        try:
            proc.terminate()
        except:
            pass
    
    print("\nUI integration test complete.")
    print("To manually verify:")
    print("1. Run: streamlit run test_ui_integration.py")
    print("2. Check that thumbnails appear side-by-side")
    print("3. Check that full plots are stacked below")

if __name__ == "__main__":
    check_streamlit_app()