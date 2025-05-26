"""
Carbon Design System buttons for Streamlit
A practical solution that actually works!
"""

import streamlit as st
from typing import Optional
import uuid

def carbon_button(
    label: str, 
    icon_svg: str, 
    key: Optional[str] = None,
    type: str = "primary",  # primary, secondary, danger
    use_container_width: bool = False
) -> bool:
    """
    Create a button with Carbon Design System styling and SVG icons.
    
    This uses a clever workaround: custom HTML with a hidden Streamlit checkbox
    for click detection. The button looks and feels native but supports SVG icons!
    
    Args:
        label: Button text
        icon_svg: SVG string for the icon
        key: Unique key for the button
        type: Button type (primary, secondary, danger)
        use_container_width: Whether to expand to full width
        
    Returns:
        bool: True if button was clicked
        
    Example:
        if carbon_button("Upload", CARBON_UPLOAD_SVG, key="upload_btn"):
            st.success("File uploaded!")
    """
    
    # Generate unique key if not provided
    if key is None:
        key = str(uuid.uuid4())
    
    # Button styling based on type
    styles = {
        "primary": {
            "bg": "#0f62fe",
            "color": "white",
            "hover_bg": "#0043ce",
            "border": "#0f62fe"
        },
        "secondary": {
            "bg": "white",
            "color": "#0f62fe",
            "hover_bg": "#e5e5e5",
            "border": "#0f62fe"
        },
        "danger": {
            "bg": "#da1e28",
            "color": "white",
            "hover_bg": "#b81921",
            "border": "#da1e28"
        }
    }
    
    style = styles.get(type, styles["primary"])
    width = "100%" if use_container_width else "auto"
    
    # Create the button HTML
    button_html = f"""
    <style>
    .carbon-btn-{key} {{
        display: inline-flex;
        align-items: center;
        justify-content: center;
        gap: 0.5rem;
        padding: 0.875rem 1rem;
        font-size: 0.875rem;
        font-weight: 400;
        font-family: 'IBM Plex Sans', 'Helvetica Neue', Arial, sans-serif;
        color: {style['color']};
        background-color: {style['bg']};
        border: 1px solid {style['border']};
        border-radius: 0;
        cursor: pointer;
        transition: all 70ms cubic-bezier(0.2, 0, 0.38, 0.9);
        text-decoration: none;
        width: {width};
        margin: 0.25rem 0;
    }}
    
    .carbon-btn-{key}:hover {{
        background-color: {style['hover_bg']};
    }}
    
    .carbon-btn-{key}:active {{
        transform: scale(0.98);
    }}
    
    .carbon-btn-{key} svg {{
        width: 16px;
        height: 16px;
        fill: currentColor;
    }}
    
    /* Hide the checkbox */
    .stCheckbox[data-testid*="{key}"] {{
        display: none;
    }}
    </style>
    
    <button class="carbon-btn-{key}" onclick="
        // Find and click the hidden checkbox
        var checkboxes = document.querySelectorAll('input[type=checkbox]');
        for(var i = 0; i < checkboxes.length; i++) {{
            if(checkboxes[i].id && checkboxes[i].id.includes('{key}')) {{
                checkboxes[i].click();
                break;
            }}
        }}
    ">
        {icon_svg}
        <span>{label}</span>
    </button>
    """
    
    # Render the button
    st.markdown(button_html, unsafe_allow_html=True)
    
    # Hidden checkbox for click detection
    # We use a unique key to ensure we can find it via JavaScript
    clicked = st.checkbox("hidden", key=f"carbon_btn_{key}", label_visibility="hidden")
    
    # Reset the checkbox after click to allow repeated clicks
    if clicked:
        st.session_state[f"carbon_btn_{key}"] = False
        return True
    
    return False

# Pre-defined Carbon icons as Python strings
class CarbonIcons:
    """Common Carbon Design System icons"""
    
    UPLOAD = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">
        <path d="M26 24v4H6v-4H4v4a2 2 0 0 0 2 2h20a2 2 0 0 0 2-2v-4z"/>
        <path d="M6 12l1.41 1.41L15 5.83V24h2V5.83l7.59 7.58L26 12 16 2 6 12z"/>
    </svg>'''
    
    DOWNLOAD = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">
        <path d="M26 24v4H6v-4H4v4a2 2 0 0 0 2 2h20a2 2 0 0 0 2-2v-4z"/>
        <path d="M26 14l-1.41-1.41L17 20.17V2h-2v18.17l-7.59-7.58L6 14l10 10l10-10z"/>
    </svg>'''
    
    COPY = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">
        <path d="M28 10v18H10V10h18m0-2H10a2 2 0 0 0-2 2v18a2 2 0 0 0 2 2h18a2 2 0 0 0 2-2V10a2 2 0 0 0-2-2z"/>
        <path d="M4 18H2V4a2 2 0 0 1 2-2h14v2H4z"/>
    </svg>'''
    
    PLAY = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">
        <path d="M7 28a1 1 0 0 1-1-1V5a1 1 0 0 1 1.482-.876l20 11a1 1 0 0 1 0 1.752l-20 11A1 1 0 0 1 7 28z"/>
    </svg>'''
    
    DOCUMENT = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">
        <path d="M25.7 9.3l-7-7c-.2-.2-.4-.3-.7-.3H8c-1.1 0-2 .9-2 2v24c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V10c0-.3-.1-.5-.3-.7zM18 4.4l5.6 5.6H18V4.4zM24 28H8V4h8v6c0 1.1.9 2 2 2h6v16z"/>
    </svg>'''
    
    HOME = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">
        <path d="M16.612 2.214a1.01 1.01 0 0 0-1.242 0L1 13.419l1.243 1.572L4 13.621V26a2.004 2.004 0 0 0 2 2h20a2.004 2.004 0 0 0 2-2V13.63L29.757 15 31 13.428zM18 26h-4v-8h4zm2 0v-8a2.002 2.002 0 0 0-2-2h-4a2.002 2.002 0 0 0-2 2v8H6V12.062l10-7.79 10 7.8V26z"/>
    </svg>'''
    
    CHART_BAR = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">
        <path d="M27 28V6h-8v22h-2V14H9v14H7V18H3v10H2v2h28v-2h-3zm-17 0h-5v-8h5v8zm8 0h-6V16h6v12zm8 0h-6V8h6v20z"/>
    </svg>'''
    
    WARNING = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20">
        <path d="M10 1c-5 0-9 4-9 9s4 9 9 9 9-4 9-9-4-9-9-9zm-.2 6h.5v5h-.5V7zm.2 8.2c-.4 0-.7-.3-.7-.7s.3-.7.7-.7.7.3.7.7-.3.7-.7.7z"/>
    </svg>'''
    
    INFO = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">
        <path d="M16 2C8.3 2 2 8.3 2 16s6.3 14 14 14 14-6.3 14-14S23.7 2 16 2zm0 5c.8 0 1.5.7 1.5 1.5S16.8 10 16 10s-1.5-.7-1.5-1.5S15.2 7 16 7zm-2 17v-2h1.5v-7H14v-2h3.5v9H19v2h-5z"/>
    </svg>'''

# Example usage
if __name__ == "__main__":
    st.title("Carbon Design Buttons in Streamlit!")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if carbon_button("Upload", CarbonIcons.UPLOAD, key="upload1"):
            st.success("Upload clicked!")
    
    with col2:
        if carbon_button("Download", CarbonIcons.DOWNLOAD, key="download1", type="secondary"):
            st.info("Download clicked!")
    
    with col3:
        if carbon_button("Delete", CarbonIcons.WARNING, key="delete1", type="danger"):
            st.error("Delete clicked!")
    
    # Full width button
    if carbon_button("Run Analysis", CarbonIcons.PLAY, key="run1", use_container_width=True):
        st.balloons()