"""
Minimal direct visualization script for Streamlit.

This script demonstrates a simple approach to visualization in Streamlit,
bypassing the complex R integration machinery.
"""

import os
import sys
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
import datetime
import time
import numpy as np

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(project_root))

# Minimal functions for visualization
def create_enrollment_visualization(enrollment_df):
    """Create a basic enrollment visualization with matplotlib."""
    # Convert to datetime if needed
    if not pd.api.types.is_datetime64_any_dtype(enrollment_df['enrollment_date']):
        enrollment_df['enrollment_date'] = pd.to_datetime(enrollment_df['enrollment_date'])
    
    # Group by month
    enrollment_df['month'] = enrollment_df['enrollment_date'].dt.strftime('%Y-%m')
    monthly_counts = enrollment_df.groupby('month').size()
    
    # Create figure and plot
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(range(len(monthly_counts)), monthly_counts.values, color='#4682B4')
    
    # Add trend line
    x = np.arange(len(monthly_counts))
    z = np.polyfit(x, monthly_counts.values, 1)
    p = np.poly1d(z)
    ax.plot(x, p(x), 'r-', linewidth=2)
    
    # Clean up appearance
    ax.set_xticks(range(len(monthly_counts)))
    ax.set_xticklabels(monthly_counts.index, rotation=45, ha='right')
    ax.set_title('Patient Enrollment by Month')
    ax.set_ylabel('Number of Patients')
    plt.tight_layout()
    
    return fig

def main():
    st.title("Simple Direct Visualization Demo")
    
    # Create sample enrollment data
    st.header("Patient Enrollment Data")
    
    # Generate enrollment dates
    dates = pd.date_range(start='2023-01-01', end='2024-12-31', freq='D')
    patient_ids = range(1, len(dates) + 1)
    
    # Add some random variation
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
    st.dataframe(df.head())
    
    # Create visualization
    st.header("Enrollment Visualization")
    
    # Create and display the visualization directly
    fig = create_enrollment_visualization(df)
    st.pyplot(fig)
    
    # Add explanation
    st.markdown("""
    This visualization is created directly with matplotlib, without the complex
    R integration machinery. It shows patient enrollment by month with a simple
    trend line.
    """)

if __name__ == "__main__":
    main()