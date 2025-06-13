"""
Example usage of the flexible icon system.
Shows how to use both emoji and SVG icons.
"""

import streamlit as st
from icons import get_icon, icon, icon_button, ICON_TYPE

# Example page using the icon system
st.title("Icon System Example")

st.header("Current Mode: " + ICON_TYPE)

# Basic usage - works with both emoji and SVG
st.write(f"{get_icon('home')} Home")
st.write(f"{get_icon('upload')} Upload a file")
st.write(f"{get_icon('download')} Download results")

# Buttons - automatically handles both types
col1, col2, col3 = st.columns(3)

with col1:
    if icon_button("Upload", "upload", use_container_width=True):
        st.success(f"{get_icon('success')} File uploaded!")

with col2:
    if icon_button("Duplicate", "duplicate", use_container_width=True):
        st.info(f"{get_icon('info')} Creating duplicate...")

with col3:
    if icon_button("Download", "download", use_container_width=True):
        st.success(f"{get_icon('success')} Download started!")

# Popovers with icons
with st.popover(f"{get_icon('upload')} Upload Protocol"):
    st.write("Upload your protocol file here")
    
# Example of how SVG icons would be added to icons.py:
st.code('''
# In icons.py, add SVG definitions:
SVG_ICONS = {
    "upload": \'\'\'<svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
        <path d="M7.646 1.146a.5.5 0 0 1 .708 0l3 3a.5.5 0 0 1-.708.708L8.5 2.707V11.5a.5.5 0 0 1-1 0V2.707L5.354 4.854a.5.5 0 1 1-.708-.708l3-3z"/>
        <path d="M4.406 13.841A1.5 1.5 0 0 0 5.5 14.5h5a1.5 1.5 0 0 0 1.094-.659l.248-.372A3 3 0 0 0 12.5 11.5H11a.5.5 0 0 1 0-1h1.5a4 4 0 0 1 .9 7.918l-.014.003A4 4 0 0 1 12.5 13H11a.5.5 0 0 1 0-1h1.5a3 3 0 0 0 .658-5.941z"/>
    </svg>\'\'\',
    
    "download": \'\'\'<svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
        <path d="M8.5 1.5A1.5 1.5 0 0 1 10 0h4a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2V2a2 2 0 0 1 2-2h6c-.314.418-.5.937-.5 1.5v6h-2a.5.5 0 0 0-.354.854l2.5 2.5a.5.5 0 0 0 .708 0l2.5-2.5A.5.5 0 0 0 10.5 7.5h-2v-6z"/>
    </svg>\'\'\',
}

# Then just change ICON_TYPE to "svg"
ICON_TYPE = "svg"
''', language="python")

# Migration path
st.header("Migration Path")
st.markdown("""
### Phase 1: Current (Emoji)
- All icons use emojis
- Simple, works everywhere
- No dependencies

### Phase 2: Future (SVG)
- Change `ICON_TYPE = "svg"` in icons.py
- Add SVG definitions to `SVG_ICONS` dict
- Icons automatically switch to SVG
- Buttons still use emoji as fallback (Streamlit limitation)

### Phase 3: Advanced (Optional)
- Custom HTML components for buttons with SVG
- Icon fonts (Font Awesome, Material Icons)
- Dynamic icon loading from files
""")

# Example of mixed usage in real code
st.header("Real Usage Example")
st.code('''
# In your pages/1_Protocol_Manager.py:
from ape.utils.icons import get_icon, icon_button

# Replace hardcoded emojis:
# OLD: with st.popover("📤 Upload", use_container_width=True):
# NEW:
with st.popover(f"{get_icon('upload')} Upload", use_container_width=True):
    st.markdown("**Upload Protocol File**")
    
# For buttons:
# OLD: if st.button("📝 Create Duplicate", ...):
# NEW:
if icon_button("Create Duplicate", "duplicate", use_container_width=True):
    ...
    
# Status messages:
# OLD: st.success("✅ Upload successful")
# NEW:
st.success(f"{get_icon('success')} Upload successful")
''', language="python")