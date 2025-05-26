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
    """
    Carbon Design System icons (v11)
    Downloaded from: https://carbondesignsystem.com/
    
    To add more icons:
    1. Visit https://carbondesignsystem.com/elements/icons/library/
    2. Search for the icon you need
    3. Download as SVG (32px size recommended)
    4. Copy the SVG content here
    
    Benefits of embedding:
    - No npm/node dependencies
    - Works on Streamlit Community Cloud
    - Fast loading (no external requests)
    - Version stable
    """
    
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

    ADD = '''<!-- Generator: Adobe Illustrator 24.0.3, SVG Export Plug-In . SVG Version: 6.00 Build 0)  -->
<svg version="1.1" id="icon" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" x="0px" y="0px"
	 width="32px" height="32px" viewBox="0 0 32 32" style="enable-background:new 0 0 32 32;" xml:space="preserve">
<style type="text/css">
	.st0{fill:none;}
</style>
<polygon points="17,15 17,8 15,8 15,15 8,15 8,17 15,17 15,24 17,24 17,17 24,17 24,15 "/>
<rect class="st0" width="32" height="32"/>
</svg>'''
    
    CLOSE = '''<svg id="icon" xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 32 32">
  <defs>
    <style>
      .cls-1 {
        fill: none;
      }
    </style>
  </defs>
  <polygon points="17.4141 16 24 9.4141 22.5859 8 16 14.5859 9.4143 8 8 9.4141 14.5859 16 8 22.5859 9.4143 24 16 17.4141 22.5859 24 24 22.5859 17.4141 16"/>
  <g id="_Transparent_Rectangle_" data-name="&amp;lt;Transparent Rectangle&amp;gt;">
    <rect class="cls-1" width="32" height="32"/>
  </g>
</svg>'''
    
    DELETE = '''<svg id="icon" xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 32 32">
  <defs>
    <style>
      .cls-1 {
        fill: none;
      }
    </style>
  </defs>
  <path d="m29,26H12c-.2651,0-.5195-.1053-.707-.2928L2.293,16.7072c-.3906-.3906-.3906-1.0237,0-1.4143L11.293,6.2928c.1875-.1875.4419-.2928.707-.2928h17c.5522,0,1,.4478,1,1v18c0,.5522-.4478,1-1,1Zm-16.5857-2h15.5857V8h-15.5857l-8,8,8,8Z"/>
  <polygon points="20.4141 16 25 11.4141 23.5859 10 19 14.5859 14.4143 10 13 11.4141 17.5859 16 13 20.5859 14.4143 22 19 17.4141 23.5859 22 25 20.5859 20.4141 16"/>
  <rect id="_Transparent_Rectangle_" data-name="&amp;lt;Transparent Rectangle&amp;gt;" class="cls-1" width="32" height="32"/>
</svg>'''
    
    SAVE = '''<svg id="icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><defs><style>.cls-1{fill:none;}</style></defs><title>save</title><path d="M27.71,9.29l-5-5A1,1,0,0,0,22,4H6A2,2,0,0,0,4,6V26a2,2,0,0,0,2,2H26a2,2,0,0,0,2-2V10A1,1,0,0,0,27.71,9.29ZM12,6h8v4H12Zm8,20H12V18h8Zm2,0V18a2,2,0,0,0-2-2H12a2,2,0,0,0-2,2v8H6V6h4v4a2,2,0,0,0,2,2h8a2,2,0,0,0,2-2V6.41l4,4V26Z"/><rect id="_Transparent_Rectangle_" data-name="&lt;Transparent Rectangle&gt;" class="cls-1" width="32" height="32"/></svg>'''
    
    SETTINGS = '''<svg id="icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><defs><style>.cls-1{fill:none;}</style></defs><title>settings</title><path d="M27,16.76c0-.25,0-.5,0-.76s0-.51,0-.77l1.92-1.68A2,2,0,0,0,29.3,11L26.94,7a2,2,0,0,0-1.73-1,2,2,0,0,0-.64.1l-2.43.82a11.35,11.35,0,0,0-1.31-.75l-.51-2.52a2,2,0,0,0-2-1.61H13.64a2,2,0,0,0-2,1.61l-.51,2.52a11.48,11.48,0,0,0-1.32.75L7.43,6.06A2,2,0,0,0,6.79,6,2,2,0,0,0,5.06,7L2.7,11a2,2,0,0,0,.41,2.51L5,15.24c0,.25,0,.5,0,.76s0,.51,0,.77L3.11,18.45A2,2,0,0,0,2.7,21L5.06,25a2,2,0,0,0,1.73,1,2,2,0,0,0,.64-.1l2.43-.82a11.35,11.35,0,0,0,1.31.75l.51,2.52a2,2,0,0,0,2,1.61h4.72a2,2,0,0,0,2-1.61l.51-2.52a11.48,11.48,0,0,0,1.32-.75l2.42.82a2,2,0,0,0,.64.1,2,2,0,0,0,1.73-1L29.3,21a2,2,0,0,0-.41-2.51ZM25.21,24l-3.43-1.16a8.86,8.86,0,0,1-2.71,1.57L18.36,28H13.64l-.71-3.55a9.36,9.36,0,0,1-2.7-1.57L6.79,24,4.43,20l2.72-2.4a8.9,8.9,0,0,1,0-3.13L4.43,12,6.79,8l3.43,1.16a8.86,8.86,0,0,1,2.71-1.57L13.64,4h4.72l.71,3.55a9.36,9.36,0,0,1,2.7,1.57L25.21,8,27.57,12l-2.72,2.4a8.9,8.9,0,0,1,0,3.13L27.57,20Z" transform="translate(0 0)"/><path d="M16,22a6,6,0,1,1,6-6A5.94,5.94,0,0,1,16,22Zm0-10a3.91,3.91,0,0,0-4,4,3.91,3.91,0,0,0,4,4,3.91,3.91,0,0,0,4-4A3.91,3.91,0,0,0,16,12Z" transform="translate(0 0)"/><rect id="_Transparent_Rectangle_" data-name="&lt;Transparent Rectangle&gt;" class="cls-1" width="32" height="32"/></svg>'''
    
    SUCCESS = '''<svg id="icon" xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 32 32">
  <defs>
    <style>
      .cls-1 {
        fill: none;
      }
    </style>
  </defs>
  <path d="M16,2A14,14,0,1,0,30,16,14,14,0,0,0,16,2ZM14,21.5908l-5-5L10.5906,15,14,18.4092,21.41,11l1.5957,1.5859Z"/>
  <polygon id="inner-path" class="cls-1" points="14 21.591 9 16.591 10.591 15 14 18.409 21.41 11 23.005 12.585 14 21.591"/>
  <rect id="_Transparent_Rectangle_" data-name="&lt;Transparent Rectangle&gt;" class="cls-1" width="32" height="32"/>
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