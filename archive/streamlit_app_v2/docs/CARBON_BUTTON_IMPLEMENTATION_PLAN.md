# Carbon Button Implementation Plan

## Overview
This document outlines the plan for integrating the `streamlit-carbon-button` component into the APE (AMD Protocol Explorer) application, replacing our current custom button styling with IBM's Carbon Design System buttons.

## Objectives
1. Improve visual consistency with professional Carbon Design System
2. Enhance accessibility with built-in ARIA labels
3. Add visual hierarchy with "default button" indicators
4. Simplify maintenance by removing custom CSS
5. Provide better user guidance with icon support

## Installation & Setup

### Dependencies
```bash
pip install streamlit-carbon-button
```

Add to `requirements.txt`:
```
streamlit-carbon-button>=0.1.0
```

### Initial Import Structure
```python
from streamlit_carbon_button import carbon_button, CarbonIcons
```

## Implementation Phases

### Phase 1: Navigation Buttons (Week 1)
**Scope**: Replace main navigation buttons across all pages

**Files to modify**:
- `APE.py` - Home navigation buttons
- `pages/1_Protocol_Manager.py` - Top navigation
- `pages/2_Run_Simulation.py` - Top navigation
- `pages/3_Analysis_Overview.py` - Top navigation
- `pages/4_Experiments.py` - Top navigation

**Implementation pattern**:
```python
# Old
if st.button("🦍 Home", key="nav_home"):
    st.switch_page("APE.py")

# New
if carbon_button("Home", 
                 icon=CarbonIcons.HOME, 
                 key="nav_home", 
                 button_type="ghost"):
    st.switch_page("APE.py")
```

### Phase 2: Primary Action Buttons (Week 2)
**Scope**: Replace main action buttons (forms, submissions)

**Key buttons**:
1. Protocol Manager:
   - Save Protocol (primary, default)
   - Load Protocol (secondary)
   - Delete Protocol (danger)
   
2. Run Simulation:
   - Run Simulation (primary, default, full width)
   - Reset Parameters (ghost)
   
3. Analysis Overview:
   - Export buttons (secondary with icons)

**Implementation pattern**:
```python
# Primary action with default indicator
if carbon_button("Run Simulation",
                 icon=CarbonIcons.PLAY,
                 key="run_sim",
                 button_type="primary",
                 is_default=True,
                 use_container_width=True):
    # Action logic
```

### Phase 3: Utility Buttons (Week 3)
**Scope**: Replace remaining utility buttons

**Includes**:
- Chart export buttons (icon-only)
- Settings/configuration buttons
- Help/info buttons
- Modal dialog buttons

**Implementation pattern**:
```python
# Icon-only button
if carbon_button("",
                 icon=CarbonIcons.DOWNLOAD,
                 key="export_png",
                 button_type="ghost",
                 aria_label="Download as PNG"):
    # Export logic
```

## Migration Strategy

### 1. Create Migration Wrapper
```python
# utils/button_migration.py
from streamlit_carbon_button import carbon_button, CarbonIcons
import streamlit as st

def ape_button(label, key, button_type="secondary", icon=None, 
               is_primary_action=False, is_dangerous=False, **kwargs):
    """
    Wrapper function to ease migration from st.button to carbon_button
    
    Args:
        label: Button text
        key: Unique key for button
        button_type: "primary", "secondary", "danger", "ghost"
        icon: CarbonIcons enum value
        is_primary_action: Whether this is the main action (shows default indicator)
        is_dangerous: Whether this is a destructive action
    """
    # Map our conventions to Carbon parameters
    if is_dangerous:
        button_type = "danger"
    
    return carbon_button(
        label,
        key=key,
        button_type=button_type,
        icon=icon,
        is_default=is_primary_action,
        **kwargs
    )
```

### 2. Icon Mapping Dictionary
```python
# utils/carbon_icons_map.py
from streamlit_carbon_button import CarbonIcons

ICON_MAP = {
    # Navigation
    'home': CarbonIcons.HOME,
    'settings': CarbonIcons.SETTINGS,
    'back': CarbonIcons.ARROW_LEFT,
    
    # Actions
    'save': CarbonIcons.SAVE,
    'load': CarbonIcons.UPLOAD,
    'delete': CarbonIcons.DELETE,
    'run': CarbonIcons.PLAY,
    'stop': CarbonIcons.STOP,
    'reset': CarbonIcons.RESET,
    
    # Data operations
    'export': CarbonIcons.EXPORT,
    'download': CarbonIcons.DOWNLOAD,
    'copy': CarbonIcons.COPY,
    'filter': CarbonIcons.FILTER,
    
    # Visualization
    'chart': CarbonIcons.CHART_BAR,
    'view': CarbonIcons.VIEW,
    'zoom_in': CarbonIcons.ZOOM_IN,
    'zoom_out': CarbonIcons.ZOOM_OUT,
    
    # Status
    'success': CarbonIcons.SUCCESS,
    'warning': CarbonIcons.WARNING,
    'error': CarbonIcons.ERROR,
    'info': CarbonIcons.INFO,
    
    # File operations
    'document': CarbonIcons.DOCUMENT,
    'folder': CarbonIcons.FOLDER,
    'add_file': CarbonIcons.DOCUMENT_ADD,
}
```

### 3. Style Configuration
```python
# utils/carbon_button_config.py
"""Carbon button configuration for APE theme"""

# Custom colors matching our theme
APE_BUTTON_COLORS = {
    "rest_bg": "#e6e2e2",      # Our warm grey
    "rest_text": "#1a1a1a",    
    "hover_bg": "#f5f5f5",     
    "active_bg": "#50e4e0",    # Our teal accent
    "active_text": "#ffffff",  
}

# Default button style preference
DEFAULT_BUTTON_STYLE = "teal-shadow"  # Options: "pulse", "glow", "ring", "elevated", "teal-shadow"
```

## Testing Strategy

### 1. Create Test Page
Create `pages/5_Button_Migration_Test.py` for A/B comparison:
```python
import streamlit as st
from streamlit_carbon_button import carbon_button, CarbonIcons

st.set_page_config(page_title="Button Migration Test", page_icon="🧪")

st.title("Carbon Button Migration Test")

# Toggle for comparison
use_carbon = st.checkbox("Use Carbon Buttons", value=True)

col1, col2 = st.columns(2)

with col1:
    st.subheader("Navigation Buttons")
    if use_carbon:
        carbon_button("Home", icon=CarbonIcons.HOME, key="c_home", button_type="ghost")
        carbon_button("Settings", icon=CarbonIcons.SETTINGS, key="c_settings", button_type="ghost")
    else:
        st.button("🏠 Home", key="s_home")
        st.button("⚙️ Settings", key="s_settings")

with col2:
    st.subheader("Action Buttons")
    if use_carbon:
        carbon_button("Save", icon=CarbonIcons.SAVE, key="c_save", 
                     button_type="primary", is_default=True)
        carbon_button("Cancel", key="c_cancel", button_type="ghost")
    else:
        st.button("💾 Save", key="s_save", type="primary")
        st.button("Cancel", key="s_cancel")

# Performance metrics
if st.checkbox("Show Performance Metrics"):
    # Add timing comparisons
    pass
```

### 2. Accessibility Testing
- Test with screen readers (NVDA, JAWS)
- Verify keyboard navigation
- Check ARIA labels on icon-only buttons
- Test high contrast mode

### 3. Visual Testing
- Light/dark mode compatibility
- Mobile responsive behaviour
- Visual regression testing with screenshots
- Cross-browser testing (Chrome, Firefox, Safari)

### 4. Performance Testing
- Page load time comparison
- Button interaction latency
- Memory usage with many buttons
- Session state interaction

## Rollback Plan

### Feature Flag Implementation
```python
# In .streamlit/config.toml or environment variable
USE_CARBON_BUTTONS = st.secrets.get("USE_CARBON_BUTTONS", False)

# In code
if USE_CARBON_BUTTONS:
    from utils.button_migration import ape_button as button_func
else:
    button_func = st.button
```

### Gradual Rollout
1. Week 1: 10% of users (internal testing)
2. Week 2: 50% of users (gather feedback)
3. Week 3: 100% deployment
4. Week 4: Remove old button code

## Success Metrics

### Quantitative
- Page load time: Should not increase by >100ms
- Button click latency: <50ms response time
- Error rate: <0.1% button-related errors
- Code reduction: Expect 200+ lines removed from custom CSS

### Qualitative
- User feedback on visual appeal
- Accessibility audit improvements
- Developer experience feedback
- Reduced CSS maintenance burden

## Risks & Mitigations

### Risk 1: Session State Conflicts
**Mitigation**: 
- Comprehensive testing of all button interactions
- Maintain unique key naming convention
- Document any behavioural changes

### Risk 2: Visual Inconsistency During Migration
**Mitigation**:
- Phase approach ensures each page is fully migrated
- Use feature flags for instant rollback
- Screenshot comparison tests

### Risk 3: Performance Degradation
**Mitigation**:
- Benchmark before and after
- Profile button-heavy pages
- Consider lazy loading for icon library

### Risk 4: User Confusion
**Mitigation**:
- Maintain similar button positions
- Keep familiar labels
- Add tooltips where helpful
- Announce changes in app

## Documentation Updates

### Files to Update
1. `README.md` - Add Carbon button dependency
2. `DESIGN_PRINCIPLES.md` - Document Carbon Design adoption
3. `utils/button_styling.py` - Mark as deprecated
4. Create `docs/CARBON_BUTTON_GUIDE.md` for developers

### Developer Guide Topics
- Basic button usage
- Icon selection guide
- Custom colour configuration
- Accessibility best practices
- Migration examples

## Timeline

### Week 1 (Days 1-7)
- [ ] Install and configure Carbon buttons
- [ ] Create migration wrapper functions
- [ ] Implement Phase 1 (Navigation)
- [ ] Create test page
- [ ] Initial testing

### Week 2 (Days 8-14)
- [ ] Implement Phase 2 (Primary Actions)
- [ ] Accessibility testing
- [ ] Performance benchmarking
- [ ] Gather team feedback

### Week 3 (Days 15-21)
- [ ] Implement Phase 3 (Utility Buttons)
- [ ] Complete visual regression tests
- [ ] Update documentation
- [ ] Plan rollout communication

### Week 4 (Days 22-28)
- [ ] Full deployment
- [ ] Monitor metrics
- [ ] Address any issues
- [ ] Remove deprecated code

## Next Steps

1. **Approval**: Review and approve this plan
2. **Test Environment**: Set up isolated test branch
3. **Proof of Concept**: Implement one page as demo
4. **Team Training**: Brief team on Carbon Design System
5. **Begin Implementation**: Start with Phase 1

## Appendix: Button Type Decision Matrix

| Current Button | Carbon Type | Icon | Default? | Notes |
|----------------|-------------|------|----------|-------|
| Home Nav | ghost | HOME | No | Subtle navigation |
| Save Protocol | primary | SAVE | Yes | Main action |
| Run Simulation | primary | PLAY | Yes | Full width |
| Delete | danger | DELETE | No | Destructive |
| Export | secondary | DOWNLOAD | No | With dropdown |
| Cancel | ghost | none | No | Dismissive |
| Settings | ghost | SETTINGS | No | Icon-only option |

## Questions for Team

1. **Default Button Animation**: Prefer `teal-shadow`, `ring`, or `elevated`?
2. **Icon Usage**: Minimal (key actions only) or comprehensive?
3. **Colour Customisation**: Keep exact APE colours or adopt Carbon palette?
4. **Migration Speed**: Aggressive (2 weeks) or conservative (4 weeks)?
5. **Training Needs**: Developer documentation sufficient or need workshop?