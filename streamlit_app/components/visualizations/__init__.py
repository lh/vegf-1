"""
Visualization package for the APE Streamlit application.

This package provides unified visualization functions that use both matplotlib
and R-based approaches, with progressive enhancement for better user experience.
"""

from streamlit_app.components.visualizations.common import is_r_available
from streamlit_app.components.visualizations.matplotlib_viz import (
    create_enrollment_visualization_matplotlib,
    create_va_over_time_plot_matplotlib,
    create_discontinuation_plot_matplotlib,
    create_dual_timeframe_plot_matplotlib
)
from streamlit_app.components.visualizations.r_integration import (
    render_enrollment_visualization,
    render_va_over_time_visualization,
    render_dual_timeframe_visualization
)

# Export key functions
__all__ = [
    # Utility functions
    'is_r_available',
    
    # Matplotlib visualizations
    'create_enrollment_visualization_matplotlib',
    'create_va_over_time_plot_matplotlib',
    'create_discontinuation_plot_matplotlib',
    'create_dual_timeframe_plot_matplotlib',
    
    # R visualizations with progressive enhancement
    'render_enrollment_visualization',
    'render_va_over_time_visualization',
    'render_dual_timeframe_visualization'
]