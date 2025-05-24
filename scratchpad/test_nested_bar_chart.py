"""
Test implementation of nested bar chart function with original data from nested_graph.py.
"""
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import os

def create_nested_bar_chart(data, category_col, subcategory_col, value_col, 
                          category_order=None, subcategory_filter=None,
                          title="Regions - Revenue by Segment",
                          figsize=(7, 5)):
    """
    Create a nested bar chart with a grey background bar and colored category bars on top.
    
    Parameters
    ----------
    data : pd.DataFrame
        DataFrame containing the data to plot
    category_col : str
        Name of the column containing the main categories
    subcategory_col : str
        Name of the column containing the subcategories
    value_col : str
        Name of the column containing the values to plot
    category_order : list, optional
        Order of categories to display, by default None
    subcategory_filter : list, optional
        List of subcategories to include (2-6), by default None (all subcategories)
    title : str, optional
        Chart title, by default "Regions - Revenue by Segment"
    figsize : tuple, optional
        Figure size, by default (7, 5)
    
    Returns
    -------
    tuple
        (fig, ax) matplotlib figure and axes objects
    """
    # Filter subcategories if specified
    if subcategory_filter is not None:
        if not 2 <= len(subcategory_filter) <= 6:
            raise ValueError("subcategory_filter must contain between 2 and 6 subcategories")
        data = data[data[subcategory_col].isin(subcategory_filter)].copy()
    
    # Apply category ordering if provided
    if category_order is not None:
        data[category_col] = pd.Categorical(
            data[category_col], categories=category_order, ordered=True
        )
    
    # Sort by category and value
    data = data.sort_values([category_col, value_col], ascending=[True, False])
    
    # Pivot data to get subcategories as columns
    pivot_df = data.pivot(
        index=category_col, columns=subcategory_col, values=value_col
    )
    
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
    
    # Fixed bar width as in original
    bar_width = 0.25
    x = np.arange(len(pivot_df.index))
    x_spacing = 2  # Increase spacing between category groups
    x_adjusted = x * x_spacing  # Adjust x positions to have space between categories
    
    # Draw background bars for totals
    ax.bar(x_adjusted, totals, width=bar_width * 3.5, color="lightgrey", zorder=0, label="Total")
    
    # Draw bars for each subcategory with centered positioning
    offset_start = -(num_subcategories - 1) / 2 * bar_width
    for i, sub_cat in enumerate(pivot_df.columns):
        ax.bar(
            x_adjusted + offset_start + i * bar_width,
            pivot_df[sub_cat],
            width=bar_width,
            label=sub_cat,
            zorder=1,
        )
    
    # Set up labels and formatting
    ax.set_xlabel(category_col)
    ax.set_ylabel(value_col)
    ax.set_title(title, loc="left")
    ax.set_xticks(x_adjusted)
    ax.set_xticklabels(pivot_df.index)
    ax.legend(title=subcategory_col)
    
    return fig, ax

def main():
    # Create the same dataset as in the original script
    data = pd.DataFrame(
        {
            "value": [364, 232, 143, 357, 204, 131, 254, 158, 91, 196, 122, 74],
            "category": [
                "West", "West", "West",
                "East", "East", "East",
                "Central", "Central", "Central",
                "South", "South", "South",
            ],
            "sub_category": [
                "Consumer", "Corporate", "Home office",
                "Consumer", "Corporate", "Home office",
                "Consumer", "Corporate", "Home office",
                "Consumer", "Corporate", "Home office",
            ],
        }
    )
    
    # Define category order (same as original)
    cat_order = ["West", "East", "Central", "South"]
    
    # Test with just 2 subcategories (Consumer and Home office)
    fig1, ax1 = create_nested_bar_chart(
        data=data,
        category_col="category",
        subcategory_col="sub_category",
        value_col="value",
        category_order=cat_order,
        subcategory_filter=["Consumer", "Home office"],
        title="Regions - Revenue (Consumer vs Home Office)",
        figsize=(7, 5)
    )
    
    # Save the 2-subcategory figure
    output_file1 = os.path.join(os.path.dirname(__file__), "nested_bar_chart_2subcats.png")
    fig1.savefig(output_file1, dpi=100, bbox_inches="tight")
    print(f"2-subcategory chart saved to: {output_file1}")
    plt.close(fig1)
    
    # Also test with all 3 subcategories to verify it still works
    fig2, ax2 = create_nested_bar_chart(
        data=data,
        category_col="category",
        subcategory_col="sub_category",
        value_col="value",
        category_order=cat_order,
        title="Regions - Revenue by Segment (All)",
        figsize=(7, 5)
    )
    
    # Save the all-subcategory figure
    output_file2 = os.path.join(os.path.dirname(__file__), "nested_bar_chart_all.png")
    fig2.savefig(output_file2, dpi=100, bbox_inches="tight")
    print(f"All-subcategory chart saved to: {output_file2}")
    
if __name__ == "__main__":
    main()