"""
Test script for the updated nested bar chart with Tufte-style legend.
"""

import pandas as pd
import matplotlib.pyplot as plt
from visualization.utils.nested_bar_chart import create_nested_bar_chart

# Create sample data exactly matching the values in the desired image
sample_data = [
    {"reason": "Administrative", "retreatment_status": "Retreated", "count": 3}, 
    {"reason": "Administrative", "retreatment_status": "Not Retreated", "count": 11}, 
    {"reason": "Not Renewed", "retreatment_status": "Retreated", "count": 19}, 
    {"reason": "Not Renewed", "retreatment_status": "Not Retreated", "count": 108}, 
    {"reason": "Planned", "retreatment_status": "Retreated", "count": 73}, 
    {"reason": "Planned", "retreatment_status": "Not Retreated", "count": 49}, 
    {"reason": "Premature", "retreatment_status": "Retreated", "count": 299}, 
    {"reason": "Premature", "retreatment_status": "Not Retreated", "count": 246}
]

# Convert to DataFrame
df = pd.DataFrame(sample_data)

# Define colors - blue for retreated, sage green for not retreated
colors = ['#4682B4', '#8FAD91']  # Steel Blue, Sage Green

# Create the chart using the nested bar chart with updated settings
fig, ax = create_nested_bar_chart(
    data=df,
    category_col="reason",
    subcategory_col="retreatment_status",
    value_col="count",
    category_order=["Administrative", "Not Renewed", "Planned", "Premature"],
    subcategory_order=["Retreated", "Not Retreated"],
    title="Discontinuation Reasons by Retreatment Status",
    figsize=(10, 6),
    colors=colors,
    background_color="#E0E0E0",  # Light grey
    bar_width=0.3,
    x_spacing=2.0,
    background_width_factor=3.0,
    background_alpha=0.6,
    bar_alpha=0.8,
    show_legend=True,
    show_grid=False,
    show_spines=False,
    data_labels=True,
    minimal_style=True
)

# Add retreatment rate at the bottom
retreated_patients = df[df['retreatment_status'] == "Retreated"]['count'].sum()
total_patients = df['count'].sum()
retreatment_rate = (retreated_patients / total_patients) * 100
fig.text(0.5, 0.01, f'Overall retreatment rate: {retreatment_rate:.1f}%',
        ha='center', va='bottom', fontsize=10)

# Ensure there's room for the retreatment rate
plt.subplots_adjust(bottom=0.15)

# Save the output to verify the changes
fig.savefig("updated_discontinuation_chart.png", dpi=100, bbox_inches="tight")
print("Updated chart saved to updated_discontinuation_chart.png")