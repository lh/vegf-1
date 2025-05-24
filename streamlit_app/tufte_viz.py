"""
Tufte-inspired visualization for Streamlit.

This script demonstrates a clean, minimalist approach to visualization
in Streamlit, inspired by Edward Tufte's principles of data visualization.
"""

import os
import sys
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import streamlit as st
import datetime
import time
from matplotlib import rcParams

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(project_root))

# Set up Tufte-inspired style for matplotlib
def set_tufte_style():
    """Set up a clean, minimalist Tufte-inspired style for matplotlib."""
    plt.style.use('seaborn-v0_8-whitegrid')
    
    # Lighter grid
    rcParams['grid.color'] = '#eeeeee'
    rcParams['grid.linestyle'] = '-'
    rcParams['grid.linewidth'] = 0.5
    
    # Text colors
    rcParams['text.color'] = '#333333'
    rcParams['axes.labelcolor'] = '#666666'
    rcParams['xtick.color'] = '#666666'
    rcParams['ytick.color'] = '#666666'
    
    # Lighter spines
    rcParams['axes.spines.top'] = False
    rcParams['axes.spines.right'] = False
    rcParams['axes.spines.left'] = False
    rcParams['axes.spines.bottom'] = True
    rcParams['axes.edgecolor'] = '#cccccc'
    rcParams['axes.linewidth'] = 0.5
    
    # Font settings
    rcParams['font.family'] = 'sans-serif'
    rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans', 'Liberation Sans', 'Helvetica', 'sans-serif']
    rcParams['axes.titlesize'] = 14
    rcParams['axes.labelsize'] = 10

def create_tufte_enrollment_visualization(enrollment_df):
    """Create a Tufte-inspired enrollment visualization."""
    # Set up the style
    set_tufte_style()
    
    # Convert to datetime if needed
    if not pd.api.types.is_datetime64_any_dtype(enrollment_df['enrollment_date']):
        enrollment_df['enrollment_date'] = pd.to_datetime(enrollment_df['enrollment_date'])
    
    # Group by month
    enrollment_df['month'] = enrollment_df['enrollment_date'].dt.strftime('%Y-%m')
    monthly_counts = enrollment_df.groupby('month').size()
    
    # Create figure
    fig, ax = plt.subplots(figsize=(10, 5), dpi=100)
    
    # Plot bars
    x = range(len(monthly_counts))
    ax.bar(x, monthly_counts.values, color='#4682B4', alpha=0.7, edgecolor='none')
    
    # Add trend line using LOESS smoothing if we have enough points
    if len(x) >= 8:
        try:
            from scipy import signal
            # Smooth the data
            smoothed = signal.savgol_filter(monthly_counts.values, 
                                          min(7, len(monthly_counts) | 1), # window length must be odd and ≤ data length
                                          2) # polynomial order
            ax.plot(x, smoothed, color='#B22222', linewidth=1.5, alpha=0.8)
        except ImportError:
            # Fallback to simple linear trend
            z = np.polyfit(x, monthly_counts.values, 1)
            p = np.poly1d(z)
            ax.plot(x, p(x), color='#B22222', linewidth=1.5, alpha=0.8)
    else:
        # Use simple linear trend for small datasets
        z = np.polyfit(x, monthly_counts.values, 1)
        p = np.poly1d(z)
        ax.plot(x, p(x), color='#B22222', linewidth=1.5, alpha=0.8)
    
    # Clean up the graph
    ax.grid(axis='x', visible=False)
    
    # Add labels and formatting
    ax.set_xticks(x)
    ax.set_xticklabels(monthly_counts.index, rotation=45, ha='right', fontsize=9)
    ax.set_title('Patient Enrollment Over Time', fontsize=14, color='#333333')
    ax.set_ylabel('Number of Patients', fontsize=10, color='#666666')
    
    # Add subtle text annotation
    total_patients = len(enrollment_df)
    plt.figtext(0.13, 0.02, f'Total of {total_patients} patients enrolled', 
               fontsize=9, color='#666666')
    
    plt.tight_layout(pad=1.5)
    return fig

def create_tufte_va_over_time_plot(va_data):
    """Create a Tufte-inspired visual acuity over time plot."""
    # Set up the style
    set_tufte_style()
    
    # Prepare data
    if isinstance(va_data, list):
        # Convert list of dicts/objects to DataFrame
        va_df = pd.DataFrame([
            {"time": point.get("time", 0) if isinstance(point, dict) else getattr(point, "time", 0),
             "visual_acuity": point.get("visual_acuity", 0) if isinstance(point, dict) else getattr(point, "visual_acuity", 0)}
            for point in va_data
        ])
    else:
        # Already a DataFrame
        va_df = va_data
    
    # Create figure
    fig, ax = plt.subplots(figsize=(10, 5), dpi=100)
    
    # Plot data points and line
    ax.plot(va_df['time'], va_df['visual_acuity'], 
            color='#4682B4', linewidth=1.5, marker='o', 
            markersize=4, alpha=0.8)
    
    # Add reference line for baseline visual acuity
    baseline_va = va_df['visual_acuity'].iloc[0] if len(va_df) > 0 else 0
    ax.axhline(y=baseline_va, color='#999999', linestyle='--', linewidth=0.8, alpha=0.5)
    
    # Add trend line using LOESS smoothing if we have enough points
    if len(va_df) >= 8:
        try:
            from scipy import signal
            # Smooth the data
            smoothed = signal.savgol_filter(va_df['visual_acuity'], 
                                          min(7, len(va_df) | 1), # window length must be odd and ≤ data length
                                          2) # polynomial order
            ax.plot(va_df['time'], smoothed, color='#B22222', linewidth=1.5, alpha=0.6)
        except ImportError:
            # Fallback to simple linear trend
            z = np.polyfit(va_df['time'], va_df['visual_acuity'], 1)
            p = np.poly1d(z)
            ax.plot(va_df['time'], p(va_df['time']), color='#B22222', linewidth=1.5, alpha=0.6)
    
    # Clean up the graph
    ax.grid(axis='x', visible=False)
    
    # Add labels and formatting
    ax.set_title('Visual Acuity Over Time', fontsize=14, color='#333333')
    ax.set_xlabel('Time (weeks)', fontsize=10, color='#666666')
    ax.set_ylabel('Visual Acuity', fontsize=10, color='#666666')
    
    # Add subtle annotations
    mean_va = va_df['visual_acuity'].mean()
    plt.figtext(0.13, 0.02, 
               f'Baseline VA: {baseline_va:.2f} | Mean VA: {mean_va:.2f}', 
               fontsize=9, color='#666666')
    
    plt.tight_layout(pad=1.5)
    return fig

def main():
    st.title("Tufte-Inspired Visualization Demo")
    
    st.markdown("""
    This demo shows visualizations inspired by Edward Tufte's principles of data visualization:
    
    1. Maximize the data-ink ratio (reduce non-data ink)
    2. Avoid chart junk (unnecessary visual elements)
    3. Use clear, direct labeling
    4. Show data variation, not design variation
    5. Integrate text, graphics, and data
    """)
    
    # Create sample enrollment data
    st.header("Patient Enrollment Visualization")
    
    # Generate enrollment dates
    dates = pd.date_range(start='2023-01-01', end='2024-12-31', freq='D')
    
    # Add some random variation for realistic patterns
    import random
    random.seed(42)
    selected_dates = random.sample(list(dates), min(1000, len(dates)))
    selected_ids = range(1, len(selected_dates) + 1)
    
    # Create DataFrame
    df = pd.DataFrame({
        'patient_id': selected_ids,
        'enrollment_date': selected_dates
    })
    
    # Show data sample
    st.write(f"Generated {len(df)} patient enrollment records")
    
    # Create and display the visualization
    fig = create_tufte_enrollment_visualization(df)
    st.pyplot(fig)
    
    # Visual acuity over time
    st.header("Visual Acuity Over Time")
    
    # Generate sample VA data
    weeks = range(0, 104, 4)  # Every 4 weeks for 2 years
    
    # Create a pattern with initial improvement then gradual decline
    base_va = 0.5  # Starting VA
    va_values = []
    for week in weeks:
        if week < 24:
            # Initial improvement phase
            va = base_va + 0.15 * (1 - np.exp(-week/12))
        else:
            # Gradual decline phase
            va = base_va + 0.15 - 0.0015 * (week - 24)
        
        # Add some random noise
        va += random.uniform(-0.02, 0.02)
        va_values.append(va)
    
    # Create DataFrame
    va_df = pd.DataFrame({
        'time': weeks,
        'visual_acuity': va_values
    })
    
    # Create and display the visualization
    fig = create_tufte_va_over_time_plot(va_df)
    st.pyplot(fig)
    
    # Add explanation
    st.markdown("""
    ### About Tufte-Inspired Visualizations
    
    These visualizations follow Tufte's principles by:
    
    - Removing unnecessary grid lines and borders
    - Using subtle colors that don't distract from the data
    - Adding reference lines to provide context
    - Integrating annotations directly in the chart
    - Focusing on the data story rather than decorative elements
    
    The result is a cleaner visualization that highlights the patterns in your data.
    """)

if __name__ == "__main__":
    main()