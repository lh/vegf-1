#!/usr/bin/env python3
"""Quick test to launch the app and verify it works."""

import subprocess
import time
import requests
import sys

print("Starting Streamlit app...")
proc = subprocess.Popen(
    ["streamlit", "run", "APE.py", "--server.headless", "true", "--server.port", "8505"],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)

# Give it time to start
time.sleep(5)

try:
    # Check if app is running
    response = requests.get("http://localhost:8505")
    if response.status_code == 200:
        print("✅ App started successfully!")
        
        # Test each page
        pages = [
            ("Home", "http://localhost:8505/"),
            ("Protocol Manager", "http://localhost:8505/Protocol_Manager"),
            ("Simulations", "http://localhost:8505/Simulations"),
            ("Analysis", "http://localhost:8505/Analysis")
        ]
        
        for name, url in pages:
            try:
                resp = requests.get(url, timeout=5)
                if resp.status_code == 200:
                    print(f"✅ {name} page loads")
                else:
                    print(f"❌ {name} page error: {resp.status_code}")
            except Exception as e:
                print(f"❌ {name} page error: {e}")
                
    else:
        print(f"❌ App failed to start: {response.status_code}")
        
except Exception as e:
    print(f"❌ Could not connect to app: {e}")
    
finally:
    # Clean up
    proc.terminate()
    proc.wait()
    print("\nApp stopped.")