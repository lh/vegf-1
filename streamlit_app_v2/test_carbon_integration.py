"""
Test script to verify Carbon button integration
"""

import streamlit as st
from utils.carbon_buttons import (
    carbon_action_button, 
    primary_action_button,
    secondary_action_button,
    danger_action_button,
    ghost_action_button,
    convert_emoji_to_icon
)

st.set_page_config(page_title="Carbon Button Test", page_icon="🧪", layout="wide")

st.title("🧪 Carbon Button Integration Test")
st.markdown("Testing the Carbon button integration for AMD Protocol Explorer")

st.markdown("---")
st.subheader("Button Types")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("**Primary**")
    if primary_action_button("Run Simulation", key="test_primary"):
        st.success("Primary clicked!")

with col2:
    st.markdown("**Secondary**")  
    if secondary_action_button("Copy Data", key="test_secondary"):
        st.info("Secondary clicked!")

with col3:
    st.markdown("**Danger**")
    if danger_action_button("Clear Results", key="test_danger"):
        st.warning("Danger clicked!")

with col4:
    st.markdown("**Ghost**")
    if ghost_action_button("Settings", key="test_ghost"):
        st.info("Ghost clicked!")

st.markdown("---")
st.subheader("Icon Integration")

# Test emoji to icon conversion
test_labels = [
    "🎯 Run Simulation",
    "📋 Copy Checksum", 
    "🗑️ Clear Previous Results",
    "💾 Save Results",
    "📊 View Analysis"
]

cols = st.columns(len(test_labels))
for i, label in enumerate(test_labels):
    with cols[i]:
        clean_label, icon = convert_emoji_to_icon(label)
        if carbon_action_button(clean_label, key=f"icon_test_{i}", icon=icon, size="sm"):
            st.caption(f"Icon: {icon}")

st.markdown("---")
st.subheader("Sizes")

sizes = ["sm", "md", "lg", "xl"]
cols = st.columns(len(sizes))
for i, size in enumerate(sizes):
    with cols[i]:
        st.markdown(f"**Size: {size}**")
        if carbon_action_button(f"{size.upper()} Button", key=f"size_{size}", size=size):
            st.caption(f"Size {size} clicked")

st.markdown("---")
st.subheader("Full Width")

if carbon_action_button("Full Width Primary Button", key="full_width", kind="primary", use_container_width=True):
    st.success("Full width button clicked!")

st.markdown("---")
st.subheader("Real Examples from App")

st.markdown("**Protocol Manager Page:**")
col1, col2 = st.columns([3, 1])
with col2:
    label, icon = convert_emoji_to_icon("📋 Copy Checksum")
    if carbon_action_button(label, key="copy_checksum_test", kind="secondary", icon=icon, size="sm"):
        st.code("abc123def456")
        st.success("Checksum displayed above")

st.markdown("**Run Simulation Page:**")
label, icon = convert_emoji_to_icon("🎯 Run Simulation")
if carbon_action_button(label, key="run_simulation_test", kind="primary", icon=icon, use_container_width=True):
    with st.spinner("Simulating..."):
        import time
        time.sleep(2)
    st.success("Simulation complete!")

# Show previous results section
if st.checkbox("Show Previous Results Section"):
    st.markdown("### Previous Results Available")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.info("**Protocol:** PRN Treatment")
    with col2:
        st.info("**Patients:** 100")
    with col3:
        st.info("**Timestamp:** 2025-01-28 12:00:00")
        
    label, icon = convert_emoji_to_icon("🗑️ Clear Previous Results")
    if carbon_action_button(label, key="clear_results_test", kind="danger", icon=icon, size="sm"):
        st.session_state.simulation_results = None
        st.rerun()