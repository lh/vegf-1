# APE V2 Design Principles

## Core Philosophy
**Context-aware interfaces that guide users through their journey**

## Visual Hierarchy

### 1. Progressive Button Styling
Our signature interaction pattern that solved the notorious Streamlit red text issue:

```python
# The winning formula
- Resting: Slightly brighter than background (#f8f9fb)
- Hover: Bright white (#ffffff) - "Hey, click me!"
- Active: Darker than background (#d0d2d6) - "Click registered"
```

This creates an intuitive brightness progression that feels natural and satisfying.

### 2. Dynamic Layout Adaptation
Interfaces should respond to user context and workflow state:

**Before Action:**
```
[  Primary Action (50%)  ] [Secondary] [Secondary] [Secondary]
```

**After Action:**
```
[Secondary] [  New Primary Action (50%)  ] [Secondary] [Secondary]
```

The visual emphasis shifts to guide users to their likely next step.

### 3. Sidebar Management
- **Collapsed by default** - Give full focus to content
- **Logo placement** - Bottom of sidebar content on main page only
- **No redundancy** - Navigation should be clear, not repetitive

## Navigation Principles

### 1. Action-Oriented Buttons
- Use verbs that describe the action: "Run Simulation", "Change Protocol"
- Include icons for quick recognition: 🎯, 📋, 📊, 🦍
- Bold text for primary actions: `**Run Simulation**`

### 2. Conditional Availability
Future enhancement: Buttons should only appear when relevant:
- "Run Simulation" - requires loaded protocol
- "View Analysis" - requires simulation results
- Guide users through the natural workflow

### 3. Consistent Placement
- Primary action on the left (Western reading pattern)
- Navigation options in consistent order
- Footer navigation only when it adds value

## Implementation Patterns

### Button Styling
```python
from utils.button_styling import style_navigation_buttons

# Apply at page level
style_navigation_buttons()
```

### Dynamic Layouts
```python
# Adapt based on state
if st.session_state.get('simulation_results'):
    columns = [1, 3, 1, 1]  # Emphasize next action
else:
    columns = [3, 1, 1, 1]  # Emphasize current action
```

### Single-Line Action Bars
Keep related actions on the same horizontal plane:
```python
col1, col2, col3, col4 = st.columns(columns)
```

## Color & Styling Rules

### No Red Flashes
Always include the red text fix in button styling.

### Subtle Elevation
- Buttons slightly brighter than background (not pure white)
- No shadows by default (clean, modern look)
- Let color changes provide the interaction feedback

### Consistent Theming
- Maintain the same interaction pattern across all pages
- Use the progressive brightness for all clickable elements
- Keep text colors stable (no flashing)

## User Flow

### Guide, Don't Force
- Make the primary action obvious through size
- Provide escape routes (Home, Change Protocol)
- Adapt the interface to the user's journey stage

### Reduce Cognitive Load
- Hide the sidebar by default
- Remove redundant navigation options
- Use clear, action-oriented labels

### Responsive Feedback
- Immediate visual feedback on hover
- Clear "pressed" state on click
- Progress indicators for long operations

## Example Implementation

```python
# Page setup
st.set_page_config(
    page_title="Page Name",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Import and apply styling
from utils.button_styling import style_navigation_buttons
style_navigation_buttons()

# Dynamic action bar
if st.session_state.get('results'):
    col_ratios = [1, 3, 1, 1]  # Emphasize "View Results"
else:
    col_ratios = [3, 1, 1, 1]  # Emphasize "Run Process"

col1, col2, col3, col4 = st.columns(col_ratios)

# Buttons with clear actions
with col1:
    if st.button("🎯 **Primary Action**", use_container_width=True):
        # Do primary thing
        
with col2:
    if condition_met:
        if st.button("📊 Next Step", use_container_width=True):
            st.switch_page("next_page.py")
```

## Key Takeaways

1. **Context is King** - The interface should know where the user is in their journey
2. **Visual Weight = Importance** - Size and brightness indicate priority
3. **Consistency Builds Trust** - Same patterns everywhere
4. **Clean Over Clever** - Simple, clear interactions win
5. **Adapt, Don't Annoy** - Change the interface to match user needs

These principles create interfaces that feel intelligent and responsive, guiding users naturally through complex workflows without overwhelming them.