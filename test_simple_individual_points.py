"""
Simple test to create a basic version of individual points visualization
"""

import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# Create test data
def create_test_data():
    """Create simple test data"""
    # Time points
    months = np.arange(0, 24, 1)
    
    # Sample sizes that decrease over time
    sample_sizes = [100 - i*4 for i in range(24)]
    
    # Mean VA with some variation
    mean_va = [70 - i*0.5 + np.sin(i*0.3)*2 for i in range(24)]
    
    # Create patient data
    patient_data = {}
    for pid in range(100):
        visits = []
        for month in months:
            # Some patients drop out
            if pid > sample_sizes[month]:
                break
            
            # Add some variation to visit times to simulate protocol intervals
            actual_month = month + np.random.normal(0, 0.2)
            va = mean_va[month] + np.random.normal(0, 5)
            
            visits.append({
                'month': actual_month,
                'va': va
            })
        
        if visits:
            patient_data[pid] = visits
    
    return months, mean_va, sample_sizes, patient_data

# Visualize
def visualize_with_individual_points():
    months, mean_va, sample_sizes, patient_data = create_test_data()
    
    fig, ax1 = plt.subplots(figsize=(12, 8))
    
    # Plot sample sizes on left axis
    ax1.bar(months, sample_sizes, alpha=0.3, color='green', label='Sample Size')
    ax1.set_xlabel('Months')
    ax1.set_ylabel('Sample Size', color='green')
    ax1.tick_params(axis='y', labelcolor='green')
    
    # Create second y-axis for VA
    ax2 = ax1.twinx()
    
    # Determine which points to show individually
    threshold = 30
    
    for i, month in enumerate(months):
        if sample_sizes[i] > threshold:
            # Plot mean with CI
            ax2.plot(month, mean_va[i], 'o-', color='blue', markersize=8)
        else:
            # Plot individual points
            points_plotted = 0
            for pid, visits in patient_data.items():
                for visit in visits:
                    if abs(visit['month'] - month) < 0.5:  # Within half month
                        ax2.scatter(visit['month'], visit['va'], 
                                  alpha=0.5, color='blue', s=20)
                        points_plotted += 1
            
            # Also plot mean as reference
            ax2.plot(month, mean_va[i], 'x', color='red', markersize=10, 
                    label=f'Mean (n={points_plotted})')
    
    ax2.set_ylabel('Visual Acuity', color='blue')
    ax2.tick_params(axis='y', labelcolor='blue')
    
    # Add threshold line
    ax1.axhline(y=threshold, color='red', linestyle='--', alpha=0.5, 
               label=f'Individual points threshold (n={threshold})')
    
    ax1.legend(loc='upper left')
    plt.title('Visual Acuity Over Time with Individual Points')
    plt.tight_layout()
    plt.savefig('test_simple_individual_points.png', dpi=150)
    print("Saved test_simple_individual_points.png")
    plt.close()

if __name__ == "__main__":
    visualize_with_individual_points()