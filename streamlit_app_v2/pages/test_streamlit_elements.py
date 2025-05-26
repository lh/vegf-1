"""
Using streamlit-elements for professional buttons
This already works and requires no custom component development!
"""

import streamlit as st

st.set_page_config(page_title="Streamlit Elements Demo", page_icon="🎯")

st.title("🎯 Alternative: streamlit-elements")
st.markdown("Professional buttons without building custom components!")

# Check if streamlit-elements is installed
try:
    from streamlit_elements import elements, mui, html
    
    st.success("✅ streamlit-elements is installed!")
    
    # Demo section
    st.header("Material-UI Buttons (Similar to Carbon)")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        with elements("button_demo1"):
            # Primary button with icon
            mui.Button(
                "Upload File",
                variant="contained",
                startIcon=mui.icons.CloudUpload(),
                onClick=lambda: st.session_state.update({"clicked": "upload"})
            )
    
    with col2:
        with elements("button_demo2"):
            # Secondary button
            mui.Button(
                "Download",
                variant="outlined",
                startIcon=mui.icons.CloudDownload(),
                onClick=lambda: st.session_state.update({"clicked": "download"})
            )
    
    with col3:
        with elements("button_demo3"):
            # Text button
            mui.Button(
                "Settings",
                variant="text",
                startIcon=mui.icons.Settings(),
                onClick=lambda: st.session_state.update({"clicked": "settings"})
            )
    
    # Show click result
    if "clicked" in st.session_state:
        st.info(f"You clicked: {st.session_state.clicked}")
    
    # More examples
    st.header("Icon Buttons")
    
    with elements("icon_buttons"):
        with mui.Box(sx={"display": "flex", "gap": 2}):
            mui.IconButton(
                mui.icons.Delete(),
                color="error",
                onClick=lambda: st.session_state.update({"action": "delete"})
            )
            mui.IconButton(
                mui.icons.Edit(),
                color="primary",
                onClick=lambda: st.session_state.update({"action": "edit"})
            )
            mui.IconButton(
                mui.icons.Share(),
                color="default",
                onClick=lambda: st.session_state.update({"action": "share"})
            )
    
    # Custom styled buttons
    st.header("Custom Styled Buttons")
    
    with elements("custom_buttons"):
        # Carbon-like styling
        mui.Button(
            "Carbon Style",
            variant="contained",
            sx={
                "backgroundColor": "#0f62fe",
                "color": "white",
                "&:hover": {
                    "backgroundColor": "#0043ce",
                },
                "textTransform": "none",
                "borderRadius": 0,
            }
        )
    
except ImportError:
    st.error("❌ streamlit-elements is not installed")
    st.markdown("""
    ### To use this approach:
    
    ```bash
    pip install streamlit-elements
    ```
    
    ### Benefits:
    - Ready-to-use Material-UI components
    - Hundreds of icons included
    - Proper event handling
    - No CSS hacks needed
    - Professional appearance
    
    ### Similar to Carbon:
    - Clean, modern design
    - Accessibility built-in
    - Consistent styling
    - Enterprise-ready
    """)

# Comparison section
st.header("📊 Comparison of Approaches")

comparison_data = {
    "Approach": ["CSS Hack (Current)", "streamlit-elements", "Custom Component"],
    "Setup Time": ["5 minutes", "10 minutes", "2-3 days"],
    "Maintenance": ["Low", "Low", "High"],
    "Flexibility": ["Medium", "High", "Very High"],
    "Professional Look": ["Good", "Excellent", "Perfect"],
    "Works Today": ["✅", "✅", "❌"],
}

import pandas as pd
df = pd.DataFrame(comparison_data)
st.dataframe(df, use_container_width=True)

st.markdown("""
### My Recommendation:

1. **For now**: Your CSS solution works great! ✅
2. **Want more?**: Try `streamlit-elements` - it's ready to use
3. **Perfect control?**: Build custom component (only if really needed)

The CSS hack is clever and sufficient for most use cases. Don't over-engineer unless you need to!
""")