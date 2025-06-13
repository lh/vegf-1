#!/usr/bin/env python3
"""
APE: AMD Protocol Explorer main runner

This script provides a simpler entry point for running the APE dashboard
with correct imports for simulation modules.
"""

import os
import sys
import subprocess

# First, import the FORCE direct fix for discontinuation tracking
print("Applying FORCE direct fix for ABS discontinuation statistics...")
try:
    import force_abs_fix
    print("✅ Applied FORCE direct fix for ABS discontinuation counting")
except ImportError:
    print("❌ Failed to apply FORCE direct fix for ABS discontinuation counting")
    
    # Fall back to the other fixes if the force fix fails
    # First, import the direct fixes for discontinuation tracking
    print("Applying direct fixes for discontinuation tracking...")

    # Import ABS-specific fix first
    try:
        import fix_abs_discontinuation
        print("✅ Applied direct fix for ABS discontinuation counting")
    except ImportError:
        print("❌ Failed to apply ABS discontinuation fix")

    # Then import generic discontinuation fix
    try:
        import fix_discontinuation_tracking
        print("✅ Applied direct fix for discontinuation tracking (prevents multiple counting)")
    except ImportError:
        print("❌ Failed to apply direct fix for discontinuation tracking")

# Then, import the patient modification module
print("Importing discontinuation_ready_patients to patch simulation...")
try:
    import discontinuation_ready_patients
    # Configure to make 50% of patients ready for discontinuation and prevent multiple discontinuations
    discontinuation_ready_patients.configure(
        discontinuation_ready_percent=0.5, 
        verbose=True,
        prevent_multiple_discontinuations=True  # Prevent the same patient from being discontinued multiple times
    )
    print("✅ Successfully imported and configured discontinuation_ready_patients")
    print("✅ Enabled prevention of multiple discontinuations for the same patient")
except ImportError:
    print("⚠️ Could not import discontinuation_ready_patients module")
    # Fall back to legacy inject_discontinuation
    try:
        import inject_discontinuation
        print("⚠️ Using legacy inject_discontinuation module instead")
    except ImportError:
        print("❌ Could not import either discontinuation module")

# Force discontinuation to be enabled in all paths
print("Ensuring discontinuation is enabled in simulation config...")
try:
    # Import SimulationConfig to modify default parameters
    from simulation.config import SimulationConfig
    
    # Monkey patch from_yaml to make sure discontinuation is enabled
    original_from_yaml = SimulationConfig.from_yaml
    
    def patched_from_yaml(cls, config_name):
        """Patched version that ensures discontinuation is enabled"""
        config = original_from_yaml(cls, config_name)
        
        # Ensure parameters exist
        if not hasattr(config, 'parameters'):
            config.parameters = {}
            
        # Ensure discontinuation parameters exist
        if 'discontinuation' not in config.parameters:
            config.parameters['discontinuation'] = {}
            
        # Force enabled to True
        config.parameters['discontinuation']['enabled'] = True
        
        # Ensure criteria exists
        if 'criteria' not in config.parameters['discontinuation']:
            config.parameters['discontinuation']['criteria'] = {}
            
        # Increase probabilities for testing
        stable_criteria = config.parameters['discontinuation']['criteria'].get('stable_max_interval', {})
        if not stable_criteria:
            config.parameters['discontinuation']['criteria']['stable_max_interval'] = {'probability': 0.9}
        else:
            config.parameters['discontinuation']['criteria']['stable_max_interval']['probability'] = 0.9
            
        print(f"✅ Patched SimulationConfig - discontinuation enabled and probability set to 0.9")
        return config
    
    # Apply the patch
    SimulationConfig.from_yaml = classmethod(patched_from_yaml)
    
except Exception as e:
    print(f"❌ Failed to ensure discontinuation parameters: {e}")

# Get the absolute path to the project root directory
project_root = os.path.dirname(os.path.abspath(__file__))

# Ensure we're in the project root directory
os.chdir(project_root)
print(f"Changed working directory to: {os.getcwd()}")

# Run streamlit command
app_path = os.path.join(project_root, "streamlit_app", "app.py")
print(f"Running app from: {app_path}")

# Run the Streamlit app using subprocess so we can see any errors immediately
subprocess.run(["streamlit", "run", app_path, "--server.port=8502"])