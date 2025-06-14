"""
Carbon Button Test Page - Compare old and new button styles
"""

import streamlit as st
from streamlit_carbon_button import carbon_button, CarbonIcons
import time
from pathlib import Path

from ape.utils.carbon_button_helpers import (
    ape_button, create_button_group, navigation_button,
    top_navigation_home_button, confirm_dialog_buttons,
    save_button, delete_button, upload_button
)

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
        # Using our helper functions
        if navigation_button("Home", key="c_home"):
            st.success("Home clicked!")
        if navigation_button("Protocol Manager", key="c_protocol"):
            st.success("Protocol Manager clicked!")
        if navigation_button("Run Simulation", key="c_simulation"):
            st.success("Run Simulation clicked!")
        if navigation_button("Analysis Overview", key="c_analysis"):
            st.success("Analysis Overview clicked!")
    else:
        if st.button("🦍 Home", key="s_home"):
            st.success("Home clicked!")
        if st.button("📋 **Protocol Manager**\n\nBrowse, view, and validate treatment protocols", 
                     key="s_protocol", use_container_width=True):
            st.success("Protocol Manager clicked!")
        if st.button("🚀 **Run Simulation**\n\nExecute simulations with selected protocols", 
                     key="s_simulation", use_container_width=True):
            st.success("Run Simulation clicked!")
        if st.button("📊 **Analysis**\n\nVisualize and compare simulation results", 
                     key="s_analysis", use_container_width=True):
            st.success("Analysis clicked!")

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
col1, col2 = st.columns(2)

with col1:
    st.subheader("Standard Actions")
    if use_carbon:
        if save_button(key="c_save_1"):
            st.success("Save clicked!")
        if upload_button(key="c_upload_1"):
            st.info("Upload clicked!")
        if delete_button(key="c_delete_1"):
            st.error("Delete clicked!")
    else:
        if st.button("💾 Save", key="s_save_1", type="primary"):
            st.success("Save clicked!")
        if st.button("📤 Upload", key="s_upload_1"):
            st.info("Upload clicked!")
        if st.button("🗑️ Delete", key="s_delete_1"):
            st.error("Delete clicked!")

with col2:
    st.subheader("Confirm Dialog")
    if use_carbon:
        confirm, cancel = confirm_dialog_buttons(
            confirm_key="c_confirm",
            cancel_key="c_cancel",
            is_danger=True
        )
        if confirm:
            st.error("Confirmed deletion!")
        if cancel:
            st.info("Cancelled")
    else:
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("🗑️ Confirm Delete", key="s_confirm", type="secondary"):
                st.error("Confirmed deletion!")
        with col_b:
            if st.button("Cancel", key="s_cancel"):
                st.info("Cancelled")

# Test full-width buttons
st.header("3. Full Width Actions")
if use_carbon:
    if ape_button("Run Simulation", key="c_run_full", icon="run", 
                 is_primary_action=True, full_width=True):
        with st.spinner("Running simulation..."):
            time.sleep(1)
        st.success("Simulation complete!")
else:
    if st.button("🚀 **Run Simulation**\n\nExecute simulations with selected protocols", 
                key="s_run_full", type="primary", use_container_width=True):
        with st.spinner("Running simulation..."):
            time.sleep(1)
        st.success("Simulation complete!")

# Test button groups
st.header("4. Button Groups")
if use_carbon:
    st.subheader("Export Actions")
    buttons = [
        {"label": "PNG", "key": "c_export_png", "icon": "download", "button_type": "ghost"},
        {"label": "SVG", "key": "c_export_svg", "icon": "download", "button_type": "ghost"},
        {"label": "CSV", "key": "c_export_csv", "icon": "download", "button_type": "ghost"},
        {"label": "PDF", "key": "c_export_pdf", "icon": "download", "button_type": "ghost"}
    ]
    results = create_button_group(buttons)
    for i, (btn, clicked) in enumerate(zip(buttons, results)):
        if clicked:
            st.info(f"Exporting as {btn['label']}...")
else:
    st.subheader("Export Actions")
    cols = st.columns(4)
    formats = ["PNG", "SVG", "CSV", "PDF"]
    for col, fmt in zip(cols, formats):
        with col:
            if st.button(f"📥 {fmt}", key=f"s_export_{fmt.lower()}"):
                st.info(f"Exporting as {fmt}...")

# Top navigation pattern
st.header("5. Top Navigation Pattern")
if use_carbon:
    col1, col2, col3 = st.columns([1, 6, 1])
    with col1:
        if top_navigation_home_button():
            st.info("Navigate to home")
    with col2:
        st.markdown("### Page Title Here")
else:
    col1, col2, col3 = st.columns([1, 6, 1])
    with col1:
        if st.button("🦍 Home", key="s_top_home"):
            st.info("Navigate to home")
    with col2:
        st.markdown("### Page Title Here")

# Performance metrics
st.header("6. Feature Comparison")
col1, col2 = st.columns(2)

with col1:
    st.subheader("Standard Streamlit Buttons")
    st.markdown("""
    **Pros:**
    - Simple API
    - Built-in to Streamlit
    - Emoji support
    
    **Cons:**
    - Limited styling options
    - No proper icon system
    - Inconsistent appearance
    - Limited button types
    """)

with col2:
    st.subheader("Carbon Buttons")
    st.markdown("""
    **Pros:**
    - Professional appearance
    - Consistent IBM Carbon design
    - Proper icon system
    - Multiple button types
    - Better accessibility
    
    **Cons:**
    - Additional dependency
    - Limited icon set (18 icons)
    - Learning curve
    """)

# Code examples
st.header("7. Implementation Examples")

with st.expander("View Carbon Button Helper Code"):
    st.code("""
# Simple navigation button
if navigation_button("Protocol Manager", key="nav_protocol"):
    st.switch_page("pages/1_Protocol_Manager.py")

# Primary action with icon
if ape_button("Run Simulation", key="run", icon="play", is_primary_action=True):
    run_simulation()

# Danger action
if delete_button(key="delete_item"):
    delete_selected_item()

# Button group
buttons = [
    {"label": "Save", "key": "save", "is_primary_action": True},
    {"label": "Cancel", "key": "cancel"}
]
results = create_button_group(buttons)
if results[0]:  # Save clicked
    save_data()
    """, language="python")

# Current implementation status
st.header("8. Migration Status")
st.info("""
**Current Status**: Day 1 - Test Infrastructure Complete
- ✅ Playwright tests created
- ✅ Button inventory documented  
- ✅ Carbon compatibility verified
- ✅ Icon mapping completed
- ✅ Helper functions created
- 🔄 Test page created (this page)
- ⏳ Next: Begin actual migration
""")

# Footer
st.markdown("---")
st.caption("🧪 Carbon Button Test Page - Part of APE V2 UI Migration")