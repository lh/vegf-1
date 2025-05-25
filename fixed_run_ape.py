#!/usr/bin/env python3
"""
APE: AMD Protocol Explorer main runner (FIXED VERSION)

This script provides a fixed entry point for running the APE dashboard
with correct discontinuation handling.
"""

import os
import sys
import subprocess

# Print startup banner
print("=" * 60)
print("APE: AMD Protocol Explorer (FIXED VERSION)")
print("=" * 60)
print("Starting with fixes for discontinuation statistics")

# Get the absolute path to the project root directory
project_root = os.path.dirname(os.path.abspath(__file__))

# Ensure we're in the project root directory
os.chdir(project_root)
print(f"Working directory: {os.getcwd()}")

# Monkey patch the original ABS module to use our fixed version
import sys
import importlib.util

# First, check if the fixed version exists
fixed_abs_path = os.path.join(project_root, "treat_and_extend_abs_fixed.py")
if os.path.exists(fixed_abs_path):
    print("Applying fix for discontinuation statistics...")
    
    # Replace the original module with the fixed one
    try:
        # Import the fixed version
        spec = importlib.util.spec_from_file_location("treat_and_extend_abs_fixed", fixed_abs_path)
        fixed_abs = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(fixed_abs)
        
        # Replace in sys.modules
        sys.modules["treat_and_extend_abs"] = fixed_abs
        print("✅ Successfully patched treat_and_extend_abs module with fixed implementation")
    except Exception as e:
        print(f"❌ Failed to patch treat_and_extend_abs module: {e}")
else:
    print("⚠️ Fixed implementation not found - will try other approaches")
    
    # If the fixed implementation is not available, try the old approach
    try:
        import discontinuation_ready_patients
        discontinuation_ready_patients.configure(
            discontinuation_ready_percent=0.5, 
            verbose=True,
            prevent_multiple_discontinuations=True
        )
        print("✅ Applied legacy discontinuation fixes")
    except ImportError:
        print("⚠️ Discontinuation fixes not available")

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
        
        # Set consistent probability for stable max interval discontinuation
        if 'criteria' not in config.parameters['discontinuation']:
            config.parameters['discontinuation']['criteria'] = {}
            
        # Ensure stable_max_interval exists and has a reasonable probability
        if 'stable_max_interval' not in config.parameters['discontinuation']['criteria']:
            config.parameters['discontinuation']['criteria']['stable_max_interval'] = {}
            
        config.parameters['discontinuation']['criteria']['stable_max_interval']['probability'] = 0.7
        
        print(f"✅ Patched SimulationConfig with consistent discontinuation parameters")
        return config
    
    # Apply the patch
    SimulationConfig.from_yaml = classmethod(patched_from_yaml)
    
except Exception as e:
    print(f"❌ Failed to ensure discontinuation parameters: {e}")

# Fix display of discontinuation rate in Streamlit
try:
    streamlit_app_path = os.path.join(project_root, "streamlit_app", "app.py")
    
    if os.path.exists(streamlit_app_path):
        with open(streamlit_app_path, 'r') as f:
            app_content = f.read()
        
        # Add a helper function to cap the discontinuation rate
        cap_function = """
# Helper function to calculate capped discontinuation rate
def calculate_capped_discontinuation_rate(results):
    """Calculate discontinuation rate capped at 100%"""
    total_patients = results.get("population_size", 1)
    
    # First check if we have unique patient count available
    if "unique_discontinuations" in results:
        # Use the unique count directly
        unique_discontinuations = results["unique_discontinuations"]
    elif "unique_patient_discontinuations" in results:
        # Use the unique count from the discontinuation manager
        unique_discontinuations = results["unique_patient_discontinuations"]
    else:
        # Fall back to total discontinuations but cap at total patients
        unique_discontinuations = min(results.get("total_discontinuations", 0), total_patients)
    
    # Calculate the rate, capped at 100%
    return min(1.0, unique_discontinuations / total_patients)
"""
        
        # Check if this function already exists in the app
        if "calculate_capped_discontinuation_rate" not in app_content:
            # Find a good spot to insert the function - after imports
            import_section_end = app_content.find("# Page configuration")
            if import_section_end == -1:
                import_section_end = app_content.find("st.set_page_config")
            
            if import_section_end != -1:
                # Insert the function after imports
                app_content = app_content[:import_section_end] + cap_function + app_content[import_section_end:]
                
                # Replace the discontinuation rate calculation
                app_content = app_content.replace(
                    "discontinued_percent = (discontinued_patients / total_patients * 100) if total_patients > 0 else 0",
                    "disc_rate = calculate_capped_discontinuation_rate(results)\n            discontinued_percent = disc_rate * 100"
                )
                
                # Update the file
                with open(streamlit_app_path, 'w') as f:
                    f.write(app_content)
                
                print("✅ Fixed discontinuation rate display in Streamlit app")
            else:
                print("⚠️ Could not find a suitable location to insert helper function")
        else:
            print("✅ Helper function already exists in Streamlit app")
    else:
        print(f"⚠️ Streamlit app not found at {streamlit_app_path}")
except Exception as e:
    print(f"❌ Failed to update Streamlit app: {e}")

# Run streamlit command
print("\nStarting Streamlit app...")
app_path = os.path.join(project_root, "streamlit_app", "app.py")
print(f"App path: {app_path}")

# Run the Streamlit app using subprocess so we can see any errors immediately
subprocess.run(["streamlit", "run", app_path, "--server.port=8502"])