"""Tufte-compliant visualization for treatment intervals.

This module provides a clean, minimalist visualization for treatment interval data
that follows Tufte's principles of data-ink ratio and clarity.
"""

import plotly.graph_objects as go
import pandas as pd
import numpy as np
from typing import Optional, Tuple


def create_interval_distribution_tufte(intervals: np.ndarray, 
                                     bin_width: Optional[int] = None) -> go.Figure:
    """
    Create a Tufte-compliant histogram for treatment intervals.
    
    Key features:
    - Automatic bin width calculation based on data
    - Minimal chart junk
    - Direct labeling of notable values
    - Appropriate scale for sparse data
    
    Args:
        intervals: Array of interval values in days
        bin_width: Optional bin width in days (auto-calculated if None)
        
    Returns:
        Plotly figure object
    """
    if len(intervals) == 0:
        return _create_empty_figure("No interval data available")
    
    # Calculate appropriate bin width if not provided
    if bin_width is None:
        # Use Freedman-Diaconis rule for bin width
        q75, q25 = np.percentile(intervals, [75, 25])
        iqr = q75 - q25
        if iqr > 0:
            bin_width = 2 * iqr / (len(intervals) ** (1/3))
            # Round to nearest 7 days for weekly bins
            bin_width = max(7, int(np.round(bin_width / 7) * 7))
        else:
            bin_width = 7  # Default to weekly bins
    
    # Create bins
    min_val = int(np.floor(intervals.min() / bin_width) * bin_width)
    max_val = int(np.ceil(intervals.max() / bin_width) * bin_width)
    bins = np.arange(min_val, max_val + bin_width, bin_width)
    
    # Calculate histogram
    counts, bin_edges = np.histogram(intervals, bins=bins)
    
    # Find non-zero bins for a cleaner display
    non_zero_mask = counts > 0
    if non_zero_mask.any():
        first_non_zero = non_zero_mask.argmax()
        last_non_zero = len(non_zero_mask) - non_zero_mask[::-1].argmax() - 1
        
        # Include one empty bin on each side for context
        start_idx = max(0, first_non_zero - 1)
        end_idx = min(len(counts), last_non_zero + 2)
        
        counts = counts[start_idx:end_idx]
        bin_edges = bin_edges[start_idx:end_idx + 1]
    
    # Create bar positions and widths
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
    
    # Create the figure
    fig = go.Figure()
    
    # Add bars
    fig.add_trace(go.Bar(
        x=bin_centers,
        y=counts,
        width=bin_width * 0.8,  # Slight gap between bars
        marker_color='#5B8FA3',  # Muted blue-gray
        marker_line_width=0,  # No borders for cleaner look
        hovertemplate='%{x:.0f} days: %{y} intervals<extra></extra>',
        showlegend=False
    ))
    
    # Add direct labels for significant bars
    if len(counts) > 0 and counts.max() > 0:
        threshold = counts.max() * 0.1  # Label bars with >10% of max count
    else:
        threshold = 0
    for i, (center, count) in enumerate(zip(bin_centers, counts)):
        if count > threshold:
            fig.add_annotation(
                x=center,
                y=count,
                text=str(int(count)),
                showarrow=False,
                yshift=10,
                font=dict(size=11, color='#444444')
            )
    
    # Calculate summary statistics for annotation
    mean_interval = np.mean(intervals)
    median_interval = np.median(intervals)
    
    # Update layout for Tufte style
    fig.update_layout(
        title=dict(
            text='Distribution of Treatment Intervals',
            font=dict(size=16, color='#333333'),
            x=0,
            xanchor='left'
        ),
        xaxis=dict(
            title=dict(
                text='Interval (days)',
                font=dict(size=14)
            ),
            showgrid=False,
            showline=True,
            linewidth=1,
            linecolor='#333333',
            tickfont=dict(size=12),
            # Set range to show only relevant data
            range=[bin_edges[0] - bin_width/2, bin_edges[-1] + bin_width/2]
        ),
        yaxis=dict(
            title=dict(
                text='Count',
                font=dict(size=14)
            ),
            showgrid=False,
            showline=True,
            linewidth=1,
            linecolor='#333333',
            tickfont=dict(size=12),
            rangemode='tozero'
        ),
        plot_bgcolor='white',
        paper_bgcolor='white',
        margin=dict(l=60, r=40, t=60, b=60),
        height=350  # Compact height for better data density
    )
    
    # Add summary annotation
    fig.add_annotation(
        text=f"Mean: {mean_interval:.1f} days | Median: {median_interval:.1f} days",
        xref="paper", yref="paper",
        x=0.99, y=0.99,
        xanchor="right", yanchor="top",
        showarrow=False,
        font=dict(size=12, color='#666666'),
        bgcolor="rgba(255,255,255,0.8)",
        borderpad=4
    )
    
    return fig


def create_interval_summary_table(intervals_df: pd.DataFrame) -> go.Figure:
    """
    Create a clean summary table for interval statistics.
    
    Args:
        intervals_df: DataFrame with interval data
        
    Returns:
        Plotly figure with a formatted table
    """
    intervals = intervals_df['interval_days'].values
    
    # Calculate statistics
    stats = {
        'Statistic': ['Count', 'Mean', 'Median', 'Std Dev', 'Min', 'Max', '25th %ile', '75th %ile'],
        'Value': [
            f"{len(intervals):,}",
            f"{np.mean(intervals):.1f} days",
            f"{np.median(intervals):.1f} days",
            f"{np.std(intervals):.1f} days",
            f"{np.min(intervals):.0f} days",
            f"{np.max(intervals):.0f} days",
            f"{np.percentile(intervals, 25):.0f} days",
            f"{np.percentile(intervals, 75):.0f} days"
        ]
    }
    
    fig = go.Figure(data=[go.Table(
        header=dict(
            values=list(stats.keys()),
            fill_color='#f0f0f0',
            align='left',
            font=dict(size=12, color='#333333'),
            height=30
        ),
        cells=dict(
            values=list(stats.values()),
            fill_color='white',
            align='left',
            font=dict(size=11, color='#555555'),
            height=25
        )
    )])
    
    fig.update_layout(
        title=dict(
            text='Treatment Interval Statistics',
            font=dict(size=14, color='#333333'),
            x=0,
            xanchor='left'
        ),
        margin=dict(l=0, r=0, t=40, b=0),
        height=280,
        paper_bgcolor='white'
    )
    
    return fig


def _create_empty_figure(message: str) -> go.Figure:
    """Create an empty figure with a message."""
    fig = go.Figure()
    
    fig.add_annotation(
        x=0.5, y=0.5,
        xref="paper", yref="paper",
        text=message,
        showarrow=False,
        font=dict(size=14, color='#666666')
    )
    
    fig.update_layout(
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        plot_bgcolor='white',
        paper_bgcolor='white',
        height=300
    )
    
    return fig