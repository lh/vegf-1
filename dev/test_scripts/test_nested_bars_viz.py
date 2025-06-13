"""
Test script for the nested bar chart version of the discontinuation-retreatment visualization.
This implements true nested bars with a log scale to better handle size differences.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# Import our visualization modules if available
try:
    from visualization.color_system import COLORS, SEMANTIC_COLORS, ALPHAS
    from streamlit_app.utils.tufte_style import set_tufte_style, style_axis, TUFTE_COLORS
except ImportError:
    # Fallback if imports fail
    TUFTE_COLORS = {
        'primary': '#4682B4',    # Steel Blue - for visual acuity data
        'primary_dark': '#2a4d6e', # Darker Steel Blue - for acuity trend lines
        'secondary': '#B22222',  # Firebrick - for critical information
        'tertiary': '#228B22',   # Forest Green - for additional data series
        'patient_counts': '#8FAD91',  # Muted Sage Green - for patient/sample counts
        'patient_counts_dark': '#5e7260', # Darker Sage Green - for patient count trend lines
        'background': '#FFFFFF', # White background
        'grid': '#EEEEEE',       # Very light gray for grid lines
        'text': '#333333',       # Dark gray for titles and labels
        'text_secondary': '#666666',  # Medium gray for secondary text
        'border': '#CCCCCC'      # Light gray for necessary borders
    }
    SEMANTIC_COLORS = {
        'acuity_data': TUFTE_COLORS['primary'],
        'acuity_trend': TUFTE_COLORS['primary_dark'],
        'patient_counts': TUFTE_COLORS['patient_counts'],
        'patient_counts_trend': TUFTE_COLORS['patient_counts_dark'],
        'critical_info': TUFTE_COLORS['secondary'],
        'additional_series': TUFTE_COLORS['tertiary']
    }
    ALPHAS = {
        'high': 0.8,
        'medium': 0.5,
        'low': 0.2,
        'very_low': 0.1,
        'patient_counts': 0.35
    }
    
    def set_tufte_style():
        # Basic matplotlib style settings
        plt.style.use('seaborn-v0_8-whitegrid')
        plt.rcParams['axes.spines.top'] = False
        plt.rcParams['axes.spines.right'] = False
        
    def style_axis(ax):
        # Hide top and right spines
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        # Make left spine invisible but keep ticks
        ax.spines['left'].set_visible(False)
        ax.tick_params(left=True, which='both')

def create_nested_discontinuation_retreatment_chart(data, fig=None, ax=None, 
                                                  title="Discontinuation Reasons and Retreatment Status",
                                                  figsize=(10, 6)):
    """
    Create a true nested bar chart showing discontinuation reasons and retreatment status.
    Uses a log scale to better handle wide differences in category sizes.
    
    Parameters
    ----------
    data : pandas.DataFrame
        DataFrame with columns:
        - 'reason': Discontinuation reason (Administrative, Planned, etc.)
        - 'retreated': Boolean or numeric (1/0) indicating retreatment
        - 'count': Number of patients
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
    x = np.arange(len(reasons))
    bar_width = 0.75
    
    # Order reasons by total count (descending)
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
    
    # Draw bars with true nesting (stacked within the total)
    for i, (reason, total) in enumerate(zip(reasons, total_counts)):
        # Draw total bar as background (light grey, wider)
        total_bar = ax.bar(i, total, width=bar_width*1.2, 
                color=TUFTE_COLORS['grid'], alpha=0.3, zorder=1,
                edgecolor='none', label='Total' if i == 0 else "")
        
        # Calculate heights for stacked segments
        retreated_count = retreated_counts[i]
        not_retreated_count = not_retreated_counts[i]
        
        # Draw segments as percentages of total within the bar
        # Retreated segment (bottom)
        if retreated_count > 0:
            retreated_bar = ax.bar(i, retreated_count, width=bar_width, 
                    color=SEMANTIC_COLORS['acuity_data'], alpha=ALPHAS['medium'], 
                    zorder=2, label='Retreated' if i == 0 else "")
        
        # Non-retreated segment (on top)
        if not_retreated_count > 0:
            not_retreated_bar = ax.bar(i, not_retreated_count, width=bar_width,
                    color=SEMANTIC_COLORS['patient_counts'], alpha=ALPHAS['patient_counts'], 
                    zorder=2, bottom=retreated_count, label='Not Retreated' if i == 0 else "")
    
    # Set log scale for y-axis
    ax.set_yscale('log')
    ax.set_ylim(bottom=1)  # Start at 1 to avoid log(0) issues
    
    # Add percentage labels on each segment
    for i, (r_count, nr_count) in enumerate(zip(retreated_counts, not_retreated_counts)):
        total = r_count + nr_count
        if total > 0:
            # Retreated percentage
            r_pct = r_count / total * 100
            if r_count > 0:
                # Position in the middle of the retreated segment
                ax.annotate(f'{r_pct:.1f}%', 
                        xy=(i, r_count/2 if r_count > 1 else 2),  # Adjust for log scale
                        ha='center', va='center',
                        color='white' if r_pct > 15 else TUFTE_COLORS['text'],
                        fontweight='bold' if r_pct < 15 else 'normal')
            
            # Not retreated percentage
            nr_pct = nr_count / total * 100
            if nr_count > 0:
                # Position in the middle of the not-retreated segment
                nr_mid_y = r_count + nr_count/2
                ax.annotate(f'{nr_pct:.1f}%', 
                        xy=(i, nr_mid_y if nr_mid_y > 1 else 2),  # Adjust for log scale
                        ha='center', va='center',
                        color='white' if nr_pct > 15 else TUFTE_COLORS['text'],
                        fontweight='bold' if nr_pct < 15 else 'normal')
    
    # Add styling
    style_axis(ax)
    
    # Add total counts above each bar
    for i, total in enumerate(total_counts):
        # For log scale, be careful with annotation placement
        y_pos = total * 1.2  # 20% above the bar on log scale
        ax.annotate(f'n={total}',
                xy=(i, y_pos),
                ha='center', va='bottom',
                color=TUFTE_COLORS['text_secondary'],
                fontsize=9)
    
    # Add small sample size warning where appropriate
    for i, total in enumerate(total_counts):
        if total < 10:  # Threshold for statistical reliability warning
            ax.annotate('⚠ Small sample',
                    xy=(i, 1.5),  # Just above the bottom of chart
                    ha='center', va='bottom',
                    color=TUFTE_COLORS['secondary'],
                    fontsize=8,
                    fontweight='bold')
    
    # Add labels and formatting
    ax.set_title(title, fontsize=14, color=TUFTE_COLORS['text'])
    ax.set_ylabel('Number of patients (log scale)', fontsize=10, color=TUFTE_COLORS['text_secondary'])
    ax.set_xticks(x)
    ax.set_xticklabels([f"{reason}\n(n={total})" for reason, total in zip(reasons, total_counts)])
    
    # Add a legend
    ax.legend(frameon=False, loc='upper right')
    
    # Add reference line for overall average retreatment rate
    total_retreated = sum(retreated_counts)
    total_patients = sum(total_counts)
    if total_patients > 0:
        overall_rate = total_retreated / total_patients * 100
        ax.annotate(f'Overall retreatment rate: {overall_rate:.1f}%',
                xy=(0.5, 0.03),  # Bottom center of the plot
                xycoords='figure fraction',
                ha='center', va='bottom',
                color=TUFTE_COLORS['text_secondary'],
                fontsize=9)
    
    # Add description
    fig.text(0.02, 0.02, 
            "Bar height shows patient count (log scale). Blue bars show patients who retreated;\nsage green bars show patients who did not retreat after discontinuation.",
            fontsize=8, color=TUFTE_COLORS['text_secondary'])
    
    fig.tight_layout(pad=1.5)
    return fig, ax

# Create sample data
reasons = ['Administrative', 'Not Renewed', 'Planned', 'Premature']
data = []

# Add retreated patients with realistic proportions
# Using more extreme example data to show the benefits of log scale
for reason in reasons:
    if reason == 'Administrative':
        count = 1  # Very small count for demonstration
    elif reason == 'Not Renewed':
        count = 6  # Small count for Not Renewed retreated
    elif reason == 'Planned':
        count = 60
    else:  # Premature
        count = 455  # Much larger for Premature
    
    data.append({
        'reason': reason,
        'retreated': True,
        'count': count
    })

# Add not retreated patients
for reason in reasons:
    if reason == 'Administrative':
        count = 6  # Administrative rarely retreated
    elif reason == 'Not Renewed':
        count = 133  # Not Renewed rarely retreated
    elif reason == 'Planned':
        count = 89  # More balanced for Planned
    else:  # Premature
        count = 92  # Small compared to retreated for Premature
    
    data.append({
        'reason': reason,
        'retreated': False,
        'count': count
    })

# Convert to DataFrame
df = pd.DataFrame(data)

# Create the nested bar visualization with log scale
fig, ax = create_nested_discontinuation_retreatment_chart(
    df, 
    title="Discontinuation Reasons and Retreatment Status (Log Scale)"
)

# Save the figure
plt.savefig('nested_discontinuation_retreatment_test.png', dpi=300, bbox_inches='tight')
print(f"Chart saved to {os.path.abspath('nested_discontinuation_retreatment_test.png')}")

# Don't show the figure interactively to avoid timeout
plt.close(fig)