"""
Chart styling templates for consistent visualization across the application.

This module provides reusable styling functions based on prototype charts,
ensuring visual consistency throughout the application.
"""

import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.axes import Axes
from typing import Tuple

# Import the central color system - fail fast, no fallbacks
from visualization.color_system import COLORS, SEMANTIC_COLORS, ALPHAS


def apply_dual_axis_style(fig: Figure, ax_counts: Axes, ax_acuity: Axes) -> None:
    """
    Apply consistent styling to dual-axis charts based on the mean VA plot prototype.
    
    This function applies:
    - Light, thin spines with specific visibility
    - Consistent colors for axes and labels
    - Standard grid styling
    - Tufte-inspired minimalist approach
    
    Parameters
    ----------
    fig : matplotlib.figure.Figure
        The figure object
    ax_counts : matplotlib.axes.Axes
        The left axis (typically for patient/sample counts)
    ax_acuity : matplotlib.axes.Axes  
        The right axis (typically for visual acuity)
    """
    # Define consistent styling parameters
    light_spine_color = '#cccccc'  # Light gray
    light_spine_alpha = 0.3
    light_spine_width = 0.5
    
    # Get colors
    counts_color = COLORS.get('patient_counts', '#8FAD91')
    acuity_color = SEMANTIC_COLORS.get('acuity_data', COLORS['primary'])
    
    # Remove top spines
    ax_counts.spines['top'].set_visible(False)
    ax_acuity.spines['top'].set_visible(False)
    
    # Configure left spine for counts
    ax_counts.spines['left'].set_visible(True)
    ax_counts.spines['left'].set_linewidth(light_spine_width)
    ax_counts.spines['left'].set_alpha(light_spine_alpha)
    ax_counts.spines['left'].set_color(light_spine_color)
    
    # Configure bottom spine
    ax_counts.spines['bottom'].set_visible(True)
    ax_counts.spines['bottom'].set_linewidth(light_spine_width)
    ax_counts.spines['bottom'].set_alpha(light_spine_alpha)
    ax_counts.spines['bottom'].set_color(light_spine_color)
    
    # Configure right spine for acuity
    ax_acuity.spines['right'].set_visible(True)
    ax_acuity.spines['right'].set_linewidth(light_spine_width)
    ax_acuity.spines['right'].set_alpha(light_spine_alpha)
    ax_acuity.spines['right'].set_color(light_spine_color)
    
    # Hide unnecessary spines
    ax_acuity.spines['bottom'].set_visible(False)
    ax_acuity.spines['left'].set_visible(False)
    ax_counts.spines['right'].set_visible(False)
    
    # Apply grid styling - only on acuity axis
    ax_counts.grid(False)
    ax_acuity.grid(True, axis='y', linestyle='--', 
                   alpha=ALPHAS.get('very_low', 0.1), 
                   color=COLORS['grid'])
    ax_acuity.grid(False, axis='x')
    
    # Set tick colors
    ax_counts.tick_params(axis='y', colors=counts_color)
    ax_counts.tick_params(axis='x', colors=COLORS['text_secondary'])
    ax_acuity.tick_params(axis='y', colors=acuity_color)


def apply_standard_layout(fig: Figure, title: str, has_legend: bool = True, legend_rows: int = 1) -> None:
    """
    Apply standard layout parameters for consistent chart spacing.
    
    Based on the standardized visual acuity plot layouts.
    
    Parameters
    ----------
    fig : matplotlib.figure.Figure
        The figure object
    title : str
        The chart title
    has_legend : bool
        Whether the chart has a legend at the top
    legend_rows : int
        Number of rows the legend will use (affects top spacing)
    """
    # Apply title with consistent positioning
    fig.suptitle(title, 
                fontsize=12, 
                color=COLORS['text'], 
                x=0.1,  # Left-aligned  
                y=0.98,  # Near the top
                ha='left')
    
    # Set standard margins - based on tested VA plot layouts
    if has_legend:
        if legend_rows > 1:
            # Multi-row legend needs more top space
            fig.subplots_adjust(left=0.12, right=0.88, top=0.88, bottom=0.15)
            plt.tight_layout(rect=[0, 0.03, 1, 0.92])
        else:
            # Single-row legend
            fig.subplots_adjust(left=0.12, right=0.88, top=0.92, bottom=0.15)
            plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    else:
        # No legend
        fig.subplots_adjust(left=0.12, right=0.88, top=0.95, bottom=0.12)
        plt.tight_layout(rect=[0, 0.02, 1, 0.98])


def apply_horizontal_legend(ax: Axes, lines1: list, labels1: list, 
                          lines2: list = None, labels2: list = None,
                          max_cols: int = 4) -> int:
    """
    Apply horizontal legend at the top of the chart.
    
    Based on the standardized visual acuity plot layouts.
    
    Parameters
    ----------
    ax : matplotlib.axes.Axes
        The axis to attach the legend to
    lines1 : list
        First set of line handles
    labels1 : list
        First set of labels
    lines2 : list, optional
        Second set of line handles
    labels2 : list, optional
        Second set of labels
    max_cols : int
        Maximum columns before wrapping to next row
        
    Returns
    -------
    int
        Number of rows used by the legend
    """
    if lines2 is not None and labels2 is not None:
        all_lines = lines1 + lines2
        all_labels = labels1 + labels2
    else:
        all_lines = lines1
        all_labels = labels1
    
    # Calculate optimal column count
    num_items = len(all_lines)
    if num_items <= max_cols:
        ncol = num_items
        legend_rows = 1
    else:
        ncol = max_cols if max_cols > 0 else 3  # Default to 3 columns
        legend_rows = (num_items + ncol - 1) // ncol  # Ceiling division
    
    # Adjust anchor position for multi-row legends
    y_anchor = 1.05 if legend_rows == 1 else 1.08
    
    ax.legend(all_lines, all_labels,
             frameon=False, 
             fontsize=9,
             loc='upper center', 
             bbox_to_anchor=(0.5, y_anchor),
             ncol=ncol,
             columnspacing=1.5)
             
    return legend_rows


def create_standard_figure(figsize: Tuple[float, float] = (10, 6), 
                         title: str = None,
                         xlabel: str = None,
                         ylabel: str = None) -> Tuple[Figure, Axes]:
    """
    Create a figure with standard size and optional basic setup.
    
    Parameters
    ----------
    figsize : tuple, optional
        Figure size in inches, default (10, 6)
    title : str, optional
        Title for the plot
    xlabel : str, optional
        Label for x-axis
    ylabel : str, optional
        Label for y-axis
    
    Returns
    -------
    tuple
        (figure, axes) objects
    """
    fig, ax = plt.subplots(figsize=figsize)
    
    if title:
        ax.set_title(title)
    if xlabel:
        ax.set_xlabel(xlabel)
    if ylabel:
        ax.set_ylabel(ylabel)
    
    return fig, ax


def set_standard_y_axis_range(ax: Axes) -> None:
    """
    Set the standard visual acuity y-axis range (0-85).
    
    Parameters
    ----------
    ax : matplotlib.axes.Axes
        The axis to set the range for
    """
    ax.set_ylim(0, 85)


def set_yearly_x_ticks(ax: Axes, max_months: int = None, use_year_labels: bool = False) -> None:
    """
    Set x-axis ticks at yearly intervals (0, 12, 24, 36, etc.)
    
    Parameters
    ----------
    ax : matplotlib.axes.Axes
        The axis to set the ticks for
    max_months : int, optional
        Maximum months to show. If None, will use current axis limits
    use_year_labels : bool, optional
        If True, show years (0, 1y, 2y, etc.). If False, show months (0, 12, 24, etc.)
    """
    if max_months is None:
        # Get current x-axis limits
        xlim = ax.get_xlim()
        max_months = int(xlim[1])
    
    # Generate tick positions at yearly intervals
    years = range(0, max_months + 1, 12)
    ax.set_xticks(list(years))
    
    # Set labels based on preference
    if use_year_labels:
        year_labels = [f"{y//12}y" if y > 0 else "0" for y in years]
        ax.set_xticklabels(year_labels)
    # else keep the default month numbers


def add_explanatory_note(fig: Figure, note: str) -> None:
    """
    Add an explanatory note at the bottom of the chart.
    
    Parameters
    ----------
    fig : matplotlib.figure.Figure
        The figure object
    note : str
        The explanatory text
    """
    fig.text(0.5, 0.01, 
            note,
            ha='center', 
            va='bottom', 
            fontsize=9, 
            color=COLORS['text_secondary'],
            style='italic', 
            wrap=True)


def format_standard_dual_axis_chart(fig: Figure, ax_counts: Axes, ax_acuity: Axes,
                                  title: str, lines1: list = None, labels1: list = None,
                                  lines2: list = None, labels2: list = None,
                                  note: str = None, primary_label: str = None,
                                  secondary_label: str = None, x_label: str = None,
                                  y_limits: Tuple[float, float] = (0, 85),
                                  colors: dict = None, use_yearly_ticks: bool = True) -> None:
    """
    Apply all standard formatting to a dual-axis chart.
    
    This is a convenience function that combines all the standard formatting
    functions for creating consistent dual-axis charts like the VA plots.
    
    Parameters
    ----------
    fig : matplotlib.figure.Figure
        The figure object
    ax_counts : matplotlib.axes.Axes
        The left axis (typically for counts)
    ax_acuity : matplotlib.axes.Axes
        The right axis (typically for acuity)
    title : str
        The chart title
    lines1 : list, optional
        Line handles from first axis
    labels1 : list, optional
        Labels from first axis
    lines2 : list, optional
        Line handles from second axis
    labels2 : list, optional
        Labels from second axis
    note : str, optional
        Explanatory note to add at bottom
    primary_label : str, optional
        Label for primary (left) y-axis
    secondary_label : str, optional
        Label for secondary (right) y-axis
    x_label : str, optional
        Label for x-axis
    y_limits : tuple, optional
        Y-axis limits, default (0, 85)
    colors : dict, optional
        Color mapping for axes
    use_yearly_ticks : bool, optional
        Whether to set x-axis ticks at yearly intervals
    """
    # Apply dual axis styling
    apply_dual_axis_style(fig, ax_counts, ax_acuity)
    
    # Set y-axis ranges
    ax_counts.set_ylim(y_limits)
    ax_acuity.set_ylim(y_limits)
    
    # Set axis labels if provided
    if primary_label:
        ax_counts.set_ylabel(primary_label)
    if secondary_label:
        ax_acuity.set_ylabel(secondary_label)
    if x_label:
        ax_counts.set_xlabel(x_label)
    
    # Set yearly x-ticks if requested
    if use_yearly_ticks:
        set_yearly_x_ticks(ax_counts)
    
    # Apply legend and get row count if lines are provided
    if lines1 and labels1 and lines2 and labels2:
        legend_rows = apply_horizontal_legend(ax_acuity, lines1, labels1, lines2, labels2)
    else:
        legend_rows = 1
    
    # Apply standard layout with appropriate spacing
    apply_standard_layout(fig, title, has_legend=True, legend_rows=legend_rows)
    
    # Add explanatory note if provided
    if note:
        add_explanatory_note(fig, note)