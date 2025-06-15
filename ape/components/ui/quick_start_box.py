"""Quick Start box component for streamlined simulation setup."""

import streamlit as st
from typing import Optional, Dict, Any


def quick_start_box(presets: Dict[str, Dict[str, Any]], default_preset: str = "medium") -> Optional[str]:
    """Display a compact Quick Start section with preset options.
    
    Args:
        presets: Dictionary of preset configurations
        default_preset: The default preset to highlight
        
    Returns:
        Selected preset key or None
    """
    # Simple header without box
    st.markdown("**Quick Start**")
    
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
                    
                # Show key stats below button in one line
                stats = f"{preset['patients']} patients • {preset['duration']} years"
                if 'runtime' in preset:
                    stats += f" • {preset['runtime']}"
                st.caption(stats)
    
    return selected_preset