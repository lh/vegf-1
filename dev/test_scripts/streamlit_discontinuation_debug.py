"""
Debug script to fix discontinuation in the Streamlit app context.

This script is specifically designed to debug the discontinuation issue
in the Streamlit app by simulating how the app initializes and configures
the enhanced discontinuation manager.
"""

from simulation.config import SimulationConfig
from simulation.enhanced_discontinuation_manager import EnhancedDiscontinuationManager
import numpy as np
from datetime import datetime, timedelta
import yaml

# Ensure reproducibility
np.random.seed(42)

def print_separator():
    print("\n" + "="*80 + "\n")

print("Loading configuration...")
config = SimulationConfig.from_yaml('test_simulation')

# Get the discontinuation parameters
discontinuation_params = config.get_treatment_discontinuation_params()
print("\nDiscontinuation parameters from config:")
print(f"Type: {type(discontinuation_params)}")
print(f"Enabled flag present: {'enabled' in discontinuation_params}")
print(f"Content: {discontinuation_params}")

print_separator()

# Directly load the discontinuation parameters from the file
with open('protocols/parameter_sets/eylea/discontinuation_parameters.yaml', 'r') as f:
    file_params = yaml.safe_load(f)
    print("Direct load of discontinuation_parameters.yaml:")
    print(file_params)

print_separator()

# Simulate how the parameters are passed in treat_and_extend_abs.py
print("Streamlit App Simulation - Current Approach:")
# This is how the streamlit app currently does it
print("Creating discontinuation managers with various parameter structures...")

# 1. The current problematic approach (original code)
original_approach = EnhancedDiscontinuationManager({"discontinuation": discontinuation_params})
print("\n1. Original approach with discontinuation_params nested:")
print(f"enabled: {original_approach.enabled}")
print(f"criteria keys: {list(original_approach.criteria.keys()) if hasattr(original_approach, 'criteria') else 'None'}")

print_separator()

# 2. Fix 1: Ensure the discontinuation params have an 'enabled' flag
fixed_params1 = discontinuation_params.copy()
fixed_params1["enabled"] = True
fixed_approach1 = EnhancedDiscontinuationManager({"discontinuation": fixed_params1})
print("\n2. Fixed approach with 'enabled' flag added to params:")
print(f"enabled: {fixed_approach1.enabled}")
print(f"criteria keys: {list(fixed_approach1.criteria.keys()) if hasattr(fixed_approach1, 'criteria') else 'None'}")

print_separator()

# 3. Use the directly loaded file (this should have the correct structure)
file_approach = EnhancedDiscontinuationManager(file_params)
print("\n3. Using parameters directly from file:")
print(f"enabled: {file_approach.enabled}")
print(f"criteria keys: {list(file_approach.criteria.keys()) if hasattr(file_approach, 'criteria') else 'None'}")

print_separator()

# Test discontinuation decision on each manager
print("Testing discontinuation decisions on each manager...")

# Create a test patient state
patient_state = {
    "disease_activity": {
        "fluid_detected": False,  # No fluid (stable)
        "consecutive_stable_visits": 3,  # 3 consecutive stable visits
        "max_interval_reached": True,  # Max interval reached
        "current_interval": 16  # Max interval (16 weeks)
    },
    "treatment_status": {
        "active": True,  # Treatment is active
        "recurrence_detected": False,
        "weeks_since_discontinuation": 0,
        "cessation_type": None
    },
    "disease_characteristics": {
        "has_PED": False
    }
}

# Test dates for evaluation
current_time = datetime.now()
treatment_start_time = current_time - timedelta(weeks=52)  # 1 year of treatment

# Test each manager with the same patient state
for i, (name, manager) in enumerate([
    ("Original approach", original_approach),
    ("Fixed approach 1 (add enabled flag)", fixed_approach1), 
    ("File parameters approach", file_approach)
]):
    # Force random seed to get consistent results
    np.random.seed(42 + i)  # Offset seeds to show different results
    
    print(f"\nTesting discontinuation on manager {i+1}: {name}")
    successful_discontinuations = 0
    
    for j in range(10):
        should_discontinue, reason, probability, cessation_type = manager.evaluate_discontinuation(
            patient_state=patient_state,
            current_time=current_time,
            treatment_start_time=treatment_start_time
        )
        
        if should_discontinue:
            successful_discontinuations += 1
            print(f"  Attempt {j+1}: DISCONTINUED - {reason} (probability: {probability:.2f})")
        else:
            print(f"  Attempt {j+1}: Not discontinued")
    
    print(f"\nSuccessful discontinuations with {name}: {successful_discontinuations} out of 10 attempts")
    print(f"Expected with 0.2 probability: ~2 discontinuations")

print_separator()
print("Recommendations for Streamlit App Fix:")
print("""
1. In the TreatAndExtendABS and TreatAndExtendDES classes, modify how the discontinuation
   parameters are passed to the EnhancedDiscontinuationManager:

   # Ensure the 'enabled' flag is present in the discontinuation parameters
   if "enabled" not in discontinuation_params:
       discontinuation_params["enabled"] = True
   
   # Pass the parameters with the correct structure
   self.discontinuation_manager = EnhancedDiscontinuationManager({"discontinuation": discontinuation_params})

2. Alternatively, for a more robust solution:
   
   discontinuation_params = self.config.get_treatment_discontinuation_params()
   # Load the full discontinuation parameters file instead of using partial params
   self.discontinuation_manager = EnhancedDiscontinuationManager({
       "discontinuation": {
           "enabled": True,
           "criteria": discontinuation_params.get("criteria", {}),
           "monitoring": discontinuation_params.get("monitoring", {}),
           "retreatment": discontinuation_params.get("retreatment", {})
       }
   })
""")