"""
Test the fallback mechanism for Carbon buttons
"""

import streamlit as st
import sys

st.set_page_config(page_title="Carbon Button Fallback Test", page_icon="🛡️", layout="wide")

st.title("🛡️ Carbon Button Fallback Test")
st.markdown("Testing the fallback mechanism when Carbon buttons are unavailable")

# Test 1: Normal operation
st.markdown("---")
st.subheader("1. Normal Operation (Carbon Available)")

from utils.carbon_buttons import carbon_action_button, convert_emoji_to_icon, CARBON_AVAILABLE

st.info(f"Carbon button available: {CARBON_AVAILABLE}")

col1, col2 = st.columns(2)
with col1:
    label, icon = convert_emoji_to_icon("🎯 Run Simulation")
    if carbon_action_button(label, key="normal_test", kind="primary", icon=icon):
        st.success("Carbon button clicked!")

with col2:
    label, icon = convert_emoji_to_icon("🗑️ Clear Results")
    if carbon_action_button(label, key="normal_danger", kind="danger", icon=icon, size="sm"):
        st.warning("Danger button clicked!")

# Test 2: Simulate Carbon failure
st.markdown("---")
st.subheader("2. Simulated Component Failure")

# Temporarily modify the module to simulate failure
import utils.carbon_buttons as cb
original_carbon_available = cb.CARBON_AVAILABLE

# Force fallback mode
cb.CARBON_AVAILABLE = False

st.warning("Simulating Carbon component unavailable - should use Streamlit fallback")

col1, col2 = st.columns(2)
with col1:
    label, icon = convert_emoji_to_icon("🎯 Run Simulation")
    if carbon_action_button(label, key="fallback_test", kind="primary", icon=icon):
        st.success("Fallback button clicked!")

with col2:
    label, icon = convert_emoji_to_icon("🗑️ Clear Results")
    if carbon_action_button(label, key="fallback_danger", kind="danger", icon=icon, size="sm"):
        st.warning("Fallback danger button clicked!")

# Restore original state
cb.CARBON_AVAILABLE = original_carbon_available

# Test 3: Test all button types in fallback mode
st.markdown("---")
st.subheader("3. All Button Types in Fallback Mode")

# Force fallback again
cb.CARBON_AVAILABLE = False

test_buttons = [
    ("📋 Copy Checksum", "copy_fallback", "secondary"),
    ("💾 Save Results", "save_fallback", "primary"),
    ("📊 View Analysis", "view_fallback", "secondary"),
    ("⚙️ Settings", "settings_fallback", "ghost"),
]

cols = st.columns(len(test_buttons))
for i, (label_with_emoji, key, kind) in enumerate(test_buttons):
    with cols[i]:
        label, icon = convert_emoji_to_icon(label_with_emoji)
        if carbon_action_button(label, key=key, kind=kind, icon=icon):
            st.caption(f"{kind} clicked")

# Restore
cb.CARBON_AVAILABLE = original_carbon_available

# Test 4: Full width fallback
st.markdown("---")
st.subheader("4. Full Width Fallback")

cb.CARBON_AVAILABLE = False

label, icon = convert_emoji_to_icon("🎯 Run Full Simulation")
if carbon_action_button(label, key="full_width_fallback", kind="primary", icon=icon, use_container_width=True):
    st.success("Full width fallback button clicked!")

cb.CARBON_AVAILABLE = original_carbon_available

# Show comparison
st.markdown("---")
st.subheader("5. Side-by-Side Comparison")

col1, col2 = st.columns(2)

with col1:
    st.markdown("**Carbon Button (if available)**")
    cb.CARBON_AVAILABLE = True
    if carbon_action_button("Carbon Style", key="carbon_compare", kind="primary"):
        st.success("Carbon clicked")

with col2:
    st.markdown("**Streamlit Fallback**")
    cb.CARBON_AVAILABLE = False
    if carbon_action_button("Streamlit Style", key="streamlit_compare", kind="primary"):
        st.success("Streamlit clicked")

# Restore final state
cb.CARBON_AVAILABLE = original_carbon_available

st.markdown("---")
st.info("""
**Fallback Behavior:**
- When Carbon buttons are unavailable, the system automatically falls back to standard Streamlit buttons
- Emojis are preserved in the fallback
- Button functionality remains the same
- No code changes needed in the application pages
""")