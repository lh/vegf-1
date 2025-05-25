"""
Test script for the new discontinuation-retreatment combined visualization.
This script creates sample data and renders the new unstacked chart.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# Import our visualization modules
from visualization.color_system import COLORS, SEMANTIC_COLORS, ALPHAS
from visualization.visualization_templates import create_discontinuation_retreatment_chart
from streamlit_app.utils.tufte_style import set_tufte_style

# Create sample data
reasons = ['Administrative', 'Planned', 'Not Renewed', 'Premature']
data = []

# Add retreated patients
for reason in reasons:
    # Sample counts with realistic proportions
    if reason == 'Administrative':
        count = 87
    elif reason == 'Planned':
        count = 152
    elif reason == 'Not Renewed':
        count = 63
    else:  # Premature
        count = 105
    
    data.append({
        'reason': reason,
        'retreated': True,
        'count': count
    })

# Add not retreated patients
for reason in reasons:
    # Sample counts with realistic proportions
    if reason == 'Administrative':
        count = 215
    elif reason == 'Planned':
        count = 94
    elif reason == 'Not Renewed':
        count = 178
    else:  # Premature
        count = 312
    
    data.append({
        'reason': reason,
        'retreated': False,
        'count': count
    })

# Convert to DataFrame
df = pd.DataFrame(data)

# Create the visualization
fig, ax = create_discontinuation_retreatment_chart(
    df, 
    title="Discontinuation Reasons and Retreatment Status"
)

# Save the figure
plt.savefig('discontinuation_retreatment_test.png', dpi=300, bbox_inches='tight')
print(f"Chart saved to {os.path.abspath('discontinuation_retreatment_test.png')}")

# Don't show the figure interactively
plt.close(fig)