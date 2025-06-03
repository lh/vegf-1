# Minimal UI Patterns for Streamlit

## Overview
This document captures the minimal UI patterns developed during the Carbon button migration, specifically for handling Streamlit's native components that can't be replaced.

## Key Principles
1. **Remove all redundant text** - Users know what page they're on
2. **Hide default Streamlit labels** - Use empty strings or CSS
3. **Minimize visual borders** - Use subtle backgrounds instead
4. **Compact spacing** - Reduce padding and margins
5. **Small, unobtrusive buttons** - Especially for secondary actions

## The "Manage" Pattern
When you need to hide Streamlit's native components (file uploaders, download buttons):

```python
# Single Carbon button that toggles visibility
if ape_button("Manage", key="manage_btn", icon="settings", full_width=True):
    st.session_state.show_manage = not st.session_state.get('show_manage', False)

if st.session_state.get('show_manage', False):
    with st.container():
        # Minimal file uploader - no label, no borders
        uploaded_file = st.file_uploader("", type=['yaml'], label_visibility="collapsed")
        
        # Minimal download button
        st.download_button(label="Download", data=data, file_name="file.yaml")
```

## Essential CSS for Minimal Streamlit Components

```css
/* Remove red active states - use teal instead */
.stButton > button:active,
.stButton > button:focus {
    color: #009688 !important;
    border-color: #009688 !important;
    box-shadow: 0 0 0 0.2rem rgba(0, 150, 136, 0.25) !important;
}

/* Make native buttons minimal */
.stDownloadButton > button,
.stFileUploader > div > div > button {
    background-color: transparent !important;
    border: 1px solid #ddd !important;
    color: #666 !important;
    padding: 0.25rem 0.75rem !important;
    font-size: 0.75rem !important;
}

/* Hide "Drag and drop file here" text */
.stFileUploader > div > div > small {
    display: none !important;
}

/* Remove borders from drop zone */
.stFileUploader [data-testid="stFileUploadDropzone"] {
    border: none !important;
    background-color: #f8f8f8 !important;
}

/* Compact spacing in containers */
.streamlit-expanderContent {
    padding: 0.5rem 1rem !important;
}
```

## Text Minimization Strategies

1. **File Uploader**: Use empty string for label
   ```python
   st.file_uploader("", type=['yaml'], label_visibility="collapsed")
   ```

2. **Download Button**: Simple action word only
   ```python
   st.download_button(label="Download", ...)  # Not "Download Protocol File"
   ```

3. **Section Headers**: Use HTML for smaller text when needed
   ```python
   st.markdown("<small><b>Section</b></small>", unsafe_allow_html=True)
   ```

4. **Warnings**: Inline small text instead of st.warning()
   ```python
   st.markdown("<small style='color: #FFA500;'>⚠️ Warning text</small>", unsafe_allow_html=True)
   ```

## Color Palette for Minimal UI
- **Borders**: `#ddd` (light gray)
- **Text**: `#666` (medium gray)
- **Backgrounds**: `#f8f8f8` (very light gray)
- **Active states**: `#009688` (teal, not red!)
- **Hover**: `#f0f0f0` (subtle gray)

## When to Use This Pattern
- When Streamlit's native components can't be replaced
- When you need to hide complex UI behind a simple button
- When the page context makes labels redundant
- When you want a clean, professional interface

## Example: Protocol Manager
Before: Upload Protocol, Download Protocol, Manage Protocols, Browse files, Drag and drop file here
After: Single "Manage" button that reveals minimal upload/download options

---
Remember: Less is more. If the user knows where they are, don't tell them again.