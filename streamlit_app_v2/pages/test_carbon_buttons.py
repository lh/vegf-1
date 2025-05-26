"""
Test page for Carbon Design System buttons
Shows all the newly downloaded Carbon icons!
"""

import streamlit as st
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from utils.carbon_button import carbon_button, CarbonIcons

st.set_page_config(page_title="Carbon Icons Demo", page_icon="🎨", layout="wide")

st.title("🎨 IBM Carbon Design System Icons")
st.markdown("All your newly downloaded Carbon icons working beautifully in Streamlit!")

# Show all available icons
st.header("📦 Complete Icon Gallery")

# Group icons by category
icon_categories = {
    "File Operations": [
        ("Upload", CarbonIcons.UPLOAD, "upload"),
        ("Download", CarbonIcons.DOWNLOAD, "download"),
        ("Save", CarbonIcons.SAVE, "save"),
        ("Copy", CarbonIcons.COPY, "copy"),
        ("Document", CarbonIcons.DOCUMENT, "document"),
    ],
    "Actions": [
        ("Add", CarbonIcons.ADD, "add"),
        ("Delete", CarbonIcons.DELETE, "delete"),
        ("Close", CarbonIcons.CLOSE, "close"),
        ("Play", CarbonIcons.PLAY, "play"),
        ("Settings", CarbonIcons.SETTINGS, "settings"),
    ],
    "Navigation": [
        ("Home", CarbonIcons.HOME, "home"),
        ("Chart", CarbonIcons.CHART_BAR, "chart"),
    ],
    "Status": [
        ("Success", CarbonIcons.SUCCESS, "success"),
        ("Warning", CarbonIcons.WARNING, "warning"),
        ("Info", CarbonIcons.INFO, "info"),
    ]
}

# Display icons by category
for category, icons in icon_categories.items():
    st.subheader(f"**{category}**")
    cols = st.columns(len(icons))
    
    for idx, (label, icon, key_base) in enumerate(icons):
        with cols[idx]:
            if carbon_button(label, icon, key=f"{key_base}_cat"):
                st.success(f"{label} clicked!")

st.divider()

# Interactive demo section
st.header("🎯 Interactive Demos")

# File management demo
col1, col2 = st.columns(2)

with col1:
    st.subheader("📁 File Manager")
    
    action_col1, action_col2, action_col3 = st.columns(3)
    
    with action_col1:
        if carbon_button("Upload", CarbonIcons.UPLOAD, key="fm_upload"):
            st.success("📤 Uploading file...")
    
    with action_col2:
        if carbon_button("Save", CarbonIcons.SAVE, key="fm_save"):
            st.info("💾 Saving...")
    
    with action_col3:
        if carbon_button("Delete", CarbonIcons.DELETE, key="fm_delete", type="danger"):
            st.error("🗑️ Deleted!")
    
    # File list mockup
    st.markdown("**Files:**")
    file_items = ["report.pdf", "data.csv", "analysis.xlsx"]
    for file in file_items:
        fcol1, fcol2, fcol3 = st.columns([3, 1, 1])
        with fcol1:
            st.write(f"📄 {file}")
        with fcol2:
            carbon_button("", CarbonIcons.DOWNLOAD, key=f"dl_{file}", type="secondary")
        with fcol3:
            carbon_button("", CarbonIcons.COPY, key=f"cp_{file}", type="secondary")

with col2:
    st.subheader("⚙️ Control Panel")
    
    if carbon_button("Settings", CarbonIcons.SETTINGS, key="ctrl_settings", use_container_width=True):
        st.info("Opening settings...")
    
    if carbon_button("Run Analysis", CarbonIcons.PLAY, key="ctrl_run", use_container_width=True):
        with st.spinner("Running analysis..."):
            import time
            time.sleep(1)
        st.success("Analysis complete!")
    
    st.markdown("**Quick Actions:**")
    
    qa_col1, qa_col2 = st.columns(2)
    with qa_col1:
        carbon_button("Add New", CarbonIcons.ADD, key="qa_add")
    with qa_col2:
        carbon_button("Close All", CarbonIcons.CLOSE, key="qa_close", type="secondary")

st.divider()

# Button style showcase
st.header("🎨 Button Styles")

style_col1, style_col2, style_col3 = st.columns(3)

with style_col1:
    st.markdown("**Primary (Default)**")
    carbon_button("Upload File", CarbonIcons.UPLOAD, key="style_primary1")
    carbon_button("Save Document", CarbonIcons.SAVE, key="style_primary2")
    carbon_button("View Chart", CarbonIcons.CHART_BAR, key="style_primary3")

with style_col2:
    st.markdown("**Secondary**")
    carbon_button("Download", CarbonIcons.DOWNLOAD, key="style_sec1", type="secondary")
    carbon_button("Copy Link", CarbonIcons.COPY, key="style_sec2", type="secondary")
    carbon_button("Settings", CarbonIcons.SETTINGS, key="style_sec3", type="secondary")

with style_col3:
    st.markdown("**Danger**")
    carbon_button("Delete File", CarbonIcons.DELETE, key="style_danger1", type="danger")
    carbon_button("Remove All", CarbonIcons.CLOSE, key="style_danger2", type="danger")
    carbon_button("Warning!", CarbonIcons.WARNING, key="style_danger3", type="danger")

st.divider()

# Real-world example
st.header("🏢 Real Application Example")

# Simulate a protocol manager interface
st.subheader("Protocol Manager")

proto_col1, proto_col2, proto_col3, proto_col4 = st.columns([3, 1, 1, 1])

with proto_col1:
    st.selectbox("Select Protocol", ["Eylea Standard", "Eylea Extended", "Custom Protocol"], key="proto_select")

with proto_col2:
    if carbon_button("Upload", CarbonIcons.UPLOAD, key="proto_upload"):
        st.success("Protocol uploaded!")

with proto_col3:
    if carbon_button("Copy", CarbonIcons.COPY, key="proto_copy"):
        st.info("Protocol copied!")

with proto_col4:
    if carbon_button("Delete", CarbonIcons.DELETE, key="proto_delete", type="danger"):
        st.error("Protocol deleted!")

# Info section
with st.expander("ℹ️ About Carbon Design System"):
    st.markdown("""
    The **IBM Carbon Design System** is IBM's open-source design system for products and digital experiences.
    
    ### Features:
    - 🎨 Clean, professional design
    - ♿ Accessibility-first approach
    - 📱 Responsive and scalable
    - 🌍 Used by IBM globally
    
    ### In This Demo:
    - All icons are actual Carbon SVGs
    - Buttons use custom HTML/CSS to match Carbon styling
    - Click detection works through hidden Streamlit checkboxes
    - Works perfectly on Streamlit Community Cloud!
    
    ### Icon Stats:
    """)
    
    # Count available icons
    icon_count = len([attr for attr in dir(CarbonIcons) if not attr.startswith('_')])
    st.metric("Available Icons", icon_count)
    
    st.markdown(f"""
    ### Your Icons:
    {', '.join([attr for attr in dir(CarbonIcons) if not attr.startswith('_')])}
    """)

# Comparison at the bottom
st.divider()
st.header("🔄 Before & After Comparison")

comp_col1, comp_col2 = st.columns(2)

with comp_col1:
    st.markdown("### 😐 Regular Streamlit Buttons")
    st.button("📤 Upload")
    st.button("📥 Download") 
    st.button("📊 View Chart")
    st.markdown("Limited to emoji/unicode only")

with comp_col2:
    st.markdown("### 😍 Carbon Design Buttons")
    carbon_button("Upload", CarbonIcons.UPLOAD, key="comp_up")
    carbon_button("Download", CarbonIcons.DOWNLOAD, key="comp_dl")
    carbon_button("View Chart", CarbonIcons.CHART_BAR, key="comp_chart")
    st.markdown("Beautiful SVG icons from IBM!")