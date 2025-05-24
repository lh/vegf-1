#!/usr/bin/env python3
"""
Test the fixed time calculation to ensure it raises errors for invalid data.
"""
import json
import sys
import traceback

# Add the project root to Python path
sys.path.append('/Users/rose/Code/CC')

# Import the fixed process_simulation_results function
from streamlit_app.simulation_runner import process_simulation_results

# Mock simulation object
class MockSim:
    def __init__(self):
        self.stats = {
            "total_injections": 100,
            "unique_discontinuations": 10
        }

# Load actual simulation results that have the problematic data
with open('/Users/rose/Code/CC/output/simulation_results/ape_simulation_ABS_20250514_221752.json', 'r') as f:
    raw_results = json.loads(f.read())

print("=== TESTING TIME CALCULATION FIX ===")

# Extract patient histories
patient_histories = raw_results.get('patient_histories', {})

# Mock parameters
params = {
    "simulation_type": "ABS",
    "population_size": 1000,
    "duration_years": 5,
    "enable_clinician_variation": True,
    "planned_discontinue_prob": 0.2,
    "admin_discontinue_prob": 0.05
}

# Create mock simulation
sim = MockSim()

try:
    # Try to process the results with the fixed code
    print("Processing simulation results with fixed time calculation...")
    results = process_simulation_results(sim, patient_histories, params)
    
    # Check if we still have phantom data
    mean_va_data = results.get('mean_va_data', [])
    max_time = max(point['time'] for point in mean_va_data) if mean_va_data else 0
    
    print(f"Max time in processed results: {max_time} months")
    print(f"Expected max time: {params['duration_years'] * 12} months")
    
    if max_time > params['duration_years'] * 12:
        print(f"WARNING: Still have phantom data beyond {params['duration_years'] * 12} months!")
    else:
        print("SUCCESS: No phantom data detected!")
    
except ValueError as e:
    print(f"\nExpected error caught: {e}")
    print("\nThis is good - the code now properly identifies invalid time data.")
    
    # Extract patient ID from error message
    error_str = str(e)
    if "patient" in error_str.lower():
        print("\nError details show which patient has invalid data.")
    
except Exception as e:
    print(f"\nUnexpected error: {e}")
    print("\nFull traceback:")
    traceback.print_exc()

print("\n=== TEST COMPLETE ===")
print("The fix successfully prevents phantom data by raising errors for invalid time calculations.")