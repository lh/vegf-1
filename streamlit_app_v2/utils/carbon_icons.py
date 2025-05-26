"""
IBM Carbon Design System icon definitions for Streamlit.
Icons from: https://carbondesignsystem.com/elements/icons/library/

To use these icons:
1. Visit the Carbon icon library
2. Download the SVG files you need
3. Copy the SVG content into the CARBON_ICONS dictionary below
"""

# Carbon Design System SVG icons
# These are placeholder examples - replace with actual Carbon SVG content
CARBON_ICONS = {
    # Example structure - replace with actual Carbon SVG content
    "download": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="16" height="16" fill="currentColor">
        <path d="M26 24v4H6v-4H4v4a2 2 0 0 0 2 2h20a2 2 0 0 0 2-2v-4z"/>
        <path d="M26 14l-1.41-1.41L17 20.17V2h-2v18.17l-7.59-7.58L6 14l10 10l10-10z"/>
    </svg>''',
    
    "upload": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="16" height="16" fill="currentColor">
        <path d="M26 24v4H6v-4H4v4a2 2 0 0 0 2 2h20a2 2 0 0 0 2-2v-4z"/>
        <path d="M6 12l1.41 1.41L15 5.83V24h2V5.83l7.59 7.58L26 12 16 2 6 12z"/>
    </svg>''',
    
    "play": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="16" height="16" fill="currentColor">
        <path d="M7 28a1 1 0 0 1-1-1V5a1 1 0 0 1 1.482-.876l20 11a1 1 0 0 1 0 1.752l-20 11A1 1 0 0 1 7 28z"/>
    </svg>''',
    
    "copy": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="16" height="16" fill="currentColor">
        <path d="M28 10v18H10V10h18m0-2H10a2 2 0 0 0-2 2v18a2 2 0 0 0 2 2h18a2 2 0 0 0 2-2V10a2 2 0 0 0-2-2z"/>
        <path d="M4 18H2V4a2 2 0 0 1 2-2h14v2H4z"/>
    </svg>''',
    
    "document": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="16" height="16" fill="currentColor">
        <path d="M25.7 9.3l-7-7c-.2-.2-.4-.3-.7-.3H8c-1.1 0-2 .9-2 2v24c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V10c0-.3-.1-.5-.3-.7zM18 4.4l5.6 5.6H18V4.4zM24 28H8V4h8v6c0 1.1.9 2 2 2h6v16z"/>
    </svg>''',
    
    "home": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="16" height="16" fill="currentColor">
        <path d="M16.612 2.214a1.01 1.01 0 0 0-1.242 0L1 13.419l1.243 1.572L4 13.621V26a2.004 2.004 0 0 0 2 2h20a2.004 2.004 0 0 0 2-2V13.63L29.757 15 31 13.428zM18 26h-4v-8h4zm2 0v-8a2.002 2.002 0 0 0-2-2h-4a2.002 2.002 0 0 0-2 2v8H6V12.062l10-7.79 10 7.8V26z"/>
    </svg>''',
    
    "chart-bar": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="16" height="16" fill="currentColor">
        <path d="M27 28V6h-8v22h-2V14H9v14H7V18H3v10H2v2h28v-2h-3zm-17 0h-5v-8h5v8zm8 0h-6V16h6v12zm8 0h-6V8h6v20z"/>
    </svg>''',
    
    "warning": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="16" height="16" fill="currentColor">
        <path d="M16 2C8.3 2 2 8.3 2 16s6.3 14 14 14 14-6.3 14-14S23.7 2 16 2zm-1.1 6h2.2v11h-2.2V8zM16 25c-.8 0-1.5-.7-1.5-1.5S15.2 22 16 22s1.5.7 1.5 1.5S16.8 25 16 25z"/>
    </svg>''',
    
    "information": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="16" height="16" fill="currentColor">
        <path d="M16 2C8.3 2 2 8.3 2 16s6.3 14 14 14 14-6.3 14-14S23.7 2 16 2zm0 5c.8 0 1.5.7 1.5 1.5S16.8 10 16 10s-1.5-.7-1.5-1.5S15.2 7 16 7zm-2 17v-2h1.5v-7H14v-2h3.5v9H19v2h-5z"/>
    </svg>''',
}

def get_carbon_icon(name: str, size: int = 16, color: str = "currentColor") -> str:
    """
    Get a Carbon Design System icon.
    
    Args:
        name: Icon name (e.g., 'download', 'upload', 'play')
        size: Icon size in pixels (default: 16)
        color: Icon color (default: 'currentColor' to inherit from parent)
    
    Returns:
        SVG string with specified size and color
    """
    svg = CARBON_ICONS.get(name, "")
    if svg:
        # Update size
        svg = svg.replace('width="16"', f'width="{size}"')
        svg = svg.replace('height="16"', f'height="{size}"')
        # Update color if not using currentColor
        if color != "currentColor":
            svg = svg.replace('fill="currentColor"', f'fill="{color}"')
    return svg

def carbon_icon_button(label: str, icon_name: str, key: str = None, **kwargs):
    """
    Create a Streamlit button with a Carbon icon.
    Since Streamlit doesn't support HTML in buttons, we use Unicode fallbacks.
    """
    import streamlit as st
    
    # Unicode fallbacks for buttons
    UNICODE_FALLBACKS = {
        "download": "↓",
        "upload": "↑",
        "play": "▶",
        "copy": "⊕",
        "document": "📄",
        "home": "⌂",
        "chart-bar": "📊",
        "warning": "⚠",
        "information": "ⓘ",
    }
    
    icon = UNICODE_FALLBACKS.get(icon_name, "")
    return st.button(f"{icon} {label}", key=key, **kwargs)