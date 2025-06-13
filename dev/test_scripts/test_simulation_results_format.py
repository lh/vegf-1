#!/usr/bin/env python3
"""
Test simulation results format and fix the data structure issues.
"""

import sys
import numpy as np
from datetime import datetime

# Add project root to path
sys.path.insert(0, '/Users/rose/Code/CC')

from simulation.config import SimulationConfig
from treat_and_extend_abs import TreatAndExtendABS
from streamlit_app.simulation_runner import process_simulation_results

# Load config using from_yaml method
config = SimulationConfig.from_yaml("test_simulation")
print(f"Config loaded")

# Override for quick test
config.num_patients = 10
config.duration_days = 365

# Create and run simulation
sim = TreatAndExtendABS(config)
print(f"Running simulation...")

# Run simulation
patient_histories = sim.run()
print(f"Simulation run, got {len(patient_histories)} patient histories")

# Mock parameters for processing
params = {
    "simulation_type": "ABS",
    "population_size": config.num_patients,
    "duration_years": config.duration_days / 365,
    "enable_clinician_variation": False,
    "planned_discontinue_prob": 0.2,
    "admin_discontinue_prob": 0.05
}

# Process results
results = process_simulation_results(sim, patient_histories, params)

print("\nResults structure:")
print(f"Keys: {list(results.keys())}")

# Check mean_va_data structure
if "mean_va_data" in results:
    mean_data = results["mean_va_data"]
    print(f"\nmean_va_data type: {type(mean_data)}")
    print(f"mean_va_data length: {len(mean_data)}")
    
    if mean_data:
        first_point = mean_data[0]
        print(f"First data point type: {type(first_point)}")
        print(f"First data point keys: {list(first_point.keys()) if isinstance(first_point, dict) else 'Not a dict'}")
        print(f"First data point: {first_point}")
        
        # Check all data points for consistency
        time_columns = set()
        for point in mean_data:
            if isinstance(point, dict):
                time_columns.update([k for k in point.keys() if 'time' in k.lower()])
        
        print(f"Time columns found: {time_columns}")
else:
    print("\nNo mean_va_data in results!")

# Check patient data structure
patient_key = "patient_data" if "patient_data" in results else "patient_histories"
if patient_key in results:
    patient_data = results[patient_key]
    print(f"\n{patient_key} type: {type(patient_data)}")
    
    if patient_data:
        if isinstance(patient_data, dict):
            sample_key = list(patient_data.keys())[0]
            sample_patient = patient_data[sample_key]
        else:
            sample_patient = patient_data[0]
        
        print(f"Sample patient type: {type(sample_patient)}")
        
        if isinstance(sample_patient, list) and sample_patient:
            first_visit = sample_patient[0]
            print(f"First visit type: {type(first_visit)}")
            if isinstance(first_visit, dict):
                print(f"First visit keys: {list(first_visit.keys())}")
                print(f"First visit: {first_visit}")
                
                # Check time keys
                time_keys = [k for k in first_visit.keys() if 'time' in k.lower()]
                print(f"Time keys in visit: {time_keys}")