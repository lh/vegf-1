"""
Debug script to check the retreatment visualization that will be used in Streamlit.
"""
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

try:
    # Try to import from the clean nested bar chart implementation
    from visualization.clean_nested_bar_chart import create_discontinuation_retreatment_chart
    print("Successfully imported from clean_nested_bar_chart")
except ImportError:
    try:
        # Fall back to the nested bar chart if clean version isn't available
        from visualization.nested_bar_chart import create_nested_discontinuation_chart as create_discontinuation_retreatment_chart
        print("Falling back to nested_bar_chart")
    except ImportError:
        print("Failed to import any chart implementation")
        raise

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
    title="Streamlit Visualization Test",
    figsize=(10, 6),
    use_log_scale=True,
    sort_by_total=True,
    small_sample_threshold=15
)

# Save the figure
output_path = 'streamlit_debug_visualization.png'
plt.savefig(output_path, dpi=150, bbox_inches='tight')
print(f"Chart saved to {os.path.abspath(output_path)}")

# Print current directory and visualization module location
print(f"Current directory: {os.getcwd()}")
print(f"Python path: {os.environ.get('PYTHONPATH', 'Not set')}")

# Try to find all visualization modules
import glob
viz_files = glob.glob("visualization/*.py")
print(f"Visualization files found: {viz_files}")

# Print out module details
import sys
for name, module in sys.modules.items():
    if 'nested_bar_chart' in name or 'clean_nested_bar_chart' in name:
        print(f"Found module: {name}, path: {getattr(module, '__file__', 'Unknown')}")