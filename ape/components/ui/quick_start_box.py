"""Quick Start box component for streamlined simulation setup."""

import streamlit as st
from typing import Optional, Dict, Any


def quick_start_box(presets: Dict[str, Dict[str, Any]], default_preset: str = "medium") -> Optional[str]:
    """Display a prominent Quick Start box with preset options.
    
    Args:
        presets: Dictionary of preset configurations
        default_preset: The default preset to highlight
        
    Returns:
        Selected preset key or None
    """
    # Create a highlighted container
    with st.container():
        st.markdown(
            """
            <div style="
                background-color: #f0f8ff;
                border: 2px solid #0066CC;
                border-radius: 0.5rem;
                padding: 1.5rem;
                margin-bottom: 1rem;
            ">
                <h3 style="margin-top: 0; color: #0066CC;">Quick Start</h3>
                <p style="margin-bottom: 1rem;">Choose a preset configuration to get started quickly:</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # Create columns for preset buttons inside the box
        preset_cols = st.columns(len(presets))
        selected_preset = None
        
        for col, (key, preset) in zip(preset_cols, presets.items()):
            with col:
                # Highlight the recommended option
                is_default = key == default_preset
                button_style = "primary" if is_default else "secondary"
                
                # Add recommendation badge
                label = preset['label']
                if is_default:
                    label = f"{label}\n(Recommended)"
                
                from ape.utils.carbon_button_helpers import navigation_button
                if navigation_button(
                    label,
                    key=f"preset_{key}",
                    help_text=preset['description'],
                    full_width=True,
                    button_type=button_style
                ):
                    selected_preset = key
                    
                # Show key stats below button
                st.caption(f"**{preset['patients']}** patients")
                st.caption(f"**{preset['duration']}** years")
                if 'runtime' in preset:
                    st.caption(f"~{preset['runtime']} runtime")
        
        # Add note about custom configuration
        st.markdown(
            """
            <p style="text-align: center; color: #666; margin-top: 1rem; margin-bottom: 0;">
                Need different settings? Customize below or use Advanced Settings
            </p>
            """,
            unsafe_allow_html=True
        )
    
    return selected_preset