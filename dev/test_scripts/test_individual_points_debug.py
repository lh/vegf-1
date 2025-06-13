#!/usr/bin/env python3
"""
Test the individual points visualization with more detailed debugging.
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import sys
sys.path.append('/Users/rose/Code/CC')
from streamlit_app.simulation_runner import generate_va_over_time_plot

# Create test data
np.random.seed(42)
num_patients = 100

# Generate patient histories
patient_histories = {}
simulation_start = datetime(2023, 1, 1)

# Create time points with decreasing sample sizes to trigger individual points
time_points = [6, 12, 18, 24, 30, 36, 42, 48, 54, 60]
mean_va_data = []

# Generate patient data
for i in range(num_patients):
    patient_id = f"PATIENT{i:03d}"
    visits = []
    
    # Create visits at specific time points
    for idx, month in enumerate(time_points):
        # Simulate attrition - fewer patients at later time points
        if i < (num_patients - idx * 10):  # Lose 10 patients per time point
            visit_date = simulation_start + timedelta(days=int(month * 30.44))
            
            # Add some random variation to VA
            base_va = 70 - idx * 2  # Gradual decline
            va = base_va + np.random.normal(0, 5)
            
            visit = {
                "date": visit_date,
                "visual_acuity": np.clip(va, 20, 100),
                "visit_type": "treatment"
            }
            visits.append(visit)
    
    patient_histories[patient_id] = visits

# Create mean VA data with decreasing sample sizes
for idx, month in enumerate(time_points):
    sample_size = num_patients - idx * 10
    mean_va = 70 - idx * 2
    
    mean_va_data.append({
        "time": float(month),
        "visual_acuity": mean_va,
        "sample_size": sample_size
    })

# Create results dictionary
results = {
    "patient_histories": patient_histories,
    "simulation_type": "ABS",
    "population_size": num_patients,
    "duration_years": 5,
    "simulation_start_date": simulation_start,
    "mean_va_data": mean_va_data
}

# Enable debug mode
import streamlit_app.simulation_runner as sr
sr.DEBUG_MODE = True

print("\nTesting visualization with individual points...")
print(f"Time points: {time_points}")
print(f"Sample sizes: {[d['sample_size'] for d in mean_va_data]}")
print(f"Patient histories: {len(patient_histories)} patients")
print(f"First patient visits: {len(patient_histories['PATIENT000'])}")

# Generate the plot
fig = generate_va_over_time_plot(results)

# Save the plot
plt.savefig('test_individual_points_debug.png', dpi=150, bbox_inches='tight')
print(f"\nPlot saved to test_individual_points_debug.png")

# Check what's in mean_va_data
print("\nMean VA data:")
for d in mean_va_data:
    print(f"  Time: {d['time']}, VA: {d['visual_acuity']:.1f}, Sample size: {d['sample_size']}")