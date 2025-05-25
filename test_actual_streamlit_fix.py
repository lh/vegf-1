#!/usr/bin/env python3
"""
Test the fix with actual simulation data.
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

print("=== TESTING WITH ACTUAL DATA ===")
print(f"Simulation type: {results.get('simulation_type')}")
print(f"Population size: {results.get('population_size')}")
print(f"Duration years: {results.get('duration_years')}")
print(f"Has patient_histories: {'patient_histories' in results}")
print(f"Has mean_va_data: {'mean_va_data' in results}")

# Check if we have the expected data
if 'mean_va_data' in results and 'patient_histories' in results:
    # Generate the visualization
    print("\nGenerating visualization...")
    fig = generate_va_over_time_plot(results)
    
    # Save the plot
    import matplotlib.pyplot as plt
    plt.savefig('test_actual_streamlit_fix.png', dpi=150, bbox_inches='tight')
    print("Plot saved to test_actual_streamlit_fix.png")
else:
    print("Missing required data for visualization")