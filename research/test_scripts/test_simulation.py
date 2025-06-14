"""
Test simulation module imports and basic functionality.
"""
import os
import sys

# Get the absolute path to the project root directory
project_root = os.path.dirname(os.path.abspath(__file__))

# Ensure we're in the project root directory
os.chdir(project_root)
print(f"Changed working directory to: {os.getcwd()}")

# Add the project root to sys.path
sys.path.append(project_root)
print(f"Added {project_root} to sys.path")

print("\nAttempting to import simulation modules...")

try:
    from simulation.config import SimulationConfig
    print("✅ SimulationConfig imported successfully")
    
    # Try to print out some attributes to confirm it's working
    print(f"  - Methods: {[m for m in dir(SimulationConfig) if not m.startswith('_')][:5]}...")
except ImportError as e:
    print(f"❌ Failed to import SimulationConfig: {e}")

try:
    import treat_and_extend_abs
    print("✅ treat_and_extend_abs imported successfully")
    
    # Try to print out some attributes to confirm it's working
    print(f"  - Module attributes: {[m for m in dir(treat_and_extend_abs) if not m.startswith('_')][:5]}...")
except ImportError as e:
    print(f"❌ Failed to import treat_and_extend_abs: {e}")

try:
    import treat_and_extend_des
    print("✅ treat_and_extend_des imported successfully")
    
    # Try to print out some attributes to confirm it's working
    print(f"  - Module attributes: {[m for m in dir(treat_and_extend_des) if not m.startswith('_')][:5]}...")
except ImportError as e:
    print(f"❌ Failed to import treat_and_extend_des: {e}")

try:
    # Try to create a SimulationConfig object
    print("\nTrying to instantiate a SimulationConfig...")
    config = SimulationConfig()
    print("✅ SimulationConfig instance created successfully")
    
    # Print some properties to confirm it's working
    print(f"  - Config has attributes: {[m for m in dir(config) if not m.startswith('_')][:5]}...")
except Exception as e:
    print(f"❌ Failed to create SimulationConfig instance: {e}")

print("\nTest complete")