"""
Tufte-inspired visualization style utilities.

This module provides functions to apply Edward Tufte's data visualization principles
to matplotlib charts, ensuring a consistent, clean aesthetic across the application.

The style emphasizes:
1. Maximizing the data-ink ratio (reduce non-data elements)
2. Avoiding chart junk (unnecessary decorative elements)
3. Using clear, direct labeling
4. Using subtle, appropriate colors
5. Minimizing distracting elements like borders and grid lines
6. Using color to establish semantic relationships:
   - Same color family for related data (e.g., bars and their trend line in calendar visualization)
   - Different colors for different data types (e.g., acuity line vs. sample size bars in patient visualization)
7. Consistency across visualizations to create a unified visual language
"""

import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np
from typing import Dict, Any, Optional, Tuple, List, Union

# Default color palette inspired by Tufte's work - subdued, functional colors
TUFTE_COLORS = {
    'primary': '#4682B4',    # Steel Blue - for main data
    'secondary': '#B22222',  # Firebrick - for trend lines and highlights
    'tertiary': '#228B22',   # Forest Green - for additional series
    'background': '#FFFFFF', # White background
    'grid': '#EEEEEE',       # Very light gray for grid lines
    'text': '#333333',       # Dark gray for titles and labels
    'text_secondary': '#666666',  # Medium gray for secondary text
    'border': '#CCCCCC'      # Light gray for necessary borders
}

def set_tufte_style(base_size: int = 11) -> None:
    """
    Apply Tufte-inspired style settings to matplotlib.
    
    This configures matplotlib to use a clean, minimal style that emphasizes
    the data while reducing visual clutter.
    
    Parameters
    ----------
    base_size : int, optional
        Base font size for the plot, by default 11
    """
    # Start with a clean base style
    plt.style.use('seaborn-v0_8-whitegrid')
    
    # Configure text properties
    plt.rcParams['text.color'] = TUFTE_COLORS['text']
    plt.rcParams['axes.labelcolor'] = TUFTE_COLORS['text_secondary']
    plt.rcParams['xtick.color'] = TUFTE_COLORS['text_secondary']
    plt.rcParams['ytick.color'] = TUFTE_COLORS['text_secondary']
    
    # Configure font properties
    plt.rcParams['font.family'] = 'sans-serif'
    plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans', 'Liberation Sans', 'Helvetica', 'sans-serif']
    plt.rcParams['axes.titlesize'] = base_size * 1.2
    plt.rcParams['axes.labelsize'] = base_size * 0.9
    
    # Configure grid properties
    plt.rcParams['grid.color'] = TUFTE_COLORS['grid']
    plt.rcParams['grid.linewidth'] = 0.5
    plt.rcParams['grid.linestyle'] = '-'
    plt.rcParams['grid.alpha'] = 0.7
    
    # Configure axis and plot properties
    plt.rcParams['axes.spines.top'] = False
    plt.rcParams['axes.spines.right'] = False
    plt.rcParams['axes.spines.bottom'] = True
    plt.rcParams['axes.spines.left'] = False
    plt.rcParams['axes.edgecolor'] = TUFTE_COLORS['border']
    plt.rcParams['axes.linewidth'] = 0.5
    
    # Figure properties
    plt.rcParams['figure.facecolor'] = TUFTE_COLORS['background']
    plt.rcParams['figure.dpi'] = 100
    
    # Legend properties
    plt.rcParams['legend.frameon'] = False
    plt.rcParams['legend.fontsize'] = base_size * 0.8


def style_axis(ax, hide_spines: List[str] = ['top', 'right', 'left'], 
               hide_grid: List[str] = ['x'], title_size: int = 14,
               label_size: int = 10) -> None:
    """
    Apply Tufte-inspired styling to a specific axis.
    
    This is useful when you need to style individual axes in a figure,
    or when creating complex visualizations that the global style doesn't
    fully address.
    
    Parameters
    ----------
    ax : matplotlib.axes.Axes
        The axis to style
    hide_spines : List[str], optional
        Spines to hide, by default ['top', 'right', 'left']
    hide_grid : List[str], optional
        Grid lines to hide, by default ['x']
    title_size : int, optional
        Font size for the axis title, by default 14
    label_size : int, optional
        Font size for the axis labels, by default 10
    """
    # Hide specified spines
    for spine in hide_spines:
        ax.spines[spine].set_visible(False)
    
    # Make bottom spine light gray and thin
    if 'bottom' not in hide_spines:
        ax.spines['bottom'].set_color(TUFTE_COLORS['border'])
        ax.spines['bottom'].set_linewidth(0.5)
    
    # Hide specified grid lines
    for grid in hide_grid:
        ax.grid(axis=grid, visible=False)
    
    # Configure grid that remains visible
    if 'x' not in hide_grid:
        ax.grid(axis='x', color=TUFTE_COLORS['grid'], linestyle='-', linewidth=0.5, alpha=0.7)
    if 'y' not in hide_grid:
        ax.grid(axis='y', color=TUFTE_COLORS['grid'], linestyle='-', linewidth=0.5, alpha=0.7)
    
    # Configure text sizes
    ax.title.set_fontsize(title_size)
    ax.title.set_color(TUFTE_COLORS['text'])
    ax.xaxis.label.set_fontsize(label_size)
    ax.yaxis.label.set_fontsize(label_size)
    ax.xaxis.label.set_color(TUFTE_COLORS['text_secondary'])
    ax.yaxis.label.set_color(TUFTE_COLORS['text_secondary'])
    
    # Configure tick parameters
    ax.tick_params(
        axis='both',
        which='both',
        bottom=True,
        top=False,
        left=False,
        right=False,
        labelsize=label_size * 0.9,
        colors=TUFTE_COLORS['text_secondary']
    )


def style_bar_chart(ax, bars, color: str = TUFTE_COLORS['primary'], 
                    alpha: float = 0.7, edge_color: Optional[str] = None) -> None:
    """
    Apply Tufte-inspired styling to bar charts.
    
    Parameters
    ----------
    ax : matplotlib.axes.Axes
        The axis containing the bar chart
    bars : matplotlib.container.BarContainer
        The bars returned from ax.bar()
    color : str, optional
        Bar color, by default TUFTE_COLORS['primary']
    alpha : float, optional
        Bar transparency, by default 0.7
    edge_color : Optional[str], optional
        Edge color for bars, by default None (no edge)
    """
    # Set bar properties
    for bar in bars:
        bar.set_color(color)
        bar.set_alpha(alpha)
        if edge_color is None:
            bar.set_edgecolor('none')
        else:
            bar.set_edgecolor(edge_color)
            bar.set_linewidth(0.5)


def style_line(ax, line, color: str = TUFTE_COLORS['primary'], 
              linewidth: float = 1.5, alpha: float = 0.8,
              add_markers: bool = False, marker_size: int = 4) -> None:
    """
    Apply Tufte-inspired styling to lines in a plot.
    
    Parameters
    ----------
    ax : matplotlib.axes.Axes
        The axis containing the line
    line : matplotlib.lines.Line2D
        The line to style
    color : str, optional
        Line color, by default TUFTE_COLORS['primary']
    linewidth : float, optional
        Line width, by default 1.5
    alpha : float, optional
        Line transparency, by default 0.8
    add_markers : bool, optional
        Whether to add markers to the line, by default False
    marker_size : int, optional
        Size of markers if used, by default 4
    """
    # Set line properties
    line.set_color(color)
    line.set_linewidth(linewidth)
    line.set_alpha(alpha)
    
    if add_markers:
        line.set_marker('o')
        line.set_markersize(marker_size)
        line.set_markerfacecolor(color)
        line.set_markeredgecolor('none')


def add_data_label(ax, x, y, label, color: str = TUFTE_COLORS['text_secondary'], 
                  fontsize: int = 9, offset: Tuple[float, float] = (0, 5)) -> None:
    """
    Add a data label directly to a plot point.
    
    This follows Tufte's principle of keeping annotation close to the data.
    
    Parameters
    ----------
    ax : matplotlib.axes.Axes
        The axis to add the label to
    x : float
        X-coordinate of the label
    y : float
        Y-coordinate of the label
    label : str
        The text to display
    color : str, optional
        Label color, by default TUFTE_COLORS['text_secondary']
    fontsize : int, optional
        Font size for the label, by default 9
    offset : Tuple[float, float], optional
        Offset (x, y) for the label position, by default (0, 5)
    """
    ax.annotate(
        label,
        xy=(x, y),
        xytext=(offset[0], offset[1]),
        textcoords='offset points',
        fontsize=fontsize,
        color=color,
        va='bottom' if offset[1] > 0 else 'top',
        ha='center'
    )


def add_reference_line(ax, value: float, axis: str = 'y', 
                      color: str = TUFTE_COLORS['text_secondary'],
                      linestyle: str = '--', linewidth: float = 0.8,
                      alpha: float = 0.5, label: Optional[str] = None) -> None:
    """
    Add a reference line to highlight an important value.
    
    Parameters
    ----------
    ax : matplotlib.axes.Axes
        The axis to add the reference line to
    value : float
        The value at which to place the reference line
    axis : str, optional
        The axis for the reference line ('x' or 'y'), by default 'y'
    color : str, optional
        Line color, by default TUFTE_COLORS['text_secondary']
    linestyle : str, optional
        Line style, by default '--'
    linewidth : float, optional
        Line width, by default 0.8
    alpha : float, optional
        Line transparency, by default 0.5
    label : Optional[str], optional
        Label for the line (for legend), by default None
    """
    if axis == 'y':
        ax.axhline(y=value, color=color, linestyle=linestyle, 
                   linewidth=linewidth, alpha=alpha, label=label)
    else:
        ax.axvline(x=value, color=color, linestyle=linestyle, 
                   linewidth=linewidth, alpha=alpha, label=label)


def add_text_annotation(fig, text: str, position: str = 'bottom-left',
                        color: str = TUFTE_COLORS['text_secondary'], 
                        fontsize: int = 9, padding: float = 0.02) -> None:
    """
    Add a text annotation to a figure.
    
    Useful for adding context, data source information, or notes directly
    on the visualization.
    
    Parameters
    ----------
    fig : matplotlib.figure.Figure
        The figure to add the annotation to
    text : str
        The text to display
    position : str, optional
        Position of the text ('bottom-left', 'bottom-right', 'top-left', 'top-right'),
        by default 'bottom-left'
    color : str, optional
        Text color, by default TUFTE_COLORS['text_secondary']
    fontsize : int, optional
        Font size, by default 9
    padding : float, optional
        Padding from the edge (as a fraction of figure dimensions), by default 0.02
    """
    # Determine x and y coordinates based on position
    if position == 'bottom-left':
        x, y = padding, padding
        ha, va = 'left', 'bottom'
    elif position == 'bottom-right':
        x, y = 1 - padding, padding
        ha, va = 'right', 'bottom'
    elif position == 'top-left':
        x, y = padding, 1 - padding
        ha, va = 'left', 'top'
    elif position == 'top-right':
        x, y = 1 - padding, 1 - padding
        ha, va = 'right', 'top'
    else:
        # Default to bottom-left
        x, y = padding, padding
        ha, va = 'left', 'bottom'
    
    fig.text(x, y, text, fontsize=fontsize, color=color, ha=ha, va=va)


def create_tufte_enrollment_chart(data, fig=None, ax=None, title: str = 'Patient Enrollment Over Time',
                                 add_trend: bool = True, figsize: Tuple[int, int] = (10, 5)) -> Tuple:
    """
    Create a Tufte-inspired enrollment chart.
    
    Parameters
    ----------
    data : pandas.DataFrame
        DataFrame with 'enrollment_date' column
    fig : matplotlib.figure.Figure, optional
        Existing figure to use, by default None (creates new figure)
    ax : matplotlib.axes.Axes, optional
        Existing axis to use, by default None (creates new axis)
    title : str, optional
        Chart title, by default 'Patient Enrollment Over Time'
    add_trend : bool, optional
        Whether to add a trend line, by default True
    figsize : Tuple[int, int], optional
        Figure size in inches, by default (10, 5)
    
    Returns
    -------
    Tuple
        (fig, ax) - The figure and axis objects
    """
    # Apply Tufte style
    set_tufte_style()
    
    # Create figure and axis if not provided
    if fig is None or ax is None:
        fig, ax = plt.subplots(figsize=figsize, dpi=100)
    
    # Ensure enrollment_date is datetime
    if 'enrollment_date' in data.columns:
        if not pd.api.types.is_datetime64_any_dtype(data['enrollment_date']):
            data = data.copy()
            data['enrollment_date'] = pd.to_datetime(data['enrollment_date'])
        
        # Group by month
        data['month'] = data['enrollment_date'].dt.strftime('%Y-%m')
        monthly_counts = data.groupby('month').size()
    else:
        # Assume data is already grouped
        monthly_counts = data
    
    # Plot bars with lighter blue to match other visualizations
    x = range(len(monthly_counts))
    bars = ax.bar(x, monthly_counts.values, color='#a8c4e5', alpha=0.3, edgecolor='none')

    # Trend line has been removed to match request
    
    # Style the chart
    style_axis(ax)
    
    # Add labels and formatting
    ax.set_xticks(x)
    ax.set_xticklabels(monthly_counts.index, rotation=45, ha='right', fontsize=9)
    ax.set_title(title, fontsize=14, color=TUFTE_COLORS['text'])
    ax.set_ylabel('Number of Patients', fontsize=10, color=TUFTE_COLORS['text_secondary'])
    
    # Add annotation for total patients
    total_patients = data.shape[0] if 'enrollment_date' in data.columns else sum(monthly_counts)
    add_text_annotation(fig, f'Total of {total_patients} patients enrolled', position='bottom-left')
    
    plt.tight_layout(pad=1.5)
    return fig, ax


def create_tufte_time_series(data, x_col: str, y_col: str, fig=None, ax=None,
                            title: str = 'Time Series', y_label: str = 'Value',
                            add_trend: bool = True, add_baseline: bool = True,
                            figsize: Tuple[int, int] = (10, 5),
                            bin_data: bool = False, bin_width: int = 4,
                            sample_size_col: Optional[str] = None) -> Tuple:
    """
    Create a Tufte-inspired time series chart.
    
    Parameters
    ----------
    data : pandas.DataFrame
        DataFrame with time series data
    x_col : str
        Column name for x-axis values (typically time)
    y_col : str
        Column name for y-axis values
    fig : matplotlib.figure.Figure, optional
        Existing figure to use, by default None (creates new figure)
    ax : matplotlib.axes.Axes, optional
        Existing axis to use, by default None (creates new axis)
    title : str, optional
        Chart title, by default 'Time Series'
    y_label : str, optional
        Y-axis label, by default 'Value'
    add_trend : bool, optional
        Whether to add a trend line, by default True
    add_baseline : bool, optional
        Whether to add baseline reference, by default True
    figsize : Tuple[int, int], optional
        Figure size in inches, by default (10, 5)
    
    Returns
    -------
    Tuple
        (fig, ax) - The figure and axis objects
    """
    # Apply Tufte style
    set_tufte_style()
    
    # Create figure and axis if not provided
    if fig is None or ax is None:
        fig, ax = plt.subplots(figsize=figsize, dpi=100)
    
    # Plot line with points
    line = ax.plot(data[x_col], data[y_col], 
                  marker='o', markersize=4, 
                  color=TUFTE_COLORS['primary'], linewidth=1.5, alpha=0.8)[0]
    
    # Add baseline reference if requested
    if add_baseline and len(data) > 0:
        baseline = data[y_col].iloc[0] if not data[y_col].iloc[0] is None else data[y_col].mean()
        add_reference_line(ax, baseline, 'y', TUFTE_COLORS['text_secondary'])
    
    # Add trend line if requested
    if add_trend and len(data) >= 3:
        try:
            from scipy import signal
            # Try to use LOESS/LOWESS smoothing if enough points
            if len(data) >= 8:
                # Window length must be odd and <= data length
                window_length = min(7, len(data) | 1)
                smoothed = signal.savgol_filter(data[y_col], window_length, 2)
                ax.plot(data[x_col], smoothed, color=TUFTE_COLORS['secondary'], 
                       linewidth=1.5, alpha=0.8)
            else:
                # Use simple linear trend for small datasets
                z = np.polyfit(range(len(data)), data[y_col], 1)
                p = np.poly1d(z)
                ax.plot(data[x_col], p(range(len(data))), 
                       color=TUFTE_COLORS['secondary'], linewidth=1.5, alpha=0.8)
        except (ImportError, ValueError):
            # Fallback to simple linear regression
            z = np.polyfit(range(len(data)), data[y_col], 1)
            p = np.poly1d(z)
            ax.plot(data[x_col], p(range(len(data))), 
                   color=TUFTE_COLORS['secondary'], linewidth=1.5, alpha=0.8)
    
    # Style the chart
    style_axis(ax)

    # Set y-axis limits explicitly to 0-85 for visual acuity if applicable
    if "acuity" in y_label.lower() or "ETDRS" in y_label:
        ax.set_ylim(0, 85)

    # Add labels and formatting
    ax.set_title(title, fontsize=14, color=TUFTE_COLORS['text'])
    ax.set_ylabel(y_label, fontsize=10, color=TUFTE_COLORS['text_secondary'])
    
    # Add summary statistics
    mean_val = data[y_col].mean()
    if add_baseline and len(data) > 0:
        baseline = data[y_col].iloc[0]
        add_text_annotation(
            fig, 
            f'Baseline: {baseline:.2f} | Mean: {mean_val:.2f}',
            position='bottom-left'
        )
    else:
        add_text_annotation(fig, f'Mean: {mean_val:.2f}', position='bottom-left')
    
    plt.tight_layout(pad=1.5)
    return fig, ax


def create_tufte_patient_time_visualization(data, time_col='time_weeks', acuity_col='visual_acuity',
                                        sample_size_col='sample_size', title='Mean Visual Acuity by Patient Time',
                                        figsize=(10, 6), bin_width=4):
    """
    Create a Tufte-inspired visual acuity by patient time visualization.

    This visualization shows mean visual acuity by patient time with sample size
    indicated by bar height, eliminating the dilution effect seen in calendar time
    analysis. Time is binned into 4-week periods to match treatment protocols.

    Parameters
    ----------
    data : pandas.DataFrame
        DataFrame with patient time data containing time, acuity, and sample size columns
    time_col : str, optional
        Column name for patient time, by default 'time_weeks'
    acuity_col : str, optional
        Column name for visual acuity, by default 'visual_acuity'
    sample_size_col : str, optional
        Column name for sample size data, by default 'sample_size'
    title : str, optional
        Chart title, by default 'Mean Visual Acuity by Patient Time'
    figsize : tuple, optional
        Figure size in inches, by default (10, 6)
    bin_width : int, optional
        Width of time bins in weeks, by default 4 (aligns with treatment protocol)

    Returns
    -------
    Tuple
        (fig, ax) - The figure and axis objects
    """
    # Apply Tufte style
    set_tufte_style()

    # Create figure and axes
    fig, ax = plt.subplots(figsize=figsize, dpi=100)

    # Group data into bins based on treatment protocol cycles
    if len(data) > 0:
        # Make a copy to avoid modification warnings
        df = data.copy()

        # Create time bins based on protocol intervals
        df['time_bin'] = (df[time_col] // bin_width) * bin_width
        # Calculate bin center for plotting (midpoint of the bin)
        df['bin_center'] = df['time_bin'] + bin_width / 2

        # Group by time bin and calculate mean acuity and total sample size
        binned_data = df.groupby('time_bin').agg({
            acuity_col: 'mean',
            sample_size_col: 'sum' if sample_size_col in df.columns else 'size',
            'bin_center': 'first'  # Take the first bin center
        }).reset_index()

        # Main axis - Visual acuity line plot with markers at bin centers
        line = ax.plot(binned_data['bin_center'], binned_data[acuity_col],
                      marker='o', markersize=5,
                      color=TUFTE_COLORS['primary'], linewidth=1.5, alpha=0.8)[0]

        # Add labels to show which weeks are included in each bin
        for idx, row in binned_data.iterrows():
            bin_start = int(row['time_bin'])
            bin_end = bin_start + bin_width - 1
            ax.annotate(f'W{bin_start}-{bin_end}',
                       xy=(row['bin_center'], -2),
                       xytext=(0, -5),
                       textcoords='offset points',
                       ha='center',
                       va='top',
                       fontsize=7,
                       color=TUFTE_COLORS['text_secondary'],
                       alpha=0.7)

        # Add reference line for baseline visual acuity
        baseline_va = binned_data[acuity_col].iloc[0] if not binned_data[acuity_col].iloc[0] is None else binned_data[acuity_col].mean()
        add_reference_line(ax, baseline_va, 'y', TUFTE_COLORS['text_secondary'])

        # Add trend line if we have enough data points
        if len(binned_data) >= 3:
            try:
                from scipy import signal
                # Use LOESS/LOWESS smoothing if enough points
                if len(binned_data) >= 6:
                    # Window length must be odd and <= data length
                    window_length = min(5, len(binned_data) | 1)  # Ensure odd number
                    smoothed = signal.savgol_filter(binned_data[acuity_col], window_length, 2)
                    # Use different color for trend line since it represents different data than the bars
                    # (line = visual acuity, bars = sample size)
                    ax.plot(binned_data['bin_center'], smoothed,
                           color=TUFTE_COLORS['secondary'],  # Different color for different data
                           linewidth=1.5, alpha=0.8,
                           label='Trend')
                else:
                    # Use simple linear trend for small datasets
                    z = np.polyfit(range(len(binned_data)), binned_data[acuity_col], 1)
                    p = np.poly1d(z)
                    # Use different color for trend line since it represents different data than the bars
                    # (line = visual acuity, bars = sample size)
                    ax.plot(binned_data['bin_center'], p(range(len(binned_data))),
                           color=TUFTE_COLORS['secondary'],  # Different color for different data
                           linewidth=1.5, alpha=0.8,
                           label='Trend')
            except (ImportError, ValueError):
                # Fallback to simple linear regression
                z = np.polyfit(range(len(binned_data)), binned_data[acuity_col], 1)
                p = np.poly1d(z)
                # Use different color for trend line since it represents different data than the bars
                # (line = visual acuity, bars = sample size)
                ax.plot(binned_data['bin_center'], p(range(len(binned_data))),
                       color=TUFTE_COLORS['secondary'],  # Different color for different data
                       linewidth=1.5, alpha=0.8,
                       label='Trend')

        # Create secondary axis for sample size bars if sample size data is provided
        if sample_size_col in data.columns:
            # Second y-axis for sample size
            ax2 = ax.twinx()

            # Plot sample size as subtle bars with width matching bin width
            bars = ax2.bar(binned_data['bin_center'], binned_data[sample_size_col],
                          alpha=0.15, color=TUFTE_COLORS['primary'], edgecolor='none',
                          width=bin_width * 0.8)  # Slightly narrower than bin width

            # Style secondary axis
            ax2.spines['top'].set_visible(False)
            ax2.spines['right'].set_visible(False)
            ax2.grid(False)
            ax2.tick_params(axis='y', colors=TUFTE_COLORS['text_secondary'])
            ax2.set_ylabel('Sample Size', color=TUFTE_COLORS['text_secondary'], fontsize=9)

    # Style the main axis
    style_axis(ax)

    # Set y-axis limits explicitly to 0-85 for visual acuity
    ax.set_ylim(0, 85)

    # Add labels and formatting
    ax.set_title(title, fontsize=14, color=TUFTE_COLORS['text'])
    ax.set_xlabel(f'Weeks Since Enrollment (grouped in {bin_width}-week intervals)',
                 fontsize=10, color=TUFTE_COLORS['text_secondary'])
    ax.set_ylabel('Visual Acuity (ETDRS letters)', fontsize=10, color=TUFTE_COLORS['text_secondary'])

    # Add explanation text about binning
    add_text_annotation(
        fig,
        f'Data binned in {bin_width}-week intervals to align with treatment protocol cycles',
        position='bottom-left',
        fontsize=8
    )

    plt.tight_layout(pad=1.5)
    return fig, ax