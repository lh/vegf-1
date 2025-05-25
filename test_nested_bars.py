"""
Test script for the new nested bar chart visualization.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# Import our visualization functions
from visualization.nested_bar_chart import create_nested_discontinuation_chart

# Create sample data
reasons = ['Premature', 'Planned', 'Not Renewed', 'Administrative']
data = []

# Add retreated patients
retreated_counts = {
    'Premature': 455,
    'Planned': 60,
    'Not Renewed': 6,
    'Administrative': 2
}

# Add not retreated patients
not_retreated_counts = {
    'Premature': 93,
    'Planned': 89,
    'Not Renewed': 119,
    'Administrative': 10
}

# Create dataframe
for reason in reasons:
    # Add retreated patients
    data.append({
        'reason': reason,
        'retreated': True,
        'count': retreated_counts[reason]
    })
    
    # Add not retreated patients
    data.append({
        'reason': reason,
        'retreated': False,
        'count': not_retreated_counts[reason]
    })

# Convert to DataFrame
df = pd.DataFrame(data)

# Create the true nested bar chart
fig, ax = create_nested_discontinuation_chart(
    df, 
    title="Discontinuation Reasons and Retreatment Status",
    figsize=(12, 6),
    use_log_scale=True,
    sort_by_total=True,
    small_sample_threshold=15
)

# Save the figure
plt.savefig('nested_discontinuation_chart_test.png', dpi=300, bbox_inches='tight')
print(f"Chart saved to {os.path.abspath('nested_discontinuation_chart_test.png')}")

# Don't show the figure interactively
plt.close(fig)