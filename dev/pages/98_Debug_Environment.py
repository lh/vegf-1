"""
Debug page to check environment detection.

This page helps verify that environment detection is working correctly
and shows all relevant environment variables.
"""

import streamlit as st
import os
from pathlib import Path

from ape.utils.environment import get_environment_info, is_streamlit_cloud, get_memory_limit_mb
from ape.core.monitoring.memory import MemoryMonitor

st.set_page_config(
    page_title="Environment Debug",
    page_icon="🐛",
    layout="wide"
)

st.title("🐛 Environment Debug")
st.markdown("Debug information for environment detection")

# Get environment info
env_info = get_environment_info()

# Main detection result
col1, col2, col3 = st.columns(3)
with col1:
    if env_info['is_cloud']:
        st.success("☁️ **Running on Streamlit Cloud**")
    else:
        st.info("💻 **Running Locally**")
        
with col2:
    st.metric("Memory Limit", f"{get_memory_limit_mb():,} MB")
    
with col3:
    monitor = MemoryMonitor()
    info = monitor.get_memory_info()
    st.metric("Current Usage", f"{info['used_mb']:.0f} MB")

# Environment details
st.markdown("---")
st.subheader("Environment Variables")

# Show relevant environment variables
env_vars = env_info['env_vars']
cols = st.columns(2)

with cols[0]:
    st.markdown("**Streamlit Cloud Indicators:**")
    for key, value in env_vars.items():
        if value:
            st.success(f"`{key}` = `{value}`")
        else:
            st.text(f"`{key}` = None")
            
with cols[1]:
    st.markdown("**Other Info:**")
    st.text(f"Platform: {env_info['platform']}")
    st.text(f"CWD: {env_info['cwd']}")
    st.text(f"Streamlit: v{env_info['streamlit_version']}")

# All environment variables in expander
with st.expander("All Environment Variables", expanded=False):
    # Filter out sensitive variables
    sensitive_patterns = ['KEY', 'SECRET', 'PASSWORD', 'TOKEN', 'CREDENTIAL']
    
    env_dict = {}
    for key, value in os.environ.items():
        # Hide sensitive values
        if any(pattern in key.upper() for pattern in sensitive_patterns):
            env_dict[key] = "***HIDDEN***"
        else:
            env_dict[key] = value
            
    # Sort and display
    for key in sorted(env_dict.keys()):
        st.text(f"{key}: {env_dict[key]}")

# Memory thresholds
st.markdown("---")
st.subheader("Memory Thresholds")

monitor = MemoryMonitor()
col1, col2 = st.columns(2)

with col1:
    st.markdown("**Current Thresholds:**")
    st.text(f"Warning: {monitor.WARNING_THRESHOLD_MB} MB")
    st.text(f"Critical: {monitor.CRITICAL_THRESHOLD_MB} MB")
    st.text(f"Limit: {monitor.LIMIT_MB} MB")
    st.text(f"Usable: {monitor.USABLE_MB} MB")
    
with col2:
    st.markdown("**Detection Logic:**")
    st.code("""
# Detection checks these indicators:
- STREAMLIT_SHARING_MODE == 'true'
- STREAMLIT_RUNTIME_ENV == 'cloud'
- 'streamlit.io' in STREAMLIT_SERVER_ADDRESS
- '/mount/src' in current directory
- STREAMLIT_COMMUNITY_CLOUD == 'true'
    """, language="python")

# Test detection
st.markdown("---")
st.subheader("Test Results")

if st.button("Run Detection Test"):
    with st.spinner("Testing environment detection..."):
        # Force re-check
        is_cloud = is_streamlit_cloud()
        
        st.write(f"Detection result: {'☁️ Cloud' if is_cloud else '💻 Local'}")
        
        # Show which indicators triggered
        st.write("Active indicators:")
        if os.environ.get('STREAMLIT_SHARING_MODE') == 'true':
            st.write("- ✅ STREAMLIT_SHARING_MODE is 'true'")
        if os.environ.get('STREAMLIT_RUNTIME_ENV') == 'cloud':
            st.write("- ✅ STREAMLIT_RUNTIME_ENV is 'cloud'")
        if 'streamlit.io' in os.environ.get('STREAMLIT_SERVER_ADDRESS', ''):
            st.write("- ✅ streamlit.io in server address")
        if '/mount/src' in os.getcwd():
            st.write("- ✅ /mount/src in working directory")
        if os.environ.get('STREAMLIT_COMMUNITY_CLOUD') == 'true':
            st.write("- ✅ STREAMLIT_COMMUNITY_CLOUD is 'true'")