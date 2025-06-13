"""
Tufte-inspired visualization style optimized for Zoom presentations.

Principles:
1. Tufte: Maximize data-ink ratio, remove chartjunk
2. Zoom: Large, clear labels that survive compression
3. Both: Focus on clarity and communication
"""

import matplotlib.pyplot as plt
import matplotlib as mpl
import seaborn as sns
from typing import Dict, Any, Optional, Tuple

# Color palette - high contrast for Zoom
COLORS = {
    'primary': '#2E86AB',      # Strong blue
    'secondary': '#E63946',    # Clear red
    'success': '#06D6A0',      # Bright teal
    'warning': '#F77F00',      # Vivid orange
    'neutral': '#264653',      # Dark blue-gray
    'light': '#F1FAEE',        # Off-white
    'grid': '#E0E0E0',         # Light gray
    
    # Disease states - high contrast
    'naive': '#3498DB',        # Bright blue
    'stable': '#27AE60',       # Clear green
    'active': '#F39C12',       # Strong orange
    'highly_active': '#E74C3C', # Vivid red
}

# Font sizes optimized for Zoom
FONT_SIZES = {
    'title': 20,          # Larger for Zoom
    'subtitle': 16,
    'label': 14,          # Minimum 14pt for Zoom
    'tick': 12,           # Minimum 12pt
    'legend': 13,
    'annotation': 12,
}

# Line weights for Zoom visibility
LINE_WEIGHTS = {
    'data': 2.5,          # Thicker for Zoom
    'axis': 1.0,
    'grid': 0.5,
    'annotation': 1.5,
}


def setup_zoom_tufte_style():
    """
    Configure matplotlib for Tufte-style plots optimized for Zoom.
    
    Balances minimal design with Zoom readability requirements.
    """
    # Reset to defaults first
    plt.rcdefaults()
    
    # Figure settings
    plt.rcParams['figure.figsize'] = (12, 8)  # 3:2 ratio, good for Zoom
    plt.rcParams['figure.dpi'] = 100
    plt.rcParams['savefig.dpi'] = 150  # Higher for exports
    plt.rcParams['figure.facecolor'] = 'white'
    
    # Font settings - larger for Zoom
    plt.rcParams['font.size'] = FONT_SIZES['tick']
    plt.rcParams['font.family'] = ['Arial', 'DejaVu Sans', 'sans-serif']
    plt.rcParams['axes.titlesize'] = FONT_SIZES['title']
    plt.rcParams['axes.labelsize'] = FONT_SIZES['label']
    plt.rcParams['xtick.labelsize'] = FONT_SIZES['tick']
    plt.rcParams['ytick.labelsize'] = FONT_SIZES['tick']
    plt.rcParams['legend.fontsize'] = FONT_SIZES['legend']
    
    # Axes settings - Tufte style
    plt.rcParams['axes.spines.top'] = False
    plt.rcParams['axes.spines.right'] = False
    plt.rcParams['axes.spines.left'] = True
    plt.rcParams['axes.spines.bottom'] = True
    plt.rcParams['axes.edgecolor'] = COLORS['neutral']
    plt.rcParams['axes.linewidth'] = LINE_WEIGHTS['axis']
    
    # Grid - subtle but visible on Zoom
    plt.rcParams['axes.grid'] = True
    plt.rcParams['grid.alpha'] = 0.3
    plt.rcParams['grid.color'] = COLORS['grid']
    plt.rcParams['grid.linewidth'] = LINE_WEIGHTS['grid']
    plt.rcParams['axes.axisbelow'] = True
    
    # Ticks - minimal but clear
    plt.rcParams['xtick.major.size'] = 5
    plt.rcParams['ytick.major.size'] = 5
    plt.rcParams['xtick.major.width'] = LINE_WEIGHTS['axis']
    plt.rcParams['ytick.major.width'] = LINE_WEIGHTS['axis']
    
    # Legend - clear for Zoom
    plt.rcParams['legend.frameon'] = False
    plt.rcParams['legend.numpoints'] = 1
    plt.rcParams['legend.scatterpoints'] = 1
    
    # Lines - thicker for Zoom
    plt.rcParams['lines.linewidth'] = LINE_WEIGHTS['data']
    plt.rcParams['lines.markersize'] = 8
    
    # Remove box around legend
    plt.rcParams['legend.edgecolor'] = 'none'


def create_figure(title: str, 
                  subtitle: Optional[str] = None,
                  figsize: Optional[Tuple[float, float]] = None) -> Tuple[plt.Figure, plt.Axes]:
    """
    Create a figure with Tufte-Zoom styling.
    
    Args:
        title: Main title (large for Zoom)
        subtitle: Optional subtitle
        figsize: Custom figure size (default: 12x8)
        
    Returns:
        fig, ax tuple
    """
    setup_zoom_tufte_style()
    
    if figsize is None:
        figsize = (12, 8)
        
    fig, ax = plt.subplots(figsize=figsize)
    
    # Title with proper spacing
    if subtitle:
        fig.suptitle(title, fontsize=FONT_SIZES['title'], y=0.98, fontweight='bold')
        ax.text(0.5, 1.05, subtitle, transform=ax.transAxes, 
                ha='center', fontsize=FONT_SIZES['subtitle'], color=COLORS['neutral'])
    else:
        ax.set_title(title, fontsize=FONT_SIZES['title'], pad=20, fontweight='bold')
    
    return fig, ax


def style_axis(ax: plt.Axes, 
               xlabel: Optional[str] = None,
               ylabel: Optional[str] = None,
               remove_top: bool = True,
               remove_right: bool = True) -> None:
    """
    Apply Tufte-Zoom styling to an axis.
    
    Args:
        ax: Matplotlib axis
        xlabel: X-axis label
        ylabel: Y-axis label  
        remove_top: Remove top spine
        remove_right: Remove right spine
    """
    # Remove spines
    if remove_top:
        ax.spines['top'].set_visible(False)
    if remove_right:
        ax.spines['right'].set_visible(False)
        
    # Style remaining spines
    ax.spines['bottom'].set_color(COLORS['neutral'])
    ax.spines['left'].set_color(COLORS['neutral'])
    
    # Labels with good spacing
    if xlabel:
        ax.set_xlabel(xlabel, fontsize=FONT_SIZES['label'], 
                     fontweight='bold', labelpad=10)
    if ylabel:
        ax.set_ylabel(ylabel, fontsize=FONT_SIZES['label'], 
                     fontweight='bold', labelpad=10)
    
    # Tick parameters
    ax.tick_params(colors=COLORS['neutral'], which='both')
    ax.tick_params(axis='both', which='major', labelsize=FONT_SIZES['tick'])
    
    # Grid
    ax.grid(True, alpha=0.3, color=COLORS['grid'], 
            linewidth=LINE_WEIGHTS['grid'], linestyle='-')
    ax.set_axisbelow(True)


def add_reference_line(ax: plt.Axes, 
                       value: float, 
                       label: str,
                       orientation: str = 'horizontal',
                       color: Optional[str] = None) -> None:
    """
    Add a reference line with Zoom-visible label.
    
    Args:
        ax: Matplotlib axis
        value: Value for reference line
        label: Label text
        orientation: 'horizontal' or 'vertical'
        color: Line color (default: neutral)
    """
    if color is None:
        color = COLORS['neutral']
        
    if orientation == 'horizontal':
        ax.axhline(value, color=color, linestyle='--', 
                  linewidth=LINE_WEIGHTS['annotation'], alpha=0.7)
        # Position label to avoid overlap
        ax.text(0.02, value, label, transform=ax.get_yaxis_transform(),
                fontsize=FONT_SIZES['annotation'], color=color,
                va='bottom', fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', 
                         edgecolor='none', alpha=0.8))
    else:
        ax.axvline(value, color=color, linestyle='--', 
                  linewidth=LINE_WEIGHTS['annotation'], alpha=0.7)
        ax.text(value, 0.98, label, transform=ax.get_xaxis_transform(),
                fontsize=FONT_SIZES['annotation'], color=color,
                ha='left', va='top', rotation=0, fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', 
                         edgecolor='none', alpha=0.8))


def format_zoom_legend(ax: plt.Axes, 
                       loc: str = 'best',
                       ncol: int = 1) -> None:
    """
    Format legend for Zoom visibility.
    
    Args:
        ax: Matplotlib axis
        loc: Legend location
        ncol: Number of columns
    """
    legend = ax.legend(loc=loc, ncol=ncol, 
                      fontsize=FONT_SIZES['legend'],
                      frameon=True, fancybox=False,
                      edgecolor='none', facecolor='white')
    
    # Set alpha on the frame patch (compatible with older matplotlib)
    if legend.get_frame():
        legend.get_frame().set_alpha(0.9)
    
    # Make legend text bold for Zoom
    for text in legend.get_texts():
        text.set_fontweight('bold')
        
    # Thicker lines in legend
    for line in legend.get_lines():
        line.set_linewidth(3)


def add_zoom_annotation(ax: plt.Axes,
                        text: str,
                        xy: Tuple[float, float],
                        xytext: Optional[Tuple[float, float]] = None,
                        arrow: bool = True) -> None:
    """
    Add annotation optimized for Zoom.
    
    Args:
        ax: Matplotlib axis
        text: Annotation text
        xy: Point to annotate
        xytext: Text position (if different from xy)
        arrow: Whether to draw arrow
    """
    if xytext is None:
        xytext = xy
        arrow = False
        
    annotation_props = {
        'fontsize': FONT_SIZES['annotation'],
        'fontweight': 'bold',
        'color': COLORS['neutral'],
        'bbox': dict(boxstyle='round,pad=0.5', 
                    facecolor=COLORS['light'], 
                    edgecolor=COLORS['neutral'],
                    linewidth=1.5)
    }
    
    if arrow:
        annotation_props['arrowprops'] = dict(
            arrowstyle='->',
            color=COLORS['neutral'],
            linewidth=LINE_WEIGHTS['annotation']
        )
        
    ax.annotate(text, xy=xy, xytext=xytext, **annotation_props)


def save_for_zoom(fig: plt.Figure, 
                  filename: str,
                  dpi: int = 150) -> None:
    """
    Save figure optimized for Zoom sharing.
    
    Args:
        fig: Matplotlib figure
        filename: Output filename
        dpi: Resolution (150 recommended for Zoom)
    """
    fig.savefig(filename, 
                dpi=dpi,
                bbox_inches='tight',
                facecolor='white',
                edgecolor='none')


# Example usage function
def example_zoom_tufte_plot():
    """Example of Tufte-style plot optimized for Zoom."""
    import numpy as np
    
    # Create figure
    fig, ax = create_figure(
        title="Visual Acuity Over Time",
        subtitle="Treat-and-Extend Protocol (n=100)"
    )
    
    # Generate example data
    months = np.arange(0, 37)
    mean_va = 70 - 5 * np.log(months + 1) + np.random.normal(0, 1, len(months))
    upper_ci = mean_va + 5
    lower_ci = mean_va - 5
    
    # Plot with Zoom-visible elements
    ax.plot(months, mean_va, color=COLORS['primary'], 
            linewidth=LINE_WEIGHTS['data'], label='Mean VA')
    ax.fill_between(months, lower_ci, upper_ci, 
                    color=COLORS['primary'], alpha=0.2)
    
    # Add reference line
    add_reference_line(ax, 70, 'Baseline', orientation='horizontal')
    
    # Style axis
    style_axis(ax, 
              xlabel='Time (months)', 
              ylabel='Visual Acuity (ETDRS letters)')
    
    # Format legend
    format_zoom_legend(ax, loc='lower left')
    
    # Add annotation
    add_zoom_annotation(ax, 
                       'Stabilization Phase',
                       xy=(24, mean_va[24]),
                       xytext=(24, mean_va[24] + 10))
    
    plt.tight_layout()
    return fig, ax