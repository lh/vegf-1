#!/usr/bin/env python3
"""Test if financial PDF download works in the UI."""

import requests
import time

# Wait for app to be ready
print("Waiting for Streamlit app to be ready...")
time.sleep(3)

# Check if the app is running
try:
    response = requests.get("http://localhost:8503")
    if response.status_code == 200:
        print("✅ Streamlit app is running on port 8503")
        print("✅ Navigate to: http://localhost:8503")
        print("\nTo test the financial PDF:")
        print("1. Go to 'Workload & Economic Analysis' page")
        print("2. Make sure you have a simulation with resource tracking enabled")
        print("3. Expand 'Export Options' at the bottom")
        print("4. Click 'Download Financial Parameters (PDF)' in the third column")
        print("\nThe PDF should:")
        print("- Show 'Imaging' instead of 'Diagnostic imaging' in the HRG Code column")
        print("- Have no text overflow issues")
        print("- Display simulation details at the top (not in an expander)")
    else:
        print("❌ App returned status code:", response.status_code)
except Exception as e:
    print("❌ Could not connect to app:", e)
    print("Make sure the app is running with: streamlit run APE.py")