"""
Styled Carbon buttons with custom colors and hover effects
"""

import streamlit as st
from typing import Optional
import uuid

def styled_carbon_button(
    label: str, 
    icon_svg: str, 
    key: Optional[str] = None,
    style: str = "minimal",  # minimal, outlined, filled
    use_container_width: bool = False
) -> bool:
    """
    Create a styled Carbon button with custom appearance.
    
    Styles:
    - minimal: Black icon on grey background, bright on hover
    - outlined: Black icon with grey border, filled on hover
    - filled: White icon on dark background
    """
    
    # Generate unique key if not provided
    if key is None:
        key = str(uuid.uuid4())
    
    width = "100%" if use_container_width else "auto"
    
    # Define styles
    styles_config = {
        "minimal": """
        .carbon-btn-{key} {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 0.5rem;
            padding: 0.625rem 1rem;
            font-size: 0.875rem;
            font-weight: 400;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            color: #393939;  /* Dark grey/black */
            background-color: #f4f4f4;  /* Light grey background */
            border: 1px solid transparent;
            border-radius: 0.25rem;
            cursor: pointer;
            transition: all 0.15s ease;
            text-decoration: none;
            width: {width};
            margin: 0.25rem 0;
        }}
        
        .carbon-btn-{key}:hover {{
            color: #161616;  /* Pure black */
            background-color: #e0e0e0;  /* Darker grey */
            transform: translateY(-1px);
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }}
        
        .carbon-btn-{key}:active {{
            color: #ffffff;  /* White text on click */
            background-color: #525252;  /* Dark grey */
            transform: translateY(0);
            box-shadow: none;
        }}
        """,
        
        "outlined": """
        .carbon-btn-{key} {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 0.5rem;
            padding: 0.625rem 1rem;
            font-size: 0.875rem;
            font-weight: 400;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            color: #393939;
            background-color: transparent;
            border: 1px solid #8d8d8d;
            border-radius: 0.25rem;
            cursor: pointer;
            transition: all 0.15s ease;
            text-decoration: none;
            width: {width};
            margin: 0.25rem 0;
        }}
        
        .carbon-btn-{key}:hover {{
            color: #161616;
            background-color: #e0e0e0;
            border-color: #393939;
        }}
        
        .carbon-btn-{key}:active {{
            color: #ffffff;
            background-color: #393939;
            border-color: #393939;
        }}
        """,
        
        "filled": """
        .carbon-btn-{key} {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 0.5rem;
            padding: 0.625rem 1rem;
            font-size: 0.875rem;
            font-weight: 400;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            color: #ffffff;
            background-color: #393939;
            border: 1px solid #393939;
            border-radius: 0.25rem;
            cursor: pointer;
            transition: all 0.15s ease;
            text-decoration: none;
            width: {width};
            margin: 0.25rem 0;
        }}
        
        .carbon-btn-{key}:hover {{
            background-color: #525252;
            border-color: #525252;
            transform: translateY(-1px);
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
        }}
        
        .carbon-btn-{key}:active {{
            background-color: #161616;
            border-color: #161616;
            transform: translateY(0);
            box-shadow: none;
        }}
        """
    }
    
    # Add icon-specific styling
    icon_style = """
        .carbon-btn-{key} svg {{
            width: 16px;
            height: 16px;
            fill: currentColor;
            transition: all 0.15s ease;
        }}
        
        /* Hide the checkbox - multiple selectors for reliability */
        .stCheckbox:has(input[id*="{key}"]) {{
            display: none !important;
            height: 0 !important;
            visibility: hidden !important;
            position: absolute !important;
            left: -9999px !important;
        }}
        
        /* Additional selector for different Streamlit versions */
        [data-testid="stCheckbox"]:has(input[id*="{key}"]) {{
            display: none !important;
        }}
        
        /* Hide the entire row containing our checkbox */
        .row-widget.stCheckbox:has(input[id*="{key}"]) {{
            display: none !important;
        }}
    """
    
    # Create the button HTML
    button_html = f"""
    <style>
    {styles_config.get(style, styles_config["minimal"]).format(key=key, width=width)}
    {icon_style.format(key=key)}
    </style>
    
    <button class="carbon-btn-{key}" onclick="
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
    clicked = st.checkbox("hidden", key=f"carbon_btn_{key}", label_visibility="hidden")
    
    # Reset the checkbox after click
    if clicked:
        st.session_state[f"carbon_btn_{key}"] = False
        return True
    
    return False

# Advanced gradient button
def gradient_carbon_button(
    label: str,
    icon_svg: str,
    key: Optional[str] = None,
    gradient_from: str = "#f4f4f4",
    gradient_to: str = "#e0e0e0",
    hover_from: str = "#e0e0e0", 
    hover_to: str = "#c6c6c6",
    use_container_width: bool = False
) -> bool:
    """
    Create a Carbon button with gradient effects
    """
    
    if key is None:
        key = str(uuid.uuid4())
    
    width = "100%" if use_container_width else "auto"
    
    button_html = f"""
    <style>
    .carbon-gradient-{key} {{
        display: inline-flex;
        align-items: center;
        justify-content: center;
        gap: 0.5rem;
        padding: 0.75rem 1.25rem;
        font-size: 0.875rem;
        font-weight: 500;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        color: #161616;
        background: linear-gradient(135deg, {gradient_from} 0%, {gradient_to} 100%);
        border: none;
        border-radius: 0.375rem;
        cursor: pointer;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        text-decoration: none;
        width: {width};
        margin: 0.25rem 0;
        position: relative;
        overflow: hidden;
    }}
    
    .carbon-gradient-{key}::before {{
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: linear-gradient(135deg, {hover_from} 0%, {hover_to} 100%);
        opacity: 0;
        transition: opacity 0.3s ease;
    }}
    
    .carbon-gradient-{key}:hover::before {{
        opacity: 1;
    }}
    
    .carbon-gradient-{key}:hover {{
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    }}
    
    .carbon-gradient-{key}:active {{
        transform: translateY(0);
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
    }}
    
    .carbon-gradient-{key} svg {{
        width: 18px;
        height: 18px;
        fill: currentColor;
        position: relative;
        z-index: 1;
    }}
    
    .carbon-gradient-{key} span {{
        position: relative;
        z-index: 1;
    }}
    
    /* Hide the checkbox */
    .stCheckbox[data-testid*="{key}"] {{
        display: none;
    }}
    </style>
    
    <button class="carbon-gradient-{key}" onclick="
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
    
    st.markdown(button_html, unsafe_allow_html=True)
    clicked = st.checkbox("hidden", key=f"carbon_gradient_{key}", label_visibility="hidden")
    
    if clicked:
        st.session_state[f"carbon_gradient_{key}"] = False
        return True
    
    return False