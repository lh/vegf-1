"""
Demo of styled Carbon buttons with custom colors and effects
"""

import streamlit as st
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from utils.carbon_button import CarbonIcons
from utils.carbon_button_styled import styled_carbon_button, gradient_carbon_button

st.set_page_config(page_title="Styled Carbon Buttons", page_icon="🎨", layout="wide")

st.title("🎨 Styled Carbon Design Buttons")
st.markdown("Black icons on grey backgrounds with beautiful hover effects!")

# Main demo
st.header("Minimal Style - Your Request")
st.markdown("Black lines on grey background, becoming bright on hover and darker on click")

col1, col2, col3, col4 = st.columns(4)

with col1:
    if styled_carbon_button("Upload", CarbonIcons.UPLOAD, key="min1", style="minimal"):
        st.success("Uploaded!")

with col2:
    if styled_carbon_button("Download", CarbonIcons.DOWNLOAD, key="min2", style="minimal"):
        st.info("Downloading...")

with col3:
    if styled_carbon_button("Save", CarbonIcons.SAVE, key="min3", style="minimal"):
        st.success("Saved!")

with col4:
    if styled_carbon_button("Settings", CarbonIcons.SETTINGS, key="min4", style="minimal"):
        st.info("Opening settings...")

st.markdown("👆 **Try hovering and clicking!** Notice how the grey gets darker on hover and inverts on click.")

st.divider()

# Different styles
st.header("Style Variations")

style_col1, style_col2, style_col3 = st.columns(3)

with style_col1:
    st.subheader("Minimal")
    st.markdown("Grey background, subtle hover")
    styled_carbon_button("Upload File", CarbonIcons.UPLOAD, key="s1", style="minimal")
    styled_carbon_button("Copy Link", CarbonIcons.COPY, key="s2", style="minimal")
    styled_carbon_button("View Chart", CarbonIcons.CHART_BAR, key="s3", style="minimal")

with style_col2:
    st.subheader("Outlined")
    st.markdown("Border only, fills on hover")
    styled_carbon_button("Add Item", CarbonIcons.ADD, key="s4", style="outlined")
    styled_carbon_button("Delete", CarbonIcons.DELETE, key="s5", style="outlined")
    styled_carbon_button("Close", CarbonIcons.CLOSE, key="s6", style="outlined")

with style_col3:
    st.subheader("Filled")
    st.markdown("Dark background, classic look")
    styled_carbon_button("Play", CarbonIcons.PLAY, key="s7", style="filled")
    styled_carbon_button("Success", CarbonIcons.SUCCESS, key="s8", style="filled")
    styled_carbon_button("Info", CarbonIcons.INFO, key="s9", style="filled")

st.divider()

# Gradient buttons
st.header("✨ Gradient Effects")
st.markdown("Premium gradient buttons with smooth transitions")

grad_col1, grad_col2, grad_col3 = st.columns(3)

with grad_col1:
    if gradient_carbon_button("Upload Premium", CarbonIcons.UPLOAD, key="g1"):
        st.balloons()

with grad_col2:
    if gradient_carbon_button(
        "Save Project", 
        CarbonIcons.SAVE, 
        key="g2",
        gradient_from="#e8f4f8",
        gradient_to="#b8e0d2",
        hover_from="#b8e0d2",
        hover_to="#95b8a6"
    ):
        st.success("Project saved!")

with grad_col3:
    if gradient_carbon_button(
        "Run Analysis",
        CarbonIcons.PLAY,
        key="g3",
        gradient_from="#fff3e0",
        gradient_to="#ffe0b2",
        hover_from="#ffe0b2",
        hover_to="#ffcc80"
    ):
        with st.spinner("Running..."):
            import time
            time.sleep(1)
        st.success("Complete!")

st.divider()

# Interactive color customizer
st.header("🎨 Color Playground")

with st.expander("Customize Your Button Colors"):
    custom_col1, custom_col2 = st.columns(2)
    
    with custom_col1:
        st.markdown("**Gradient Colors**")
        from_color = st.color_picker("From Color", "#f4f4f4")
        to_color = st.color_picker("To Color", "#e0e0e0")
        hover_from = st.color_picker("Hover From", "#e0e0e0")
        hover_to = st.color_picker("Hover To", "#c6c6c6")
    
    with custom_col2:
        st.markdown("**Preview**")
        if gradient_carbon_button(
            "Custom Button",
            CarbonIcons.SETTINGS,
            key="custom",
            gradient_from=from_color,
            gradient_to=to_color,
            hover_from=hover_from,
            hover_to=hover_to
        ):
            st.success("Looking good!")

st.divider()

# Real application example
st.header("📱 Real Application Example")

app_col1, app_col2 = st.columns([2, 1])

with app_col1:
    st.subheader("Document Manager")
    
    # Search bar mockup
    search_col1, search_col2 = st.columns([4, 1])
    with search_col1:
        st.text_input("Search documents...", key="search", label_visibility="collapsed")
    with search_col2:
        styled_carbon_button("Search", CarbonIcons.SAVE, key="search_btn", style="minimal")
    
    # Document list
    docs = [
        ("Annual Report 2024.pdf", "2.4 MB", "Jan 15"),
        ("Project Proposal.docx", "156 KB", "Jan 14"),
        ("Budget Analysis.xlsx", "3.1 MB", "Jan 12")
    ]
    
    for doc_name, size, date in docs:
        doc_col1, doc_col2, doc_col3, doc_col4 = st.columns([3, 1, 1, 1])
        
        with doc_col1:
            st.markdown(f"📄 **{doc_name}**  \n<small style='color: #666;'>{size} • {date}</small>", unsafe_allow_html=True)
        
        with doc_col2:
            styled_carbon_button("", CarbonIcons.DOWNLOAD, key=f"dl_{doc_name}", style="minimal")
        
        with doc_col3:
            styled_carbon_button("", CarbonIcons.COPY, key=f"cp_{doc_name}", style="minimal")
        
        with doc_col4:
            styled_carbon_button("", CarbonIcons.DELETE, key=f"del_{doc_name}", style="outlined")

with app_col2:
    st.subheader("Actions")
    
    if styled_carbon_button("Upload New", CarbonIcons.UPLOAD, key="app_upload", 
                           style="minimal", use_container_width=True):
        st.info("Upload dialog would open here")
    
    if styled_carbon_button("Create Folder", CarbonIcons.ADD, key="app_folder",
                           style="outlined", use_container_width=True):
        st.info("New folder created")
    
    if gradient_carbon_button("Generate Report", CarbonIcons.CHART_BAR, key="app_report",
                             use_container_width=True):
        st.success("Report generated!")

st.divider()

# CSS explanation
with st.expander("🔧 How It Works"):
    st.markdown("""
    ### The Magic of SVG + CSS
    
    Since Carbon icons use `fill="currentColor"`, they inherit the text color of their container.
    This allows us to control their appearance with CSS:
    
    ```css
    /* Normal state - black on grey */
    .carbon-btn {
        color: #393939;  /* Dark grey/black icon */
        background-color: #f4f4f4;  /* Light grey background */
    }
    
    /* Hover - darker grey background */
    .carbon-btn:hover {
        color: #161616;  /* Pure black icon */
        background-color: #e0e0e0;  /* Darker grey */
    }
    
    /* Active (clicked) - inverted colors */
    .carbon-btn:active {
        color: #ffffff;  /* White icon */
        background-color: #525252;  /* Dark grey background */
    }
    ```
    
    ### Benefits Over Regular Buttons:
    1. **Complete style control** - Any color combination
    2. **Smooth transitions** - Professional micro-interactions  
    3. **State feedback** - Clear hover and click states
    4. **Consistent with your brand** - Match any design system
    5. **Accessible** - Maintains button semantics
    """)

# Footer
st.markdown("---")
st.markdown("🎨 **Styled with CSS** • 🔧 **Powered by Carbon Design System** • 🚀 **Works on Streamlit Cloud**")