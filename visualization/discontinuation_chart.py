"""
Module implementing a nested bar chart for discontinuation and retreatment visualization.

This visualization combines discontinuation reasons and retreatment status into a unified
chart with stacked segments and optional log scale.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

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

def create_discontinuation_retreatment_chart(data, fig=None, ax=None, 
                                            title="Discontinuation Reasons and Retreatment Status",
                                            figsize=(10, 6), use_log_scale=True,
                                            sort_by_total=True, small_sample_threshold=10):
    """
    Create a Tufte-inspired visualization showing discontinuation reasons with retreatment status.
    
    This chart combines discontinuation reasons and retreatment status into a unified visualization
    using a nested bar approach with optional log scale:
    - Grey rectangle shows total discontinued patients for each reason
    - Blue segments show retreated patients for each discontinuation type
    - Sage green segments show non-retreated patients for each discontinuation type
    - Log scale option for better visualization when counts vary widely
    
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
        Figure size (width, height) in inches, by default (10, 6)
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
    
    x = np.arange(len(reasons))
    bar_width = 0.75
    
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
    
    # Draw bars
    for i, (reason, total) in enumerate(zip(reasons, total_counts)):
        # Draw total bar as background (light grey, wider)
        total_bar = ax.bar(i, total, width=bar_width*1.2, 
                color=TUFTE_COLORS['grid'], alpha=0.3, zorder=1,
                edgecolor='none', label='Total' if i == 0 else "")
        
        # Get counts for this reason
        retreated_count = retreated_counts[i]
        not_retreated_count = not_retreated_counts[i]
        
        # Draw the segments as stacked bars
        if retreated_count > 0:
            retreated_bar = ax.bar(i, retreated_count, width=bar_width, 
                    color=SEMANTIC_COLORS['acuity_data'], alpha=ALPHAS['medium'], 
                    zorder=2, label='Retreated' if i == 0 else "")
        
        if not_retreated_count > 0:
            not_retreated_bar = ax.bar(i, not_retreated_count, width=bar_width,
                    bottom=retreated_count, 
                    color=SEMANTIC_COLORS['patient_counts'], alpha=ALPHAS['patient_counts'], 
                    zorder=2, label='Not Retreated' if i == 0 else "")
    
    # Add percentage labels on each segment
    for i, (r_count, nr_count) in enumerate(zip(retreated_counts, not_retreated_counts)):
        total = r_count + nr_count
        if total > 0:
            # Retreated percentage
            r_pct = r_count / total * 100
            if r_count > 0:
                # Position label properly based on scale
                y_pos = r_count/2 if not use_log_scale or r_count > 1 else 2
                
                ax.annotate(f'{r_pct:.1f}%', 
                        xy=(i, y_pos),
                        ha='center', va='center',
                        color='white' if r_pct > 15 else TUFTE_COLORS['text'],
                        fontweight='bold' if r_pct < 15 else 'normal')
            
            # Not retreated percentage
            nr_pct = nr_count / total * 100
            if nr_count > 0:
                # Position in the middle of the not-retreated segment
                if use_log_scale:
                    nr_mid_y = max(r_count + nr_count/2, 2) if r_count > 0 else max(nr_count/2, 2)
                else:
                    nr_mid_y = r_count + nr_count/2
                
                ax.annotate(f'{nr_pct:.1f}%', 
                        xy=(i, nr_mid_y),
                        ha='center', va='center',
                        color='white' if nr_pct > 15 else TUFTE_COLORS['text'],
                        fontweight='bold' if nr_pct < 15 else 'normal')
    
    # Add styling
    style_axis(ax)
    
    # Add total counts above each bar
    for i, total in enumerate(total_counts):
        # For log scale, be careful with annotation placement
        y_pos = total * 1.2 if use_log_scale else total + (max(total_counts) * 0.02)
        ax.annotate(f'n={total}',
                xy=(i, y_pos),
                ha='center', va='bottom',
                color=TUFTE_COLORS['text_secondary'],
                fontsize=9)
    
    # Add small sample size warning where appropriate
    for i, total in enumerate(total_counts):
        if total < small_sample_threshold:  # Threshold for statistical reliability warning
            # Position based on scale type
            y_pos = 1.5 if use_log_scale else total/2
            try:
                ax.annotate('⚠ Small sample',
                        xy=(i, y_pos),
                        ha='center', va='bottom',
                        color=TUFTE_COLORS['secondary'],
                        fontsize=8,
                        fontweight='bold')
            except:
                # Fallback if warning symbol doesn't work
                ax.annotate('! Small sample',
                        xy=(i, y_pos),
                        ha='center', va='bottom',
                        color=TUFTE_COLORS['secondary'],
                        fontsize=8,
                        fontweight='bold')
    
    # Add labels and formatting
    ax.set_title(title, fontsize=14, color=TUFTE_COLORS['text'])
    y_label = 'Number of patients (log scale)' if use_log_scale else 'Number of patients'
    ax.set_ylabel(y_label, fontsize=10, color=TUFTE_COLORS['text_secondary'])
    ax.set_xticks(x)
    ax.set_xticklabels([f"{reason}\n(n={total})" for reason, total in zip(reasons, total_counts)])
    
    # Add a legend
    ax.legend(frameon=False, loc='upper right')
    
    # Add reference line for overall average retreatment rate
    total_retreated = sum(retreated_counts)
    total_patients = sum(total_counts)
    if total_patients > 0:
        overall_rate = total_retreated / total_patients * 100
        fig.text(0.5, 0.01,
               f'Overall retreatment rate: {overall_rate:.1f}%',
               ha='center', va='bottom',
               color=TUFTE_COLORS['text_secondary'],
               fontsize=9)
    
    # Add description
    scale_desc = "(log scale)" if use_log_scale else ""
    fig.text(0.02, 0.02, 
            f"Bar height shows patient count {scale_desc}. Blue segments show patients who retreated;\nsage green segments show patients who did not retreat after discontinuation.",
            fontsize=8, color=TUFTE_COLORS['text_secondary'])
    
    fig.tight_layout(pad=1.5)
    return fig, ax