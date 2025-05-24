#!/usr/bin/env python3
"""
Test the data filtering fix to remove phantom data after simulation duration.
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

print("=== TESTING DATA FILTER FIX ===")
print(f"Simulation duration: {results.get('duration_years')} years")
print(f"Expected max months: {results.get('duration_years', 5) * 12}")

# Generate the visualization
fig = generate_va_over_time_plot(results)

# Save the plot
import matplotlib.pyplot as plt
plt.savefig('test_data_filter_fix.png', dpi=150, bbox_inches='tight')
print(f"\nPlot saved to test_data_filter_fix.png")

# Check the data that's actually being plotted
import pandas as pd
mean_va_data = results['mean_va_data']
df = pd.DataFrame(mean_va_data)
print(f"\nOriginal data points: {len(df)}")
print(f"Time range in original data: {df['time'].min()} to {df['time'].max()} months")

# Apply the same filter as in the visualization
duration_years = results.get("duration_years", 5)
max_months = duration_years * 12
filtered_df = df[df['time'] <= max_months]
print(f"\nFiltered data points: {len(filtered_df)}")
print(f"Time range after filter: {filtered_df['time'].min()} to {filtered_df['time'].max()} months")