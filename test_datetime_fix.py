#!/usr/bin/env python3
"""
Test the datetime fix for individual points visualization.
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

# Generate patient histories with datetime objects (not strings)
patient_histories = {}
simulation_start = datetime(2023, 1, 1)

for i in range(num_patients):
    patient_id = f"PATIENT{i:03d}"
    visits = []
    
    # Create visits over 5 years with varying frequencies
    current_date = simulation_start
    initial_va = np.random.normal(65, 10)
    current_va = initial_va
    
    for month in range(60):  # 5 years of monthly potential visits
        # Random visit frequency (not all months have visits)
        if np.random.random() < 0.8:  # 80% chance of visit
            # Add a visit with slight variation in timing
            visit_date = current_date + timedelta(days=np.random.randint(-5, 5))
            
            # VA improves initially then gradually declines
            if month < 6:
                current_va += np.random.normal(1.5, 1)
            else:
                current_va += np.random.normal(-0.2, 0.5)
            
            visit = {
                "date": visit_date,  # datetime object, not string
                "visual_acuity": np.clip(current_va, 20, 100),
                "visit_type": "treatment" if month % 3 == 0 else "monitoring"
            }
            visits.append(visit)
        
        current_date += timedelta(days=30)
    
    patient_histories[patient_id] = visits

# Create results dictionary
results = {
    "patient_histories": patient_histories,
    "simulation_type": "ABS",
    "population_size": num_patients,
    "duration_years": 5,
    "simulation_start_date": simulation_start
}

# Test with various time points
time_months = [6, 12, 24, 36, 48, 60]
df_data = []

# Generate data with decreasing sample sizes
for idx, month in enumerate(time_months):
    # Simulate decreasing sample size over time
    active_patients = num_patients - int(idx * 10)  # Lose 10 patients per time point
    
    # Add to dataframe
    df_data.append({
        "time_months": month,
        "mean_va": 70 - idx * 2,  # Gradual decline
        "std_va": 5 + idx * 0.5,  # Increasing variability
        "sample_size": active_patients
    })

df = pd.DataFrame(df_data)

# Test the visualization with individual points
print("\nTesting visualization with individual points...")
# Set the debug mode to see output
import streamlit_app.simulation_runner as sr
sr.DEBUG_MODE = True

# Generate the visual acuity data for the results
mean_va_data = []
for month in time_months:
    # Find visits near this time point
    va_values = []
    for patient_id, visits in patient_histories.items():
        for visit in visits:
            visit_date = visit["date"]
            visit_month = (visit_date - simulation_start).days / 30.44
            if abs(visit_month - month) < 0.5:  # Within half month tolerance
                va_values.append(visit["visual_acuity"])
                break
    
    if va_values:
        mean_va_data.append({
            "time": float(month),
            "visual_acuity": float(np.mean(va_values)),
            "sample_size": len(va_values)
        })

results["mean_va_data"] = mean_va_data

fig = generate_va_over_time_plot(results)

# Save the plot
plt.savefig('test_datetime_fix_plot.png', dpi=150, bbox_inches='tight')
print(f"Plot saved to test_datetime_fix_plot.png")

# Show some debug info
print(f"\nTest data summary:")
print(f"- {num_patients} patients")
print(f"- Simulation start: {simulation_start}")
print(f"- Sample patient has {len(patient_histories['PATIENT000'])} visits")
print(f"- First visit: {patient_histories['PATIENT000'][0]}")
print("\nDataframe:")
print(df)