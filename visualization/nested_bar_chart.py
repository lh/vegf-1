"""
Module implementing a true nested bar chart for discontinuation and retreatment visualization.

This visualization combines discontinuation reasons and retreatment status into a unified
chart with segments inside a total bar and optional log scale.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Import our centralized styling systems if available
try:
    from visualization.color_system import COLORS, SEMANTIC_COLORS, ALPHAS
    from streamlit_app.utils.tufte_style import (
        set_tufte_style, style_axis, TUFTE_COLORS
    )
except ImportError:
    # Fallback definitions if imports fail
    TUFTE_COLORS = {
        'primary': '#4682B4',    # Steel Blue
        'grid': '#EEEEEE',       # Very light gray
        'text': '#333333',       # Dark gray
        'text_secondary': '#666666',  # Medium gray
        'secondary': '#B22222',  # Firebrick red
    }
    SEMANTIC_COLORS = {
        'acuity_data': '#4682B4',       # Steel Blue
        'patient_counts': '#8FAD91',    # Sage Green
    }
    ALPHAS = {
        'medium': 0.5,
        'patient_counts': 0.35,
    }
    
    def set_tufte_style():
        plt.style.use('seaborn-v0_8-whitegrid')
        plt.rcParams['axes.spines.top'] = False
        plt.rcParams['axes.spines.right'] = False
    
    def style_axis(ax):
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)

def create_nested_discontinuation_chart(data, fig=None, ax=None, 
                                       title="Discontinuation Reasons and Retreatment Status",
                                       figsize=(12, 6), use_log_scale=True,
                                       sort_by_total=True, small_sample_threshold=10):
    """
    Create a Tufte-inspired visualization showing discontinuation reasons with retreatment status
    using true nested bars with segments inside a total bar.
    
    Parameters
    ----------
    data : pandas.DataFrame
        DataFrame with columns:
        - 'reason': Discontinuation reason (Administrative, Planned, etc.)
        - 'retreated': Boolean or numeric (1/0) indicating retreatment
        - 'count': Number of patients
    fig : matplotlib.figure.Figure, optional
        Existing figure to use, by default None
    ax : matplotlib.axes.Axes, optional
        Existing axis to use, by default None
    title : str, optional
        Chart title, by default "Discontinuation Reasons and Retreatment Status"
    figsize : tuple, optional
        Figure size (width, height) in inches, by default (12, 6)
    use_log_scale : bool, optional
        Whether to use a logarithmic y-axis scale, by default True
    sort_by_total : bool, optional
        Whether to sort categories by total count (descending), by default True
    small_sample_threshold : int, optional
        Threshold below which to show a small sample warning, by default 10
        
    Returns
    -------
    tuple
        (fig, ax) - Figure and axes objects
    """
    # Apply Tufte style
    set_tufte_style()
    
    # Create figure and axes if not provided
    if fig is None or ax is None:
        fig, ax = plt.subplots(figsize=figsize, dpi=100)
    
    # Remove all axes spines
    for spine in ax.spines.values():
        spine.set_visible(False)
    
    # Prepare data
    # Calculate total for each reason
    totals = data.groupby('reason')['count'].sum().reset_index()
    
    # Calculate counts for retreated and not retreated
    retreated = data[data['retreated'] == True].groupby('reason')['count'].sum().reset_index()
    not_retreated = data[data['retreated'] == False].groupby('reason')['count'].sum().reset_index()
    
    # Set up plotting parameters
    reasons = totals['reason'].tolist()
    
    # Sort reasons by total count if requested
    if sort_by_total:
        order_idx = np.argsort(-totals['count'].values)
        reasons = [reasons[i] for i in order_idx]
    
    # Prepare ordered counts
    total_counts = []
    retreated_counts = []
    not_retreated_counts = []
    
    for reason in reasons:
        total_counts.append(totals[totals['reason'] == reason]['count'].values[0])
        
        # Get retreated count, defaulting to 0 if not found
        r_count = 0
        if reason in retreated['reason'].values:
            r_count = retreated[retreated['reason'] == reason]['count'].values[0]
        retreated_counts.append(r_count)
        
        # Get not retreated count, defaulting to 0 if not found
        nr_count = 0
        if reason in not_retreated['reason'].values:
            nr_count = not_retreated[not_retreated['reason'] == reason]['count'].values[0]
        not_retreated_counts.append(nr_count)
    
    # Set log scale if requested
    if use_log_scale:
        ax.set_yscale('log')
        ax.set_ylim(bottom=1)  # Start at 1 to avoid log(0) issues
    
    # Create a bar chart with columns for each region
    num_categories = len(reasons)
    bar_width = 0.8  # Width of each group of bars
    group_width = 0.9  # Total width for all segments within a group
    
    # Calculate x positions
    x = np.arange(num_categories)
    
    # Draw light grey background bars for totals
    bg_bars = ax.bar(x, total_counts, width=bar_width, 
                    color='#E0E0E0', edgecolor='none', alpha=0.8, zorder=1)
    
    # Calculate segment widths, ensuring they all add up to group_width * bar_width
    seg_width = group_width * bar_width / 2  # Up to 2 segments (retreated and not retreated)
    
    # Add value labels for each total
    for i, total in enumerate(total_counts):
        category_name = reasons[i]
        
        # Add the category name and total above each bar
        if use_log_scale:
            label_y = total * 1.3
        else:
            label_y = total + (max(total_counts) * 0.05)
            
        ax.text(x[i], label_y,
                f"{category_name}\n{total:,}",
                ha='center', va='bottom',
                fontsize=11, color=TUFTE_COLORS['text'],
                fontweight='bold')
    
    # Add segment bars for retreated and non-retreated
    for i in range(num_categories):
        # Calculate positions for segments
        retreated_count = retreated_counts[i]
        not_retreated_count = not_retreated_counts[i]
        
        # Left segment position (retreated)
        retreated_x = x[i] - seg_width/2
        
        # Right segment position (not retreated)
        not_retreated_x = x[i] + seg_width/2
        
        # Add the retreated segment (blue)
        if retreated_count > 0:
            retreated_bar = ax.bar(retreated_x, retreated_count, width=seg_width,
                                  color=SEMANTIC_COLORS['acuity_data'], 
                                  edgecolor='white', linewidth=0.5,
                                  label='Retreated' if i == 0 else "")
            
            # Add value label
            ax.text(retreated_x, retreated_count/2,
                   f"{retreated_count:,}",
                   ha='center', va='center',
                   color='white' if retreated_count / total_counts[i] > 0.3 else TUFTE_COLORS['text'],
                   fontsize=10, fontweight='bold')
        
        # Add the not retreated segment (sage green)
        if not_retreated_count > 0:
            not_retreated_bar = ax.bar(not_retreated_x, not_retreated_count, width=seg_width,
                                      color=SEMANTIC_COLORS['patient_counts'],
                                      edgecolor='white', linewidth=0.5,
                                      label='Not Retreated' if i == 0 else "")
            
            # Add value label
            ax.text(not_retreated_x, not_retreated_count/2,
                   f"{not_retreated_count:,}",
                   ha='center', va='center',
                   color='white' if not_retreated_count / total_counts[i] > 0.3 else TUFTE_COLORS['text'],
                   fontsize=10, fontweight='bold')
    
    # Add small sample size warning where appropriate
    for i, total in enumerate(total_counts):
        if total < small_sample_threshold:  # Threshold for statistical reliability warning
            # Position based on scale type
            y_pos = 1.5 if use_log_scale else total * 0.5
            # Use plain text to avoid font issues
            ax.text(x[i], y_pos, 'Small sample',
                   ha='center', va='bottom',
                   color=TUFTE_COLORS['secondary'],
                   fontsize=8, fontweight='bold',
                   bbox=dict(facecolor='white', alpha=0.7, pad=2, boxstyle='round,pad=0.2'))
    
    # Add legend directly at the top of the chart
    legend_colors = [
        patches.Patch(facecolor=SEMANTIC_COLORS['acuity_data'], label='Retreated'),
        patches.Patch(facecolor=SEMANTIC_COLORS['patient_counts'], label='Not Retreated')
    ]
    ax.legend(handles=legend_colors, loc='upper center', frameon=False,
             bbox_to_anchor=(0.5, 1.05), ncol=2)
    
    # Setting up the axes
    ax.set_title(title, fontsize=14, fontweight='bold', color=TUFTE_COLORS['text'])
    
    # Set y-axis label
    y_label = 'Number of patients (log scale)' if use_log_scale else 'Number of patients'
    ax.set_ylabel(y_label, fontsize=10, color=TUFTE_COLORS['text_secondary'])
    
    # Configure x-axis
    ax.set_xticks([])  # Remove x-ticks since we have labels on the bars
    
    # Add reference line for overall average retreatment rate
    total_retreated = sum(retreated_counts)
    total_patients = sum(total_counts)
    if total_patients > 0:
        overall_rate = total_retreated / total_patients * 100
        fig.text(0.5, 0.01,
               f"Overall retreatment rate: {overall_rate:.1f}%",
               ha='center', va='bottom',
               color=TUFTE_COLORS['text_secondary'],
               fontsize=9)
    
    # Set grid for y-axis only
    ax.grid(axis='y', linestyle='--', alpha=0.3, color='#cccccc')
    
    # Use figure adjustments instead of tight_layout to avoid warnings
    plt.subplots_adjust(left=0.1, right=0.9, top=0.85, bottom=0.15)
    return fig, ax


def create_discontinuation_retreatment_chart(data, fig=None, ax=None, 
                                            title="Discontinuation Reasons and Retreatment Status",
                                            figsize=(12, 6), use_log_scale=True,
                                            sort_by_total=True, small_sample_threshold=10):
    """
    Convenience function to match the interface from the old chart.
    Simply calls through to the new implementation.
    """
    return create_nested_discontinuation_chart(data, fig, ax, title, figsize, 
                                              use_log_scale, sort_by_total, 
                                              small_sample_threshold)