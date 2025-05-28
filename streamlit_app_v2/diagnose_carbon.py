"""
Diagnose Carbon button integration
"""

import streamlit as st
import sys
import traceback

st.set_page_config(page_title="Carbon Button Diagnostic", page_icon="🔍", layout="wide")

st.title("🔍 Carbon Button Diagnostic")

# Test 1: Check import
st.subheader("1. Import Test")
try:
    from briquette import carbon_button
    st.success("✅ Carbon button component imported successfully")
    
    # Try to use it directly
    st.write("Testing direct carbon_button usage:")
    clicks = carbon_button("Test Direct", key="direct_test")
    st.write(f"Direct carbon_button returned: {clicks}")
    
except Exception as e:
    st.error(f"❌ Failed to import Carbon button: {e}")
    st.code(traceback.format_exc())

# Test 2: Check our wrapper
st.subheader("2. Wrapper Module Test")
try:
    import utils.carbon_buttons as cb
    st.info(f"CARBON_AVAILABLE flag: {cb.CARBON_AVAILABLE}")
    
    # Test the wrapper function
    st.write("Testing wrapped carbon_action_button:")
    if cb.carbon_action_button("Test Wrapper", key="wrapper_test"):
        st.success("Wrapper button clicked!")
        
except Exception as e:
    st.error(f"❌ Failed to use wrapper: {e}")
    st.code(traceback.format_exc())

# Test 3: Check session state
st.subheader("3. Session State")
st.write("Current session state keys:")
st.code(list(st.session_state.keys()))

# Test 4: Force different scenarios
st.subheader("4. Scenario Testing")

col1, col2 = st.columns(2)

with col1:
    st.markdown("**Scenario A: Normal Operation**")
    try:
        from utils.carbon_buttons import carbon_action_button
        if carbon_action_button("Normal Test", key="scenario_normal"):
            st.success("Normal clicked!")
    except Exception as e:
        st.error(f"Error: {e}")

with col2:
    st.markdown("**Scenario B: Force Fallback**")
    try:
        import utils.carbon_buttons as cb
        # Save original state
        original = cb.CARBON_AVAILABLE
        # Force fallback
        cb.CARBON_AVAILABLE = False
        
        if cb.carbon_action_button("Fallback Test", key="scenario_fallback"):
            st.success("Fallback clicked!")
            
        # Restore
        cb.CARBON_AVAILABLE = original
    except Exception as e:
        st.error(f"Error: {e}")

# Test 5: Component visibility
st.subheader("5. Component Rendering Test")
st.write("If you see buttons below, the component is rendering:")

# Try different approaches
st.markdown("**Approach 1: Direct import**")
try:
    from briquette import carbon_button
    carbon_button("Direct Import Button", key="vis_direct")
except Exception as e:
    st.error(f"Direct import failed: {e}")

st.markdown("**Approach 2: Via wrapper**")
try:
    from utils.carbon_buttons import carbon_action_button
    carbon_action_button("Wrapper Button", key="vis_wrapper")
except Exception as e:
    st.error(f"Wrapper failed: {e}")

# Show Python path
st.subheader("6. Python Environment")
st.code(f"Python executable: {sys.executable}")
st.code(f"Python version: {sys.version}")

# Check if briquette is in the path
st.write("Checking briquette installation:")
try:
    import briquette
    st.code(f"briquette location: {briquette.__file__}")
    st.code(f"briquette version: {getattr(briquette, '__version__', 'unknown')}")
except ImportError:
    st.error("briquette not found in Python path")