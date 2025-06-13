"""
Centralized export configuration for all visualizations.

Provides a consistent way to configure export options across all Plotly charts
in the application, with user-selectable format options.
"""

import streamlit as st
import streamlit.components.v1 as components
from typing import Dict, Any, Optional


def get_export_config(
    filename: str = "chart", 
    width: Optional[int] = None,
    height: Optional[int] = None,
    scale: float = 1.0
) -> Dict[str, Any]:
    """
    Get Plotly config with user-selected export format.
    
    Args:
        filename: Base filename for exports (without extension)
        width: Export width in pixels (defaults based on format)
        height: Export height in pixels (defaults based on format)
        scale: Scale factor for raster exports
        
    Returns:
        Dictionary with Plotly configuration options
    """
    # Get format from session state or default
    export_format = st.session_state.get('export_format', 'png')
    
    # Set default dimensions based on format if not provided
    if width is None:
        width = 1400 if export_format == 'svg' else 1200
    if height is None:
        height = 800 if export_format == 'svg' else 720
    
    # For PNG, allow higher scale for better quality
    if export_format == 'png':
        scale = st.session_state.get('export_scale', 2.0)
    
    
    config = {
        'toImageButtonOptions': {
            'format': export_format,
            'filename': filename,
            'height': height,
            'width': width,
            'scale': scale
        },
        'displayModeBar': True,
        'displaylogo': False,
        'modeBarButtonsToAdd': ['toImage'],
        'modeBarButtonsToRemove': ['pan2d', 'lasso2d', 'select2d', 'autoScale2d'],
        # Disable keyboard shortcuts that don't work well in Streamlit
        'doubleClick': False,
        'showTips': False,
        'showAxisDragHandles': False,
        'showAxisRangeEntryBoxes': False
    }
    
    return config


def render_export_settings(location: str = "sidebar") -> None:
    """
    Render export format selector in the UI.
    
    Args:
        location: Where to render - "sidebar" or "main"
    """
    # Initialize export settings in session state if not present
    if 'export_format' not in st.session_state:
        st.session_state.export_format = 'png'
    if 'export_scale' not in st.session_state:
        st.session_state.export_scale = 2.0
    
    container = st.sidebar if location == "sidebar" else st
    
    with container.expander("📊 Export Settings", expanded=False):
        # Format selection
        current_format = st.session_state.get('export_format', 'png')
        
        format_options = {
            'png': 'PNG (Raster)',
            'svg': 'SVG (Vector)',
            'jpeg': 'JPEG (Compressed)',
            'webp': 'WebP (Modern)'
        }
        
        selected_format = container.selectbox(
            "Export Format",
            options=list(format_options.keys()),
            format_func=lambda x: format_options[x],
            index=list(format_options.keys()).index(current_format),
            help="Choose the format for downloading charts"
        )
        
        # Update session state if changed
        if selected_format != current_format:
            st.session_state.export_format = selected_format
        
        # Format-specific options
        if selected_format == 'png':
            current_scale = st.session_state.get('export_scale', 2.0)
            scale = container.slider(
                "PNG Quality Scale",
                min_value=1.0,
                max_value=4.0,
                value=current_scale,
                step=0.5,
                help="Higher values = better quality but larger files"
            )
            if scale != current_scale:
                st.session_state.export_scale = scale
        
        
        
        # Quick copy button for config
        if container.checkbox("Show config code", value=False):
            container.code(f"""
# Add to any Plotly chart:
from ape.utils.export_config import get_export_config
config = get_export_config(filename="my_chart")
st.plotly_chart(fig, config=config)
            """, language="python")


def apply_export_config(fig, filename: str = "chart", **kwargs) -> Dict[str, Any]:
    """
    Apply export configuration to a Plotly figure and return the config.
    
    This is a convenience function that gets the config and can also
    apply any figure-level settings if needed.
    
    Args:
        fig: Plotly figure object
        filename: Base filename for exports
        **kwargs: Additional arguments passed to get_export_config
        
    Returns:
        The configuration dictionary
    """
    config = get_export_config(filename=filename, **kwargs)
    
    # Could add figure-level modifications here if needed
    # For example, ensuring fonts embed properly in SVG:
    if st.session_state.get('export_format') == 'svg':
        fig.update_layout(
            font=dict(family="Arial, sans-serif")  # Use web-safe fonts for SVG
        )
    
    return config


# Convenience function for common chart types
def get_sankey_export_config() -> Dict[str, Any]:
    """Get export config optimized for Sankey diagrams."""
    # For Sankey, we want minimal interaction - just view and export
    config = get_export_config(
        filename="treatment_pattern_sankey",
        width=1400,
        height=800
    )
    
    # Remove all interaction buttons except download
    config['modeBarButtonsToRemove'] = [
        'pan2d', 'zoom2d', 'zoomIn2d', 'zoomOut2d', 
        'autoScale2d', 'resetScale2d', 'lasso2d', 
        'select2d', 'toggleSpikelines', 'hoverClosestCartesian',
        'hoverCompareCartesian'
    ]
    
    # Only keep the download button
    config['modeBarButtonsToAdd'] = ['toImage']
    
    # Disable all interactivity that might show keyboard shortcuts
    config.update({
        'staticPlot': False,  # Keep false so download still works
        'scrollZoom': False,
        'doubleClick': False,
        'showTips': False,
        'showAxisDragHandles': False,
        'showAxisRangeEntryBoxes': False,
        'displayModeBar': 'hover'  # Only show on hover
    })
    
    return config


def get_line_chart_export_config() -> Dict[str, Any]:
    """Get export config optimized for line charts."""
    return get_export_config(
        filename="visual_acuity_chart",
        width=1200,
        height=600
    )


def get_heatmap_export_config() -> Dict[str, Any]:
    """Get export config optimized for heatmaps."""
    return get_export_config(
        filename="heatmap",
        width=1000,
        height=1000
    )