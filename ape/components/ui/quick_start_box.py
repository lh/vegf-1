"""Quick Start box component for streamlined simulation setup."""

import streamlit as st
from typing import Optional, Dict, Any


def quick_start_box(presets: Dict[str, Dict[str, Any]], default_preset: str = "medium", 
                   title: str = "Quick Start", engine_widget = None) -> Optional[str]:
    """Display a compact Quick Start section with preset options.
    
    Args:
        presets: Dictionary of preset configurations
        default_preset: The default preset to highlight
        title: Title to display (defaults to "Quick Start")
        engine_widget: Optional widget to display on the right
        
    Returns:
        Selected preset key or None
    """
    # Create columns for title and engine selector
    if engine_widget is not None:
        title_col, engine_col = st.columns([3, 1])
        with title_col:
            # Truncate title if too long
            display_title = title if len(title) <= 40 else title[:37] + "..."
            st.markdown(f"**{display_title}**")
        with engine_col:
            engine_widget()
    else:
        # Simple header without box
        st.markdown(f"**{title}**")
    
    # Create columns for preset buttons
    preset_cols = st.columns(len(presets))
    selected_preset = None
    
    for col, (key, preset) in zip(preset_cols, presets.items()):
            with col:
                # Highlight the recommended option
                is_default = key == default_preset
                button_style = "primary" if is_default else "secondary"
                
                # Use label as is
                label = preset['label']
                
                from ape.utils.carbon_button_helpers import navigation_button
                if navigation_button(
                    label,
                    key=f"preset_{key}",
                    help_text=preset['description'],
                    full_width=True,
                    button_type=button_style
                ):
                    selected_preset = key
    
    return selected_preset