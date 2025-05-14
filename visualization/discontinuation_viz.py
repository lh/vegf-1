"""
Visualization module for discontinuation and retreatment analysis.

This module provides functions for visualizing discontinuation reasons and retreatment status
using nested bar charts.
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from typing import Optional, Dict, List, Tuple

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from visualization.utils.nested_bar_chart import create_nested_bar_chart


def create_discontinuation_retreatment_chart(
    data: pd.DataFrame,
    title: str = "Discontinuation Reasons by Retreatment Status",
    figsize: Tuple[int, int] = (10, 6),
    save_path: Optional[str] = None,
    retreat_colors: Optional[List[str]] = None,
) -> Tuple[plt.Figure, plt.Axes]:
    """
    Create a nested bar chart showing discontinuation reasons with retreatment status.
    
    Parameters
    ----------
    data : pd.DataFrame
        DataFrame containing discontinuation and retreatment data with columns:
        - 'discontinuation_reason': The reason for discontinuation
        - 'retreatment_status': Whether the patient was retreated ('Retreated' or 'Not Retreated')
        - 'count': The number of patients in each category
    title : str, optional
        Chart title, by default "Discontinuation Reasons by Retreatment Status"
    figsize : tuple, optional
        Figure size, by default (10, 6)
    save_path : str, optional
        Path to save the figure, by default None (figure is not saved)
    retreat_colors : list, optional
        Custom colors for retreatment status, by default None which uses
        muted blue for retreated and muted red for not retreated
        
    Returns
    -------
    tuple
        (fig, ax) matplotlib figure and axes objects
    """
    # Define default colors if not provided
    if retreat_colors is None:
        retreat_colors = ["#4878A6", "#A65C48"]  # Muted blue for retreated, muted red for not retreated
        
    # Define the order of discontinuation reasons
    reason_order = ["Administrative", "Not Renewed", "Planned", "Premature"]
    
    # Define the order of retreatment status
    retreat_order = ["Retreated", "Not Retreated"]
    
    # Create the chart
    fig, ax = create_nested_bar_chart(
        data=data,
        category_col="discontinuation_reason",
        subcategory_col="retreatment_status",
        value_col="count",
        category_order=reason_order,
        subcategory_order=retreat_order,
        title=title,
        figsize=figsize,
        colors=retreat_colors,
        background_color="#e5e5e5",  # Light grey for background
        background_alpha=0.3,        # Very transparent background
        bar_alpha=0.9,               # Slightly transparent bars
        minimal_style=True,          # Use Tufte-inspired minimal style
        data_labels=True             # Show data values on bars
    )
    
    # Save the figure if a path is provided
    if save_path:
        fig.savefig(save_path, dpi=300, bbox_inches="tight")
    
    return fig, ax


def generate_sample_data() -> pd.DataFrame:
    """
    Generate sample data for demonstration purposes.
    
    Returns
    -------
    pd.DataFrame
        Sample data frame with discontinuation reasons and retreatment status
    """
    # Create sample data
    data = {
        "discontinuation_reason": [
            "Administrative", "Administrative", 
            "Not Renewed", "Not Renewed",
            "Planned", "Planned",
            "Premature", "Premature"
        ],
        "retreatment_status": [
            "Retreated", "Not Retreated",
            "Retreated", "Not Retreated", 
            "Retreated", "Not Retreated",
            "Retreated", "Not Retreated"
        ],
        "count": [
            45, 120,      # Administrative
            30, 180,      # Not Renewed
            85, 50,       # Planned
            120, 95       # Premature
        ]
    }
    
    return pd.DataFrame(data)


if __name__ == "__main__":
    # Generate sample data
    sample_data = generate_sample_data()
    
    # Create the chart
    fig, ax = create_discontinuation_retreatment_chart(
        data=sample_data,
        title="Discontinuation Reasons by Retreatment Status",
        save_path="discontinuation_retreatment_chart.png"
    )
    
    # Save the chart without showing it
    print(f"Chart saved to: {os.path.join(os.getcwd(), 'discontinuation_retreatment_chart.png')}")