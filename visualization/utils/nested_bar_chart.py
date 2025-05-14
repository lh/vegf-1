"""
Nested bar chart with category totals as background bars.

This module provides a function to create nested bar charts where each category
has colored bars for subcategories displayed over a light grey background bar
that represents the total value for that category.
"""
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import os
from typing import Optional, List, Tuple, Union


def create_nested_bar_chart(
    data: pd.DataFrame,
    category_col: str,
    subcategory_col: str,
    value_col: str,
    category_order: Optional[List[str]] = None,
    subcategory_order: Optional[List[str]] = None,
    subcategory_filter: Optional[List[str]] = None,
    title: str = "Categories by Subcategory",
    figsize: Tuple[int, int] = (7, 5),
    colors: Optional[List[str]] = None,
    background_color: str = "lightgrey",
    bar_width: float = 0.25,
    x_spacing: float = 2.0,
    background_width_factor: float = 3.5,
    background_alpha: float = 1.0,
    bar_alpha: float = 1.0,
    show_legend: bool = True,
    show_grid: bool = False,
    show_spines: bool = True,
    data_labels: bool = False,
    minimal_style: bool = False,
) -> Tuple[plt.Figure, plt.Axes]:
    """
    Create a nested bar chart with a grey background bar and colored category bars on top.

    The chart displays categories as groups, with subcategories as colored bars within each group.
    A light grey background bar shows the total value for each category.

    Parameters
    ----------
    data : pd.DataFrame
        DataFrame containing the data to plot with columns for categories, subcategories, and values
    category_col : str
        Name of the column containing the main categories
    subcategory_col : str
        Name of the column containing the subcategories
    value_col : str
        Name of the column containing the values to plot
    category_order : list, optional
        Order of categories to display, by default None (uses order in data)
    subcategory_order : list, optional
        Order of subcategories to display, by default None (uses order in data)
    subcategory_filter : list, optional
        List of subcategories to include (2-6), by default None (all subcategories)
    title : str, optional
        Chart title, by default "Categories by Subcategory"
    figsize : tuple, optional
        Figure size, by default (7, 5)
    colors : list, optional
        List of colors for subcategory bars, by default None (uses matplotlib defaults)
    background_color : str, optional
        Color of the background total bars, by default "lightgrey"
    bar_width : float, optional
        Width of the subcategory bars, by default 0.25
    x_spacing : float, optional
        Spacing multiplier between category groups, by default 2.0
    background_width_factor : float, optional
        Width factor for the background bar relative to bar_width, by default 3.5
    background_alpha : float, optional
        Transparency level for background bars (0.0 to 1.0), by default 1.0 (opaque)
    bar_alpha : float, optional
        Transparency level for subcategory bars (0.0 to 1.0), by default 1.0 (opaque)
    show_legend : bool, optional
        Whether to display the legend, by default True
    show_grid : bool, optional
        Whether to display grid lines, by default False
    show_spines : bool, optional
        Whether to display the axes spines (borders), by default True
    data_labels : bool, optional
        Whether to display value labels on top of bars, by default False
    minimal_style : bool, optional
        Apply Tufte-inspired minimal style (removes most chart junk), by default False

    Returns
    -------
    tuple
        (fig, ax) matplotlib figure and axes objects
        
    Raises
    ------
    ValueError
        If fewer than 2 or more than 6 subcategories are included
    """
    # Make a copy of the data to avoid modifying the original
    data = data.copy()
    
    # Filter subcategories if specified
    if subcategory_filter is not None:
        if not 2 <= len(subcategory_filter) <= 6:
            raise ValueError("subcategory_filter must contain between 2 and 6 subcategories")
        data = data[data[subcategory_col].isin(subcategory_filter)]
        
        # If both filter and order are provided, ensure order only includes filtered items
        if subcategory_order is not None:
            subcategory_order = [cat for cat in subcategory_order if cat in subcategory_filter]
    
    # Apply category ordering if provided
    if category_order is not None:
        data[category_col] = pd.Categorical(
            data[category_col], categories=category_order, ordered=True
        )
    
    # Apply subcategory ordering if provided
    if subcategory_order is not None:
        data[subcategory_col] = pd.Categorical(
            data[subcategory_col], categories=subcategory_order, ordered=True
        )
    
    # Sort by category and value
    data = data.sort_values([category_col, value_col], ascending=[True, False])
    
    # Pivot data to get subcategories as columns
    pivot_df = data.pivot(
        index=category_col, columns=subcategory_col, values=value_col
    )
    
    # Handle missing values that might occur after pivoting
    pivot_df = pivot_df.fillna(0)
    
    # Get number of subcategories
    num_subcategories = len(pivot_df.columns)
    if num_subcategories < 2:
        raise ValueError("At least 2 subcategories are required")
    if num_subcategories > 6:
        raise ValueError("Maximum of 6 subcategories supported")
    
    # Calculate totals for each category
    totals = pivot_df.sum(axis=1)
    
    # Create figure and axes
    fig, ax = plt.subplots(figsize=figsize)
    
    # Apply minimal style if requested (Tufte-inspired)
    if minimal_style:
        # Override other style options
        show_grid = False
        show_spines = False
        
        # Apply minimalist style to figure
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.tick_params(axis='y', length=0)
        ax.tick_params(axis='x', length=3)
        plt.rcParams['axes.facecolor'] = 'white'
        plt.rcParams['figure.facecolor'] = 'white'
    
    # Handle grid
    if show_grid:
        ax.grid(axis='y', linestyle=':', alpha=0.7)
    
    # Handle spines (borders)
    if not show_spines:
        for spine in ax.spines.values():
            spine.set_visible(False)
    
    # Set up x positions for bars
    x = np.arange(len(pivot_df.index))
    x_adjusted = x * x_spacing  # Adjust x positions to have space between categories
    
    # Draw background bars for totals
    background_width = bar_width * background_width_factor
    ax.bar(
        x_adjusted, 
        totals, 
        width=background_width, 
        color=background_color, 
        alpha=background_alpha,
        zorder=0, 
        label="Total"
    )
    
    # Calculate offset for centering subcategory bars
    offset_start = -(num_subcategories - 1) / 2 * bar_width
    
    # Draw bars for each subcategory with centered positioning
    for i, sub_cat in enumerate(pivot_df.columns):
        # Select color if provided
        color = colors[i] if colors is not None and i < len(colors) else None
        
        # Draw the bars
        bars = ax.bar(
            x_adjusted + offset_start + i * bar_width,
            pivot_df[sub_cat],
            width=bar_width,
            label=sub_cat,
            color=color,
            alpha=bar_alpha,
            zorder=1,
        )
        
        # Add data labels if requested
        if data_labels:
            for bar in bars:
                height = bar.get_height()
                ax.text(
                    bar.get_x() + bar.get_width()/2.,
                    height + (max(totals) * 0.01),  # Slight offset above bar
                    f'{int(height)}',  # Format as integer
                    ha='center', 
                    va='bottom',
                    fontsize=8,
                    alpha=0.8
                )
    
    # Set up labels and formatting
    ax.set_xlabel(category_col)
    ax.set_ylabel(value_col)
    ax.set_title(title, loc="left")
    ax.set_xticks(x_adjusted)
    ax.set_xticklabels(pivot_df.index)
    
    # Add legend only if requested
    if show_legend:
        # Format the legend title to remove underscores and capitalize
        title = subcategory_col.replace('_', ' ').title()
        # Create legend without frame (no box/line around it)
        ax.legend(title=title, frameon=False)
    else:
        ax.get_legend().remove() if ax.get_legend() else None
    
    # Ensure tight layout
    fig.tight_layout()
    
    return fig, ax