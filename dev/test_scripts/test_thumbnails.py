#!/usr/bin/env python3
"""
Test script for VA thumbnail visualizations.
"""

import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path so imports work
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from test_va_distribution_plot import generate_mock_patient_data
from streamlit_app.simulation_runner import (
    generate_va_over_time_thumbnail, 
    generate_va_distribution_thumbnail,
    generate_va_over_time_plot,
    generate_va_distribution_plot
)

def test_thumbnails():
    """Test the thumbnail plots."""
    print("Testing VA thumbnail plots...")
    
    # Generate mock data
    patient_data = generate_mock_patient_data()
    
    # Create mock results structure
    results = {
        'patient_data': patient_data,
        'simulation_type': 'ABS',
        'population_size': len(patient_data),
        'duration_years': 5
    }
    
    # Add mean_va_data for the standard plot
    from collections import defaultdict
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
    
    # Create a figure with all 4 plots
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 10))
    
    # Generate thumbnails
    thumb1 = generate_va_over_time_thumbnail(results)
    thumb2 = generate_va_distribution_thumbnail(results)
    
    # Generate full plots
    full1 = generate_va_over_time_plot(results)
    full2 = generate_va_distribution_plot(results)
    
    # Save all plots
    thumb1.savefig('/Users/rose/Code/CC/test_thumb_mean.png', dpi=300, bbox_inches='tight')
    thumb2.savefig('/Users/rose/Code/CC/test_thumb_dist.png', dpi=300, bbox_inches='tight')
    
    print("Thumbnails saved to:")
    print("- test_thumb_mean.png")
    print("- test_thumb_dist.png")
    
    plt.close('all')
    
    # Create a composite figure showing the layout
    fig, axes = plt.subplots(3, 2, figsize=(14, 12), 
                            gridspec_kw={'height_ratios': [1, 3, 3]})
    
    # Add title
    fig.suptitle('Visual Acuity Visualization Layout', fontsize=16, y=0.98)
    
    # Thumbnails
    axes[0, 0].text(0.5, 0.5, 'Mean + 95% CI\n(Thumbnail)', 
                   ha='center', va='center', fontsize=12,
                   bbox=dict(boxstyle="round,pad=0.3", facecolor='lightblue'))
    axes[0, 0].set_xlim(0, 1)
    axes[0, 0].set_ylim(0, 1)
    axes[0, 0].axis('off')
    
    axes[0, 1].text(0.5, 0.5, 'Patient Distribution\n(Thumbnail)', 
                   ha='center', va='center', fontsize=12,
                   bbox=dict(boxstyle="round,pad=0.3", facecolor='lightgreen'))
    axes[0, 1].set_xlim(0, 1)
    axes[0, 1].set_ylim(0, 1)
    axes[0, 1].axis('off')
    
    # Full plots placeholders
    axes[1, 0].text(0.5, 0.5, 'Mean Visual Acuity\nwith Confidence Intervals\n(Full Plot)', 
                   ha='center', va='center', fontsize=14)
    axes[1, 0].set_title('Mean Visual Acuity with Confidence Intervals', pad=10)
    axes[1, 0].grid(True, alpha=0.3)
    
    axes[1, 1].axis('off')  # Empty space
    
    axes[2, 0].text(0.5, 0.5, 'Distribution of\nVisual Acuity\n(Full Plot)', 
                   ha='center', va='center', fontsize=14)
    axes[2, 0].set_title('Distribution of Visual Acuity', pad=10)
    axes[2, 0].grid(True, alpha=0.3)
    
    axes[2, 1].axis('off')  # Empty space
    
    plt.tight_layout()
    plt.savefig('/Users/rose/Code/CC/test_layout.png', dpi=300, bbox_inches='tight')
    
    print("\nLayout mockup saved to: test_layout.png")
    print("\nLayout structure:")
    print("1. Top row: Side-by-side thumbnails for quick comparison")
    print("2. Middle & bottom: Full plots stacked vertically for detailed analysis")

if __name__ == "__main__":
    test_thumbnails()