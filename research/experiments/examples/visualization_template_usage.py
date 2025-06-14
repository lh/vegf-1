"""
Example demonstrating how to use the enhanced visualization templates.

This example shows how to create consistent dual-axis charts using the
new template functions.
"""

import numpy as np
import matplotlib.pyplot as plt

from visualization.chart_templates import (
    create_standard_figure,
    format_standard_dual_axis_chart,
    apply_dual_axis_style,
    apply_horizontal_legend,
    apply_standard_layout,
    set_standard_y_axis_range,
    add_explanatory_note
)


def create_va_plot_with_templates():
    """Create a visual acuity plot using the new template functions."""
    # Create standard figure
    fig = plt.figure(figsize=(10, 6))
    ax_counts = fig.add_subplot(111)
    ax_acuity = ax_counts.twinx()
    
    # Generate sample data
    months = np.arange(0, 36, 3)
    treated_counts = [100, 95, 90, 85, 80, 75, 70, 65, 60, 55, 50, 48]
    control_counts = [50, 48, 45, 42, 40, 38, 35, 33, 30, 28, 25, 23]
    treated_acuity = [60, 62, 64, 65, 66, 67, 68, 68, 68, 67, 66, 65]
    control_acuity = [60, 58, 56, 54, 52, 50, 48, 46, 44, 42, 40, 38]
    
    # Plot the data
    lines1 = []
    labels1 = []
    
    # Patient counts (left axis)
    line1, = ax_counts.plot(months, treated_counts, color='#8FAD91', linewidth=2)
    lines1.append(line1)
    labels1.append('Treated (n)')
    
    line2, = ax_counts.plot(months, control_counts, color='#8FAD91', linewidth=2, linestyle='--')
    lines1.append(line2)
    labels1.append('Control (n)')
    
    # Visual acuity (right axis)
    lines2 = []
    labels2 = []
    
    line3, = ax_acuity.plot(months, treated_acuity, color='#FF8A8A', linewidth=2)
    lines2.append(line3)
    labels2.append('Treated VA')
    
    line4, = ax_acuity.plot(months, control_acuity, color='#FF8A8A', linewidth=2, linestyle='--')
    lines2.append(line4)
    labels2.append('Control VA')
    
    # Apply formatting using the convenience function
    format_standard_dual_axis_chart(
        fig, ax_counts, ax_acuity,
        title="Visual Acuity and Patient Retention Over Time",
        lines1=lines1, labels1=labels1,
        lines2=lines2, labels2=labels2,
        primary_label="Patient Count",
        secondary_label="Visual Acuity (Letters)",
        x_label="Time (Months)",
        y_limits=(0, 100),  # Accommodate both scales
        note="This example demonstrates the use of visualization templates for consistent chart styling."
    )
    
    # Override y-limits for acuity axis specifically
    ax_acuity.set_ylim(0, 85)
    
    return fig


def create_simpler_plot_with_templates():
    """Create a simpler plot using individual template functions."""
    # Create standard figure with basic setup
    fig, ax = create_standard_figure(
        title="Treatment Response Over Time",
        xlabel="Time (Months)",
        ylabel="Response Rate (%)"
    )
    
    # Generate sample data
    months = np.arange(0, 36, 3)
    response_rate = [30, 45, 60, 70, 75, 78, 80, 82, 83, 83, 82, 80]
    
    # Plot the data
    ax.plot(months, response_rate, color='#7DB8E8', linewidth=2.5, marker='o')
    
    # Apply standard layout without legend
    apply_standard_layout(fig, "Treatment Response Over Time", has_legend=False)
    
    # Add an explanatory note
    add_explanatory_note(fig, "Response rate measured as percentage of patients achieving ≥15 letter improvement.")
    
    return fig


if __name__ == "__main__":
    # Create example plots
    fig1 = create_va_plot_with_templates()
    fig2 = create_simpler_plot_with_templates()
    
    # Save the plots
    fig1.savefig('/Users/rose/Code/CC/examples/template_va_plot.png', dpi=150, bbox_inches='tight')
    fig2.savefig('/Users/rose/Code/CC/examples/template_simple_plot.png', dpi=150, bbox_inches='tight')
    
    # Display
    plt.show()