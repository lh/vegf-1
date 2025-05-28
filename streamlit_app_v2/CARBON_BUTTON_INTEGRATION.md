# Carbon Button Integration Guide

## Overview

This guide documents the integration of Carbon Design System buttons into the AMD Protocol Explorer (APE) V2 application. The integration provides subtle, scientific styling while maintaining reliability through automatic fallback to standard Streamlit buttons.

## Features

### 1. Automatic Fallback
- If Carbon buttons are unavailable (not installed, import error, runtime error), the system automatically falls back to standard Streamlit buttons
- No code changes needed in application pages
- Maintains full functionality in fallback mode

### 2. Subtle Scientific Styling
- Light mode: Warm grey (#e6e2e2) with teal accent (#50e4e0)
- Dark mode: Pink-grey (#ecdcdc) with darker teal (#67cccc)
- Increased icon size (20px) for better visibility
- No superlatives or marketing language

### 3. Icon Integration
- Automatic conversion of emoji prefixes to Carbon icons
- Preserves emojis in fallback mode
- Supports common scientific app actions

## Installation

Add to `requirements.txt`:
```
git+https://github.com/lh/streamlit-carbon-button.git
```

## Usage

### Basic Implementation

```python
from utils.carbon_buttons import carbon_action_button, convert_emoji_to_icon

# Simple button
if carbon_action_button("Run Analysis", key="run_analysis"):
    # Handle click
    pass

# Button with emoji icon
label, icon = convert_emoji_to_icon("🎯 Run Simulation")
if carbon_action_button(label, key="run_sim", kind="primary", icon=icon):
    # Handle click
    pass
```

### Button Types

```python
from utils.carbon_buttons import (
    primary_action_button,
    secondary_action_button,
    danger_action_button,
    ghost_action_button
)

# Primary (main actions)
if primary_action_button("Run Simulation", key="primary"):
    pass

# Secondary (supporting actions)
if secondary_action_button("Copy Data", key="secondary"):
    pass

# Danger (destructive actions)
if danger_action_button("Clear Results", key="danger"):
    pass

# Ghost (subtle actions)
if ghost_action_button("Settings", key="ghost"):
    pass
```

### Full Width Buttons

```python
if carbon_action_button(
    "Run Full Analysis",
    key="full_width",
    kind="primary",
    use_container_width=True
):
    pass
```

### Icon Mapping

The system automatically converts these emojis to Carbon icons:
- 📋 → Copy
- 🎯 → Play
- 🗑️ → TrashCan
- 💾 → Save
- 📊 → ChartLine
- ⚙️ → Settings
- ➕ → Add
- ✏️ → Edit
- 🔍 → Search

## Migration from Standard Buttons

### Before:
```python
if st.button("🎯 Run Simulation", type="primary", use_container_width=True):
    # Handle click
```

### After:
```python
from utils.carbon_buttons import carbon_action_button, convert_emoji_to_icon

label, icon = convert_emoji_to_icon("🎯 Run Simulation")
if carbon_action_button(label, key="run_simulation", kind="primary", icon=icon, use_container_width=True):
    # Handle click
```

## Error Handling

The integration includes comprehensive error handling:

1. **Import Failure**: Falls back to Streamlit buttons if Carbon component not installed
2. **Runtime Errors**: Catches exceptions and falls back gracefully
3. **Logging**: Errors are logged for debugging without disrupting user experience

## Testing

### Test Files
- `test_carbon_integration.py` - Tests all Carbon button features
- `test_fallback.py` - Tests fallback mechanism

### Running Tests
```bash
streamlit run test_carbon_integration.py
streamlit run test_fallback.py
```

## Best Practices

1. **Always provide unique keys** for each button to maintain state properly
2. **Use emoji-to-icon conversion** for consistent iconography
3. **Choose appropriate button kinds**:
   - `primary` for main actions
   - `secondary` for supporting actions
   - `danger` for destructive actions
   - `ghost` for subtle actions
4. **Test both modes** - with Carbon available and in fallback mode
5. **Keep labels concise** - scientific and professional language only

## Troubleshooting

### Buttons not appearing
- Check that the Carbon button package is installed
- Verify unique keys are used for each button
- Check browser console for JavaScript errors

### Fallback not working
- Ensure `utils/carbon_buttons.py` is properly imported
- Check Python logs for import errors
- Verify button parameters are compatible with st.button()

### Styling issues
- Clear browser cache
- Check for conflicting CSS
- Verify Carbon component version

## Current Integration Status

### Completed Pages
- ✅ Protocol Manager (`pages/1_Protocol_Manager.py`)
  - Copy Checksum button
- ✅ Run Simulation (`pages/2_Run_Simulation.py`)
  - Run Simulation button
  - Clear Previous Results button

### Utility Module
- ✅ `utils/carbon_buttons.py` - Core integration module with fallback support

### Requirements
- ✅ Updated `requirements.txt` with Carbon button package

## Future Enhancements

1. Add more Carbon icons for scientific actions
2. Support for button groups
3. Integration with form submissions
4. Custom theme configuration
5. Performance monitoring and optimization