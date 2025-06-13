#!/usr/bin/env python3
"""
Test the time column fix for individual points visualization.
"""
import json
import sys
sys.path.append('/Users/rose/Code/CC')

# Enable debug mode
import streamlit_app.simulation_runner as sr
sr.DEBUG_MODE = True

# Import the visualization function
from streamlit_app.simulation_runner import generate_va_over_time_plot

# Load actual simulation results
with open('/Users/rose/Code/CC/output/simulation_results/ape_simulation_ABS_20250514_221752.json', 'r') as f:
    results = json.loads(f.read())

print("=== TESTING TIME COLUMN FIX ===")

# Get just a subset of the data to speed up testing
import pandas as pd
mean_va_data = results['mean_va_data']
df = pd.DataFrame(mean_va_data)

# Find time points with small sample sizes
small_samples = df[df['sample_size'] <= 30]
print(f"Found {len(small_samples)} time points with sample size <= 30")
print(f"Time column name: {'time_months' if 'time_months' in df.columns else 'time'}")
print(f"First few small sample times: {small_samples['time'].values[:5]}")

# Limit patient histories to speed up the test
patient_histories = results['patient_histories']
limited_patients = dict(list(patient_histories.items())[:100])  # Just first 100 patients
results['patient_histories'] = limited_patients

print(f"\nLimited to {len(limited_patients)} patients for testing")

# Generate the visualization
print("\nGenerating visualization...")
fig = generate_va_over_time_plot(results)

# Save the plot
import matplotlib.pyplot as plt
plt.savefig('test_time_fix.png', dpi=150, bbox_inches='tight')
print("Plot saved to test_time_fix.png")