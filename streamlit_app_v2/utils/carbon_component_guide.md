# Creating a Proper Streamlit Carbon Button Component

## Difficulty Level: Medium (2-3 days for a developer familiar with React)

### What's Involved:

## 1. Project Structure
```
carbon-button-component/
├── frontend/                 # React/TypeScript code
│   ├── src/
│   │   ├── CarbonButton.tsx # Main component
│   │   └── index.tsx        # Entry point
│   ├── package.json
│   └── tsconfig.json
├── carbon_button/           # Python package
│   ├── __init__.py         # Python interface
│   └── frontend/           # Built JS files
├── setup.py                # Python package setup
└── MANIFEST.in
```

## 2. Frontend Code (React/TypeScript)
```typescript
// CarbonButton.tsx
import React from "react"
import { Streamlit, ComponentProps } from "streamlit-component-lib"

interface CarbonButtonProps extends ComponentProps {
  args: {
    label: string
    icon: string
    buttonType: "primary" | "secondary" | "danger"
    disabled: boolean
  }
}

const CarbonButton: React.FC<CarbonButtonProps> = ({ args }) => {
  const { label, icon, buttonType, disabled } = args

  const handleClick = () => {
    // Send click event to Python
    Streamlit.setComponentValue(true)
  }

  return (
    <button 
      className={`carbon-btn carbon-btn--${buttonType}`}
      onClick={handleClick}
      disabled={disabled}
    >
      <span dangerouslySetInnerHTML={{ __html: icon }} />
      <span>{label}</span>
    </button>
  )
}

export default CarbonButton
```

## 3. Python Interface
```python
# carbon_button/__init__.py
import streamlit.components.v1 as components
import os

# Development mode
_DEVELOP_MODE = os.getenv("STREAMLIT_COMPONENT_DEV_MODE", False)

if _DEVELOP_MODE:
    # Hot reloading for development
    _component_func = components.declare_component(
        "carbon_button",
        url="http://localhost:3001",  # Dev server URL
    )
else:
    # Production - use built files
    parent_dir = os.path.dirname(os.path.abspath(__file__))
    build_dir = os.path.join(parent_dir, "frontend/build")
    _component_func = components.declare_component(
        "carbon_button", 
        path=build_dir
    )

def carbon_button(label, icon, key=None, button_type="primary", disabled=False):
    """Create a Carbon Design System button"""
    
    # Call the component
    clicked = _component_func(
        label=label,
        icon=icon,
        buttonType=button_type,
        disabled=disabled,
        key=key,
        default=False,
    )
    
    return clicked or False
```

## 4. Build Process
```json
// frontend/package.json
{
  "name": "carbon-button",
  "version": "1.0.0",
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build",
    "test": "react-scripts test"
  },
  "dependencies": {
    "react": "^18.0.0",
    "streamlit-component-lib": "^2.0.0",
    "@carbon/react": "^1.0.0"  // Official Carbon React components
  }
}
```

## 5. Setup & Distribution
```python
# setup.py
from setuptools import setup, find_packages

setup(
    name="streamlit-carbon-button",
    version="1.0.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=["streamlit>=1.0.0"],
    package_data={
        "carbon_button": ["frontend/build/**/*"]
    }
)
```

## Time Breakdown:

### Day 1: Setup & Basic Component (6-8 hours)
- Set up React/TypeScript project
- Create basic button component
- Implement Streamlit communication
- Test in development mode

### Day 2: Styling & Features (6-8 hours)
- Integrate Carbon Design System properly
- Add all button variants
- Handle all props and states
- Test edge cases

### Day 3: Build & Package (4-6 hours)
- Production build configuration
- Python packaging
- Documentation
- Publish to PyPI (optional)

## Easier Alternative: Use streamlit-elements

```python
# This already exists and works today!
pip install streamlit-elements

from streamlit_elements import elements, mui

with elements("carbon_style_button"):
    mui.Button(
        "Upload",
        variant="contained",
        startIcon=mui.icons.Upload(),
        onClick=lambda: print("Clicked!")
    )
```

## Is It Worth It?

### Pros of Custom Component:
- Perfect integration with Streamlit
- No CSS hacks needed
- Can use full Carbon React library
- Reusable across projects
- Could share with community

### Cons:
- 2-3 days of development
- Need React/TypeScript knowledge
- Maintenance burden
- Build process complexity
- Testing across Streamlit versions

## My Recommendation:

**For your project**: The current CSS solution works fine! It's a clever hack that gets the job done.

**If you have many projects**: Consider investing in a proper component or using streamlit-elements.

**For the Streamlit community**: Someone should definitely make this! It would be a popular component.

## Quick Decision Tree:

1. **Just need it to work?** → Use current CSS solution ✅
2. **Want perfect integration?** → Try streamlit-elements first
3. **Need exact Carbon specs?** → Build custom component
4. **Have React skills & time?** → Definitely build it!

The difficulty isn't in the complexity - it's in learning the ecosystem if you're not already familiar with React and the Streamlit component architecture.