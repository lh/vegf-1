"""
Streamlit-optimized visualization for discontinuation and retreatment analysis.
"""
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import json
from typing import Optional, List, Tuple

def create_discontinuation_retreatment_chart(
    data: pd.DataFrame,
    title: str = "Discontinuation Reasons by Retreatment Status",
    figsize: Tuple[int, int] = (10, 6),
    save_path: Optional[str] = None,
    minimal_style: bool = True
) -> Tuple[plt.Figure, plt.Axes]:
    """
    Create a Tufte-inspired chart for discontinuation reasons and retreatment status.
    
    Parameters
    ----------
    data : pd.DataFrame
        DataFrame with columns: discontinuation_reason, retreatment_status, count
    title : str
        Chart title
    figsize : tuple
        Figure size as (width, height)
    save_path : str, optional
        Path to save the figure
    minimal_style : bool
        Whether to use minimal Tufte-inspired style
        
    Returns
    -------
    tuple
        (fig, ax) matplotlib figure and axes objects
    """
    # Define colors with reduced alpha - even more muted
    retreat_color = "#5686B3"  # Lighter muted blue
    not_retreat_color = "#B37866"  # Lighter muted red
    bg_color = "#e5e5e5"  # Light grey

    # Alpha values (further reduced)
    bg_alpha = 0.15      # Very transparent background
    bar_alpha = 0.65     # Slightly more transparent bars
    
    # Sort and prepare data
    reason_order = ["Administrative", "Not Renewed", "Planned", "Premature"]
    retreat_order = ["Retreated", "Not Retreated"]
    
    # Pivot data for plotting
    pivot_df = data.pivot(
        index="discontinuation_reason", 
        columns="retreatment_status", 
        values="count"
    ).fillna(0)
    
    # Reorder rows and columns
    pivot_df = pivot_df.reindex(index=reason_order, columns=retreat_order)
    
    # Calculate totals
    totals = pivot_df.sum(axis=1)
    
    # Create figure
    fig, ax = plt.subplots(figsize=figsize)
    
    # Apply minimal style if requested
    if minimal_style:
        # Remove top and right spines
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)
        
        # Remove y-axis ticks
        ax.tick_params(axis='y', length=0)
        
        # Set clean background
        plt.rcParams['axes.facecolor'] = 'white'
        plt.rcParams['figure.facecolor'] = 'white'
        
        # Add light gridlines
        ax.grid(axis='y', linestyle=':', alpha=0.3, zorder=0)
    
    # Setup bar positions
    x = np.arange(len(pivot_df.index))
    x_adjusted = x * 2  # Increase spacing between bars
    bar_width = 0.35
    
    # Draw background bars for totals
    background_width = bar_width * 3.0
    ax.bar(
        x_adjusted,
        totals,
        width=background_width,
        color=bg_color,
        alpha=bg_alpha,  # Using the reduced alpha value
        zorder=0,
        label="_nolegend_"  # Don't include in legend
    )
    
    # Calculate offsets for centered bars
    offset_start = -bar_width / 2
    
    # Draw bars for retreated patients
    retreated_bars = ax.bar(
        x_adjusted + offset_start,
        pivot_df["Retreated"],
        width=bar_width,
        label="Retreated",
        color=retreat_color,
        alpha=bar_alpha,  # Using the reduced alpha value
        zorder=1
    )

    # Draw bars for non-retreated patients
    not_retreated_bars = ax.bar(
        x_adjusted + offset_start + bar_width,
        pivot_df["Not Retreated"],
        width=bar_width,
        label="Not Retreated",
        color=not_retreat_color,
        alpha=bar_alpha,  # Using the reduced alpha value
        zorder=1
    )
    
    # Add data labels to bars
    def add_labels(bars):
        for bar in bars:
            height = bar.get_height()
            if height > 0:  # Only add labels to bars with values
                ax.text(
                    bar.get_x() + bar.get_width()/2.,
                    height,
                    f'{int(height)}',
                    ha='center',
                    va='bottom',
                    fontsize=10,
                    fontweight='bold'
                )
    
    add_labels(retreated_bars)
    add_labels(not_retreated_bars)
    
    # No percentage labels as requested
    
    # Set up labels and formatting
    ax.set_xlabel("")
    ax.set_ylabel("Patient Count")
    ax.set_title(title, loc="left", fontsize=14, fontweight='bold')
    ax.set_xticks(x_adjusted)
    ax.set_xticklabels(pivot_df.index, fontsize=11)
    
    # Add legend
    ax.legend(
        title="Retreatment Status",
        loc="upper right",
        frameon=True,
        framealpha=0.9,
        edgecolor='lightgrey'
    )
    
    # No percentage explanation text
    
    # Ensure tight layout
    fig.tight_layout()
    
    # Save if path provided
    if save_path:
        fig.savefig(save_path, dpi=300, bbox_inches="tight")
    
    return fig, ax


def load_sample_data():
    """Load sample data based on actual discontinuation counts."""
    # Actual discontinuation counts
    discontinuation_counts = {
        'Administrative': 14,
        'Not Renewed': 127,
        'Planned': 122,
        'Premature': 545
    }
    
    # Made-up retreatment percentages
    admin_retreat_pct = 0.25      # 25% of Administrative discontinuations are retreated
    not_renewed_retreat_pct = 0.15 # 15% of Not Renewed discontinuations are retreated
    planned_retreat_pct = 0.60     # 60% of Planned discontinuations are retreated
    premature_retreat_pct = 0.55   # 55% of Premature discontinuations are retreated
    
    data = [
        {"discontinuation_reason": "Administrative", "retreatment_status": "Retreated", 
         "count": int(discontinuation_counts['Administrative'] * admin_retreat_pct)},
        {"discontinuation_reason": "Administrative", "retreatment_status": "Not Retreated", 
         "count": discontinuation_counts['Administrative'] - int(discontinuation_counts['Administrative'] * admin_retreat_pct)},
        
        {"discontinuation_reason": "Not Renewed", "retreatment_status": "Retreated", 
         "count": int(discontinuation_counts['Not Renewed'] * not_renewed_retreat_pct)},
        {"discontinuation_reason": "Not Renewed", "retreatment_status": "Not Retreated", 
         "count": discontinuation_counts['Not Renewed'] - int(discontinuation_counts['Not Renewed'] * not_renewed_retreat_pct)},
        
        {"discontinuation_reason": "Planned", "retreatment_status": "Retreated", 
         "count": int(discontinuation_counts['Planned'] * planned_retreat_pct)},
        {"discontinuation_reason": "Planned", "retreatment_status": "Not Retreated", 
         "count": discontinuation_counts['Planned'] - int(discontinuation_counts['Planned'] * planned_retreat_pct)},
        
        {"discontinuation_reason": "Premature", "retreatment_status": "Retreated", 
         "count": int(discontinuation_counts['Premature'] * premature_retreat_pct)},
        {"discontinuation_reason": "Premature", "retreatment_status": "Not Retreated", 
         "count": discontinuation_counts['Premature'] - int(discontinuation_counts['Premature'] * premature_retreat_pct)},
    ]
    
    return pd.DataFrame(data)


if __name__ == "__main__":
    # Load sample data
    df = load_sample_data()
    
    # Create and save chart
    fig, ax = create_discontinuation_retreatment_chart(
        data=df,
        title="Discontinuation Reasons by Retreatment Status",
        save_path="streamlit_discontinuation_chart.png"
    )
    
    print("Chart saved to: streamlit_discontinuation_chart.png")