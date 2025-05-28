"""
Carbon Button Integration for AMD Protocol Explorer

This module provides a seamless interface to the streamlit-carbon-button component,
matching the subtle, scientific styling requirements of the application.

Includes automatic fallback to standard Streamlit buttons if Carbon buttons fail.
"""

import streamlit as st
from typing import Optional, Literal
import logging

# Set up logging
logger = logging.getLogger(__name__)

# Try to import Carbon button, with fallback flag
CARBON_AVAILABLE = True
try:
    from briquette import carbon_button
except ImportError:
    logger.warning("Carbon button component not available, using standard Streamlit buttons as fallback")
    CARBON_AVAILABLE = False

# Icon mapping for common actions in the app
ICON_MAP = {
    "📋": "Copy",  # Copy icon
    "🎯": "Play",  # Play/Run icon
    "🗑️": "TrashCan",  # Delete icon
    "💾": "Save",  # Save icon
    "📊": "ChartLine",  # Chart icon
    "⚙️": "Settings",  # Settings icon
    "➕": "Add",  # Add icon
    "✏️": "Edit",  # Edit icon
    "🔍": "Search",  # Search icon
}


def carbon_action_button(
    label: str,
    key: str,
    kind: Literal["primary", "secondary", "danger", "ghost"] = "primary",
    size: Literal["sm", "md", "lg", "xl", "2xl"] = "md",
    icon: Optional[str] = None,
    use_container_width: bool = False,
    disabled: bool = False,
    help: Optional[str] = None
) -> bool:
    """
    Create a Carbon Design System button that returns True when clicked.
    
    This wrapper provides a simple interface similar to st.button() while
    using the Carbon Design System styling. Falls back to standard Streamlit
    buttons if Carbon component is not available.
    
    Args:
        label: Button text
        key: Unique key for the button
        kind: Button style variant
        size: Button size
        icon: Optional Carbon icon name
        use_container_width: Whether to expand to container width
        disabled: Whether button is disabled
        help: Tooltip text
        
    Returns:
        bool: True if button was clicked, False otherwise
    """
    # Fallback to standard Streamlit button if Carbon not available
    if not CARBON_AVAILABLE:
        # Add icon emoji back if it was extracted
        if icon and icon in ICON_MAP.values():
            # Find the emoji for this icon
            emoji = next((k for k, v in ICON_MAP.items() if v == icon), "")
            display_label = f"{emoji} {label}" if emoji else label
        else:
            display_label = label
        
        # Map kind to type for st.button
        button_type = "primary" if kind == "primary" else "secondary"
        
        return st.button(
            display_label,
            key=f"fallback_{key}",
            type=button_type,
            use_container_width=use_container_width,
            disabled=disabled,
            help=help
        )
    
    # Try to use Carbon button with error handling
    try:
        # Initialize session state for this button if not exists
        if key not in st.session_state:
            st.session_state[key] = 0
        
        # Create container for full width support
        if use_container_width:
            container = st.container()
            with container:
                # Apply full width styling
                st.markdown(
                    f"""
                    <style>
                    [data-testid="stVerticalBlock"] > [style*="flex-direction: column;"] > [data-testid="stVerticalBlock"]:has(iframe[title="briquette.carbon_button"]) {{
                        width: 100%;
                    }}
                    iframe[title="briquette.carbon_button"] {{
                        width: 100% !important;
                    }}
                    </style>
                    """,
                    unsafe_allow_html=True
                )
                clicks = carbon_button(
                    label=label,
                    key=f"carbon_{key}",
                    kind=kind,
                    size=size,
                    icon=icon,
                    disabled=disabled
                )
        else:
            clicks = carbon_button(
                label=label,
                key=f"carbon_{key}",
                kind=kind,
                size=size,
                icon=icon,
                disabled=disabled
            )
        
        # Add help tooltip if provided
        if help:
            st.caption(help)
        
        # Check if button was clicked
        if clicks > st.session_state[key]:
            st.session_state[key] = clicks
            return True
        return False
        
    except Exception as e:
        # Log the error and fall back to standard button
        logger.error(f"Carbon button failed: {e}")
        
        # Add icon emoji back if it was extracted
        if icon and icon in ICON_MAP.values():
            emoji = next((k for k, v in ICON_MAP.items() if v == icon), "")
            display_label = f"{emoji} {label}" if emoji else label
        else:
            display_label = label
        
        # Map kind to type for st.button
        button_type = "primary" if kind == "primary" else "secondary"
        
        return st.button(
            display_label,
            key=f"fallback_{key}",
            type=button_type,
            use_container_width=use_container_width,
            disabled=disabled,
            help=help
        )


def primary_action_button(label: str, key: str, **kwargs) -> bool:
    """Create a primary action button (teal in light mode, pink-grey in dark)."""
    return carbon_action_button(label, key, kind="primary", **kwargs)


def secondary_action_button(label: str, key: str, **kwargs) -> bool:
    """Create a secondary action button."""
    return carbon_action_button(label, key, kind="secondary", **kwargs)


def danger_action_button(label: str, key: str, **kwargs) -> bool:
    """Create a danger/warning action button."""
    return carbon_action_button(label, key, kind="danger", **kwargs)


def ghost_action_button(label: str, key: str, **kwargs) -> bool:
    """Create a ghost (borderless) action button."""
    return carbon_action_button(label, key, kind="ghost", **kwargs)


def convert_emoji_to_icon(label: str) -> tuple[str, Optional[str]]:
    """
    Extract emoji from label and convert to Carbon icon name.
    
    Returns:
        tuple: (clean_label, icon_name)
    """
    # Check if label starts with an emoji
    for emoji, icon in ICON_MAP.items():
        if label.startswith(emoji):
            clean_label = label.replace(emoji, "").strip()
            return clean_label, icon
    
    return label, None