# IBM Carbon Design System Icons in Streamlit

## Quick Start

### 1. Get the Icons from Carbon

Visit: https://carbondesignsystem.com/elements/icons/library/

Search and download these icons:
- **Download** → "Download" (16px)
- **Upload** → "Upload" (16px)
- **Run** → "Play" or "PlayFilled" (16px)
- **Duplicate** → "Copy" (16px)
- **Protocol** → "Document" or "DocumentBlank" (16px)
- **Home** → "Home" (16px)
- **Analysis** → "ChartBar" or "Analytics" (16px)
- **Warning** → "Warning" or "WarningFilled" (16px)
- **Information** → "Information" or "InformationFilled" (16px)

### 2. Implementation Strategy

Since Streamlit buttons don't support SVG/HTML, we have three approaches:

#### Approach 1: Unicode Symbols (Recommended for Buttons)
Already implemented in `icons.py`. Just change:
```python
ICON_TYPE = "unicode"  # Clean, works everywhere
```

#### Approach 2: Carbon SVGs for Non-Button Elements
Use Carbon SVGs in headers, text, and custom components:
```python
import streamlit as st
from utils.carbon_icons import get_carbon_icon

# In headers and text
st.markdown(f'{get_carbon_icon("download", size=20)} Download Results', unsafe_allow_html=True)

# In columns for button-like appearance
col1, col2 = st.columns([1, 10])
with col1:
    st.markdown(get_carbon_icon("upload", size=24), unsafe_allow_html=True)
with col2:
    if st.button("Upload File"):
        # Handle upload
```

#### Approach 3: Hybrid Approach (Best of Both)
Use Unicode for buttons, Carbon SVGs elsewhere:
```python
# Buttons use unicode
if st.button(f"{get_icon('upload')} Upload", key="upload_btn"):
    st.success("File uploaded!")

# Headers use Carbon SVG
st.markdown(f'''
<h3 style="display: flex; align-items: center; gap: 8px;">
    {get_carbon_icon("chart-bar", size=24)}
    Analysis Results
</h3>
''', unsafe_allow_html=True)
```

### 3. Adding Carbon SVGs to Your Project

1. Download the SVG files from Carbon
2. Open each SVG file in a text editor
3. Copy the SVG content
4. Add to `SVG_ICONS` in `icons.py`:

```python
SVG_ICONS = {
    "download": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="16" height="16" fill="currentColor">
        <!-- Paste Carbon SVG path elements here -->
    </svg>''',
    # Add more icons...
}
```

### 4. Example Implementation

```python
# pages/1_Protocol_Manager.py
from utils.icons import get_icon, ICON_TYPE

# Current emoji implementation
with st.popover(f"{get_icon('upload')} Upload", use_container_width=True):
    # Upload logic

# Works with all icon types without code changes!
```

### 5. Custom Styled Carbon Buttons (Advanced)

For a more Carbon-like appearance:
```python
def carbon_style_button(label: str, icon_name: str, key: str = None):
    """Create a Carbon-styled button area"""
    container = st.container()
    with container:
        col1, col2, col3 = st.columns([1, 8, 1])
        with col2:
            # Style the container
            st.markdown("""
            <style>
            .carbon-button {
                background: #f4f4f4;
                border: 1px solid #e0e0e0;
                padding: 8px 16px;
                border-radius: 0;
                transition: all 0.1s;
                cursor: pointer;
            }
            .carbon-button:hover {
                background: #e0e0e0;
            }
            </style>
            """, unsafe_allow_html=True)

            # Create button with unicode icon
            return st.button(f"{get_icon(icon_name)} {label}",
                           key=key, use_container_width=True)
```

## Benefits of This Approach

1. **Future-proof**: Easy to switch between emoji, unicode, and SVG
2. **Consistent**: One icon system throughout the app
3. **Accessible**: Unicode symbols work everywhere
4. **Professional**: Carbon icons give a polished look
5. **Flexible**: Mix approaches based on context