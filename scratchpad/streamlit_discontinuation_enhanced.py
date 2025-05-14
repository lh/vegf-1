"""
Enhanced Streamlit-optimized visualization for discontinuation and retreatment analysis.
"""
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import json
from typing import Optional, List, Tuple
import matplotlib.ticker as mtick

def create_enhanced_discontinuation_chart(
    data: pd.DataFrame,
    title: str = "Discontinuation Reasons by Retreatment Status",
    figsize: Tuple[int, int] = (10, 6),
    save_path: Optional[str] = None,
    minimal_style: bool = True,
    show_percentages: bool = True,
    show_totals: bool = True
) -> Tuple[plt.Figure, plt.Axes]:
    """
    Create an enhanced Tufte-inspired chart for discontinuation reasons and retreatment status.
    
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
    show_percentages : bool
        Whether to show retreatment percentages
    show_totals : bool
        Whether to show total count annotations
        
    Returns
    -------
    tuple
        (fig, ax) matplotlib figure and axes objects
    """
    # Define colors
    retreat_color = "#4878A6"  # Muted blue
    not_retreat_color = "#A65C48"  # Muted red
    bg_color = "#e5e5e5"  # Light grey
    
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
    
    # Get the percentage of total for each discontinuation reason
    total_patients = totals.sum()
    reason_pcts = totals / total_patients * 100
    
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
        alpha=0.3,
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
        alpha=0.9,
        zorder=1
    )
    
    # Draw bars for non-retreated patients
    not_retreated_bars = ax.bar(
        x_adjusted + offset_start + bar_width,
        pivot_df["Not Retreated"],
        width=bar_width,
        label="Not Retreated",
        color=not_retreat_color,
        alpha=0.9,
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
    
    # Calculate and show retreatment percentages
    if show_percentages:
        for i, (reason, total) in enumerate(totals.items()):
            if total > 0:  # Avoid division by zero
                retreated = pivot_df.loc[reason, "Retreated"]
                retreat_pct = retreated / total * 100
                
                # Add percentage label above the background bar
                ax.text(
                    x_adjusted[i],
                    total + (max(totals) * 0.03),  # Small offset above the total bar
                    f"{retreat_pct:.1f}%",
                    ha='center',
                    va='bottom',
                    fontsize=9,
                    alpha=0.8,
                    color='#555555'
                )
    
    # Add total count and percentage of all discontinuations
    if show_totals:
        for i, (reason, total) in enumerate(totals.items()):
            # Calculate percentage of all discontinuations
            pct_of_all = total / total_patients * 100
            
            # Add labels below x-axis
            ax.text(
                x_adjusted[i],
                -max(totals) * 0.05,  # Position below axis
                f"Total: {int(total)}\n({pct_of_all:.1f}% of all)",
                ha='center',
                va='top',
                fontsize=8,
                color='#555555'
            )
    
    # Set up labels and formatting
    ax.set_xlabel("")
    ax.set_ylabel("Patient Count")
    ax.set_title(title, loc="left", fontsize=14, fontweight='bold')
    ax.set_xticks(x_adjusted)
    ax.set_xticklabels(pivot_df.index, fontsize=11)
    
    # Extend y-axis a bit for the percentage labels
    y_max = max(totals) * 1.1
    ax.set_ylim(0, y_max)
    
    # Add legend
    ax.legend(
        title="Retreatment Status",
        loc="upper right",
        frameon=True,
        framealpha=0.9,
        edgecolor='lightgrey'
    )
    
    # Add subtitle with explanation
    if show_percentages:
        ax.text(
            0.01, 0.01,
            "Percentages above bars show retreat rate for each category\nPercentages below show proportion of all discontinuations",
            transform=ax.transAxes,
            ha='left',
            va='bottom',
            fontsize=8,
            alpha=0.7,
            style='italic'
        )
    
    # Add total discontinuations as text
    ax.text(
        0.99, 0.01,
        f"Total Discontinuations: {int(total_patients)}",
        transform=ax.transAxes,
        ha='right',
        va='bottom',
        fontsize=9,
        fontweight='bold',
        alpha=0.8
    )
    
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
         "count": round(discontinuation_counts['Administrative'] * admin_retreat_pct)},
        {"discontinuation_reason": "Administrative", "retreatment_status": "Not Retreated", 
         "count": discontinuation_counts['Administrative'] - round(discontinuation_counts['Administrative'] * admin_retreat_pct)},
        
        {"discontinuation_reason": "Not Renewed", "retreatment_status": "Retreated", 
         "count": round(discontinuation_counts['Not Renewed'] * not_renewed_retreat_pct)},
        {"discontinuation_reason": "Not Renewed", "retreatment_status": "Not Retreated", 
         "count": discontinuation_counts['Not Renewed'] - round(discontinuation_counts['Not Renewed'] * not_renewed_retreat_pct)},
        
        {"discontinuation_reason": "Planned", "retreatment_status": "Retreated", 
         "count": round(discontinuation_counts['Planned'] * planned_retreat_pct)},
        {"discontinuation_reason": "Planned", "retreatment_status": "Not Retreated", 
         "count": discontinuation_counts['Planned'] - round(discontinuation_counts['Planned'] * planned_retreat_pct)},
        
        {"discontinuation_reason": "Premature", "retreatment_status": "Retreated", 
         "count": round(discontinuation_counts['Premature'] * premature_retreat_pct)},
        {"discontinuation_reason": "Premature", "retreatment_status": "Not Retreated", 
         "count": discontinuation_counts['Premature'] - round(discontinuation_counts['Premature'] * premature_retreat_pct)},
    ]
    
    return pd.DataFrame(data)


if __name__ == "__main__":
    # Load sample data
    df = load_sample_data()
    
    # Create and save enhanced chart
    fig, ax = create_enhanced_discontinuation_chart(
        data=df,
        title="Discontinuation Reasons by Retreatment Status",
        save_path="streamlit_discontinuation_enhanced.png",
        show_percentages=True,
        show_totals=True
    )
    
    print("Enhanced chart saved to: streamlit_discontinuation_enhanced.png")