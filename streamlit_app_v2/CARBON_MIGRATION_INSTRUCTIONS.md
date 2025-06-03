# Carbon Button Migration Instructions

## Overview
This document describes the successful migration from Streamlit's default buttons to IBM Carbon Design System buttons in the AMD Protocol Explorer (APE) V2 application.

## Migration Status: ✅ COMPLETE

### Latest Updates (2025-06-03)
- **Manage Button Pattern**: Implemented a clean solution for Streamlit's native file upload/download buttons that can't be replaced with Carbon buttons
  - Created a single Carbon "Manage" button that reveals an expander with upload/download options
  - Styled native Streamlit buttons to be minimal and unobtrusive
  - Removed red active state styling from all buttons
  - Changed "Browse files" to "Browse" using JavaScript
  - Simplified download button text (removed emoji)

### What Was Accomplished
1. **Home Page (APE.py)**: 
   - Replaced emoji-based navigation buttons with professional Carbon buttons
   - Added state-aware button logic (disabled states with helpful messages)
   - Removed dependency on custom button styling

2. **Protocol Manager Page**:
   - Migrated all buttons including Home, Upload, Duplicate, Delete, Download
   - Replaced emoji icons with Carbon icons
   - Maintained all functionality with improved appearance

3. **Run Simulation Page**:
   - Migrated navigation and action buttons
   - Replaced emojis with Carbon icons
   - Maintained dynamic button layout based on application state

4. **Analysis Overview Page**:
   - Migrated Home navigation button
   - Removed chart emoji from page title

5. **Infrastructure Changes**:
   - Created `utils/carbon_button_helpers.py` with reusable helper functions
   - Deprecated old `button_styling.py` (renamed to `button_styling_deprecated.py`)
   - Updated tests to check for Carbon button classes

## Key Design Decisions
1. **No Emojis**: Per user preference, all emoji icons were replaced with professional Carbon icons
2. **Limited Icon Set**: Working with 18 available Carbon icons, mapped semantic names to available icons
3. **State-Aware UI**: Buttons are disabled when appropriate actions aren't available
4. **Consistent Styling**: All buttons now use IBM Carbon Design System for professional appearance

## Carbon Button Helper Functions
The `utils/carbon_button_helpers.py` module provides:
- `ape_button()`: Main wrapper with APE-specific defaults
- `navigation_button()`: For page navigation buttons
- `top_navigation_home_button()`: Consistent Home button
- `create_button_group()`: For button groups
- `save_button()`, `delete_button()`, `upload_button()`: Common actions

## Icon Mapping
Available Carbon icons (18 total) mapped to semantic uses:
- Navigation: HOME, SETTINGS
- Actions: SAVE, UPLOAD, DELETE, DOWNLOAD, COPY, PLAY, CLOSE
- Data: FILTER, SEARCH, ADD
- Visualization: CHART_BAR
- Files: DOCUMENT
- Status: INFO, HELP, WARNING, SUCCESS

## Usage Example
```python
from utils.carbon_button_helpers import navigation_button, ape_button

# Navigation button
if navigation_button("Protocol Manager", key="nav_protocol"):
    st.switch_page("pages/1_Protocol_Manager.py")

# Primary action button
if ape_button("Run Simulation", key="run", icon="play", is_primary_action=True):
    run_simulation()

# Danger button
if ape_button("Delete", key="delete", is_danger=True):
    delete_item()
```

## Testing
- Visual regression tests updated to check for Carbon button classes
- All pages tested manually and via screenshots
- Button functionality preserved across all pages

## Future Considerations
1. Additional Carbon components could be integrated (forms, modals, etc.)
2. Custom icon additions if needed beyond the 18 available
3. Theme customization using Carbon's color system

## Dependencies
- `streamlit-carbon-button>=1.0.0` added to requirements.txt
- No other new dependencies required

## Rollback Instructions
If needed to rollback:
1. Rename `button_styling_deprecated.py` back to `button_styling.py`
2. Revert changes in all page files to use old button imports
3. Remove `streamlit-carbon-button` from requirements.txt
4. Delete `utils/carbon_button_helpers.py`

---
Migration completed successfully on 2025-06-03