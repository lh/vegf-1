#!/usr/bin/env python3
"""Run the analyze_treatment_states.py script."""

import subprocess
import sys

# Run the script
result = subprocess.run([sys.executable, "analyze_treatment_states.py"], capture_output=True, text=True)

print("STDOUT:")
print(result.stdout)
print("\nSTDERR:")
print(result.stderr)
print(f"\nReturn code: {result.returncode}")