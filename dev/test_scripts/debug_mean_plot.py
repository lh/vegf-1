#!/usr/bin/env python3
"""
Debug the mean plot generation issue.
"""

import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict
import traceback

# Mock data generation
def generate_mock_data():
    """Generate mock simulation results."""
    # Generate patient data
    np.random.seed(42)
    patient_data = {}
    
    for i in range(100):
        visits = []
        current_va = np.random.normal(70, 10)
        for month in range(60):
            current_va += np.random.normal(-0.1, 2)  # Slight decline with noise
            current_va = np.clip(current_va, 0, 85)
            visits.append({
                'time': month,
                'vision': current_va
            })
        patient_data[f'patient_{i}'] = visits
    
    # Create mean_va_data
    time_va_map = defaultdict(list)
    for patient_id, visits in patient_data.items():
        for visit in visits:
            time_month = visit['time']
            time_va_map[time_month].append(visit['vision'])
    
    mean_va_data = []
    for time_month in sorted(time_va_map.keys()):
        va_values = time_va_map[time_month]
        mean_va_data.append({
            'time_months': time_month,
            'visual_acuity': np.mean(va_values),
            'std_error': np.std(va_values) / np.sqrt(len(va_values)),
            'sample_size': len(va_values)
        })
    
    return {
        'patient_data': patient_data,
        'mean_va_data': mean_va_data,
        'simulation_type': 'ABS',
        'population_size': 100,
        'duration_years': 5
    }

# Generate results
results = generate_mock_data()

# Try to generate the mean plot and catch the error
try:
    from streamlit_app.simulation_runner import generate_va_over_time_plot
    fig = generate_va_over_time_plot(results)
    plt.savefig('/Users/rose/Code/CC/debug_mean_plot.png')
    print("Plot generated successfully!")
except Exception as e:
    print(f"Error generating plot: {e}")
    print("\nFull traceback:")
    traceback.print_exc()
    
    # Let's check the data structure
    print("\nData structure check:")
    print(f"Keys in results: {results.keys()}")
    print(f"Type of mean_va_data: {type(results['mean_va_data'])}")
    print(f"Length of mean_va_data: {len(results['mean_va_data'])}")
    if results['mean_va_data']:
        print(f"First element: {results['mean_va_data'][0]}")
        print(f"Keys in first element: {results['mean_va_data'][0].keys()}")