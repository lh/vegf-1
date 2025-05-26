"""
Cleaner Carbon button implementation using session state
"""

import streamlit as st
from typing import Optional
import hashlib

def carbon_button_clean(
    label: str,
    icon_svg: str, 
    key: str,
    type: str = "primary",
    use_container_width: bool = False
) -> bool:
    """
    Carbon button using session state instead of hidden checkboxes.
    This avoids the checkbox visibility issues entirely.
    """
    
    # Initialize session state for this button
    if f"button_{key}_clicked" not in st.session_state:
        st.session_state[f"button_{key}_clicked"] = False
    
    # Generate a unique component key
    component_key = hashlib.md5(f"carbon_{key}".encode()).hexdigest()[:8]
    
    # Button styling
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
        "minimal": {
            "bg": "#f4f4f4",
            "color": "#393939",
            "hover_bg": "#e0e0e0",
            "border": "transparent"
        }
    }
    
    style = styles.get(type, styles["primary"])
    width = "100%" if use_container_width else "auto"
    
    # Create button with unique ID
    button_html = f"""
    <style>
    .carbon-{component_key} {{
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
    
    .carbon-{component_key}:hover {{
        background-color: {style['hover_bg']};
    }}
    
    .carbon-{component_key}:active {{
        transform: scale(0.98);
    }}
    
    .carbon-{component_key} svg {{
        width: 16px;
        height: 16px;
        fill: currentColor;
    }}
    </style>
    
    <button class="carbon-{component_key}" id="btn_{component_key}">
        {icon_svg}
        <span>{label}</span>
    </button>
    
    <script>
    // Use Streamlit's setComponentValue if available
    document.getElementById('btn_{component_key}').addEventListener('click', function() {{
        // Set a flag in sessionStorage
        window.sessionStorage.setItem('carbon_clicked_{key}', 'true');
        // Force Streamlit to rerun
        window.location.href = window.location.href;
    }});
    </script>
    """
    
    # Render the button
    st.markdown(button_html, unsafe_allow_html=True)
    
    # Check if button was clicked (this is a simplified version)
    # In practice, you'd need to use Streamlit components for proper communication
    clicked = st.session_state[f"button_{key}_clicked"]
    
    # Reset after returning true
    if clicked:
        st.session_state[f"button_{key}_clicked"] = False
        return True
    
    return False


# Simpler approach: Container-based buttons
def carbon_container_button(
    label: str,
    icon_svg: str,
    key: str,
    type: str = "minimal"
) -> bool:
    """
    Uses a container with markdown for the icon and a regular button.
    No hidden elements needed!
    """
    
    # Create a unique container
    container = st.container()
    
    with container:
        # Apply custom styling to this container only
        st.markdown(f"""
        <style>
        [data-testid="stVerticalBlock"]:has(button:contains("{label}")) {{
            background-color: {"#f4f4f4" if type == "minimal" else "transparent"};
            border-radius: 0.25rem;
            padding: 0;
            margin: 0.25rem 0;
        }}
        
        [data-testid="stVerticalBlock"]:has(button:contains("{label}")) button {{
            background-color: transparent !important;
            border: none !important;
            width: 100%;
            text-align: left;
            padding: 0.5rem 1rem !important;
        }}
        
        [data-testid="stVerticalBlock"]:has(button:contains("{label}")):hover {{
            background-color: {"#e0e0e0" if type == "minimal" else "#f4f4f4"};
        }}
        
        .carbon-icon-{key} {{
            display: inline-block;
            vertical-align: middle;
            margin-right: 0.5rem;
        }}
        
        .carbon-icon-{key} svg {{
            width: 16px;
            height: 16px;
            fill: currentColor;
        }}
        </style>
        """, unsafe_allow_html=True)
        
        # Create columns for icon and button
        col1, col2 = st.columns([0.1, 0.9], gap="small")
        
        with col1:
            st.markdown(f'<div class="carbon-icon-{key}">{icon_svg}</div>', unsafe_allow_html=True)
        
        with col2:
            # Regular Streamlit button
            return st.button(label, key=key, use_container_width=True)