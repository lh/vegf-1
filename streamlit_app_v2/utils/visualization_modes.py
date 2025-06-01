"""
Dual visualization modes: Presentation (Zoom) and Analysis (Tufte).

Users can toggle between modes based on their current needs.
"""

import streamlit as st
import matplotlib.pyplot as plt
from typing import Dict, Any, Optional


class VisualizationMode:
    """Manages visualization style modes."""
    
    # Mode definitions
    MODES = {
        'presentation': {
            'name': '🎥 Presentation Mode',
            'description': 'Optimized for Zoom/screen sharing',
            'font_scale': 1.2,
            'line_scale': 1.5,
            'grid_alpha': 0.3,
            'annotation_size': 14,
            'min_font_size': 12,
            'colors': {
                'primary': '#2E86AB',
                'secondary': '#E63946',
                'success': '#06D6A0',
                'warning': '#F77F00',
                'neutral': '#264653',
                # Treatment pattern states
                'pre_treatment': '#9ECAE1',
                'initial_treatment': '#9ECAE1',
                'intensive_monthly': '#4A90E2',
                'regular_6_8_weeks': '#7FBA00',
                'extended_12_weeks': '#5A8F00',
                'maximum_extension': '#3C5F00',
                'treatment_gap_3_6': '#FFD700',
                'extended_gap_6_12': '#FF9500',
                'long_gap_12_plus': '#FF6347',
                'restarted_after_gap': '#FF1493',
                'irregular_pattern': '#FFA500',
                'no_further_visits': '#999999',
                # Terminal states (lighter versions)
                'terminal_initial': 'rgba(158, 202, 225, 0.5)',
                'terminal_intensive': 'rgba(74, 144, 226, 0.5)',
                'terminal_regular': 'rgba(127, 186, 0, 0.5)',
                'terminal_extended': 'rgba(90, 142, 0, 0.5)',
                'terminal_maximum': 'rgba(60, 95, 0, 0.5)',
                # Terminal status colors
                'terminal_active': '#27ae60',  # Green for still active
                'terminal_discontinued': '#e74c3c',  # Red for discontinued
            }
        },
        'analysis': {
            'name': '📊 Analysis Mode',
            'description': 'Subtle styling for detailed analysis',
            'font_scale': 0.9,
            'line_scale': 1.0,
            'grid_alpha': 0.15,
            'annotation_size': 10,
            'min_font_size': 9,
            'colors': {
                'primary': '#5A7C8A',
                'secondary': '#B85450',
                'success': '#4A9B7F',
                'warning': '#D4812B',
                'neutral': '#4A5568',
                # Treatment pattern states (more subtle for analysis)
                'pre_treatment': '#A8C6D4',
                'initial_treatment': '#A8C6D4',
                'intensive_monthly': '#6B9DC7',
                'regular_6_8_weeks': '#8FC15C',
                'extended_12_weeks': '#6F9649',
                'maximum_extension': '#4F6B35',
                'treatment_gap_3_6': '#E6C84D',
                'extended_gap_6_12': '#E6A04D',
                'long_gap_12_plus': '#D97A6B',
                'restarted_after_gap': '#D97AAE',
                'irregular_pattern': '#E6A866',
                'no_further_visits': '#A6A6A6',
                # Terminal states (lighter versions)
                'terminal_initial': 'rgba(168, 198, 212, 0.4)',
                'terminal_intensive': 'rgba(107, 157, 199, 0.4)',
                'terminal_regular': 'rgba(143, 193, 92, 0.4)',
                'terminal_extended': 'rgba(111, 150, 73, 0.4)',
                'terminal_maximum': 'rgba(79, 107, 53, 0.4)',
                # Terminal status colors
                'terminal_active': '#27ae60',  # Green for still active
                'terminal_discontinued': '#e74c3c',  # Red for discontinued
            }
        }
    }
    
    @staticmethod
    def get_current_mode() -> str:
        """Get current visualization mode from session state."""
        if 'viz_mode' not in st.session_state:
            st.session_state.viz_mode = 'analysis'  # Default
        return st.session_state.viz_mode
    
    @staticmethod
    def set_mode(mode: str) -> None:
        """Set visualization mode."""
        if mode in VisualizationMode.MODES:
            st.session_state.viz_mode = mode
            
    @staticmethod
    def get_style_params() -> Dict[str, Any]:
        """Get style parameters for current mode."""
        mode = VisualizationMode.get_current_mode()
        return VisualizationMode.MODES[mode]
    
    @staticmethod
    def render_mode_selector() -> str:
        """Render mode selector in sidebar."""
        current_mode = VisualizationMode.get_current_mode()
        
        # Create radio button selector
        mode_names = {k: v['name'] for k, v in VisualizationMode.MODES.items()}
        
        selected = st.sidebar.radio(
            "Visualization Mode",
            options=list(mode_names.keys()),
            format_func=lambda x: mode_names[x],
            index=list(mode_names.keys()).index(current_mode),
            help="Switch between presentation and analysis modes"
        )
        
        # Update mode if changed
        if selected != current_mode:
            VisualizationMode.set_mode(selected)
            st.rerun()
            
        # Show mode description
        mode_info = VisualizationMode.MODES[selected]
        st.sidebar.info(f"**{mode_info['description']}**")
        
        return selected


def apply_visualization_mode(fig: Optional[plt.Figure] = None) -> Dict[str, Any]:
    """
    Apply current visualization mode settings.
    
    Args:
        fig: Optional matplotlib figure to apply settings to
        
    Returns:
        Dictionary of style parameters
    """
    params = VisualizationMode.get_style_params()
    
    # Base font size
    base_font = 12
    
    # Apply matplotlib settings
    plt.rcParams.update({
        'font.size': base_font * params['font_scale'],
        'axes.titlesize': base_font * params['font_scale'] * 1.5,
        'axes.labelsize': base_font * params['font_scale'] * 1.2,
        'xtick.labelsize': base_font * params['font_scale'],
        'ytick.labelsize': base_font * params['font_scale'],
        'legend.fontsize': base_font * params['font_scale'],
        'lines.linewidth': 2 * params['line_scale'],
        'lines.markersize': 8 * params['line_scale'],
        'grid.alpha': params['grid_alpha'],
    })
    
    # Apply to specific figure if provided
    if fig is not None:
        for ax in fig.get_axes():
            # Update grid
            ax.grid(True, alpha=params['grid_alpha'])
            
            # Update spine visibility based on mode
            if params['font_scale'] > 1:  # Presentation mode
                ax.spines['top'].set_visible(False)
                ax.spines['right'].set_visible(False)
                ax.spines['left'].set_linewidth(1.5)
                ax.spines['bottom'].set_linewidth(1.5)
            else:  # Analysis mode
                for spine in ax.spines.values():
                    spine.set_linewidth(0.8)
                    spine.set_alpha(0.8)
    
    return params


def mode_aware_figure(title: str, 
                      figsize: Optional[tuple] = None,
                      **kwargs) -> tuple:
    """
    Create a figure with mode-aware styling.
    
    Args:
        title: Figure title
        figsize: Figure size (will be adjusted based on mode)
        **kwargs: Additional arguments for plt.subplots
        
    Returns:
        fig, ax tuple
    """
    params = VisualizationMode.get_style_params()
    
    # Adjust figure size based on mode
    if figsize is None:
        if params['font_scale'] > 1:  # Presentation
            figsize = (12, 8)
        else:  # Analysis
            figsize = (10, 6)
    
    # Apply mode settings
    apply_visualization_mode()
    
    # Create figure
    fig, ax = plt.subplots(figsize=figsize, **kwargs)
    
    # Set title with mode-appropriate styling
    if params['font_scale'] > 1:  # Presentation
        ax.set_title(title, fontweight='bold', pad=20)
    else:  # Analysis
        ax.set_title(title, pad=15)
    
    # Apply mode-specific styling
    apply_visualization_mode(fig)
    
    return fig, ax


def get_mode_colors() -> Dict[str, str]:
    """Get color palette for current mode."""
    params = VisualizationMode.get_style_params()
    return params['colors']


# Convenience function for Streamlit apps
def init_visualization_mode():
    """
    Initialize visualization mode in a Streamlit app.
    
    Call this in your app's main function or at the top of pages.
    """
    
    # Render selector in sidebar
    mode = VisualizationMode.render_mode_selector()
    
    # Add keyboard shortcut hint
    if st.sidebar.checkbox("Show Keyboard Shortcuts", value=False):
        st.sidebar.markdown("""
        **Keyboard Shortcuts** (coming soon):
        - `P`: Switch to Presentation Mode
        - `A`: Switch to Analysis Mode
        - `E`: Export current view
        """)
    
    return mode


# Export size presets based on mode
def get_export_size(format: str = 'png') -> Dict[str, Any]:
    """Get export size based on current mode and format."""
    mode = VisualizationMode.get_current_mode()
    
    if mode == 'presentation':
        return {
            'png': {'dpi': 150, 'width': 1920, 'height': 1080},
            'pdf': {'dpi': 300, 'width': 11, 'height': 8.5},
            'svg': {'width': 1920, 'height': 1080}
        }.get(format, {'dpi': 150})
    else:  # analysis
        return {
            'png': {'dpi': 300, 'width': 2400, 'height': 1600},
            'pdf': {'dpi': 600, 'width': 11, 'height': 8.5},
            'svg': {'width': 2400, 'height': 1600}
        }.get(format, {'dpi': 300})