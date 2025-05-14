"""
Clean nested bar chart implementation for discontinuation and retreatment visualization.

This module provides a simple and clear implementation of a nested bar chart
where segments (retreated and not retreated) are shown inside a light grey
background bar representing the total.

Features:
- Grey background bar for total count
- Blue (retreated) and sage green (not retreated) segments
- Log scale option for better display of disparate sizes
- Small sample warning for categories below threshold
- Clean, Tufte-inspired styling
"""
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from typing import Tuple, Optional, List, Dict, Union

# Import the central color system if available
try:
    from visualization.color_system import COLORS, SEMANTIC_COLORS, ALPHAS
except ImportError:
    # Fallback if the central color system is not available
    COLORS = {
        'primary': '#4682B4',    # Steel Blue for acuity data
        'secondary': '#B22222',  # Firebrick for critical information
        'patient_counts': '#8FAD91',  # Muted Sage Green for patient counts
    }
    ALPHAS = {
        'high': 0.8,        # High opacity for primary elements
        'medium': 0.5,      # Medium opacity for standard elements
        'low': 0.2,         # Low opacity for background elements
        'very_low': 0.1,    # Very low opacity for subtle elements
        'patient_counts': 0.35  # Opacity for patient count visualizations
    }
    SEMANTIC_COLORS = {
        'acuity_data': COLORS['primary'],       # Blue for visual acuity data
        'patient_counts': COLORS['patient_counts'],  # Sage Green for patient counts
        'critical_info': COLORS['secondary'],   # Red for critical information
    }

def create_discontinuation_retreatment_chart(
    data: pd.DataFrame,
    title: str = "Discontinuation Reasons and Retreatment Status",
    figsize: Tuple[int, int] = (10, 6),
    use_log_scale: bool = True,
    sort_by_total: bool = True,
    small_sample_threshold: int = 10
) -> Tuple[plt.Figure, plt.Axes]:
    """
    Create a clean nested bar chart showing discontinuation reasons with retreatment status.
    
    Parameters
    ----------
    data : pd.DataFrame
        DataFrame containing columns:
        - reason: Discontinuation reason
        - retreated: Boolean indicating retreatment status
        - count: Number of patients in each category
    title : str, optional
        Plot title, by default "Discontinuation Reasons and Retreatment Status"
    figsize : Tuple[int, int], optional
        Figure size in inches, by default (10, 6)
    use_log_scale : bool, optional
        Whether to use a logarithmic scale for the count axis, by default True
    sort_by_total : bool, optional
        Whether to sort categories by total count (descending), by default True
    small_sample_threshold : int, optional
        Threshold for marking categories with small sample sizes, by default 10
        
    Returns
    -------
    Tuple[plt.Figure, plt.Axes]
        The created figure and axes objects for further customization
    """
    # Calculate totals for each category
    totals = data.groupby('reason')['count'].sum().reset_index()
    
    # Sort by total count if requested
    if sort_by_total:
        totals = totals.sort_values('count', ascending=False)
    
    reasons = totals['reason'].tolist()
    reason_totals = totals['count'].tolist()
    
    # Set up plot
    fig, ax = plt.subplots(figsize=figsize)
    
    # Use log scale if requested
    if use_log_scale:
        ax.set_yscale('log')
        
        # Set y-axis limits for log scale to start just below the smallest value
        smallest_value = min([count for count in data['count'] if count > 0])
        ax.set_ylim(bottom=max(0.9, smallest_value * 0.5))  # Start at 0.9 or half of smallest value
        
        # Add grid for better readability with log scale
        ax.grid(True, axis='y', linestyle='--', alpha=0.3, color='#cccccc')
    
    # Define colors
    bg_color = '#E0E0E0'  # Light grey for background bars
    retreated_color = SEMANTIC_COLORS['acuity_data']  # Blue for retreated
    not_retreated_color = SEMANTIC_COLORS['patient_counts']  # Sage green for not retreated
    
    # Set up positions
    x = np.arange(len(reasons))
    bar_width = 0.75  # Width of the background (total) bar

    # For the segments, use a narrower width with spacing between them
    segment_width = bar_width * 0.4  # Each segment takes 40% of total width
    segment_spacing = bar_width * 0.1  # 10% spacing between segments

    # Draw background bars for totals
    bg_bars = ax.bar(x, reason_totals, width=bar_width, color=bg_color,
                    edgecolor='none', alpha=0.8, zorder=1)

    # Add retreated and not retreated segments
    for i, reason in enumerate(reasons):
        # Get data for this reason
        retreated_count = data[(data['reason'] == reason) & (data['retreated'] == True)]['count'].sum()
        not_retreated_count = data[(data['reason'] == reason) & (data['retreated'] == False)]['count'].sum()

        # Position segments inside the total bar with proper spacing
        # For retreated (left segment)
        left_pos = x[i] - (segment_width + segment_spacing/2)
        # For not retreated (right segment)
        right_pos = x[i] + segment_spacing/2
        
        # Draw retreated segment (blue)
        if retreated_count > 0:
            ax.bar(left_pos, retreated_count, width=segment_width, color=retreated_color,
                   edgecolor='white', linewidth=0.5, zorder=2,
                   label='Retreated' if i == 0 else None)

            # Add value label inside retreated segment
            ax.text(left_pos, retreated_count/2, str(retreated_count),
                   ha='center', va='center',
                   color='white' if retreated_count >= 50 else 'black',
                   fontweight='bold')

        # Draw not retreated segment (sage green)
        if not_retreated_count > 0:
            ax.bar(right_pos, not_retreated_count, width=segment_width, color=not_retreated_color,
                   edgecolor='white', linewidth=0.5, zorder=2,
                   label='Not Retreated' if i == 0 else None)

            # Add value label inside not retreated segment
            ax.text(right_pos, not_retreated_count/2, str(not_retreated_count),
                   ha='center', va='center',
                   color='white' if not_retreated_count >= 50 else 'black',
                   fontweight='bold')
        
        # Add reason and total above each bar
        if use_log_scale:
            # For log scale, position labels at a fixed height above the maximum value
            label_y = max(retreated_count, not_retreated_count) * 2.0 if max(retreated_count, not_retreated_count) > 0 else 1
        else:
            # For linear scale, position labels a fixed distance above the bar
            label_y = reason_totals[i] + (max(reason_totals) * 0.05)
            
        ax.text(x[i], label_y, f'{reason}\n{reason_totals[i]}', 
                ha='center', va='bottom', fontweight='bold')
    
    # Add small sample warning for categories with fewer than threshold patients
    for i, total in enumerate(reason_totals):
        if total < small_sample_threshold:
            # Position warning based on scale
            if use_log_scale:
                # For log scale, position at a fixed height
                warning_y = 1.2
            else:
                # For linear scale, position relative to bar height
                warning_y = total * 0.1
                
            ax.text(x[i], warning_y, 'Small sample', 
                   ha='center', va='center',
                   color='#D81B60', fontsize=8, fontweight='bold',
                   bbox=dict(facecolor='white', alpha=0.9, pad=2, 
                            boxstyle='round,pad=0.3', edgecolor='#D81B60', linewidth=1),
                   zorder=10)
    
    # Configure axes
    ax.set_xticks([])  # Hide x-ticks since we have labels directly on the bars
    ax.set_ylabel('Number of Patients (log scale)' if use_log_scale else 'Number of Patients')
    ax.set_title(title)
    ax.legend(loc='upper right')
    
    # Remove spines
    for spine in ['top', 'right', 'bottom']:
        ax.spines[spine].set_visible(False)
    
    # Add retreatment rate at the bottom
    total_patients = data['count'].sum()
    retreated_patients = data[data['retreated'] == True]['count'].sum()
    retreatment_rate = (retreated_patients / total_patients) * 100
    fig.text(0.5, 0.01, f'Overall retreatment rate: {retreatment_rate:.1f}%', 
             ha='center', va='bottom', fontsize=10)
    
    # Adjust layout to make room for retreatment rate text
    plt.tight_layout(rect=[0, 0.05, 1, 0.95])
    
    return fig, ax

# Backward compatibility alias
create_nested_discontinuation_chart = create_discontinuation_retreatment_chart