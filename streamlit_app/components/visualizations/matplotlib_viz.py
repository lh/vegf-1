"""
Matplotlib-based visualizations for the APE Streamlit application.

This module provides visualization functions using matplotlib,
which are used for immediate display and as fallbacks when R is not available.
"""

import logging
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from typing import Dict, Any, Optional, List, Tuple, Union

# Import the central color system
try:
    from visualization.color_system import COLORS, SEMANTIC_COLORS, ALPHAS
except ImportError:
    # Fallback if the central color system is not available
    COLORS = {
        'primary': '#4682B4',    # Steel Blue - for visual acuity data
        'secondary': '#B22222',  # Firebrick - for critical information
        'patient_counts': '#8FAD91',  # Muted Sage Green - for patient counts
    }
    ALPHAS = {
        'high': 0.8,        # High opacity for primary elements
        'medium': 0.5,      # Medium opacity for standard elements
        'low': 0.2,         # Low opacity for background elements
        'very_low': 0.1,    # Very low opacity for subtle elements
        'patient_counts': 0.5  # Consistent opacity for all patient/sample count visualizations
    }
    SEMANTIC_COLORS = {
        'acuity_data': COLORS['primary'],
        'patient_counts': COLORS['patient_counts'],
        'critical_info': COLORS['secondary'],
    }

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_enrollment_visualization_matplotlib(
    enrollment_df: pd.DataFrame, 
    title: str = "Patient Enrollment by Month",
    figsize: Tuple[int, int] = (8, 4),
    dpi: int = 80
) -> plt.Figure:
    """Create a matplotlib visualization of patient enrollment.
    
    Parameters
    ----------
    enrollment_df : pandas.DataFrame
        DataFrame with patient enrollment data
    title : str, optional
        Title for the visualization, by default "Patient Enrollment by Month"
    figsize : Tuple[int, int], optional
        Figure size in inches, by default (8, 4)
    dpi : int, optional
        Figure resolution, by default 80
    
    Returns
    -------
    matplotlib.figure.Figure
        Matplotlib figure object
    """
    try:
        # Group by month
        enrollment_df['month'] = enrollment_df['enrollment_date'].dt.strftime('%Y-%m')
        monthly_counts = enrollment_df['month'].value_counts().sort_index()
        
        # Create figure
        fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
        
        # Simple bar chart - use sage green with consistent alpha for patient counts
        ax.bar(range(len(monthly_counts)), monthly_counts.values,
               color=SEMANTIC_COLORS['patient_counts'],
               alpha=ALPHAS['patient_counts'])
        
        # Clean up the appearance
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        # Set labels and title
        ax.set_title(title, fontsize=12)
        ax.set_ylabel('Patients')
        
        # X-axis labels
        ax.set_xticks(range(len(monthly_counts)))
        ax.set_xticklabels(monthly_counts.index, rotation=45, ha='right')
        
        plt.tight_layout()
        return fig
    except Exception as e:
        logger.error(f"Error creating matplotlib visualization: {e}")
        # Create a simple error figure
        fig, ax = plt.subplots(figsize=figsize)
        ax.text(0.5, 0.5, f"Error creating visualization: {e}", 
                ha='center', va='center', transform=ax.transAxes)
        return fig


def create_va_over_time_plot_matplotlib(
    results: Dict[str, Any],
    figsize: Tuple[int, int] = (10, 5),
    dpi: int = 80
) -> plt.Figure:
    """Create a visual acuity over time plot using matplotlib.
    
    Parameters
    ----------
    results : Dict[str, Any]
        Simulation results containing mean_va_data
    figsize : Tuple[int, int], optional
        Figure size in inches, by default (10, 5)
    dpi : int, optional
        Figure resolution, by default 80
    
    Returns
    -------
    matplotlib.figure.Figure
        Matplotlib figure object
    """
    try:
        # Extract data
        if "mean_va_data" not in results or not results["mean_va_data"]:
            raise ValueError("No visual acuity data found in results")
        
        va_data = results["mean_va_data"]
        
        # Prepare data for plotting
        times = []
        vas = []
        
        for point in va_data:
            times.append(point.get("time", 0) if isinstance(point, dict) else getattr(point, "time", 0))
            vas.append(point.get("visual_acuity", 0) if isinstance(point, dict) else getattr(point, "visual_acuity", 0))
        
        # Create figure
        fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
        
        # Plot data
        ax.plot(times, vas, 'o-', color='#4682B4', linewidth=2, markersize=4)
        
        # Clean up the appearance
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        # Set labels and title
        ax.set_title("Visual Acuity Over Time", fontsize=14)
        ax.set_xlabel("Time (weeks)", fontsize=12)
        ax.set_ylabel("Visual Acuity", fontsize=12)
        
        # Add grid for readability
        ax.grid(axis='y', linestyle='--', alpha=0.7)
        
        plt.tight_layout()
        return fig
    except Exception as e:
        logger.error(f"Error creating VA over time plot: {e}")
        # Create a simple error figure
        fig, ax = plt.subplots(figsize=figsize)
        ax.text(0.5, 0.5, f"Error creating VA visualization: {e}", 
                ha='center', va='center', transform=ax.transAxes)
        return fig


def create_discontinuation_plot_matplotlib(
    results: Dict[str, Any],
    figsize: Tuple[int, int] = (10, 5),
    dpi: int = 80
) -> Union[plt.Figure, List[plt.Figure]]:
    """Create a discontinuation plot using matplotlib.
    
    Parameters
    ----------
    results : Dict[str, Any]
        Simulation results containing discontinuation data
    figsize : Tuple[int, int], optional
        Figure size in inches, by default (10, 5)
    dpi : int, optional
        Figure resolution, by default 80
    
    Returns
    -------
    Union[plt.Figure, List[plt.Figure]]
        Matplotlib figure object or list of figures
    """
    try:
        # Check if we have discontinuation data
        if "discontinuation_counts" not in results:
            raise ValueError("No discontinuation data found in results")
        
        # Extract discontinuation counts
        disc_counts = results["discontinuation_counts"]
        
        # Convert to dictionary if it's not already
        if not isinstance(disc_counts, dict):
            disc_counts = disc_counts.as_dict() if hasattr(disc_counts, "as_dict") else {"Unknown": 0}
        
        # Create figure
        fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
        
        # Create bar chart
        labels = list(disc_counts.keys())
        values = list(disc_counts.values())
        
        # Sort by values (descending)
        sorted_indices = np.argsort(values)[::-1]
        labels = [labels[i] for i in sorted_indices]
        values = [values[i] for i in sorted_indices]
        
        # Plot
        bars = ax.bar(labels, values, color=SEMANTIC_COLORS['acuity_data'], alpha=ALPHAS['medium'])
        
        # Clean up the appearance
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        # Set labels and title
        ax.set_title("Discontinuations by Type", fontsize=14)
        ax.set_ylabel("Count", fontsize=12)
        
        # Rotate x labels for readability
        plt.xticks(rotation=45, ha='right')
        
        # Add data labels
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                    f'{int(height)}',
                    ha='center', va='bottom', rotation=0)
        
        plt.tight_layout()
        return fig
    except Exception as e:
        logger.error(f"Error creating discontinuation plot: {e}")
        # Create a simple error figure
        fig, ax = plt.subplots(figsize=figsize)
        ax.text(0.5, 0.5, f"Error creating discontinuation visualization: {e}", 
                ha='center', va='center', transform=ax.transAxes)
        return fig


def create_dual_timeframe_plot_matplotlib(
    results: Dict[str, Any],
    figsize: Tuple[int, int] = (12, 5),
    dpi: int = 80
) -> plt.Figure:
    """Create a dual timeframe plot using matplotlib.
    
    Parameters
    ----------
    results : Dict[str, Any]
        Simulation results containing calendar_time_va and patient_time_va
    figsize : Tuple[int, int], optional
        Figure size in inches, by default (12, 5)
    dpi : int, optional
        Figure resolution, by default 80
    
    Returns
    -------
    plt.Figure
        Matplotlib figure object
    """
    try:
        # Check if we have the required data
        if "calendar_time_va" not in results or "patient_time_va" not in results:
            raise ValueError("Missing calendar_time_va or patient_time_va in results")
        
        # Extract data
        calendar_data = results["calendar_time_va"]
        patient_data = results["patient_time_va"]
        
        # Create figure with two subplots
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize, dpi=dpi)
        
        # Calendar time plot
        ax1.plot(
            [point["month"] for point in calendar_data], 
            [point["mean_va"] for point in calendar_data], 
            marker='o', color='#4682B4', linewidth=2
        )
        ax1.set_title("Mean VA by Calendar Time")
        ax1.set_xlabel("Months Since Simulation Start")
        ax1.set_ylabel("Mean Visual Acuity")
        ax1.grid(axis='y', linestyle='--', alpha=0.7)
        ax1.spines['top'].set_visible(False)
        ax1.spines['right'].set_visible(False)
        
        # Patient time plot
        ax2.plot(
            [point["week"] for point in patient_data], 
            [point["mean_va"] for point in patient_data], 
            marker='o', color='#6A5ACD', linewidth=2
        )
        ax2.set_title("Mean VA by Patient Time")
        ax2.set_xlabel("Weeks Since Patient Enrollment")
        ax2.set_ylabel("Mean Visual Acuity")
        ax2.grid(axis='y', linestyle='--', alpha=0.7)
        ax2.spines['top'].set_visible(False)
        ax2.spines['right'].set_visible(False)
        
        plt.tight_layout()
        return fig
    except Exception as e:
        logger.error(f"Error creating dual timeframe plot: {e}")
        # Create a simple error figure
        fig, ax = plt.subplots(figsize=figsize)
        ax.text(0.5, 0.5, f"Error creating dual timeframe visualization: {e}", 
                ha='center', va='center', transform=ax.transAxes)
        return fig