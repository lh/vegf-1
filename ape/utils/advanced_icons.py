"""
Advanced icon implementation with better SVG button support.
"""

import streamlit as st
from typing import Optional

def svg_button(label: str, svg: str, key: str = None, 
               width: int = 20, height: int = 20, 
               **kwargs) -> bool:
    """
    Create a button with an inline SVG icon using custom HTML.
    
    This is a workaround for Streamlit's lack of native SVG button support.
    It creates a custom styled button that looks like a regular Streamlit button.
    """
    import uuid
    
    # Generate unique key if not provided
    if key is None:
        key = str(uuid.uuid4())
    
    # Create button styling that matches Streamlit's default
    button_style = """
    <style>
    .svg-button {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        padding: 0.25rem 0.75rem;
        font-weight: 400;
        color: inherit;
        background-color: transparent;
        border: 1px solid rgba(49, 51, 63, 0.2);
        border-radius: 0.5rem;
        cursor: pointer;
        transition: all 0.2s;
        font-family: "Source Sans Pro", sans-serif;
        font-size: 1rem;
        width: 100%;
        text-decoration: none;
    }
    
    .svg-button:hover {
        border-color: rgb(255, 75, 75);
        color: rgb(255, 75, 75);
    }
    
    .svg-button svg {
        margin-right: 0.5rem;
        flex-shrink: 0;
    }
    
    .svg-button:active {
        transform: scale(0.98);
    }
    </style>
    """
    
    # Inject the SVG with proper sizing
    sized_svg = svg.replace('width="16"', f'width="{width}"').replace('height="16"', f'height="{height}"')
    
    # Create the button HTML
    button_html = f"""
    {button_style}
    <button class="svg-button" onclick="window.svgButtonClicked_{key} = true">
        {sized_svg}
        <span>{label}</span>
    </button>
    """
    
    # Display the button
    st.markdown(button_html, unsafe_allow_html=True)
    
    # Check if button was clicked using JavaScript bridge
    # This is a simplified version - in production you'd use Streamlit components
    return False  # This would need proper state management

# Alternative approach: Icon + Text columns
def icon_text_button(icon_svg: str, label: str, key: str = None, **kwargs) -> bool:
    """
    Create a button-like interface using columns.
    More reliable than custom HTML but slightly different appearance.
    """
    col1, col2 = st.columns([1, 10], gap="small")
    
    with col1:
        st.markdown(f'<div style="padding-top: 6px;">{icon_svg}</div>', 
                   unsafe_allow_html=True)
    
    with col2:
        return st.button(label, key=key, **kwargs)

# Even simpler: Use Unicode symbols that look like icons
UNICODE_ICONS = {
    "upload": "⬆",     # Up arrow
    "download": "⬇",   # Down arrow  
    "duplicate": "⊕",  # Circled plus
    "delete": "⊗",     # Circled X
    "home": "⌂",       # House
    "settings": "⚙",   # Gear
    "play": "▶",       # Play
    "refresh": "↻",    # Refresh
    "check": "✓",      # Check
    "cross": "✗",      # Cross
    "info": "ⓘ",       # Info
    "warning": "⚠",    # Warning
}

def get_unicode_icon(name: str, fallback: str = "") -> str:
    """Get a Unicode symbol that looks like an icon."""
    return UNICODE_ICONS.get(name, fallback)