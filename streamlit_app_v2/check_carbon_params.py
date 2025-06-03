#!/usr/bin/env python3
"""Check carbon_button parameters"""

import inspect
from streamlit_carbon_button import carbon_button

# Get the signature
sig = inspect.signature(carbon_button)

print("carbon_button parameters:")
print("=" * 50)
for param_name, param in sig.parameters.items():
    if param.default == inspect.Parameter.empty:
        print(f"{param_name} (required)")
    else:
        print(f"{param_name} = {param.default}")

print("\nFull signature:")
print(carbon_button.__doc__ if carbon_button.__doc__ else "No docstring available")