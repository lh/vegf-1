"""Centralized Tufte style constants for consistent visualization styling.

This module provides all Tufte-style constants in one place to ensure
consistency across all visualizations in the application.
"""

# Font sizes for different elements
TUFTE_FONT_SIZES = {
    'title': 16,
    'subtitle': 14,
    'label': 14,
    'tick': 12,
    'annotation': 11,
    'caption': 10,
}

# Line weights for different elements
TUFTE_LINE_WEIGHTS = {
    'axis': 1.0,
    'grid': 0.5,
    'annotation': 1.0,
    'reference': 0.8,
}

# Colors for Tufte styling (non-semantic, structural elements)
TUFTE_COLORS = {
    'neutral': '#264653',      # Dark blue-gray for axes and text
    'grid': '#E0E0E0',        # Light gray for subtle grids
    'annotation': '#666666',   # Medium gray for annotations
    'background': 'white',     # Clean white background
    'text': '#333333',        # Dark gray for main text
    'caption': '#666666',     # Medium gray for captions
}

# Margin settings for different chart types
TUFTE_MARGINS = {
    'default': dict(l=60, r=40, t=40, b=60),
    'compact': dict(l=40, r=20, t=20, b=40),
    'with_title': dict(l=60, r=40, t=60, b=60),
    'minimal': dict(l=20, r=20, t=20, b=20),
}

# Common Plotly layout configuration
TUFTE_PLOTLY_CONFIG = {
    'font': dict(family='Arial', size=TUFTE_FONT_SIZES['tick']),
    'plot_bgcolor': TUFTE_COLORS['background'],
    'paper_bgcolor': TUFTE_COLORS['background'],
    'margin': TUFTE_MARGINS['default'],
}

# Axis configuration for Plotly
TUFTE_AXIS_CONFIG = {
    'showgrid': False,
    'showline': True,
    'linewidth': TUFTE_LINE_WEIGHTS['axis'],
    'linecolor': TUFTE_COLORS['neutral'],
    'ticks': 'outside',
    'ticklen': 5,
    'tickwidth': TUFTE_LINE_WEIGHTS['axis'],
    'tickcolor': TUFTE_COLORS['neutral'],
    'tickfont': dict(size=TUFTE_FONT_SIZES['tick']),
    'titlefont': dict(size=TUFTE_FONT_SIZES['label']),
}

# Grid configuration when needed
TUFTE_GRID_CONFIG = {
    'showgrid': True,
    'gridwidth': TUFTE_LINE_WEIGHTS['grid'],
    'gridcolor': TUFTE_COLORS['grid'],
    'zeroline': False,
}


def apply_tufte_style(fig, include_grid=False, title=None):
    """Apply Tufte styling to a Plotly figure.
    
    Args:
        fig: Plotly figure object
        include_grid: Whether to include subtle grid lines
        title: Optional title for the chart
        
    Returns:
        Modified figure object
    """
    # Base layout
    fig.update_layout(**TUFTE_PLOTLY_CONFIG)
    
    # Title if provided
    if title:
        fig.update_layout(
            title=dict(
                text=title,
                font=dict(size=TUFTE_FONT_SIZES['title'], color=TUFTE_COLORS['text']),
                x=0,
                xanchor='left'
            ),
            margin=TUFTE_MARGINS['with_title']
        )
    
    # X-axis styling
    xaxis_config = TUFTE_AXIS_CONFIG.copy()
    if include_grid:
        xaxis_config.update(TUFTE_GRID_CONFIG)
    fig.update_xaxes(**xaxis_config)
    
    # Y-axis styling
    yaxis_config = TUFTE_AXIS_CONFIG.copy()
    if include_grid:
        yaxis_config.update(TUFTE_GRID_CONFIG)
    fig.update_yaxes(**yaxis_config)
    
    return fig


def get_tufte_layout_config(include_grid=False, title=None):
    """Get a complete Tufte-style layout configuration for Plotly.
    
    Args:
        include_grid: Whether to include subtle grid lines
        title: Optional title configuration
        
    Returns:
        Dictionary of layout configuration
    """
    config = TUFTE_PLOTLY_CONFIG.copy()
    
    # X-axis
    config['xaxis'] = TUFTE_AXIS_CONFIG.copy()
    if include_grid:
        config['xaxis'].update(TUFTE_GRID_CONFIG)
    
    # Y-axis
    config['yaxis'] = TUFTE_AXIS_CONFIG.copy()
    if include_grid:
        config['yaxis'].update(TUFTE_GRID_CONFIG)
    
    # Title if provided
    if title:
        config['title'] = dict(
            text=title,
            font=dict(size=TUFTE_FONT_SIZES['title'], color=TUFTE_COLORS['text']),
            x=0,
            xanchor='left'
        )
        config['margin'] = TUFTE_MARGINS['with_title']
    
    # Common settings
    config['showlegend'] = False  # Tufte prefers direct labeling
    config['height'] = 400  # Default height
    
    return config