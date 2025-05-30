# Complete Carbon Button Integration Guide

This guide provides step-by-step instructions for integrating Carbon Design System buttons into a Streamlit application, with all details needed for replication.

## Prerequisites

- Streamlit application
- Python 3.7+
- Git for installing from GitHub

## Step 1: Install the Carbon Button Component

Add to your `requirements.txt`:
```
git+https://github.com/lh/streamlit-carbon-button.git
```

Or install directly:
```bash
pip install git+https://github.com/lh/streamlit-carbon-button.git
```

## Step 2: Create the Carbon Button Utility Module

Create `utils/carbon_buttons.py` with this exact content:

```python
"""
Carbon Button Integration for Streamlit Applications

This module provides a seamless interface to the streamlit-carbon-button component.
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
        kind: Button style variant (primary, secondary, danger, ghost)
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
        
        # Call Carbon button with proper parameters
        clicks = carbon_button(
            label=label,
            key=f"carbon_{key}",
            button_type=kind,  # Carbon button uses button_type, not kind
            icon=icon,
            disabled=disabled,
            use_container_width=use_container_width  # Pass this to the component
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
    """Create a primary action button."""
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
```

## Step 3: Update Your Streamlit Pages

### Example 1: Simple Button Replacement

**Before:**
```python
if st.button("Run Analysis", type="primary"):
    # Handle click
    pass
```

**After:**
```python
from utils.carbon_buttons import carbon_action_button

if carbon_action_button("Run Analysis", key="run_analysis", kind="primary"):
    # Handle click
    pass
```

### Example 2: Button with Emoji Icon

**Before:**
```python
if st.button("🎯 Run Simulation", type="primary", use_container_width=True):
    # Handle click
    pass
```

**After:**
```python
from utils.carbon_buttons import carbon_action_button, convert_emoji_to_icon

label, icon = convert_emoji_to_icon("🎯 Run Simulation")
if carbon_action_button(label, key="run_simulation", kind="primary", icon=icon, use_container_width=True):
    # Handle click
    pass
```

### Example 3: Different Button Types

```python
from utils.carbon_buttons import (
    primary_action_button,
    secondary_action_button,
    danger_action_button,
    ghost_action_button
)

# Primary button (main actions)
if primary_action_button("Submit", key="submit"):
    st.success("Submitted!")

# Secondary button (supporting actions)
if secondary_action_button("Copy", key="copy"):
    st.info("Copied!")

# Danger button (destructive actions)
if danger_action_button("Delete", key="delete"):
    st.warning("Deleted!")

# Ghost button (subtle actions)
if ghost_action_button("Settings", key="settings"):
    st.info("Settings opened!")
```

## Step 4: Complete Page Example

Here's a complete example showing how to update a Streamlit page:

```python
"""
Example Page with Carbon Buttons
"""

import streamlit as st
from utils.carbon_buttons import carbon_action_button, convert_emoji_to_icon

st.set_page_config(page_title="Example Page", page_icon="📋")

st.title("📋 Example Page")

# Simple button
if carbon_action_button("Click Me", key="simple_button"):
    st.success("Button clicked!")

# Button with emoji icon
label, icon = convert_emoji_to_icon("📋 Copy Data")
if carbon_action_button(label, key="copy_data", kind="secondary", icon=icon):
    st.code("Data copied to clipboard")
    
# Full width button
label, icon = convert_emoji_to_icon("🎯 Run Analysis")
if carbon_action_button(label, key="run_analysis", kind="primary", icon=icon, use_container_width=True):
    with st.spinner("Running analysis..."):
        # Your analysis code here
        pass
    st.success("Analysis complete!")

# Danger button
label, icon = convert_emoji_to_icon("🗑️ Clear Results")
if carbon_action_button(label, key="clear_results", kind="danger", icon=icon):
    st.session_state.clear()
    st.rerun()
```

## Step 5: Important Notes

### 1. Unique Keys Required
Every Carbon button MUST have a unique `key` parameter. This is used for state management.

### 2. Parameter Mapping
- Carbon buttons use `button_type`, not `kind` internally (the wrapper handles this)
- No `size` parameter - Carbon buttons have a fixed size
- `use_container_width` is supported natively

### 3. Icon System
The `convert_emoji_to_icon` function maps common emojis to Carbon icons:
- 📋 → Copy
- 🎯 → Play
- 🗑️ → TrashCan
- 💾 → Save
- 📊 → ChartLine
- ⚙️ → Settings
- ➕ → Add
- ✏️ → Edit
- 🔍 → Search

### 4. Button Types
- `primary` - Main actions (blue/teal)
- `secondary` - Supporting actions (grey)
- `danger` - Destructive actions (red)
- `ghost` - Borderless/subtle actions

### 5. Fallback Behavior
If the Carbon component fails to load or encounters an error:
- Automatically falls back to standard Streamlit buttons
- Preserves functionality
- Logs errors for debugging
- No code changes needed

## Step 6: Testing Your Integration

Create a test file to verify everything works:

```python
"""
test_carbon_integration.py - Test Carbon button integration
"""

import streamlit as st
from utils.carbon_buttons import carbon_action_button, CARBON_AVAILABLE

st.title("Carbon Button Test")

# Check if Carbon is available
st.info(f"Carbon buttons available: {CARBON_AVAILABLE}")

# Test basic button
if carbon_action_button("Test Button", key="test"):
    st.success("Carbon button working!")

# Test with icon
label, icon = convert_emoji_to_icon("🎯 Test with Icon")
if carbon_action_button(label, key="test_icon", icon=icon):
    st.success("Icon button working!")
```

Run with:
```bash
streamlit run test_carbon_integration.py
```

## Troubleshooting

### Buttons appear as standard Streamlit buttons
1. Check if the Carbon component is installed: `pip list | grep carbon`
2. Check browser console (F12) for JavaScript errors
3. Check terminal for Python import errors

### Buttons don't appear at all
1. Ensure unique keys for each button
2. Check if the page is reloading properly
3. Try clearing browser cache

### Icons not showing
1. Verify the emoji is in the ICON_MAP
2. Check if the icon name is correct
3. Try without icon first to isolate the issue

## Directory Structure

Your project should have this structure:
```
your_app/
├── app.py
├── pages/
│   ├── 1_Page_One.py
│   └── 2_Page_Two.py
├── utils/
│   └── carbon_buttons.py
└── requirements.txt
```

## Summary

1. Install: `pip install git+https://github.com/lh/streamlit-carbon-button.git`
2. Copy the `carbon_buttons.py` utility module exactly as shown
3. Import and use `carbon_action_button` instead of `st.button`
4. Always provide unique keys
5. Use `convert_emoji_to_icon` for emoji → icon conversion
6. The system automatically falls back to standard buttons if needed

That's it! Your Streamlit app now has professional Carbon Design System buttons with automatic fallback for reliability.