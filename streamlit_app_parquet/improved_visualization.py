"""
Improved visualization approach for Streamlit app that first renders matplotlib
visualization, then attempts to replace it with R visualization if available.
"""

import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import os
from datetime import datetime

def render_enrollment_visualization(enroll_df):
    """
    Render patient enrollment visualization with immediate matplotlib display,
    followed by an R visualization if available.
    
    Parameters
    ----------
    enroll_df : pandas.DataFrame
        DataFrame containing enrollment data with 'enrollment_date' column
    """
    # First, create the matplotlib visualization for immediate display
    # Group by month
    enroll_df['month'] = enroll_df['enrollment_date'].dt.strftime('%Y-%m')
    monthly_counts = enroll_df['month'].value_counts().sort_index()
    
    # Create a small figure
    fig, ax = plt.subplots(figsize=(8, 4), dpi=80)
    
    # Keep only top 10 months if there are too many
    if len(monthly_counts) > 10:
        monthly_counts = monthly_counts.iloc[:10]
    
    # Simple bar chart
    ax.bar(range(len(monthly_counts)), monthly_counts.values, color='#4682B4')
    
    # Clean up the appearance
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    # Set labels and title
    ax.set_title('Patient Enrollment by Month', fontsize=12)
    ax.set_ylabel('Patients')
    
    # X-axis labels
    if len(monthly_counts) > 8:
        # Show fewer labels
        indices = range(len(monthly_counts))
        labels = [monthly_counts.index[i] if i % 2 == 0 else "" for i in indices]
        ax.set_xticks(indices)
        ax.set_xticklabels(labels, rotation=45, ha='right')
    else:
        ax.set_xticks(range(len(monthly_counts)))
        ax.set_xticklabels(monthly_counts.index, rotation=45, ha='right')
    
    plt.tight_layout()
    
    # Create a placeholder for the visualization that we'll update
    viz_placeholder = st.empty()
    
    # Show the matplotlib version immediately
    viz_placeholder.pyplot(fig)
    plt.close(fig)
    
    # Now try to load R visualization in the background
    try:
        # Try to import without erroring
        try:
            from streamlit_app.r_integration import create_enrollment_visualization
            r_available = True
        except ImportError:
            r_available = False
            
        if r_available:
            # Create dictionary of enrollment dates
            enrollment_dates = {}
            for idx, row in enroll_df.iterrows():
                enrollment_dates[f"P{idx:04d}"] = row['enrollment_date']
            
            # Attempt R visualization without blocking UI
            r_viz_path = create_enrollment_visualization(enrollment_dates)
            
            if r_viz_path and os.path.exists(r_viz_path):
                # Replace matplotlib vis with R visualization
                viz_placeholder.image(r_viz_path, use_container_width=True)
                # Add a small indicator that this is the enhanced version
                st.caption("Enhanced visualization with trend analysis (R)")
    except Exception as e:
        # Silently fail - we still have the matplotlib version displayed
        print(f"R visualization attempt failed silently: {e}")
        
    return monthly_counts  # Return the monthly counts for any further analysis