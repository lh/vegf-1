"""
Test to determine if we're using Carbon buttons or Streamlit fallback
"""

import streamlit as st
from utils.carbon_buttons import carbon_action_button, CARBON_AVAILABLE, convert_emoji_to_icon

st.set_page_config(page_title="Carbon or Fallback Test", page_icon="🔍")

st.title("🔍 Carbon Button Detection Test")

st.markdown("---")
st.subheader("1. Component Status")

# Check if Carbon is available
if CARBON_AVAILABLE:
    st.success(f"✅ Carbon component is AVAILABLE (CARBON_AVAILABLE = {CARBON_AVAILABLE})")
    st.write("The app should be using actual Carbon buttons.")
else:
    st.warning(f"⚠️ Carbon component NOT available (CARBON_AVAILABLE = {CARBON_AVAILABLE})")
    st.write("The app is using Streamlit fallback buttons.")

# Try direct import
st.subheader("2. Direct Import Test")
try:
    from briquette import carbon_button
    st.success("✅ Direct import of briquette.carbon_button successful")
    st.code("from briquette import carbon_button  # Works!")
except ImportError as e:
    st.error(f"❌ Cannot import Carbon button: {e}")

# Check actual rendering
st.subheader("3. Button Rendering Test")
st.write("If these are Carbon buttons, they should have:")
st.write("- Rounded corners with Carbon Design styling")
st.write("- Different hover effects than standard Streamlit")
st.write("- Custom colors (warm grey/teal in light mode)")

col1, col2 = st.columns(2)

with col1:
    st.markdown("**Test Button:**")
    if carbon_action_button("I'm a button", key="test_render"):
        st.write("Clicked!")

with col2:
    st.markdown("**With Icon:**")
    label, icon = convert_emoji_to_icon("🎯 Icon Button")
    if carbon_action_button(label, key="test_icon", icon=icon):
        st.write("Icon clicked!")

# Session state check
st.subheader("4. Session State Keys")
st.write("Carbon buttons use 'carbon_' prefix, fallback uses 'fallback_' prefix:")

# Filter for button-related keys
button_keys = [k for k in st.session_state.keys() if 'carbon_' in k or 'fallback_' in k]
if button_keys:
    for key in button_keys:
        if 'carbon_' in key:
            st.success(f"✅ {key} - Using Carbon button")
        elif 'fallback_' in key:
            st.warning(f"⚠️ {key} - Using fallback")
else:
    st.info("No button keys found yet. Click a button to see.")

# Visual comparison
st.subheader("5. Visual Comparison")

col1, col2 = st.columns(2)

with col1:
    st.markdown("**Your current buttons:**")
    if carbon_action_button("Primary", key="vis_primary", kind="primary"):
        pass
    if carbon_action_button("Secondary", key="vis_secondary", kind="secondary"):
        pass
    if carbon_action_button("Danger", key="vis_danger", kind="danger"):
        pass

with col2:
    st.markdown("**Standard Streamlit buttons:**")
    if st.button("Primary", key="st_primary", type="primary"):
        pass
    if st.button("Secondary", key="st_secondary", type="secondary"):
        pass
    # Note: Streamlit doesn't have a native "danger" type
    if st.button("Danger (as secondary)", key="st_danger", type="secondary"):
        pass

st.info("""
**How to tell the difference:**
- Carbon buttons have more rounded corners
- Carbon buttons have different shadow/depth effects
- Carbon danger buttons are red (Streamlit doesn't have danger type)
- Check the browser DevTools - Carbon buttons are in an iframe
""")

# Force test both modes
st.subheader("6. Force Test Both Modes")

import utils.carbon_buttons as cb

col1, col2 = st.columns(2)

with col1:
    st.markdown("**Force Carbon Mode:**")
    original = cb.CARBON_AVAILABLE
    cb.CARBON_AVAILABLE = True
    
    if cb.carbon_action_button("Force Carbon", key="force_carbon"):
        st.write("Carbon clicked")
    
    cb.CARBON_AVAILABLE = original

with col2:
    st.markdown("**Force Fallback Mode:**")
    original = cb.CARBON_AVAILABLE
    cb.CARBON_AVAILABLE = False
    
    if cb.carbon_action_button("Force Fallback", key="force_fallback"):
        st.write("Fallback clicked")
    
    cb.CARBON_AVAILABLE = original