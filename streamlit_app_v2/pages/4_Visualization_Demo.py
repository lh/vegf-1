"""
Visualization Demo - Showcase dual-mode visualization system.
"""

import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from utils.visualization_modes import (
    init_visualization_mode, mode_aware_figure, 
    get_mode_colors, apply_visualization_mode,
    VisualizationMode
)
from utils.tufte_zoom_style import (
    style_axis, add_reference_line, format_zoom_legend,
    add_zoom_annotation
)
from utils.style_constants import StyleConstants

st.set_page_config(page_title="Visualization Demo", page_icon="🎨", layout="wide")

st.title("🎨 Visualization Mode Demo")
st.markdown("""
This page demonstrates the dual visualization mode system with StyleConstants integration. 
Toggle between **Presentation Mode** (optimized for Zoom) and **Analysis Mode** (subtle Tufte style) 
using the selector in the sidebar.
""")

# Show StyleConstants info
with st.expander("📏 Active Style Constants", expanded=False):
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**Vision Scale**")
        st.code(f"""
Range: {StyleConstants.VISION_SCALE['min']}-{StyleConstants.VISION_SCALE['max']} letters
Ticks: {StyleConstants.get_vision_ticks()}
        """)
    
    with col2:
        st.markdown("**Time Divisions**")
        st.code(f"""
Week: {StyleConstants.TIME_SCALE['week']} days
Month: {StyleConstants.TIME_SCALE['month']} days
Quarter: {StyleConstants.TIME_SCALE['quarter']} days
        """)
    
    with col3:
        st.markdown("**Precision Rules**")
        st.code(f"""
Counts: {StyleConstants.PRECISION['counts']} decimals
Stats: {StyleConstants.PRECISION['statistics']} decimal
Percentages: {StyleConstants.PRECISION['percentages']} decimal
        """)

# Initialize visualization mode
current_mode = init_visualization_mode()
mode_info = VisualizationMode.MODES[current_mode]

# Display current mode info
col1, col2 = st.columns([2, 1])
with col1:
    st.info(f"**Current Mode**: {mode_info['name']} - {mode_info['description']}")
with col2:
    st.metric("Font Scale", f"{mode_info['font_scale']:.1f}x")
    st.metric("Line Scale", f"{mode_info['line_scale']:.1f}x")

# Generate sample data
np.random.seed(42)
months = np.arange(0, 37)
baseline_va = 70
vision_trajectory = baseline_va - 5 * np.log(months + 1) + np.random.normal(0, 2, len(months))
# Use StyleConstants for vision bounds
vision_trajectory = np.clip(vision_trajectory, 
                           StyleConstants.VISION_SCALE['min'], 
                           StyleConstants.VISION_SCALE['max'])

# Example 1: Line Plot
st.header("Example 1: Vision Trajectory")

fig, ax = mode_aware_figure("Visual Acuity Over Time - Treat and Extend Protocol")
colors = get_mode_colors()

# Main data line
ax.plot(months, vision_trajectory, color=colors['primary'], 
        label='Mean VA', linewidth=2.5 if current_mode == 'presentation' else 1.5)

# Confidence interval
ci_width = 5
ax.fill_between(months, vision_trajectory - ci_width, vision_trajectory + ci_width,
                color=colors['primary'], alpha=0.2, label='95% CI')

# Reference line
add_reference_line(ax, baseline_va, 'Baseline', color=colors['neutral'])

# Styling
style_axis(ax, xlabel='Time (months)', ylabel='Visual Acuity (ETDRS letters)')

# Apply StyleConstants for axes
ax.set_xlim(0, 36)
ax.set_ylim(StyleConstants.VISION_SCALE['min'], StyleConstants.VISION_SCALE['max'])
ax.set_yticks(StyleConstants.get_vision_ticks())

# Set month ticks at yearly intervals
ax.set_xticks([0, 12, 24, 36])

# Apply spine rules based on mode
StyleConstants.apply_spine_rules(ax, current_mode)

# Add annotation based on mode
if current_mode == 'presentation':
    add_zoom_annotation(ax, 'Treatment Response', 
                       xy=(6, vision_trajectory[6]), 
                       xytext=(6, vision_trajectory[6] + 8))
else:
    ax.annotate('Treatment Response', xy=(6, vision_trajectory[6]),
                xytext=(6, vision_trajectory[6] + 5),
                fontsize=10, ha='center', color=colors['neutral'])

format_zoom_legend(ax, loc='lower left')
st.pyplot(fig)

# Example 2: Bar Chart Comparison
st.header("Example 2: Protocol Comparison")

protocols = ['Standard T&E', 'Intensive', 'PRN', 'Fixed Q8W']
injections = [8.2, 10.5, 6.3, 9.0]
vision_gains = [5.2, 7.1, 3.8, 6.0]

col1, col2 = st.columns(2)

with col1:
    fig, ax = mode_aware_figure("Average Injections per Year")
    colors = get_mode_colors()
    
    bars = ax.bar(protocols, injections, color=colors['primary'], 
                   edgecolor=colors['neutral'], linewidth=1.5)
    
    # Add value labels on bars
    for bar, value in zip(bars, injections):
        height = bar.get_height()
        label_size = 14 if current_mode == 'presentation' else 10
        # Use StyleConstants formatting
        formatted_value = StyleConstants.format_statistic(value)
        ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                formatted_value, ha='center', va='bottom',
                fontsize=label_size, fontweight='bold')
    
    style_axis(ax, ylabel='Injections per Year')
    ax.set_ylim(0, 12)
    
    # Rotate labels if in presentation mode
    if current_mode == 'presentation':
        plt.xticks(rotation=45, ha='right')
    
    st.pyplot(fig)

with col2:
    fig, ax = mode_aware_figure("Mean Vision Gain at Year 1")
    colors = get_mode_colors()
    
    bars = ax.bar(protocols, vision_gains, color=colors['success'], 
                   edgecolor=colors['neutral'], linewidth=1.5)
    
    # Add value labels
    for bar, value in zip(bars, vision_gains):
        height = bar.get_height()
        label_size = 14 if current_mode == 'presentation' else 10
        # Use StyleConstants formatting - vision gains should be integers
        formatted_value = f'+{StyleConstants.format_vision(value)}'
        ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                formatted_value, ha='center', va='bottom',
                fontsize=label_size, fontweight='bold')
    
    style_axis(ax, ylabel='Vision Gain (ETDRS letters)')
    ax.set_ylim(0, 8)
    
    if current_mode == 'presentation':
        plt.xticks(rotation=45, ha='right')
    
    st.pyplot(fig)

# Example 3: Scatter Plot
st.header("Example 3: Treatment Response Correlation")

n_patients = 100
baseline_values = np.random.normal(65, 10, n_patients)
final_values = baseline_values + np.random.normal(5, 8, n_patients)
# Use StyleConstants for vision bounds
baseline_values = np.clip(baseline_values, StyleConstants.VISION_SCALE['min'], StyleConstants.VISION_SCALE['max'])
final_values = np.clip(final_values, StyleConstants.VISION_SCALE['min'], StyleConstants.VISION_SCALE['max'])

fig, ax = mode_aware_figure("Baseline vs Final Vision")
colors = get_mode_colors()

# Scatter plot
scatter = ax.scatter(baseline_values, final_values, 
                    alpha=0.6 if current_mode == 'presentation' else 0.4,
                    color=colors['primary'],
                    s=50 if current_mode == 'presentation' else 30,
                    edgecolor=colors['neutral'],
                    linewidth=0.5)

# Unity line
ax.plot([40, 85], [40, 85], '--', color=colors['neutral'], 
        linewidth=1.5, label='No change')

# Regression line
z = np.polyfit(baseline_values, final_values, 1)
p = np.poly1d(z)
x_line = np.linspace(40, 85, 100)
ax.plot(x_line, p(x_line), color=colors['secondary'], 
        linewidth=2.5 if current_mode == 'presentation' else 1.5,
        label=f'Trend (slope={z[0]:.2f})')

style_axis(ax, xlabel='Baseline Vision (letters)', 
          ylabel='Final Vision (letters)')

# Apply StyleConstants for both axes
ax.set_xlim(StyleConstants.VISION_SCALE['min'], StyleConstants.VISION_SCALE['max'])
ax.set_ylim(StyleConstants.VISION_SCALE['min'], StyleConstants.VISION_SCALE['max'])
ax.set_xticks(StyleConstants.get_vision_ticks())
ax.set_yticks(StyleConstants.get_vision_ticks())

# Apply spine rules
StyleConstants.apply_spine_rules(ax, current_mode)

format_zoom_legend(ax, loc='lower right')

st.pyplot(fig)

# Mode comparison
st.header("Mode Comparison")
st.markdown("""
### Key Differences:

| Feature | Presentation Mode | Analysis Mode |
|---------|------------------|---------------|
| **Font Size** | 20% larger | Standard size |
| **Line Weight** | 50% thicker | Standard weight |
| **Colors** | High contrast | Subtle palette |
| **Grid** | More visible (30% opacity) | Subtle (15% opacity) |
| **Annotations** | Large & bold | Small & discrete |
| **Purpose** | Screen sharing, talks | Detailed analysis |
""")

# Export options
st.header("Export Options")
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("**Presentation Mode Exports**")
    st.code("""
    # HD for Zoom (1920x1080)
    fig.savefig('plot.png', dpi=150)
    
    # PowerPoint slide
    fig.savefig('slide.png', dpi=300)
    """)

with col2:
    st.markdown("**Analysis Mode Exports**")
    st.code("""
    # High-res for papers
    fig.savefig('figure.png', dpi=600)
    
    # Vector for editing
    fig.savefig('figure.svg')
    """)

with col3:
    st.markdown("**Quick Toggle**")
    st.info("""
    Simply change the mode in the sidebar 
    and all plots will update instantly!
    
    Future: Keyboard shortcuts
    - `P` for Presentation
    - `A` for Analysis
    """)

# Tips
with st.expander("💡 Pro Tips"):
    st.markdown("""
    - **Before a Zoom call**: Switch to Presentation Mode
    - **For publications**: Use Analysis Mode and export at high DPI
    - **For live demos**: Presentation Mode with larger click targets
    - **For detailed review**: Analysis Mode shows more data density
    - **Mixed audience**: Start in Presentation, switch to Analysis for Q&A
    """)

# StyleConstants Examples
st.header("StyleConstants Formatting Examples")
col1, col2 = st.columns(2)

with col1:
    st.markdown("**Value Formatting**")
    examples = [
        ("Vision", 73.4, StyleConstants.format_vision(73.4)),
        ("Patient Count", 156.7, StyleConstants.format_count(156.7)),
        ("Statistic", 8.234, StyleConstants.format_statistic(8.234)),
        ("Percentage", 0.8534, StyleConstants.format_percentage(0.8534)),
    ]
    for name, raw, formatted in examples:
        st.code(f"{name}: {raw} → {formatted}")

with col2:
    st.markdown("**Axis Range Rules**")
    st.code(f"""
# Count data (e.g., patients)
{StyleConstants.get_axis_range([5, 12, 8, 15], 'count')}

# Non-count data (e.g., intervals)
{StyleConstants.get_axis_range([28, 35, 42, 56], 'interval')}

# Vision data always uses fixed scale
{StyleConstants.get_axis_range([65, 70, 75], 'vision')}
    """)

st.markdown("---")
st.caption("This dual-mode system ensures your visualizations are always optimized for their intended use!")