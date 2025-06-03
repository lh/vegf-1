# Carbon Button Implementation Plan - Aggressive Timeline

## Overview
Full application conversion to Carbon buttons in 2 weeks, leveraging the fact that we're not yet live. No phased rollout needed - we'll convert the entire application before publishing.

## Key Decisions
- **Default Button Style**: `teal-shadow` 
- **Icon Usage**: Comprehensive with fallback to text for project-specific actions
- **Colours**: Use Carbon defaults (teal matches our logo perfectly)
- **Timeline**: 2 weeks aggressive implementation
- **Documentation**: Developer-only

## Week 1: Full Implementation

### Day 1-2: Setup & Core Infrastructure
**Morning Day 1**:
```bash
pip install streamlit-carbon-button
# Update requirements.txt
```

**Create core utilities**:

`utils/carbon_button_helpers.py`:
```python
from streamlit_carbon_button import carbon_button, CarbonIcons
from typing import Optional

# Icon mapping for common actions
ICON_MAP = {
    # Navigation
    'home': CarbonIcons.HOME,
    'settings': CarbonIcons.SETTINGS,
    'back': CarbonIcons.ARROW_LEFT,
    'forward': CarbonIcons.ARROW_RIGHT,
    
    # Actions
    'save': CarbonIcons.SAVE,
    'load': CarbonIcons.UPLOAD,
    'delete': CarbonIcons.DELETE,
    'run': CarbonIcons.PLAY,
    'stop': CarbonIcons.STOP,
    'reset': CarbonIcons.RESET,
    'refresh': CarbonIcons.RENEW,
    
    # Data operations
    'export': CarbonIcons.EXPORT,
    'download': CarbonIcons.DOWNLOAD,
    'copy': CarbonIcons.COPY,
    'filter': CarbonIcons.FILTER,
    'search': CarbonIcons.SEARCH,
    
    # Visualization
    'chart': CarbonIcons.CHART_BAR,
    'view': CarbonIcons.VIEW,
    'analyze': CarbonIcons.ANALYTICS,
    
    # File operations
    'document': CarbonIcons.DOCUMENT,
    'folder': CarbonIcons.FOLDER,
    'add': CarbonIcons.ADD,
    
    # Status
    'info': CarbonIcons.INFORMATION,
    'help': CarbonIcons.HELP,
    'warning': CarbonIcons.WARNING,
    'success': CarbonIcons.CHECKMARK,
}

def ape_button(
    label: str,
    key: str,
    icon: Optional[str] = None,
    button_type: str = "secondary",
    is_primary_action: bool = False,
    full_width: bool = False,
    **kwargs
) -> bool:
    """
    APE-specific wrapper for carbon_button with sensible defaults
    """
    # Auto-detect icon if not provided
    if icon is None and label.lower() in ICON_MAP:
        icon = ICON_MAP[label.lower()]
    elif isinstance(icon, str) and icon in ICON_MAP:
        icon = ICON_MAP[icon]
    
    # Primary actions get special treatment
    if is_primary_action:
        button_type = "primary"
        kwargs['is_default'] = True
        kwargs['default_style'] = "teal-shadow"
    
    return carbon_button(
        label=label,
        key=key,
        icon=icon,
        button_type=button_type,
        use_container_width=full_width,
        **kwargs
    )
```

### Day 3-4: Navigation & Main Pages

**Convert all navigation buttons across**:
- `APE.py`
- `pages/1_Protocol_Manager.py`
- `pages/2_Run_Simulation.py`
- `pages/3_Analysis_Overview.py`
- `pages/4_Experiments.py`

**Pattern for navigation**:
```python
# Top of each page
from utils.carbon_button_helpers import ape_button, CarbonIcons

# Navigation section
col1, col2, col3 = st.columns([1, 6, 1])
with col1:
    if ape_button("Home", key="nav_home", icon="home", button_type="ghost"):
        st.switch_page("APE.py")
```

### Day 5-6: Form Actions & Primary Buttons

**Protocol Manager conversions**:
```python
# Save button - primary action
if ape_button("Save Protocol", 
              key="save_protocol",
              icon="save",
              is_primary_action=True):
    save_protocol()

# Load button - secondary action  
if ape_button("Load Protocol",
              key="load_protocol", 
              icon="load"):
    load_protocol()

# Delete button - danger action
if carbon_button("Delete Protocol",
                 key="delete_protocol",
                 icon=CarbonIcons.DELETE,
                 button_type="danger"):
    delete_protocol()
```

**Run Simulation conversions**:
```python
# Main run button
if ape_button("Run Simulation",
              key="run_sim",
              icon="run",
              is_primary_action=True,
              full_width=True):
    run_simulation()
```

### Day 7: Analysis & Export Buttons

**Export functionality pattern**:
```python
# In export settings
for format in ['PNG', 'SVG', 'JPEG', 'WebP']:
    if carbon_button("",
                     key=f"export_{format.lower()}",
                     icon=CarbonIcons.DOWNLOAD,
                     button_type="ghost",
                     aria_label=f"Export as {format}"):
        export_chart(format)
```

**Project-specific actions (text fallback)**:
```python
# Where icons don't clearly convey meaning
if ape_button("Calculate Discontinuation Rate",
              key="calc_disc_rate",
              # No icon - too specific
              button_type="secondary"):
    calculate_discontinuation_rate()
```

## Week 2: Polish & Optimization

### Day 8-9: Remove Old Code
- Delete `utils/button_styling.py`
- Remove all custom button CSS
- Update imports throughout codebase
- Remove button-related styling from `utils/style_constants.py`

### Day 10-11: Testing & Refinement
**Create comprehensive test script**:
```python
# tests/test_carbon_buttons.py
import streamlit as st
from utils.carbon_button_helpers import ape_button

def test_all_button_types():
    """Visual test of all button configurations"""
    
    # Test navigation buttons
    assert ape_button("Home", "test_home", icon="home", button_type="ghost")
    
    # Test primary actions
    assert ape_button("Save", "test_save", is_primary_action=True)
    
    # Test icon-only buttons
    assert carbon_button("", "test_icon_only", 
                        icon=CarbonIcons.SETTINGS,
                        aria_label="Settings")
    
    # Test full width
    assert ape_button("Process All", "test_full", full_width=True)
```

### Day 12-13: Documentation
**Create `docs/CARBON_BUTTON_DEVELOPER_GUIDE.md`**:
```markdown
# Carbon Button Developer Guide

## Quick Reference

### Basic Usage
```python
from utils.carbon_button_helpers import ape_button

# Standard button
if ape_button("Click Me", key="unique_key"):
    # Handle click

# Primary action with default indicator
if ape_button("Save", key="save", is_primary_action=True):
    # This will show teal shadow effect

# With icon (auto-detected or explicit)
if ape_button("Export", key="export"):  # Auto-detects export icon
    # Handle export

# Project-specific action (no icon)
if ape_button("Calculate Treatment Intervals", key="calc"):
    # Text-only for clarity
```

### Button Types
- `primary` - Main actions (blue)
- `secondary` - Default, secondary actions (grey)
- `danger` - Destructive actions (red)
- `ghost` - Subtle actions (transparent)

### When to Use Icons
✅ **Use icons for**:
- Common actions (save, load, export, delete)
- Navigation (home, back, forward)
- Status indicators (success, warning, error)

❌ **Use text-only for**:
- Project-specific calculations
- Complex medical terms
- Multi-word specific actions
```

### Day 14: Final Testing & Deployment
- Run full application test suite
- Visual regression testing
- Performance benchmarking
- Deploy to staging environment

## Implementation Checklist

### Files to Convert (Priority Order)

**Day 3-4**:
- [ ] `APE.py`
- [ ] `pages/1_Protocol_Manager.py`
- [ ] `pages/2_Run_Simulation.py`
- [ ] `pages/3_Analysis_Overview.py`
- [ ] `pages/4_Experiments.py`

**Day 5-6**:
- [ ] `components/treatment_patterns/enhanced_tab.py`
- [ ] All form submissions in Protocol Manager
- [ ] All simulation controls

**Day 7**:
- [ ] Export functionality in `utils/export_config.py`
- [ ] Chart interaction buttons
- [ ] Modal/dialog buttons

**Day 8-9**:
- [ ] Remove `utils/button_styling.py`
- [ ] Remove `style_navigation_buttons()` calls
- [ ] Clean up CSS imports

## Testing Checklist

- [ ] All buttons have unique keys
- [ ] Icon-only buttons have aria-labels
- [ ] Primary actions have teal-shadow effect
- [ ] Dangerous actions use danger type
- [ ] No custom button CSS remains
- [ ] Session state still works correctly
- [ ] Navigation flow unchanged
- [ ] Export functionality works
- [ ] Forms submit correctly

## Common Patterns

### Navigation Header
```python
col1, col2, col3 = st.columns([1, 6, 1])
with col1:
    if ape_button("Home", key="nav_home", icon="home", button_type="ghost"):
        st.switch_page("APE.py")
with col2:
    st.title("Page Title")
```

### Form with Primary Action
```python
# Form inputs...

col1, col2 = st.columns([3, 1])
with col2:
    if ape_button("Submit", key="submit_form", is_primary_action=True):
        process_form()
with col1:
    if ape_button("Reset", key="reset_form", button_type="ghost"):
        reset_form()
```

### Export Options
```python
with st.expander("Export Options"):
    col1, col2, col3, col4 = st.columns(4)
    
    for col, fmt in zip([col1, col2, col3, col4], ['PNG', 'SVG', 'PDF', 'CSV']):
        with col:
            if carbon_button(fmt, 
                           key=f"export_{fmt.lower()}",
                           icon=CarbonIcons.DOWNLOAD,
                           button_type="secondary",
                           use_container_width=True):
                export_data(fmt)
```

## Success Criteria

1. **All st.button() calls replaced** (except in test files)
2. **No custom button CSS remains**
3. **Consistent use of teal-shadow for primary actions**
4. **Icons used appropriately with text fallback**
5. **All tests passing**
6. **No performance degradation**
7. **Clean, maintainable code**

## Post-Implementation

1. **Remove deprecated files**:
   - `utils/button_styling.py`
   - `utils/icon_button_solutions.py`
   - Any button-related CSS

2. **Update documentation**:
   - Remove button styling from `DESIGN_PRINCIPLES.md`
   - Update `README.md` with Carbon button dependency

3. **Create migration tag**:
   ```bash
   git tag -a "pre-carbon-buttons" -m "Last version before Carbon button migration"
   git push origin --tags
   ```