"""
Carbon Button Helpers for Streamlit APE Application

Provides a consistent wrapper around streamlit-carbon-button with
APE-specific defaults and icon mappings.
"""

from typing import Optional, Dict, Any, List
import streamlit as st

from streamlit_carbon_button import carbon_button, CarbonIcons

CARBON_AVAILABLE = True

# Icon mapping based on available Carbon icons (260 total in v1.3.0)
# Maps semantic names to actual CarbonIcons
ICON_MAP = {
    # Navigation
    'home': CarbonIcons.HOME,
    'settings': CarbonIcons.SETTINGS,
    'menu': CarbonIcons.MENU,
    'back': CarbonIcons.ARROW_LEFT,
    'forward': CarbonIcons.ARROW_RIGHT,
    
    # Actions
    'save': CarbonIcons.SAVE,
    'load': CarbonIcons.UPLOAD,
    'upload': CarbonIcons.UPLOAD,
    'delete': CarbonIcons.DELETE,
    'download': CarbonIcons.DOWNLOAD,
    'copy': CarbonIcons.COPY,
    'duplicate': CarbonIcons.COPY,
    'edit': CarbonIcons.EDIT,
    'play': CarbonIcons.PLAY,
    'run': CarbonIcons.PLAY,
    'close': CarbonIcons.CLOSE,
    'dismiss': CarbonIcons.CLOSE,
    'export': CarbonIcons.EXPORT,
    'refresh': CarbonIcons.RENEW,
    'reset': CarbonIcons.RESET,
    'swap': CarbonIcons.ARROWS_HORIZONTAL,
    
    # Data operations
    'filter': CarbonIcons.FILTER,
    'search': CarbonIcons.SEARCH,
    'add': CarbonIcons.ADD,
    'new': CarbonIcons.ADD,
    'sort': CarbonIcons.SORT_ASCENDING,
    'table': CarbonIcons.TABLE,
    
    # Visualization & Analytics
    'chart': CarbonIcons.CHART_BAR,
    'analysis': CarbonIcons.ANALYTICS,
    'analytics': CarbonIcons.ANALYTICS,
    'compare': CarbonIcons.CHART_BAR_OVERLAY,
    'line_chart': CarbonIcons.CHART_LINE,
    'scatter': CarbonIcons.CHART_SCATTER,
    'histogram': CarbonIcons.CHART_HISTOGRAM,
    'waterfall': CarbonIcons.CHART_WATERFALL,
    'report': CarbonIcons.REPORT,
    'dashboard': CarbonIcons.DASHBOARD,
    
    # File operations
    'document': CarbonIcons.DOCUMENT,
    'protocol': CarbonIcons.DOCUMENT,
    'csv': CarbonIcons.CSV,
    'pdf': CarbonIcons.PDF,
    'json': CarbonIcons.JSON,
    
    # Status
    'info': CarbonIcons.INFO,
    'help': CarbonIcons.HELP,
    'warning': CarbonIcons.WARNING,
    'success': CarbonIcons.SUCCESS,
    
    # View modes
    'view': CarbonIcons.VIEW,
    'view_off': CarbonIcons.VIEW_OFF,
    'side_by_side': CarbonIcons.SIDE_PANEL_OPEN,
    'overlay': CarbonIcons.CHART_BAR_OVERLAY,
    'maximize': CarbonIcons.MAXIMIZE,
    'minimize': CarbonIcons.MINIMIZE,
    'expand': CarbonIcons.EXPAND_ALL,
    'collapse': CarbonIcons.COLLAPSE_ALL,
    
    # Time/Calendar
    'time': CarbonIcons.TIME,
    'timer': CarbonIcons.TIMER,
    'calendar': CarbonIcons.CALENDAR,
    
    # Arrows for navigation/comparison
    'arrow_up': CarbonIcons.ARROW_UP,
    'arrow_down': CarbonIcons.ARROW_DOWN,
    'arrow_left': CarbonIcons.ARROW_LEFT,
    'arrow_right': CarbonIcons.ARROW_RIGHT,
    'chevron_up': CarbonIcons.CHEVRON_UP,
    'chevron_down': CarbonIcons.CHEVRON_DOWN,
}

# Button style configuration
BUTTON_STYLES = {
    'navigation': {'button_type': 'ghost', 'size': 'sm'},
    'primary_action': {'button_type': 'primary'},
    'secondary_action': {'button_type': 'secondary'},
    'danger_action': {'button_type': 'danger'},
    'ghost_action': {'button_type': 'ghost'},
}


def ape_button(
    label: str,
    key: str,
    icon: Optional[str] = None,
    button_type: str = "secondary",
    is_primary_action: bool = False,
    is_danger: bool = False,
    full_width: bool = False,
    disabled: bool = False,
    help_text: Optional[str] = None,
    **kwargs
) -> bool:
    """
    APE-specific wrapper for carbon_button with sensible defaults.
    
    Args:
        label: Button text (can be empty for icon-only buttons)
        key: Unique key for button (required by Streamlit)
        icon: Icon name (string) or CarbonIcons enum value
        button_type: "primary", "secondary", "danger", "ghost"
        is_primary_action: Makes this the default action with special styling
        is_danger: Shorthand for button_type="danger"
        full_width: Expand button to container width
        disabled: Disable button interaction
        help_text: Tooltip text on hover
        **kwargs: Additional arguments passed to carbon_button
    
    Returns:
        bool: True if button was clicked
    """
    # Handle danger shorthand
    if is_danger:
        button_type = "danger"
    
    # Auto-detect icon if not provided and label is provided
    if icon is None and label:
        # Try exact match first
        label_lower = label.lower()
        if label_lower in ICON_MAP:
            icon = ICON_MAP[label_lower]
        else:
            # Try to find icon from keywords in label
            for keyword, icon_value in ICON_MAP.items():
                if keyword in label_lower:
                    icon = icon_value
                    break
    elif isinstance(icon, str) and icon in ICON_MAP:
        # Convert string icon name to CarbonIcons enum
        icon = ICON_MAP[icon]
    elif isinstance(icon, str) and icon.upper() in dir(CarbonIcons):
        # Try direct CarbonIcons attribute
        icon = getattr(CarbonIcons, icon.upper())
    
    # Apply primary action settings
    if is_primary_action:
        button_type = "primary"
        kwargs['is_default'] = True  # Adds teal shadow for default action
    
    # Handle icon-only buttons
    if not label and icon:
        kwargs['aria_label'] = kwargs.get('aria_label', key.replace('_', ' ').title())
    
    # Note: carbon_button doesn't support tooltips/help text directly
    # We could potentially add this as a separate st.info or in documentation
    
    return carbon_button(
        label=label,
        key=key,
        icon=icon,
        button_type=button_type,
        use_container_width=full_width,
        disabled=disabled,
        **kwargs
    )


def create_button_group(buttons: List[Dict[str, Any]], cols: Optional[List[float]] = None) -> List[bool]:
    """
    Create a group of buttons in columns.
    
    Args:
        buttons: List of button configurations (dicts with ape_button parameters)
        cols: Column width ratios (defaults to equal widths)
    
    Returns:
        List of button states (True if clicked)
    
    Example:
        buttons = [
            {"label": "Save", "key": "save_btn", "icon": "save", "is_primary_action": True},
            {"label": "Cancel", "key": "cancel_btn"},
            {"label": "Delete", "key": "delete_btn", "is_danger": True}
        ]
        results = create_button_group(buttons, cols=[2, 1, 1])
        if results[0]:  # Save was clicked
            save_data()
    """
    if cols is None:
        cols = [1] * len(buttons)
    
    columns = st.columns(cols)
    results = []
    
    for col, btn_config in zip(columns, buttons):
        with col:
            # Extract button config, ensuring required parameters
            if 'key' not in btn_config:
                raise ValueError(f"Button config missing required 'key': {btn_config}")
            
            result = ape_button(**btn_config)
            results.append(result)
    
    return results


def navigation_button(page_name: str, icon_name: Optional[str] = None, **kwargs) -> bool:
    """
    Create a navigation button with consistent styling.
    
    Args:
        page_name: Name of the page to navigate to
        icon_name: Optional icon name (will auto-detect if not provided)
        **kwargs: Additional arguments for ape_button
    
    Returns:
        bool: True if button was clicked
    """
    # Default navigation button styling
    kwargs.setdefault('button_type', 'secondary')
    kwargs.setdefault('full_width', False)
    
    # Auto-detect icon based on common page names
    if icon_name is None:
        page_lower = page_name.lower()
        if 'home' in page_lower:
            icon_name = 'home'
        elif 'protocol' in page_lower:
            icon_name = 'protocol'
        elif 'run' in page_lower or 'simulation' in page_lower:
            icon_name = 'run'
        elif 'analysis' in page_lower or 'overview' in page_lower:
            icon_name = 'analysis'
    
    return ape_button(
        label=page_name,
        icon=icon_name,
        **kwargs
    )


def top_navigation_home_button() -> bool:
    """
    Create a consistent "Home" button for top navigation across pages.
    
    Returns:
        bool: True if clicked
    """
    return ape_button(
        label="Home",
        key="top_home",
        icon="home",
        button_type="ghost"
    )


def confirm_dialog_buttons(
    confirm_label: str = "Confirm",
    cancel_label: str = "Cancel",
    confirm_key: str = "confirm",
    cancel_key: str = "cancel",
    is_danger: bool = False
) -> tuple[bool, bool]:
    """
    Create a standard confirm/cancel button pair.
    
    Args:
        confirm_label: Label for confirm button
        cancel_label: Label for cancel button
        confirm_key: Key for confirm button
        cancel_key: Key for cancel button
        is_danger: Whether the confirm action is dangerous
    
    Returns:
        tuple[bool, bool]: (confirm_clicked, cancel_clicked)
    """
    buttons = [
        {
            "label": confirm_label,
            "key": confirm_key,
            "button_type": "danger" if is_danger else "primary",
            "is_primary_action": not is_danger
        },
        {
            "label": cancel_label,
            "key": cancel_key,
            "button_type": "secondary"
        }
    ]
    
    results = create_button_group(buttons, cols=[1, 1])
    return results[0], results[1]


# Convenience functions for common button patterns
def save_button(key: str = "save", **kwargs) -> bool:
    """Create a standard save button."""
    return ape_button(
        label="Save",
        key=key,
        icon="save",
        is_primary_action=True,
        **kwargs
    )


def delete_button(key: str = "delete", **kwargs) -> bool:
    """Create a standard delete button."""
    return ape_button(
        label="Delete",
        key=key,
        icon="delete",
        is_danger=True,
        **kwargs
    )


def upload_button(key: str = "upload", **kwargs) -> bool:
    """Create a standard upload button."""
    return ape_button(
        label="Upload",
        key=key,
        icon="upload",
        button_type="secondary",
        **kwargs
    )