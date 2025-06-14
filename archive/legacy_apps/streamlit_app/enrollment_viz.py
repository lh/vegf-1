"""
Simple, robust enrollment visualization function for Streamlit.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

def create_simple_enrollment_histogram(enrollment_dates):
    """
    Create an ultra-minimal text-based visualization of enrollment.
    This function creates a small, fixed-size image that simply shows
    enrollment statistics as text to avoid any image size issues.

    Parameters
    ----------
    enrollment_dates : dict
        Dictionary mapping patient IDs to enrollment dates

    Returns
    -------
    matplotlib.figure.Figure
        Figure containing the enrollment statistics
    """
    # Create a tiny fixed-size figure
    fig = plt.figure(figsize=(4, 3), dpi=60)

    # Clear any existing plots and set up a simple text-only display
    plt.clf()
    plt.axis('off')

    try:
        # Calculate basic statistics safely
        total_patients = len(enrollment_dates)

        # Get the start and end dates if available
        if total_patients > 0:
            dates = [d for d in enrollment_dates.values() if d is not None]
            if dates:
                # Convert to datetime objects if they aren't already
                dates = [d if isinstance(d, datetime) else pd.to_datetime(d) for d in dates]

                # Get min and max dates
                min_date = min(dates).strftime("%Y-%m-%d")
                max_date = max(dates).strftime("%Y-%m-%d")

                # Add text to the figure
                plt.text(0.5, 0.8, f"Total Patients: {total_patients}",
                        ha='center', fontsize=10)
                plt.text(0.5, 0.6, f"First Enrollment: {min_date}",
                        ha='center', fontsize=9)
                plt.text(0.5, 0.4, f"Last Enrollment: {max_date}",
                        ha='center', fontsize=9)
                plt.text(0.5, 0.2, "Full visualization disabled",
                        ha='center', fontsize=8, color='gray')
            else:
                plt.text(0.5, 0.5, f"Total Patients: {total_patients}",
                        ha='center', fontsize=10)
        else:
            plt.text(0.5, 0.5, "No enrollment data available",
                    ha='center', fontsize=10)

    except Exception as e:
        # Fallback if any error occurs
        plt.text(0.5, 0.5, "Enrollment data available",
                ha='center', fontsize=10)
        plt.text(0.5, 0.3, "(Visualization disabled)",
                ha='center', fontsize=8, color='gray')
        print(f"Error in enrollment visualization: {e}")

    # Force tight layout with minimal padding
    plt.tight_layout(pad=0.1)

    # Save with very low resolution
    try:
        plt.savefig("patient_enrollment_histogram.png", dpi=60, format='png',
                   bbox_inches='tight')
    except Exception as e:
        print(f"Error saving enrollment figure: {e}")

    return fig