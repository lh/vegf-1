#!/usr/bin/env python3
"""
Launch AMD Protocol Explorer V2

Clean implementation with full parameter traceability.
"""

import os
import sys
import subprocess

print("🚀 Launching AMD Protocol Explorer V2")
print("=" * 50)
print("Key features:")
print("✅ No hidden parameters - everything explicit")
print("✅ Full audit trail for reproducibility")  
print("✅ Protocol-driven simulations")
print("✅ Clean V2 architecture")
print("=" * 50)

# Ensure we're in the project root directory
project_root = os.path.dirname(os.path.abspath(__file__))
os.chdir(project_root)

# Launch the V2 app
app_path = os.path.join(project_root, "streamlit_app_v2", "APE.py")
subprocess.run(["streamlit", "run", app_path, "--server.port=8503"])