"""
Chart builder utilities for consistent visualization creation.

Provides a fluent API for building charts with consistent styling,
proper axis configuration, and dual-mode support.
"""

import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
from typing import Optional, Tuple, Dict, Any, Callable
import streamlit as st

from .visualization_modes import mode_aware_figure, get_mode_colors
from .tufte_zoom_style import style_axis, format_zoom_legend, add_reference_line
from .style_constants import StyleConstants


class ChartBuilder:
    """
    Fluent API for building consistent charts.
    
    Example:
        chart = (ChartBuilder("Vision Over Time")
                .with_vision_axis('y')
                .with_time_axis('x', duration_days=730)
                .plot(lambda ax, colors: ax.plot(x, y, color=colors['primary']))
                .add_reference_line(70, 'Baseline')
                .build())
        st.pyplot(chart.figure)
    """
    
    def __init__(self, title: str, figsize: Optional[Tuple[float, float]] = None):
        """Initialize chart builder with title."""
        self.title = title
        self.figsize = figsize
        self.xlabel = None
        self.ylabel = None
        self.x_axis_type = None
        self.y_axis_type = None
        self.x_axis_config = {}
        self.y_axis_config = {}
        self.plot_functions = []
        self.post_style_functions = []
        self.legend_config = {'loc': 'best'}
        self._figure = None
        self._axis = None
        self._colors = None
        self._mode = None
        
    def with_labels(self, xlabel: Optional[str] = None, ylabel: Optional[str] = None) -> 'ChartBuilder':
        """Set axis labels."""
        if xlabel:
            self.xlabel = xlabel
        if ylabel:
            self.ylabel = ylabel
        return self
        
    def with_vision_axis(self, axis: str = 'y') -> 'ChartBuilder':
        """Configure axis for vision data (0-100 ETDRS letters)."""
        if axis == 'x':
            self.x_axis_type = 'vision'
        else:
            self.y_axis_type = 'vision'
        return self
        
    def with_count_axis(self, axis: str = 'y') -> 'ChartBuilder':
        """Configure axis for count data (integer only)."""
        if axis == 'x':
            self.x_axis_type = 'count'
        else:
            self.y_axis_type = 'count'
        return self
        
    def with_time_axis(self, axis: str = 'x', duration_days: int = 365, 
                      preferred_unit: str = 'months') -> 'ChartBuilder':
        """Configure axis for time data."""
        config = {
            'duration_days': duration_days,
            'preferred_unit': preferred_unit
        }
        if axis == 'x':
            self.x_axis_type = 'time'
            self.x_axis_config = config
        else:
            self.y_axis_type = 'time'
            self.y_axis_config = config
        return self
        
    def plot(self, plot_function: Callable[[plt.Axes, Dict[str, str]], None]) -> 'ChartBuilder':
        """
        Add a plotting function.
        
        The function receives (ax, colors) and should perform the plotting.
        """
        self.plot_functions.append(plot_function)
        return self
        
    def add_reference_line(self, value: float, label: str, 
                          orientation: str = 'horizontal',
                          color_key: str = 'neutral') -> 'ChartBuilder':
        """Add a reference line to the chart."""
        def add_line(ax, colors):
            add_reference_line(ax, value, label, orientation, colors.get(color_key))
            
        self.post_style_functions.append(add_line)
        return self
        
    def with_legend(self, loc: str = 'best', ncol: int = 1) -> 'ChartBuilder':
        """Configure legend."""
        self.legend_config = {'loc': loc, 'ncol': ncol}
        return self
        
    def _apply_axis_config(self, ax: plt.Axes, mode: str):
        """Apply axis configuration based on types."""
        # X-axis configuration
        if self.x_axis_type == 'vision':
            ax.set_xlim(StyleConstants.VISION_SCALE['min'], StyleConstants.VISION_SCALE['max'])
            ax.set_xticks(StyleConstants.get_vision_ticks())
        elif self.x_axis_type == 'count':
            ax.xaxis.set_major_locator(MaxNLocator(integer=True))
        elif self.x_axis_type == 'time':
            duration = self.x_axis_config.get('duration_days', 365)
            unit = self.x_axis_config.get('preferred_unit', 'months')
            time_ticks = StyleConstants.get_time_ticks(duration, preferred_unit=unit)
            
            # Special handling for month-based x-axis
            if self.xlabel and 'month' in self.xlabel.lower():
                # Get clean month ticks directly
                max_months = int(duration / 30.44)
                month_ticks = StyleConstants.get_month_ticks(max_months)
                ax.set_xticks(month_ticks)
                ax.set_xticklabels([str(m) for m in month_ticks])
            else:
                ax.set_xticks(time_ticks)
            
        # Y-axis configuration
        if self.y_axis_type == 'vision':
            ax.set_ylim(StyleConstants.VISION_SCALE['min'], StyleConstants.VISION_SCALE['max'])
            ax.set_yticks(StyleConstants.get_vision_ticks())
        elif self.y_axis_type == 'count':
            ax.yaxis.set_major_locator(MaxNLocator(integer=True))
        elif self.y_axis_type == 'time':
            duration = self.y_axis_config.get('duration_days', 365)
            unit = self.y_axis_config.get('preferred_unit', 'months')
            time_ticks = StyleConstants.get_time_ticks(duration, preferred_unit=unit)
            ax.set_yticks(time_ticks)
    
    def build(self) -> 'ChartBuilder':
        """Build the chart with all configurations."""
        # Get current mode - fail if not available
        current_mode = st.session_state.get('viz_mode')
        if current_mode is None:
            raise RuntimeError(
                "Visualization mode not initialized! "
                "Ensure init_visualization_mode() is called at the start of your page."
            )
        
        # Create figure and get colors
        self._figure, self._axis = mode_aware_figure(self.title, figsize=self.figsize)
        self._colors = get_mode_colors()
        self._mode = current_mode
        
        # Execute all plot functions
        for plot_func in self.plot_functions:
            plot_func(self._axis, self._colors)
            
        # Apply basic styling
        style_axis(self._axis, xlabel=self.xlabel, ylabel=self.ylabel)
        
        # Apply axis configuration
        self._apply_axis_config(self._axis, current_mode)
        
        # Apply spine rules AFTER style_axis - this is critical!
        StyleConstants.apply_spine_rules(self._axis, current_mode)
        
        # Execute post-style functions (reference lines, etc.)
        for post_func in self.post_style_functions:
            post_func(self._axis, self._colors)
            
        # Format legend if there are labeled elements
        if self._axis.get_legend_handles_labels()[0]:
            format_zoom_legend(self._axis, **self.legend_config)
                
        return self
        
    @property
    def figure(self) -> plt.Figure:
        """Get the built figure."""
        if self._figure is None:
            self.build()
        return self._figure
        
    @property 
    def axis(self) -> plt.Axes:
        """Get the axis."""
        if self._axis is None:
            self.build()
        return self._axis


def vision_distribution_chart(baseline: list, final: list) -> ChartBuilder:
    """Convenience function for vision distribution charts."""
    return (ChartBuilder("Vision Distribution: Baseline vs Final")
            .with_labels(xlabel='Vision (ETDRS letters)', ylabel='Number of Patients')
            .with_vision_axis('x')
            .with_count_axis('y')
            .plot(lambda ax, colors: [
                ax.hist(baseline, bins=20, alpha=0.6, label='Baseline',
                       color=colors['primary'], edgecolor=colors['neutral'], linewidth=1.5),
                ax.hist(final, bins=20, alpha=0.6, label='Final',
                       color=colors['secondary'], edgecolor=colors['neutral'], linewidth=1.5)
            ])
            .with_legend(loc='upper left'))


def vision_change_chart(changes: list) -> ChartBuilder:
    """Convenience function for vision change charts."""
    import numpy as np
    mean_change = np.mean(changes)
    
    return (ChartBuilder("Distribution of Vision Changes")
            .with_labels(xlabel='Vision Change (ETDRS letters)', ylabel='Number of Patients')
            .with_count_axis('y')
            .plot(lambda ax, colors: 
                ax.hist(changes, bins=20, color=colors['success'],
                       alpha=0.7, edgecolor=colors['neutral'], linewidth=1.5))
            .add_reference_line(0, 'No change', 'vertical', 'secondary')
            .add_reference_line(mean_change, f'Mean: {StyleConstants.format_vision(mean_change)}',
                               'vertical', 'primary'))