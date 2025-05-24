"""
Simple nested bar chart test with a very basic dataset.
"""
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Create simple test data
data = {
    'category': ['A', 'A', 'B', 'B'],
    'subcategory': ['A1', 'A2', 'B1', 'B2'],
    'value': [4, 6, 7, 8]
}

df = pd.DataFrame(data)

# Calculate totals for each category
totals = df.groupby('category')['value'].sum().reset_index()
totals_dict = dict(zip(totals['category'], totals['value']))

# Set up plot
fig, ax = plt.subplots(figsize=(8, 6))

# Define colors
bg_color = '#E0E0E0'  # Light grey for background bars
subcategory_colors = ['#4682B4', '#8FAD91']  # Blue and sage green for subcategories

# Set up positions
categories = ['A', 'B']
x = np.arange(len(categories))
bar_width = 0.6
subcategory_width = bar_width / 2  # Width for each subcategory

# Draw background bars for totals
bg_bars = ax.bar(x, [totals_dict[cat] for cat in categories], 
                width=bar_width, color=bg_color, edgecolor='none', 
                alpha=0.8, zorder=1)

# Add subcategory bars
for i, (cat, subgroup) in enumerate(df.groupby('category')):
    values = subgroup['value'].values
    
    # Position subcategory bars inside the total bar (left and right)
    ax.bar(x[i] - subcategory_width/2, values[0], 
           width=subcategory_width, color=subcategory_colors[0], 
           edgecolor='white', linewidth=0.5, zorder=2, label='Subcategory 1' if i == 0 else None)
    
    ax.bar(x[i] + subcategory_width/2, values[1], 
           width=subcategory_width, color=subcategory_colors[1], 
           edgecolor='white', linewidth=0.5, zorder=2, label='Subcategory 2' if i == 0 else None)
    
    # Add subcategory value labels inside bars
    for j, val in enumerate(values):
        pos_x = x[i] - subcategory_width/2 if j == 0 else x[i] + subcategory_width/2
        ax.text(pos_x, val/2, str(val), ha='center', va='center', 
                color='white' if val > 5 else 'black', fontweight='bold')
    
    # Add total label above bar
    ax.text(x[i], totals_dict[cat] + 0.5, f'Total: {totals_dict[cat]}', 
            ha='center', va='bottom', fontweight='bold')

# Configure axes
ax.set_xticks(x)
ax.set_xticklabels(categories)
ax.set_ylabel('Value')
ax.set_title('Simple Nested Bar Chart')
ax.legend(loc='upper right')

# Remove spines
for spine in ['top', 'right']:
    ax.spines[spine].set_visible(False)

# Save and show
plt.tight_layout()
plt.savefig('simple_nested_bars.png', dpi=150, bbox_inches='tight')
print("Chart saved to simple_nested_bars.png")