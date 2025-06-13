#!/usr/bin/env python3
"""
Test script for the new VA distribution plot visualization.
"""

import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from collections import defaultdict

# Mock the color system constants
COLORS = {
    'primary': '#4682B4',
    'primary_dark': '#2a4d6e',
    'text': '#333333',
    'text_secondary': '#666666',
    'grid': '#EEEEEE',
}

def generate_mock_patient_data(n_patients=200, months=60):
    """Generate mock patient data with realistic VA patterns."""
    patient_data = {}
    
    # Different patient profiles with different VA trajectories
    profiles = {
        'stable': {'initial_mean': 75, 'initial_std': 8, 'monthly_change': 0, 'noise': 2},
        'improving': {'initial_mean': 65, 'initial_std': 10, 'monthly_change': 0.2, 'noise': 3},
        'declining': {'initial_mean': 80, 'initial_std': 5, 'monthly_change': -0.3, 'noise': 2.5},
        'variable': {'initial_mean': 70, 'initial_std': 12, 'monthly_change': 0, 'noise': 5}
    }
    
    profile_weights = [0.3, 0.2, 0.3, 0.2]  # Weights for each profile
    patient_profiles = np.random.choice(list(profiles.keys()), n_patients, p=profile_weights)
    
    baseline_date = datetime(2024, 1, 1)
    
    for patient_id in range(n_patients):
        profile = profiles[patient_profiles[patient_id]]
        
        # Generate initial VA
        initial_va = np.random.normal(profile['initial_mean'], profile['initial_std'])
        initial_va = np.clip(initial_va, 0, 85)  # Keep within ETDRS range
        
        visits = []
        current_va = initial_va
        
        # Generate visits with some dropout
        dropout_month = np.random.randint(months//2, months+10)  # Some patients drop out
        
        for month in range(min(months, dropout_month)):
            # Apply monthly change and noise
            current_va += profile['monthly_change'] + np.random.normal(0, profile['noise'])
            current_va = np.clip(current_va, 0, 85)
            
            visit = {
                'date': baseline_date + timedelta(days=month*30),
                'vision': current_va,
                'time': month
            }
            visits.append(visit)
        
        patient_data[f'patient_{patient_id}'] = visits
    
    return patient_data

def test_distribution_plot():
    """Test the distribution plot with mock data."""
    print("Testing VA distribution plot...")
    
    # Generate mock data
    patient_data = generate_mock_patient_data()
    
    # Create mock results structure
    results = {
        'patient_data': patient_data,
        'simulation_type': 'ABS',
        'population_size': len(patient_data),
        'duration_years': 5
    }
    
    # Generate the plot (inline function since we can't import)
    from streamlit_app.simulation_runner import generate_va_distribution_plot
    
    fig = generate_va_distribution_plot(results)
    
    # Save the plot
    output_path = '/Users/rose/Code/CC/test_va_distribution_plot.png'
    fig.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Plot saved to: {output_path}")
    
    # Also test with the standard mean plot for comparison
    from streamlit_app.simulation_runner import generate_va_over_time_plot
    
    # Add mean_va_data for the standard plot
    # Aggregate data for mean plot
    time_va_map = defaultdict(list)
    for patient_id, visits in patient_data.items():
        for visit in visits:
            time_month = round(visit['time'])
            time_va_map[time_month].append(visit['vision'])
    
    mean_va_data = []
    for time_month in sorted(time_va_map.keys()):
        va_values = time_va_map[time_month]
        if va_values:
            mean_va_data.append({
                'time': time_month,
                'time_months': time_month,
                'visual_acuity': np.mean(va_values),
                'std_error': np.std(va_values) / np.sqrt(len(va_values)),
                'sample_size': len(va_values)
            })
    
    results['mean_va_data'] = mean_va_data
    
    fig2 = generate_va_over_time_plot(results)
    output_path2 = '/Users/rose/Code/CC/test_va_mean_plot.png'
    fig2.savefig(output_path2, dpi=300, bbox_inches='tight')
    print(f"Mean plot saved to: {output_path2}")
    
    plt.close('all')
    
    print("\nTest complete! Check the generated plots to see:")
    print("1. The distribution plot showing percentile bands")
    print("2. The mean plot showing confidence intervals")
    print("\nNote the key differences:")
    print("- Distribution plot shows where actual patients are")
    print("- Mean plot shows our confidence in the average")

if __name__ == "__main__":
    test_distribution_plot()