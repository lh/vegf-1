"""
Streamlit Button Styling Utilities

This module provides solutions for the notorious Streamlit button red text issue.
After much CSS wrestling, we've found the winning combination!
"""

import streamlit as st
from typing import Optional, Dict, Any


def remove_button_red_text():
    """
    Removes the red text that appears when clicking Streamlit buttons.
    
    THE SOLUTION: Target the <p> tags inside buttons directly and force their color
    with !important on ALL states, plus remove transitions.
    
    Usage:
        Just call this function once in your app (ideally near the top):
        
        from utils.button_styling import remove_button_red_text
        remove_button_red_text()
    """
    st.markdown("""
    <style>
        /* Target the specific p tags that turn red - this is the key */
        div[data-testid="stButton"] button p {
            color: #262730 !important;
            transition: none !important;
        }
        
        /* Force color on all states */
        div[data-testid="stButton"] button:hover p,
        div[data-testid="stButton"] button:active p,
        div[data-testid="stButton"] button:focus p {
            color: #262730 !important;
        }
        
        /* Target markdown bold text specifically */
        div[data-testid="stButton"] button p strong {
            color: #262730 !important;
        }
    </style>
    """, unsafe_allow_html=True)


def style_navigation_buttons(
    bg_color: str = "#f8f9fb",  # Just slightly brighter than background  
    hover_color: str = "#ffffff",  # Bright white on hover
    active_color: str = "#d0d2d6",  # Darker than background on click
    height: str = "120px",
    include_red_fix: bool = True,
    use_shadow: bool = False  # Clean, no shadows by default
):
    """
    Style buttons to look like navigation cards with hover effects.
    
    Args:
        bg_color: Background color for normal state
        hover_color: Background color on hover (should be darker)
        active_color: Background color when clicked (darkest)
        height: Height of the button cards
        include_red_fix: Whether to include the red text fix
        
    Usage:
        from utils.button_styling import style_navigation_buttons
        style_navigation_buttons()
        
        # Then create your buttons normally
        if st.button("Navigate somewhere"):
            st.switch_page("pages/somewhere.py")
    """
    # Build shadow CSS if enabled
    shadow_css = ""
    if use_shadow:
        shadow_css = "box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);"
        shadow_hover = "box-shadow: 0 2px 4px rgba(0, 0, 0, 0.12);"
        shadow_active = "box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.1);"
    else:
        shadow_hover = ""
        shadow_active = ""
    
    css = f"""
    <style>
        /* Style buttons as cards - include ALL button types */
        div[data-testid="stButton"] button,
        button[kind="secondary"],
        button[kind="primary"],
        div.stPopover button {{
            background-color: {bg_color};
            border: 1px solid {hover_color};
            border-radius: 8px;
            transition: all 0.2s ease;
            {shadow_css}
        }}
        
        /* Hover state - darker with subtle shadow */
        div[data-testid="stButton"] button:hover,
        button[kind="secondary"]:hover,
        button[kind="primary"]:hover,
        div.stPopover button:hover {{
            background-color: {hover_color};
            border-color: {active_color};
            {shadow_hover}
        }}
        
        /* Active state - pressed appearance */
        div[data-testid="stButton"] button:active,
        button[kind="secondary"]:active,
        button[kind="primary"]:active,
        div.stPopover button:active {{
            background-color: {active_color} !important;
            border-color: {active_color} !important;
            {shadow_active}
        }}
        
        /* Remove focus outline */
        div[data-testid="stButton"] button:focus,
        button[kind="secondary"]:focus,
        button[kind="primary"]:focus,
        div.stPopover button:focus {{
            outline: none !important;
            box-shadow: none !important;
        }}
    """
    
    if include_red_fix:
        css += """
        /* THE FIX: Target p tags directly to prevent red text - INCLUDING POPOVERS */
        div[data-testid="stButton"] button p,
        button[kind="secondary"] p,
        button[kind="primary"] p,
        div.stPopover button p,
        [data-testid="baseButton-secondary"] p {
            color: #262730 !important;
            transition: none !important;
        }
        
        div[data-testid="stButton"] button:hover p,
        div[data-testid="stButton"] button:active p,
        div[data-testid="stButton"] button:focus p,
        button[kind="secondary"]:hover p,
        button[kind="secondary"]:active p,
        button[kind="secondary"]:focus p,
        button[kind="primary"]:hover p,
        button[kind="primary"]:active p,
        button[kind="primary"]:focus p,
        div.stPopover button:hover p,
        div.stPopover button:active p,
        div.stPopover button:focus p,
        [data-testid="baseButton-secondary"]:hover p,
        [data-testid="baseButton-secondary"]:active p,
        [data-testid="baseButton-secondary"]:focus p {
            color: #262730 !important;
        }
        
        div[data-testid="stButton"] button p strong,
        button[kind="secondary"] p strong,
        button[kind="primary"] p strong,
        div.stPopover button p strong,
        [data-testid="baseButton-secondary"] p strong {
            color: #262730 !important;
        }
    """
    
    
    # Always hide popover chevrons and fix their color
    css += """
        /* Hide popover chevrons completely */
        div.stPopover svg {
            display: none !important;
        }
        
        /* Just in case, also force chevron color to prevent red */
        div.stPopover svg path {
            fill: #262730 !important;
            stroke: #262730 !important;
        }
    """
    
    css += "</style>"
    st.markdown(css, unsafe_allow_html=True)


def create_button_group_styling(
    buttons: Dict[str, str],
    columns: int = 3
) -> None:
    """
    Create a group of styled navigation buttons.
    
    Args:
        buttons: Dictionary of {button_text: page_path}
        columns: Number of columns for button layout
        
    Usage:
        buttons = {
            "📋 **Protocol Manager**\\n\\nBrowse protocols": "pages/1_Protocol_Manager.py",
            "🚀 **Run Simulation**\\n\\nExecute sims": "pages/2_Run_Simulation.py",
            "📊 **Analysis**\\n\\nView results": "pages/3_Analysis_Overview.py"
        }
        create_button_group_styling(buttons)
    """
    # Apply styling
    style_navigation_buttons()
    
    # Create columns and buttons
    cols = st.columns(columns)
    
    for idx, (text, path) in enumerate(buttons.items()):
        with cols[idx % columns]:
            if st.button(text, use_container_width=True):
                st.switch_page(path)


# For backward compatibility
def apply_no_red_button_fix():
    """Deprecated: Use remove_button_red_text() instead."""
    remove_button_red_text()


def style_navigation_buttons_subtle(include_red_fix: bool = True):
    """
    Alternative subtle styling - very light buttons with minimal shadows.
    Perfect for a clean, modern look.
    """
    style_navigation_buttons(
        bg_color="#fafbfc",      # Very subtle off-white
        hover_color="#f6f8fa",   # Slightly darker on hover
        active_color="#f0f2f4",  # More contrast on click
        include_red_fix=include_red_fix,
        use_shadow=True          # Subtle shadows
    )


def style_navigation_buttons_flat(include_red_fix: bool = True):
    """
    Flat design - no shadows, just color changes.
    Clean and minimalist.
    """
    style_navigation_buttons(
        bg_color="#f8f9fa",      # Light gray
        hover_color="#e9ecef",   # Medium gray on hover
        active_color="#dee2e6",  # Darker on click
        include_red_fix=include_red_fix,
        use_shadow=False         # No shadows
    )


def style_navigation_buttons_progressive(include_red_fix: bool = True):
    """
    Progressive brightness - subtle light → bright → dark.
    Resting: Slightly brighter than background
    Hover: Bright/white to draw attention  
    Click: Darker than background for pressed feel
    """
    style_navigation_buttons(
        bg_color="#f8f9fb",      # Just slightly brighter than background
        hover_color="#ffffff",   # Bright white on hover
        active_color="#d0d2d6",  # Darker than background on click
        include_red_fix=include_red_fix,
        use_shadow=False         # Clean, no shadows
    )


# Document the CSS pattern for reference
CSS_PATTERN = """
The key insight for removing Streamlit's red button text:

1. Target the <p> tags INSIDE buttons, not the button itself
2. Use !important on the color property
3. Remove transitions to prevent color animation
4. Apply to ALL states (normal, hover, active, focus)
5. Don't forget <strong> tags for bold text

Critical CSS:
-----------
div[data-testid="stButton"] button p {
    color: #262730 !important;
    transition: none !important;
}

This overrides Streamlit's JavaScript-applied inline styles.
"""