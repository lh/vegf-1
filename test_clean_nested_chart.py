"""
Test the clean nested bar chart implementation.
"""
import pandas as pd
import matplotlib.pyplot as plt
from visualization.clean_nested_bar_chart import create_discontinuation_retreatment_chart

# Create sample data for discontinuation and retreatment
data = [
    {'reason': 'Premature', 'retreated': True, 'count': 455},
    {'reason': 'Premature', 'retreated': False, 'count': 93},
    {'reason': 'Planned', 'retreated': True, 'count': 60},
    {'reason': 'Planned', 'retreated': False, 'count': 89},
    {'reason': 'Not Renewed', 'retreated': True, 'count': 6},
    {'reason': 'Not Renewed', 'retreated': False, 'count': 119},
    {'reason': 'Administrative', 'retreated': True, 'count': 2},
    {'reason': 'Administrative', 'retreated': False, 'count': 10},
]

df = pd.DataFrame(data)

# Create the chart
fig, ax = create_discontinuation_retreatment_chart(
    data=df,
    title="Discontinuation Reasons and Retreatment Status",
    figsize=(10, 6),
    use_log_scale=True,
    sort_by_total=True,
    small_sample_threshold=15
)

# Save the figure
plt.savefig('clean_nested_chart.png', dpi=150, bbox_inches='tight')
print("Chart saved to clean_nested_chart.png")

# Create a linear scale version for comparison
fig2, ax2 = create_discontinuation_retreatment_chart(
    data=df,
    title="Discontinuation Reasons and Retreatment Status (Linear Scale)",
    figsize=(10, 6),
    use_log_scale=False,  # Use linear scale
    sort_by_total=True,
    small_sample_threshold=15
)

# Save the linear scale version
plt.savefig('clean_nested_chart_linear.png', dpi=150, bbox_inches='tight')
print("Linear scale chart saved to clean_nested_chart_linear.png")