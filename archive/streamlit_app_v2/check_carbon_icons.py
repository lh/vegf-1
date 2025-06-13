#!/usr/bin/env python3
"""
Script to check available Carbon icons
"""

# Create a test environment and check icons
import subprocess
import sys
import tempfile
import os

with tempfile.TemporaryDirectory() as tmpdir:
    # Create a test script
    test_script = os.path.join(tmpdir, "list_icons.py")
    with open(test_script, "w") as f:
        f.write("""
import streamlit_carbon_button
from streamlit_carbon_button import CarbonIcons

# Get all available icons
print("Available Carbon Icons:")
print("=" * 50)

# Get all attributes that don't start with underscore
icons = [attr for attr in dir(CarbonIcons) if not attr.startswith('_')]

# Group and display
for icon in sorted(icons):
    print(f"CarbonIcons.{icon}")

print(f"\\nTotal icons available: {len(icons)}")

# Check specific icons we want to use
desired_icons = [
    'HOME', 'DOCUMENT', 'PLAY', 'ROCKET', 'ANALYTICS', 'CHART_BAR',
    'UPLOAD', 'DOWNLOAD', 'COPY', 'DELETE', 'TRASH_CAN', 'RENEW',
    'RESET', 'CHECKMARK', 'CLOSE', 'ARROW_RIGHT', 'SAVE',
    'USER', 'SETTINGS', 'INFORMATION', 'WARNING', 'ERROR',
    'CHEMISTRY', 'MEDICATION', 'DASHBOARD', 'FILTER', 'SEARCH',
    'EXPORT', 'ADD', 'ARROW_LEFT', 'VIEW', 'DATA_VIS'
]

print("\\nChecking desired icons:")
print("=" * 50)
for icon in desired_icons:
    if hasattr(CarbonIcons, icon):
        print(f"✓ {icon}")
    else:
        print(f"✗ {icon} - NOT FOUND")
""")
    
    # Run in the virtual environment used for testing
    result = subprocess.run(
        [sys.executable, test_script],
        capture_output=True,
        text=True
    )
    
    print(result.stdout)
    if result.stderr:
        print("Errors:", result.stderr)