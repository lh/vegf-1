"""
Clean implementation of a nested bar chart for discontinuation and retreatment visualization.
"""
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

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

# Calculate totals for each category
totals = df.groupby('reason')['count'].sum().reset_index()
totals = totals.sort_values('count', ascending=False)  # Sort by total count
reasons = totals['reason'].tolist()
reason_totals = totals['count'].tolist()

# Set up plot
fig, ax = plt.subplots(figsize=(10, 6))

# Use log scale to handle disparate category sizes
ax.set_yscale('log')

# Define colors
bg_color = '#E0E0E0'  # Light grey for background bars
retreated_color = '#4682B4'  # Blue for retreated
not_retreated_color = '#8FAD91'  # Sage green for not retreated

# Set up positions
x = np.arange(len(reasons))
bar_width = 0.75
segment_width = bar_width / 2  # Width for each segment

# Draw background bars for totals
bg_bars = ax.bar(x, reason_totals, width=bar_width, color=bg_color, 
                edgecolor='none', alpha=0.8, zorder=1)

# Add retreated and not retreated segments
for i, reason in enumerate(reasons):
    # Get data for this reason
    retreated_count = df[(df['reason'] == reason) & (df['retreated'] == True)]['count'].sum()
    not_retreated_count = df[(df['reason'] == reason) & (df['retreated'] == False)]['count'].sum()
    
    # Position segments inside the total bar (left and right)
    retreated_x = x[i] - segment_width/2
    not_retreated_x = x[i] + segment_width/2
    
    # Draw retreated segment (blue)
    ax.bar(retreated_x, retreated_count, width=segment_width, color=retreated_color, 
           edgecolor='white', linewidth=0.5, zorder=2, 
           label='Retreated' if i == 0 else None)
    
    # Draw not retreated segment (sage green)
    ax.bar(not_retreated_x, not_retreated_count, width=segment_width, color=not_retreated_color, 
           edgecolor='white', linewidth=0.5, zorder=2,
           label='Not Retreated' if i == 0 else None)
    
    # Add value labels inside each segment
    for pos_x, count in [(retreated_x, retreated_count), (not_retreated_x, not_retreated_count)]:
        if count > 0:  # Only add labels to segments with values
            ax.text(pos_x, count/2, str(count), ha='center', va='center', 
                    color='white' if count > 50 else 'black', fontweight='bold')
    
    # Add reason and total above each bar
    ax.text(x[i], reason_totals[i] + (max(reason_totals) * 0.05), 
            f'{reason}\n{reason_totals[i]}', ha='center', va='bottom', fontweight='bold')

# Add small sample warning for categories with fewer than 15 patients
small_sample_threshold = 15
for i, total in enumerate(reason_totals):
    if total < small_sample_threshold:
        # For log scale, position the warning at a fixed position
        ax.text(x[i], 1.2, 'Small sample', ha='center', va='center',
                color='#D81B60', fontsize=8, fontweight='bold',
                bbox=dict(facecolor='white', alpha=0.9, pad=2,
                         boxstyle='round,pad=0.3', edgecolor='#D81B60', linewidth=1),
                zorder=10)

# Configure axes
ax.set_xticks([])  # Hide x-ticks since we have labels directly on the bars
ax.set_ylabel('Number of Patients (log scale)')
ax.set_title('Discontinuation Reasons and Retreatment Status')
ax.legend(loc='upper right')

# Set y-axis limits for log scale to start just below the smallest value
smallest_value = min([count for count in df['count'] if count > 0])
ax.set_ylim(bottom=max(0.9, smallest_value * 0.5))  # Start at 0.9 or half of smallest value

# Add grid for better readability with log scale
ax.grid(True, axis='y', linestyle='--', alpha=0.3, color='#cccccc')

# Remove spines
for spine in ['top', 'right', 'bottom']:
    ax.spines[spine].set_visible(False)

# Add retreatment rate at the bottom
total_patients = df['count'].sum()
retreated_patients = df[df['retreated'] == True]['count'].sum()
retreatment_rate = (retreated_patients / total_patients) * 100
fig.text(0.5, 0.01, f'Overall retreatment rate: {retreatment_rate:.1f}%', 
         ha='center', va='bottom', fontsize=10)

# Save and show
plt.tight_layout(rect=[0, 0.05, 1, 0.95])  # Make room for retreatment rate text
plt.savefig('retreatment_bars.png', dpi=150, bbox_inches='tight')
print("Chart saved to retreatment_bars.png")