"""
Test page for Carbon Design System buttons
"""

import streamlit as st
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from utils.carbon_button import carbon_button, CarbonIcons

st.set_page_config(page_title="Carbon Button Test", page_icon="🎨")

st.title("🎨 Carbon Design System Buttons")
st.markdown("Beautiful IBM Carbon icons working in Streamlit buttons!")

# Test different button types
st.subheader("Button Types")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("**Primary Actions**")
    if carbon_button("Upload File", CarbonIcons.UPLOAD, key="up1"):
        st.success("✓ Upload clicked!")
    
    if carbon_button("Run Analysis", CarbonIcons.PLAY, key="run1"):
        st.success("✓ Running!")

with col2:
    st.markdown("**Secondary Actions**")
    if carbon_button("Download", CarbonIcons.DOWNLOAD, key="dl1", type="secondary"):
        st.info("📥 Downloading...")
    
    if carbon_button("Copy", CarbonIcons.COPY, key="cp1", type="secondary"):
        st.info("📋 Copied!")

with col3:
    st.markdown("**Danger Zone**")
    if carbon_button("Delete", CarbonIcons.WARNING, key="del1", type="danger"):
        st.error("🗑️ Deleted!")

# Full width buttons
st.subheader("Full Width Buttons")

if carbon_button("View Documentation", CarbonIcons.DOCUMENT, key="doc1", use_container_width=True):
    st.info("Opening documentation...")

if carbon_button("Go Home", CarbonIcons.HOME, key="home1", use_container_width=True, type="secondary"):
    st.info("Going home...")

# In context usage
st.subheader("In Context")

with st.expander("File Management"):
    col1, col2 = st.columns(2)
    with col1:
        if carbon_button("Upload", CarbonIcons.UPLOAD, key="up2"):
            st.success("File uploaded!")
    with col2:
        if carbon_button("Download", CarbonIcons.DOWNLOAD, key="dl2"):
            st.success("File downloaded!")

# Compare with regular buttons
st.subheader("Comparison")

col1, col2 = st.columns(2)

with col1:
    st.markdown("**Carbon Buttons**")
    carbon_button("Beautiful", CarbonIcons.CHART_BAR, key="carb1")
    carbon_button("Professional", CarbonIcons.INFO, key="carb2", type="secondary")

with col2:
    st.markdown("**Regular Streamlit**")
    st.button("📊 Basic")
    st.button("ℹ️ Limited", type="secondary")