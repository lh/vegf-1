"""
Simple test of Carbon button integration
"""

import streamlit as st
from utils.carbon_buttons import carbon_action_button, convert_emoji_to_icon

st.set_page_config(page_title="Carbon Button Simple Test", page_icon="🧪", layout="wide")

st.title("🧪 Carbon Button Simple Test")

st.markdown("---")
st.subheader("Basic Buttons")

col1, col2, col3, col4 = st.columns(4)

with col1:
    if carbon_action_button("Primary", key="test_primary", kind="primary"):
        st.success("Primary clicked!")

with col2:
    if carbon_action_button("Secondary", key="test_secondary", kind="secondary"):
        st.info("Secondary clicked!")

with col3:
    if carbon_action_button("Danger", key="test_danger", kind="danger"):
        st.warning("Danger clicked!")

with col4:
    if carbon_action_button("Ghost", key="test_ghost", kind="ghost"):
        st.info("Ghost clicked!")

st.markdown("---")
st.subheader("With Icons (from emoji)")

# Test emoji to icon conversion
label1, icon1 = convert_emoji_to_icon("🎯 Run Simulation")
if carbon_action_button(label1, key="icon_run", icon=icon1):
    st.success("Run clicked!")

label2, icon2 = convert_emoji_to_icon("📋 Copy Checksum")
if carbon_action_button(label2, key="icon_copy", icon=icon2, kind="secondary"):
    st.info("Copy clicked!")

label3, icon3 = convert_emoji_to_icon("🗑️ Clear Results")
if carbon_action_button(label3, key="icon_clear", icon=icon3, kind="danger"):
    st.warning("Clear clicked!")

st.markdown("---")
st.subheader("Full Width")

label, icon = convert_emoji_to_icon("🎯 Run Full Width Simulation")
if carbon_action_button(label, key="full_width", kind="primary", icon=icon, use_container_width=True):
    st.success("Full width button clicked!")

st.markdown("---")
st.subheader("Real App Examples")

col1, col2 = st.columns([3, 1])
with col2:
    # Protocol Manager style
    label, icon = convert_emoji_to_icon("📋 Copy Checksum")
    if carbon_action_button(label, key="app_copy", kind="secondary", icon=icon):
        st.code("abc123def456")
        st.success("Checksum displayed above")

# Run Simulation style
st.markdown("### Run Simulation")
label, icon = convert_emoji_to_icon("🎯 Run Simulation")
if carbon_action_button(label, key="app_run", kind="primary", icon=icon, use_container_width=True):
    with st.spinner("Simulating..."):
        import time
        time.sleep(1)
    st.success("Simulation complete!")

# Clear results style
if st.checkbox("Show previous results"):
    col1, col2, col3 = st.columns(3)
    with col1:
        st.info("**Protocol:** PRN Treatment")
    with col2:
        st.info("**Patients:** 100")
    with col3:
        st.info("**Timestamp:** 2025-01-28")
    
    label, icon = convert_emoji_to_icon("🗑️ Clear Previous Results")
    if carbon_action_button(label, key="app_clear", kind="danger", icon=icon):
        st.rerun()