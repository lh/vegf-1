# Carbon Button Implementation Plan - Aggressive Timeline (Improved)

## Overview
Full application conversion to Carbon buttons in 2 weeks using a **Test-Driven Development (TDD)** approach. We'll capture all existing button behaviors with Playwright tests BEFORE migration, ensuring zero regressions.

## Key Decisions
- **Default Button Style**: `teal-shadow` 
- **Icon Usage**: Comprehensive with fallback to text for project-specific actions
- **Colours**: Use Carbon defaults (teal matches our logo perfectly)
- **Timeline**: 2 weeks aggressive implementation
- **Documentation**: Developer-only
- **Testing Strategy**: TDD with Playwright (see [CARBON_BUTTON_TDD_PLAN.md](./CARBON_BUTTON_TDD_PLAN.md))
- **Migration Safety**: All existing functionality captured in tests first

## Pre-Implementation Checklist

### Day 0: Test Infrastructure Setup
- [ ] Install Playwright: `npm install -D @playwright/test` 
- [ ] Set up test configuration (see [TDD Plan](./CARBON_BUTTON_TDD_PLAN.md#phase-0-test-infrastructure-setup-day-0))
- [ ] Create baseline tests for ALL existing buttons
- [ ] Run baseline tests and save screenshots
- [ ] Create feature branch: `feature/carbon-buttons`
- [ ] Verify Carbon button compatibility with current Streamlit version
- [ ] Document all existing button locations and types
- [ ] Create button inventory spreadsheet
- [ ] Test Carbon button installation in isolated environment

## Test-Driven Development Integration

This implementation plan follows a strict TDD approach. **No button migration happens without tests**.

### 📋 Related Documents
- **[CARBON_BUTTON_TDD_PLAN.md](./CARBON_BUTTON_TDD_PLAN.md)** - Complete TDD strategy with Playwright
- Test templates and examples
- CI/CD integration
- Performance benchmarking

### TDD Migration Workflow

Every button migration follows this process:

1. **Write Tests First**: Capture current button behavior using Playwright
2. **Run Tests**: Ensure they pass with existing buttons (baseline)
3. **Migrate Code**: Replace with Carbon buttons while tests are running
4. **Run Tests Again**: Ensure they still pass (no regressions)
5. **Refactor**: Improve code while keeping tests green
6. **Commit**: Only when ALL tests pass

### Test Categories
- **Functional Tests**: Button clicks, navigation, form submission
- **Visual Tests**: Screenshot comparisons
- **Performance Tests**: Load time, response time
- **Accessibility Tests**: ARIA labels, keyboard navigation
- **E2E Tests**: Complete user journeys

### Quick Test Commands
```bash
# Before starting ANY migration work
npm run test:baseline        # Capture current behavior
npm run test:visual         # Save screenshot baselines

# During migration (run continuously)
npm run test:watch          # Live test feedback
npm run test:comparison     # Compare old vs new

# After migration
npm run test:all           # Full regression suite
npm run test:perf          # Performance validation
npm run test:a11y          # Accessibility check
```

For detailed test examples and implementation, see [CARBON_BUTTON_TDD_PLAN.md](./CARBON_BUTTON_TDD_PLAN.md).

## Week 1: Full Implementation

### Day 1: Baseline Test Creation

**Morning**:
- Set up Playwright test infrastructure
- Create baseline tests for navigation buttons (see [Navigation Tests](./CARBON_BUTTON_TDD_PLAN.md#enhanced-navigation-button-tests))
- Create baseline tests for form actions (see [Form Tests](./CARBON_BUTTON_TDD_PLAN.md#enhanced-form-action-tests))
- Run all tests and save baseline screenshots

**Afternoon**:
- Create performance baseline tests
- Create accessibility baseline tests
- Document all button behaviors in test reports
- Commit all tests to version control

```bash
# Run baseline capture
npm run test:baseline -- --update-snapshots
npm run test:baseline -- --reporter=html
```

### Day 2: Setup & Core Infrastructure

**Morning Day 2**:
```bash
# Create and activate virtual environment for testing
python -m venv venv_carbon_test
source venv_carbon_test/bin/activate  # or venv_carbon_test\Scripts\activate on Windows

# Test installation
pip install streamlit-carbon-button
pip install -r requirements.txt

# Verify no conflicts
python -c "import streamlit_carbon_button; print('Success!')"
```

**Create core utilities**:

`utils/carbon_button_helpers.py`:
```python
from streamlit_carbon_button import carbon_button, CarbonIcons
from typing import Optional, Dict, Any
import streamlit as st

# Extended icon mapping for APE-specific actions
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
    'visualize': CarbonIcons.DATA_VIS,
    'visualise': CarbonIcons.DATA_VIS,  # British spelling
    
    # File operations
    'document': CarbonIcons.DOCUMENT,
    'folder': CarbonIcons.FOLDER,
    'add': CarbonIcons.ADD,
    'new': CarbonIcons.ADD,
    
    # Status
    'info': CarbonIcons.INFORMATION,
    'help': CarbonIcons.HELP,
    'warning': CarbonIcons.WARNING,
    'success': CarbonIcons.CHECKMARK,
    'error': CarbonIcons.ERROR,
    
    # APE-specific
    'protocol': CarbonIcons.DOCUMENT,
    'simulation': CarbonIcons.PLAY,
    'patient': CarbonIcons.USER,
    'treatment': CarbonIcons.MEDICATION,
    'analysis': CarbonIcons.ANALYTICS,
    'overview': CarbonIcons.DASHBOARD,
    'experiment': CarbonIcons.CHEMISTRY,
}

# Button style configuration
BUTTON_STYLES = {
    'navigation': {'button_type': 'ghost', 'size': 'sm'},
    'primary_action': {'button_type': 'primary', 'is_default': True, 'default_style': 'teal-shadow'},
    'secondary_action': {'button_type': 'secondary'},
    'danger_action': {'button_type': 'danger'},
    'export': {'button_type': 'ghost', 'size': 'sm'},
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
    
    # Auto-detect icon if not provided
    if icon is None:
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
        icon = ICON_MAP[icon]
    
    # Apply primary action settings
    if is_primary_action:
        button_type = "primary"
        kwargs['is_default'] = True
        kwargs['default_style'] = "teal-shadow"
    
    # Handle icon-only buttons
    if not label and icon:
        kwargs['aria_label'] = kwargs.get('aria_label', key.replace('_', ' ').title())
    
    # Add help text as tooltip
    if help_text:
        kwargs['title'] = help_text
    
    return carbon_button(
        label=label,
        key=key,
        icon=icon,
        button_type=button_type,
        use_container_width=full_width,
        disabled=disabled,
        **kwargs
    )

def create_button_group(buttons: list[Dict[str, Any]], cols: Optional[list[float]] = None) -> list[bool]:
    """
    Create a group of buttons in columns.
    
    Args:
        buttons: List of button configurations
        cols: Column width ratios (defaults to equal widths)
    
    Returns:
        List of button states (True if clicked)
    """
    if cols is None:
        cols = [1] * len(buttons)
    
    columns = st.columns(cols)
    results = []
    
    for col, btn_config in zip(columns, buttons):
        with col:
            result = ape_button(**btn_config)
            results.append(result)
    
    return results
```

**Create test comparison page**:

`pages/99_Carbon_Button_Test.py`:
```python
import streamlit as st
from utils.carbon_button_helpers import ape_button, create_button_group, CarbonIcons
import time

st.set_page_config(page_title="Carbon Button Test", page_icon="🧪", layout="wide")

st.title("Carbon Button Migration Test Page")
st.markdown("Compare old and new button styles side by side")

# Toggle for comparison
use_carbon = st.checkbox("Use Carbon Buttons", value=True)

# Test different button scenarios
st.header("1. Navigation Buttons")
col1, col2 = st.columns(2)

with col1:
    st.subheader("Old Style" if not use_carbon else "Carbon Style")
    if use_carbon:
        if ape_button("Home", key="c_home", icon="home", button_type="ghost"):
            st.success("Home clicked!")
        if ape_button("Protocol Manager", key="c_protocol", icon="protocol", button_type="ghost"):
            st.success("Protocol Manager clicked!")
    else:
        if st.button("🏠 Home", key="s_home"):
            st.success("Home clicked!")
        if st.button("📄 Protocol Manager", key="s_protocol"):
            st.success("Protocol Manager clicked!")

with col2:
    st.subheader("Button Variations")
    if use_carbon:
        # Show different Carbon button types
        if ape_button("Primary Action", key="c_primary", is_primary_action=True):
            st.info("Primary action triggered")
        if ape_button("Secondary", key="c_secondary"):
            st.info("Secondary action")
        if ape_button("Danger Zone", key="c_danger", is_danger=True):
            st.error("Danger action!")
        if ape_button("", key="c_icon_only", icon=CarbonIcons.SETTINGS, 
                     aria_label="Settings"):
            st.info("Icon-only button clicked")
    else:
        if st.button("Primary Action", key="s_primary", type="primary"):
            st.info("Primary action triggered")
        if st.button("Secondary", key="s_secondary"):
            st.info("Secondary action")
        if st.button("⚠️ Danger Zone", key="s_danger"):
            st.error("Danger action!")
        if st.button("⚙️", key="s_icon_only"):
            st.info("Icon-only button clicked")

# Test form actions
st.header("2. Form Actions")
with st.form("test_form"):
    st.text_input("Protocol Name", key="protocol_name")
    
    col1, col2, col3 = st.columns([3, 1, 1])
    with col2:
        if use_carbon:
            submitted = st.form_submit_button("Save", type="primary")
        else:
            submitted = st.form_submit_button("💾 Save", type="primary")
    
    with col3:
        if use_carbon:
            if st.form_submit_button("Cancel"):
                st.info("Cancelled")
        else:
            if st.form_submit_button("Cancel"):
                st.info("Cancelled")
    
    if submitted:
        st.success("Form submitted!")

# Test full-width buttons
st.header("3. Full Width Actions")
if use_carbon:
    if ape_button("Run Simulation", key="c_run_full", icon="run", 
                 is_primary_action=True, full_width=True):
        with st.spinner("Running simulation..."):
            time.sleep(2)
        st.success("Simulation complete!")
else:
    if st.button("▶️ Run Simulation", key="s_run_full", type="primary", 
                use_container_width=True):
        with st.spinner("Running simulation..."):
            time.sleep(2)
        st.success("Simulation complete!")

# Test export buttons
st.header("4. Export Actions")
export_formats = ['PNG', 'SVG', 'JPEG', 'WebP']

if use_carbon:
    # Using button group helper
    buttons = [
        {"label": fmt, "key": f"c_export_{fmt.lower()}", "icon": "export", 
         "button_type": "ghost"}
        for fmt in export_formats
    ]
    results = create_button_group(buttons)
    for fmt, clicked in zip(export_formats, results):
        if clicked:
            st.info(f"Exporting as {fmt}...")
else:
    cols = st.columns(len(export_formats))
    for col, fmt in zip(cols, export_formats):
        with col:
            if st.button(f"📥 {fmt}", key=f"s_export_{fmt.lower()}"):
                st.info(f"Exporting as {fmt}...")

# Performance metrics
st.header("5. Performance Metrics")
if st.checkbox("Show Performance Comparison"):
    st.info("Performance metrics would be displayed here")
    # Add actual performance comparison code

# Accessibility test
st.header("6. Accessibility Features")
if use_carbon:
    st.markdown("""
    Carbon buttons include:
    - ✅ Built-in ARIA labels
    - ✅ Keyboard navigation support
    - ✅ High contrast mode compatibility
    - ✅ Screen reader optimizations
    """)
else:
    st.markdown("""
    Standard buttons:
    - ⚠️ Limited ARIA support
    - ✅ Basic keyboard navigation
    - ⚠️ Manual contrast adjustments needed
    - ⚠️ Limited screen reader support
    """)
```

### Day 3-4: Navigation & Main Pages (TDD Migration)

**Before ANY code changes**:
```bash
# Run navigation tests to ensure baseline
npm run test:watch -- --grep "Navigation"

# Keep tests running in watch mode during migration
```

**Migration Process**:
1. Run navigation tests - verify all green ✅
2. Migrate ONE navigation button
3. Run tests - fix if broken
4. Commit when tests pass
5. Repeat for next button

**Create migration tracking sheet**:

`docs/CARBON_BUTTON_MIGRATION_TRACKER.md`:
```markdown
# Carbon Button Migration Tracker

## Status Legend
- 🟢 Complete
- 🟡 In Progress
- 🔴 Not Started
- ⚠️ Needs Review

## File Status

### Main Application
| File | Status | Notes | Reviewer |
|------|--------|-------|----------|
| APE.py | 🔴 | Main navigation | - |
| requirements.txt | 🔴 | Add carbon dependency | - |

### Pages
| File | Status | Notes | Reviewer |
|------|--------|-------|----------|
| pages/1_Protocol_Manager.py | 🔴 | Complex forms | - |
| pages/2_Run_Simulation.py | 🔴 | Primary actions | - |
| pages/3_Analysis_Overview.py | 🔴 | Export buttons | - |
| pages/4_Experiments.py | 🔴 | If exists | - |

### Components
| File | Status | Notes | Reviewer |
|------|--------|-------|----------|
| components/treatment_patterns/enhanced_tab.py | 🔴 | Export actions | - |
| components/treatment_patterns/interval_analyzer.py | 🔴 | Check for buttons | - |
| components/treatment_patterns/pattern_analyzer.py | 🔴 | Check for buttons | - |

### Utilities
| File | Status | Notes | Reviewer |
|------|--------|-------|----------|
| utils/carbon_button_helpers.py | 🟢 | Created | - |
| utils/button_styling.py | 🔴 | To be removed | - |
| utils/export_config.py | 🔴 | Export buttons | - |
| utils/style_constants.py | 🔴 | Remove button styles | - |

## Button Inventory

### Navigation Buttons
- [ ] Home (all pages)
- [ ] Protocol Manager nav
- [ ] Run Simulation nav
- [ ] Analysis Overview nav
- [ ] Back/Forward buttons

### Action Buttons
- [ ] Save Protocol (primary)
- [ ] Load Protocol
- [ ] Delete Protocol (danger)
- [ ] Run Simulation (primary, full-width)
- [ ] Reset Parameters
- [ ] Stop Simulation

### Export Buttons
- [ ] Export PNG
- [ ] Export SVG
- [ ] Export JPEG
- [ ] Export WebP
- [ ] Export Data (CSV)

### Form Buttons
- [ ] Submit forms
- [ ] Cancel actions
- [ ] Reset forms

## Testing Checklist
- [ ] All buttons have unique keys
- [ ] Icon-only buttons have aria-labels
- [ ] Session state preserved
- [ ] No visual regressions
- [ ] Performance acceptable
- [ ] Accessibility improved
```

### Day 5-6: Form Actions & Primary Buttons (TDD Migration)

**Test-Driven Process**:
```bash
# Focus on form functionality tests
npm run test:watch -- --grep "Form|Save|Load|Delete"

# After each button migration, run full suite
npm run test:all -- --grep "Protocol Manager"
```

**Migration Checklist**:
- [ ] Run form action tests - baseline ✅
- [ ] Migrate Save button → run tests → fix issues
- [ ] Migrate Load button → run tests → fix issues  
- [ ] Migrate Delete button → run tests → fix issues
- [ ] Run visual regression tests
- [ ] Run accessibility tests
- [ ] Commit when all tests green

**Add error handling patterns**:

```python
# In carbon_button_helpers.py, add:

def safe_button_migration(old_button_func, new_button_func, *args, **kwargs):
    """
    Safe migration wrapper that can fall back to old buttons if needed.
    """
    try:
        return new_button_func(*args, **kwargs)
    except Exception as e:
        st.warning(f"Carbon button error: {e}. Falling back to standard button.")
        # Extract label from args/kwargs
        label = args[0] if args else kwargs.get('label', 'Click')
        key = kwargs.get('key', 'fallback_' + str(hash(label)))
        return old_button_func(label, key=key)

# Usage during migration:
if safe_button_migration(st.button, ape_button, "Save", key="save_btn", is_primary_action=True):
    save_data()
```

### Day 7: Analysis & Export Buttons (TDD Migration)

**Test-Driven Export Migration**:
```bash
# Test export functionality continuously
npm run test:watch -- --grep "Export"

# Verify downloads work
npm run test:comparison -- --grep "download"
```

**Export Migration Steps**:
1. Run export tests with old buttons ✅
2. Migrate PNG export → test → verify download
3. Migrate SVG export → test → verify download
4. Migrate other formats → test each
5. Run performance comparison tests
6. Commit when all exports working

**Enhanced export pattern with error handling**:

```python
def create_export_buttons(formats: list[str], prefix: str = "export"):
    """Create a row of export buttons with consistent styling."""
    cols = st.columns(len(formats))
    
    for col, fmt in zip(cols, formats):
        with col:
            # Icon-only for space efficiency
            if carbon_button(
                "",
                key=f"{prefix}_{fmt.lower()}",
                icon=CarbonIcons.DOWNLOAD,
                button_type="ghost",
                aria_label=f"Export as {fmt}",
                title=f"Export as {fmt}",  # Tooltip
                use_container_width=True
            ):
                return fmt  # Return which format was clicked
    
    return None

# Usage:
selected_format = create_export_buttons(['PNG', 'SVG', 'JPEG', 'WebP'])
if selected_format:
    export_chart(selected_format)
```

## Week 2: Polish & Optimization

### Day 8-9: Remove Old Code (With Test Coverage)

**Pre-removal Testing**:
```bash
# Run FULL test suite before removing old code
npm run test:all

# Generate coverage report
npm run test:all -- --reporter=html

# Ensure 100% button functionality covered
```

**Safe removal checklist**:
```bash
# Before removing old code, create safety backup
git checkout -b backup/pre-carbon-removal
git push origin backup/pre-carbon-removal

# Search for all button references
grep -r "st.button" --include="*.py" . > button_references.txt
grep -r "button_styling" --include="*.py" . > styling_references.txt

# Review before deletion
```

### Day 10-11: Testing & Refinement

**Comprehensive Test Suite Execution**:
```bash
# Run all test categories
npm run test:all             # Functional tests
npm run test:visual          # Visual regression
npm run test:a11y           # Accessibility 
npm run test:perf           # Performance

# Generate final test report
npm run test:all -- --reporter=html
open playwright-report/index.html
```

**Test Results Review**:
- [ ] All functional tests passing
- [ ] Visual changes approved
- [ ] Accessibility improved (fewer violations)
- [ ] Performance within limits (<100ms increase)
- [ ] No console errors
- [ ] Downloads working correctly

**Automated testing script**:

`tests/test_carbon_migration.py`:
```python
import pytest
import streamlit as st
from utils.carbon_button_helpers import ape_button, ICON_MAP

def test_icon_mapping():
    """Ensure all common words have icon mappings."""
    common_terms = ['save', 'load', 'export', 'home', 'run', 'delete']
    for term in common_terms:
        assert term in ICON_MAP, f"Missing icon mapping for '{term}'"

def test_button_keys_unique():
    """Verify button keys are unique across pages."""
    # This would scan all files and check for duplicate keys
    pass

def test_aria_labels():
    """Ensure icon-only buttons have aria labels."""
    # Test that empty label buttons have aria-label set
    pass

@pytest.mark.parametrize("button_type", ["primary", "secondary", "danger", "ghost"])
def test_button_types(button_type):
    """Test all button types render correctly."""
    # Would need Streamlit testing framework
    pass
```

### Day 12-13: Documentation

**Add troubleshooting section**:

```markdown
## Troubleshooting Guide

### Common Issues

#### 1. Button not responding
- Check key uniqueness
- Verify session state isn't conflicting
- Ensure Carbon button is properly imported

#### 2. Icon not showing
- Verify icon name in ICON_MAP
- Check CarbonIcons enum has the icon
- Use text fallback for unclear icons

#### 3. Styling issues
- Clear browser cache
- Check for CSS conflicts
- Verify Carbon button version

#### 4. Session state problems
```python
# Debug session state
if st.checkbox("Debug Session State"):
    st.json(dict(st.session_state))
```

### Migration Rollback Plan

If critical issues arise:
```bash
# Quick rollback
git checkout backup/pre-carbon-removal
git checkout -b fix/carbon-issues

# Or use feature flag
USE_CARBON_BUTTONS = st.secrets.get("USE_CARBON_BUTTONS", False)
```
```

## Performance Optimization

### Button Rendering Optimization
```python
# Cache icon lookups
@st.cache_data
def get_icon_for_label(label: str):
    """Cache icon lookups for performance."""
    label_lower = label.lower()
    if label_lower in ICON_MAP:
        return ICON_MAP[label_lower]
    
    for keyword, icon in ICON_MAP.items():
        if keyword in label_lower:
            return icon
    
    return None
```

### Lazy Loading
```python
# Only import Carbon buttons when needed
def lazy_import_carbon():
    """Lazy import to improve initial page load."""
    global carbon_button, CarbonIcons
    if 'carbon_button' not in globals():
        from streamlit_carbon_button import carbon_button, CarbonIcons
    return carbon_button, CarbonIcons
```

## Success Metrics

### Test-Driven Success Criteria
All metrics verified through automated Playwright tests:

### Quantitative Metrics (Automated)
- [ ] Page load time: ≤ 100ms increase (measured by performance tests)
- [ ] Button response time: < 50ms (measured by interaction tests)
- [ ] Memory usage: ≤ 10% increase (measured by performance monitor)
- [ ] Bundle size: Document increase (measured by build analysis)
- [ ] Test coverage: 100% of button functionality
- [ ] Zero failing tests before deployment

### Qualitative Metrics (Test Reports)
- [ ] Visual consistency: 0 unapproved visual changes
- [ ] Accessibility: Fewer violations than baseline
- [ ] All user journeys: Passing E2E tests
- [ ] Download functionality: All formats working

### Test Dashboard
```bash
# View test metrics dashboard
npm run test:all -- --reporter=html
# Includes: pass/fail rates, performance metrics, screenshots
```

## Risk Mitigation

### High-Risk Areas
1. **Session State Conflicts**
   - Test extensively with forms
   - Document any behavior changes
   
2. **Performance on Button-Heavy Pages**
   - Profile Analysis Overview page
   - Consider pagination if needed

3. **Mobile Responsiveness**
   - Test on various screen sizes
   - Adjust button sizes for mobile

4. **Browser Compatibility**
   - Test on Chrome, Firefox, Safari, Edge
   - Document any limitations

## Post-Implementation Monitoring

### Week 3: Monitoring Phase
- Monitor error logs for button-related issues
- Track performance metrics via automated tests
- Run nightly regression tests
- Fix any edge cases found by tests

### Continuous Testing
```yaml
# .github/workflows/nightly-tests.yml
name: Nightly Carbon Button Tests
on:
  schedule:
    - cron: '0 2 * * *'  # 2 AM daily
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: npm ci
      - run: npx playwright install
      - run: npm run test:all
      - run: npm run test:perf
```

### Success Celebration
- Team demo of new UI with test results
- Document lessons learned
- Share performance improvements (with metrics)
- Plan next UI enhancements

## TDD Benefits Realized

1. **Zero Regressions**: Every button behavior preserved
2. **Confidence**: Tests prove functionality works
3. **Documentation**: Tests document expected behavior
4. **Performance**: Metrics tracked automatically
5. **Accessibility**: Improvements measured objectively
6. **Maintenance**: Tests catch future breaks

## Test Maintenance Going Forward

- Keep all tests running in CI/CD
- Update tests when adding new buttons
- Visual regression baseline updates quarterly
- Performance benchmarks tracked over time
- Accessibility scores monitored monthly