"""
Local implementation of Carbon Design System buttons for Streamlit.
This is a fallback in case the PyPI package is not available.
"""

import streamlit as st
from enum import Enum
from typing import Optional, Union

class CarbonIcons(Enum):
    """Available Carbon Design System icons."""
    HOME = "🏠"
    SETTINGS = "⚙️"
    SAVE = "💾"
    UPLOAD = "📤"
    DELETE = "🗑️"
    DOWNLOAD = "📥"
    COPY = "📋"
    PLAY = "▶️"
    CLOSE = "❌"
    FILTER = "🔍"
    SEARCH = "🔎"
    ADD = "➕"
    CHART_BAR = "📊"
    DOCUMENT = "📄"
    INFO = "ℹ️"
    HELP = "❓"
    WARNING = "⚠️"
    SUCCESS = "✅"

def carbon_button(
    label: str,
    key: str,
    icon: Optional[Union[CarbonIcons, str]] = None,
    button_type: str = "secondary",
    use_container_width: bool = False,
    disabled: bool = False,
    is_default: bool = False,
    aria_label: Optional[str] = None,
    **kwargs
) -> bool:
    """
    Local implementation of Carbon Design System button.
    Falls back to standard Streamlit button with emoji icons.
    """
    # Get icon value if it's an enum
    icon_str = ""
    if icon:
        if isinstance(icon, CarbonIcons):
            icon_str = icon.value + " "
        elif isinstance(icon, str):
            icon_str = icon + " "
    
    # Construct button label with icon
    full_label = f"{icon_str}{label}".strip()
    
    # Style mapping for button types
    if button_type == "primary":
        button_style = "primary"
    else:
        button_style = "secondary"
    
    # Create the button
    return st.button(
        full_label,
        key=key,
        use_container_width=use_container_width,
        disabled=disabled,
        type=button_style,
        help=aria_label
    )