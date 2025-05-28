# Carbon Button Integration: Lessons Learned

## Why the Simple Test Works (and the Complex One Didn't)

### The Key Difference: API Mismatch

The main issue was that I initially wrote the wrapper assuming the Carbon button component had a different API than it actually does.

### What I Got Wrong:

1. **Parameter name**: Used `kind` instead of `button_type`
2. **Size parameter**: Assumed it existed, but it doesn't
3. **Over-engineering**: Added complex full-width styling when the component handles it natively

### What Works:

```python
# CORRECT - matches actual Carbon button API
carbon_button(
    label="Click me",
    key="unique_key",
    button_type="primary",  # NOT "kind"
    icon=icon,             # Optional icon
    disabled=False,
    use_container_width=False,
    colors=None            # Optional custom colors
)
```

## Lessons for Integration

### 1. Always Check the Actual API First

Before writing a wrapper, verify the exact function signature:

```python
from briquette import carbon_button
import inspect
print(inspect.signature(carbon_button))
```

Output:
```
(label: str, icon: str = '', key: str = None, button_type: str = 'primary', 
 disabled: bool = False, use_container_width: bool = False, colors: dict = None) -> bool
```

### 2. Start Simple, Then Add Complexity

Instead of starting with a complex wrapper with fallbacks, first test direct usage:

```python
# Step 1: Test direct usage
from briquette import carbon_button
if carbon_button("Test", key="test1"):
    st.write("Clicked!")

# Step 2: Add simple wrapper
def my_button(label, key, **kwargs):
    return carbon_button(label, key=key, **kwargs)

# Step 3: Add features incrementally
```

### 3. Common Pitfalls to Avoid

1. **Don't assume parameter names** - check the actual component
2. **Don't add styling hacks** - test if the component handles it natively
3. **Test each feature individually** before combining them

### 4. Debugging Strategy

When buttons appear as standard Streamlit buttons instead of Carbon:

1. **Check browser console** for JavaScript errors
2. **Check terminal** for Python errors (they might be caught by try/except)
3. **Test direct component usage** without wrappers
4. **Verify the component is properly installed**

## Corrected Integration Guide

### Step 1: Install the Component
```bash
pip install git+https://github.com/lh/streamlit-carbon-button.git
```

### Step 2: Simple Direct Usage
```python
from briquette import carbon_button

# Basic button
if carbon_button("Click me", key="button1"):
    st.write("Clicked!")

# With options
if carbon_button(
    "Run Analysis",
    key="button2",
    button_type="primary",  # primary, secondary, danger, ghost
    use_container_width=True
):
    st.write("Running...")
```

### Step 3: Add Icon Support (Optional)
```python
# If you want to convert emojis to Carbon icons
def convert_emoji_to_icon(label):
    icon_map = {
        "🎯": "Play",
        "📋": "Copy",
        "🗑️": "TrashCan",
    }
    
    for emoji, icon_name in icon_map.items():
        if label.startswith(emoji):
            return label.replace(emoji, "").strip(), icon_name
    
    return label, None

# Usage
label, icon = convert_emoji_to_icon("🎯 Run Simulation")
if carbon_button(label, key="run", icon=icon):
    st.write("Running simulation...")
```

### Step 4: Add Fallback (If Needed)
```python
# Only add fallback if you need graceful degradation
try:
    from briquette import carbon_button
    CARBON_AVAILABLE = True
except ImportError:
    CARBON_AVAILABLE = False

def safe_button(label, key, button_type="primary", **kwargs):
    if CARBON_AVAILABLE:
        try:
            return carbon_button(label, key=key, button_type=button_type, **kwargs)
        except Exception as e:
            # Fallback on error
            pass
    
    # Fallback to standard button
    return st.button(label, key=f"fallback_{key}", type=button_type if button_type == "primary" else "secondary")
```

## Summary

The key to successful integration is:

1. **Know your component's API** - don't assume, verify
2. **Start simple** - get basic usage working first
3. **Test incrementally** - add features one at a time
4. **Match the component's expectations** - use correct parameter names and types

The simple test works because it uses the Carbon button component exactly as designed, without assumptions or unnecessary complexity.