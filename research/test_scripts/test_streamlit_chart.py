"""
Test script to verify that our Streamlit visualizations work correctly.
"""

import pandas as pd
import matplotlib.pyplot as plt
from streamlit_app.discontinuation_chart import create_discontinuation_retreatment_chart

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

# Create the chart using our existing visualization function
fig, ax = create_discontinuation_retreatment_chart(
    data=df,
    title="Discontinuation Reasons by Retreatment Status",
    figsize=(10, 6),
    show_data_labels=True,
    minimal_style=True
)

# Save the output to verify the changes
fig.savefig("streamlit_discontinuation_chart.png", dpi=100, bbox_inches="tight")
print("Streamlit chart saved to streamlit_discontinuation_chart.png")