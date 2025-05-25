#!/usr/bin/env python3
"""
Create a visual mockup of the UI layout to verify the design.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Create figure
fig, ax = plt.subplots(figsize=(12, 14))

# Define layout parameters
width = 10
thumbnail_height = 1.5
full_plot_height = 3.5
spacing = 0.3

y_current = 12

# Title
ax.text(width/2, y_current, 'Visual Acuity Over Time', 
        ha='center', fontsize=16, weight='bold')
y_current -= 0.8

# Quick Comparison header
ax.text(width/2, y_current, 'Quick Comparison', 
        ha='center', fontsize=14, weight='bold')
y_current -= 0.4

# Thumbnails
thumb_y = y_current - thumbnail_height
# Thumbnail 1 - Mean + CI
rect1 = patches.Rectangle((0.5, thumb_y), width/2-0.75, thumbnail_height,
                         linewidth=1, edgecolor='blue', facecolor='lightblue', alpha=0.3)
ax.add_patch(rect1)
ax.text(width/4, thumb_y + thumbnail_height/2, 'Mean + 95% CI\n(Thumbnail)', 
        ha='center', va='center', fontsize=10)

# Thumbnail 2 - Distribution
rect2 = patches.Rectangle((width/2+0.25, thumb_y), width/2-0.75, thumbnail_height,
                         linewidth=1, edgecolor='green', facecolor='lightgreen', alpha=0.3)
ax.add_patch(rect2)
ax.text(3*width/4, thumb_y + thumbnail_height/2, 'Patient Distribution\n(Thumbnail)', 
        ha='center', va='center', fontsize=10)

y_current = thumb_y - spacing

# Full plot 1 header
ax.text(width/2, y_current, 'Mean Visual Acuity with Confidence Intervals', 
        ha='center', fontsize=14, weight='bold')
y_current -= 0.3

# Full plot 1
plot1_y = y_current - full_plot_height
rect3 = patches.Rectangle((0.5, plot1_y), width-1, full_plot_height,
                         linewidth=2, edgecolor='blue', facecolor='white')
ax.add_patch(rect3)
ax.text(width/2, plot1_y + full_plot_height/2, 'Full Mean + CI Plot\n(Detailed View)', 
        ha='center', va='center', fontsize=12)
ax.text(width/2, plot1_y + 0.2, 
        'Note: The 95% confidence interval shows our statistical confidence\nin the mean value, not the range of patient vision scores.',
        ha='center', va='bottom', fontsize=9, style='italic', color='gray')

y_current = plot1_y - spacing

# Full plot 2 header
ax.text(width/2, y_current, 'Distribution of Visual Acuity', 
        ha='center', fontsize=14, weight='bold')
y_current -= 0.3

# Full plot 2
plot2_y = y_current - full_plot_height
rect4 = patches.Rectangle((0.5, plot2_y), width-1, full_plot_height,
                         linewidth=2, edgecolor='green', facecolor='white')
ax.add_patch(rect4)
ax.text(width/2, plot2_y + full_plot_height/2, 'Full Distribution Plot\n(Percentile Bands)', 
        ha='center', va='center', fontsize=12)
ax.text(width/2, plot2_y + 0.2, 
        'This plot shows the actual distribution of patient vision scores,\nnot statistical confidence intervals.',
        ha='center', va='bottom', fontsize=9, style='italic', color='gray')

# Add annotations
ax.annotate('Side-by-side for\nquick comparison', 
            xy=(width/2, thumb_y + thumbnail_height), 
            xytext=(width + 0.5, thumb_y + thumbnail_height + 0.5),
            arrowprops=dict(arrowstyle='->', color='red'),
            fontsize=10, color='red')

ax.annotate('Stacked for\ndetailed analysis', 
            xy=(width - 0.5, plot1_y + full_plot_height/2), 
            xytext=(width + 0.5, plot1_y + full_plot_height/2),
            arrowprops=dict(arrowstyle='->', color='red'),
            fontsize=10, color='red')

# Set up the axes
ax.set_xlim(0, width + 1.5)
ax.set_ylim(0, 13)
ax.set_aspect('equal')
ax.axis('off')

plt.title('VA Visualization UI Layout Design', pad=20, fontsize=18, weight='bold')
plt.tight_layout()
plt.savefig('/Users/rose/Code/CC/ui_layout_design.png', dpi=300, bbox_inches='tight', facecolor='white')
plt.close()

print("UI layout design saved to: ui_layout_design.png")

# Also create a simple data flow diagram
fig, ax = plt.subplots(figsize=(10, 6))

# Box for simulation results
results_box = patches.Rectangle((1, 4), 2, 1,
                               linewidth=2, edgecolor='black', facecolor='lightyellow')
ax.add_patch(results_box)
ax.text(2, 4.5, 'Simulation\nResults', ha='center', va='center', fontsize=12, weight='bold')

# Arrows and data branches
ax.arrow(3, 4.5, 0.8, 0, head_width=0.1, head_length=0.1, fc='black', ec='black')
ax.arrow(3, 4.5, 0.8, -1.5, head_width=0.1, head_length=0.1, fc='black', ec='black')

# Mean data box
mean_box = patches.Rectangle((4, 4), 2.5, 1,
                            linewidth=2, edgecolor='blue', facecolor='lightblue')
ax.add_patch(mean_box)
ax.text(5.25, 4.5, 'mean_va_data', ha='center', va='center', fontsize=11)

# Patient data box
patient_box = patches.Rectangle((4, 2), 2.5, 1,
                               linewidth=2, edgecolor='green', facecolor='lightgreen')
ax.add_patch(patient_box)
ax.text(5.25, 2.5, 'patient_data', ha='center', va='center', fontsize=11)

# Visualization boxes
ax.arrow(6.5, 4.5, 0.8, 0, head_width=0.1, head_length=0.1, fc='blue', ec='blue')
mean_viz_box = patches.Rectangle((7.5, 4), 2, 1,
                                linewidth=2, edgecolor='blue', facecolor='white')
ax.add_patch(mean_viz_box)
ax.text(8.5, 4.5, 'Mean + CI\nPlot', ha='center', va='center', fontsize=11)

ax.arrow(6.5, 2.5, 0.8, 0, head_width=0.1, head_length=0.1, fc='green', ec='green')
dist_viz_box = patches.Rectangle((7.5, 2), 2, 1,
                                linewidth=2, edgecolor='green', facecolor='white')
ax.add_patch(dist_viz_box)
ax.text(8.5, 2.5, 'Distribution\nPlot', ha='center', va='center', fontsize=11)

# Error box
ax.arrow(5.25, 1.9, 0, -0.4, head_width=0.1, head_length=0.1, fc='red', ec='red')
error_box = patches.Rectangle((4, 0.5), 2.5, 0.8,
                             linewidth=2, edgecolor='red', facecolor='pink')
ax.add_patch(error_box)
ax.text(5.25, 0.9, 'Error if missing', ha='center', va='center', fontsize=10, color='red')

ax.set_xlim(0, 10)
ax.set_ylim(0, 6)
ax.axis('off')
ax.set_title('Data Flow for VA Visualizations', fontsize=16, weight='bold', pad=20)

plt.tight_layout()
plt.savefig('/Users/rose/Code/CC/data_flow_diagram.png', dpi=300, bbox_inches='tight', facecolor='white')
plt.close()

print("Data flow diagram saved to: data_flow_diagram.png")