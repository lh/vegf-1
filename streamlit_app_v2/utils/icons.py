"""
Icon definitions for the Streamlit application.
Supports both emoji and SVG icons for easy migration.
"""

from typing import Union, Dict, Any
import streamlit as st

# Icon type can be 'emoji', 'svg', or 'unicode'
ICON_TYPE = "emoji"  # Options: "emoji", "svg", "unicode"

# Emoji icon definitions
EMOJI_ICONS = {
    # Navigation
    "home": "🦍",  # Could be: 🏠, 🏡, ⌂, ◉
    "protocol": "📋",  # Could be: 📄, 🗂️, 📑, ⚙️
    "simulation": "🚀",  # Could be: ▶️, ⏵, ➤, 🎯
    "analysis": "📊",  # Could be: 📈, 📉, 📐, 🔍
    
    # Actions
    "upload": "📤",  # Could be: ⬆️, ↑, 🔼, 📁
    "download": "📥",  # Could be: ⬇️, ↓, 🔽, 💾
    "download_temp": "💾",  # For temporary files
    "duplicate": "📝",  # Could be: 🔁, ➕, 📑, 📋
    "delete": "🗑️",  # Could be: ✕, ❌, 🚮, ⊗
    "refresh": "🔄",  # Could be: ↻, ⟳, ⟲, 🔃
    
    # Status
    "success": "✅",  # Could be: ✓, ☑️, 👍, ✨
    "error": "❌",  # Could be: ✗, ⚠️, 🚫, ⛔
    "warning": "⚠️",  # Could be: ⚡, 🔔, ⚑, ❗
    "info": "ℹ️",  # Could be: 💡, 🔍, 📢, 💭
    
    # Other
    "run": "🎯",  # Could be: ▶️, ➤, ⏵, 🏃
    "close": "✕",  # Could be: ✖️, ❌, ⊗, ×
}

# Unicode icon definitions (clean, minimalist alternative to emoji)
UNICODE_ICONS = {
    # Navigation
    "home": "⌂",      # House symbol
    "protocol": "☰",   # Hamburger/list symbol
    "simulation": "▶", # Play symbol
    "analysis": "📊",  # Keep emoji for charts (no good unicode alternative)
    
    # Actions
    "upload": "↑",     # Up arrow
    "download": "↓",   # Down arrow
    "download_temp": "⇩", # Thick down arrow
    "duplicate": "⊕",  # Circled plus
    "delete": "×",     # Multiplication sign
    "refresh": "↻",    # Clockwise arrow
    
    # Status
    "success": "✓",    # Check mark
    "error": "✗",      # Ballot X
    "warning": "⚠",    # Warning sign
    "info": "ⓘ",       # Information
    
    # Other
    "run": "▶",        # Play symbol
    "close": "×",      # Multiplication sign
}

# SVG icon definitions (to be populated when switching to SVG)
# These would be actual Carbon Design System SVGs
SVG_ICONS = {
    # Example SVG icon structure:
    # "home": '<svg width="16" height="16" viewBox="0 0 32 32" fill="currentColor"><path d="..."/></svg>',
    
    # For now, we'll return the emoji as fallback
    # When ready, replace these with actual SVG strings
}

def get_icon(name: str, fallback: str = "", size: int = 16, color: str = "currentColor") -> str:
    """
    Get icon by name with optional fallback.
    
    Args:
        name: Icon name
        fallback: Fallback text/emoji if icon not found
        size: Icon size (only used for SVG)
        color: Icon color (only used for SVG)
    
    Returns:
        Icon string (emoji, unicode, or HTML for SVG)
    """
    if ICON_TYPE == "emoji":
        return EMOJI_ICONS.get(name, fallback)
    elif ICON_TYPE == "unicode":
        return UNICODE_ICONS.get(name, fallback)
    elif ICON_TYPE == "svg":
        svg = SVG_ICONS.get(name)
        if svg:
            # Inject size and color into SVG
            svg = svg.replace('width="16"', f'width="{size}"')
            svg = svg.replace('height="16"', f'height="{size}"')
            svg = svg.replace('fill="currentColor"', f'fill="{color}"')
            return svg
        # Fallback to unicode if SVG not defined
        return UNICODE_ICONS.get(name, fallback)
    else:
        return fallback

def icon(name: str, fallback: str = "", size: int = 16, color: str = "currentColor", 
         inline: bool = True) -> Union[str, None]:
    """
    Render an icon in Streamlit.
    
    For emoji: returns the emoji string
    For SVG: renders using st.markdown with unsafe_allow_html
    
    Args:
        name: Icon name
        fallback: Fallback text/emoji if icon not found
        size: Icon size (only used for SVG)
        color: Icon color (only used for SVG)
        inline: Whether to render inline (for SVG)
    
    Returns:
        Emoji string or None (SVG is rendered directly)
    """
    icon_content = get_icon(name, fallback, size, color)
    
    if ICON_TYPE == "svg" and icon_content.startswith("<svg"):
        # For SVG, we need to render it with HTML
        if inline:
            # Inline SVG for use in text
            html = f'<span style="display: inline-block; vertical-align: middle;">{icon_content}</span>'
        else:
            # Block SVG
            html = icon_content
        st.markdown(html, unsafe_allow_html=True)
        return None
    else:
        # For emoji, just return the string
        return icon_content

def icon_button(label: str, icon_name: str, **kwargs) -> bool:
    """
    Create a button with an icon.
    Handles both emoji and SVG icons seamlessly.
    """
    if ICON_TYPE == "emoji":
        # Simple emoji in label
        icon_str = get_icon(icon_name, "")
        return st.button(f"{icon_str} {label}", **kwargs)
    else:
        # For SVG, we need a more complex approach
        # This is a limitation of Streamlit - buttons don't support HTML
        # So we fall back to emoji for buttons
        icon_str = EMOJI_ICONS.get(icon_name, "")
        return st.button(f"{icon_str} {label}", **kwargs)