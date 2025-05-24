"""
Script to verify the discontinuation manager fix.
This script initializes the enhanced discontinuation manager both ways (old and fixed)
and outputs the results to verify the fix works correctly.
"""

from simulation.config import SimulationConfig
from simulation.enhanced_discontinuation_manager import EnhancedDiscontinuationManager
import yaml
import numpy as np

# Set random seed for reproducibility
np.random.seed(42)

def print_separator():
    print("\n" + "="*80 + "\n")

print("Loading configuration...")
config = SimulationConfig.from_yaml('eylea_literature_based')

# Get the discontinuation parameters
discontinuation_params = config.get_treatment_discontinuation_params()
print("\nDiscontinuation parameters from config:")
print(f"Type: {type(discontinuation_params)}")
print(f"Enabled flag present: {'enabled' in discontinuation_params}")
print(f"Content: {discontinuation_params}")

print_separator()

# Initialize both ways to compare
print("OLD WAY (Double nesting - problematic):")
old_manager = EnhancedDiscontinuationManager({"discontinuation": discontinuation_params})
print(f"Enabled: {old_manager.enabled}")
print(f"Stable max interval probability: {old_manager.criteria.get('stable_max_interval', {}).get('probability', 0)}")

print_separator()

# Try the fixed way
print("FIXED WAY (With enabled flag):")
fixed_params = discontinuation_params.copy()
fixed_params["enabled"] = True
fixed_manager = EnhancedDiscontinuationManager({"discontinuation": fixed_params})
print(f"Enabled: {fixed_manager.enabled}")
print(f"Stable max interval probability: {fixed_manager.criteria.get('stable_max_interval', {}).get('probability', 0)}")

print_separator()

# Test discontinuation decision
print("Testing discontinuation decision with the fixed manager:")

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

# Test with the fixed manager
from datetime import datetime, timedelta
current_time = datetime.now()
treatment_start_time = current_time - timedelta(weeks=52)  # 1 year of treatment

# Force random seed to get consistent results
np.random.seed(42)

# Make 10 evaluation attempts to verify the discontinuation probability works
print("\nMaking 10 evaluation attempts to verify discontinuation works:")
successful_discontinuations = 0

for i in range(10):
    should_discontinue, reason, probability, cessation_type = fixed_manager.evaluate_discontinuation(
        patient_state=patient_state,
        current_time=current_time,
        treatment_start_time=treatment_start_time
    )
    
    if should_discontinue:
        successful_discontinuations += 1
        print(f"  Attempt {i+1}: DISCONTINUED - {reason} (probability: {probability:.2f})")
    else:
        print(f"  Attempt {i+1}: Not discontinued")

print(f"\nSuccessful discontinuations: {successful_discontinuations} out of 10 attempts")
print(f"Expected with 0.2 probability: ~2 discontinuations")

if successful_discontinuations > 0:
    print("\nFIX CONFIRMED: Discontinuation is now working!")
else:
    print("\nWARNING: No discontinuations occurred, additional investigation needed.")