"""
Test the actual application pages with Carbon buttons
"""

import streamlit as st
import subprocess
import time

st.set_page_config(page_title="App Pages Test", page_icon="🧪", layout="wide")

st.title("🧪 Test Application Pages")
st.markdown("Test the Carbon button integration in the actual app pages")

# Provide links to test pages
st.markdown("---")
st.subheader("Test Pages")

st.markdown("""
### 1. Protocol Manager
- Navigate to: [Protocol Manager](http://localhost:8501/Protocol_Manager)
- Test the "📋 Copy Checksum" button
- Should show as a Carbon button with Copy icon

### 2. Run Simulation
- Navigate to: [Run Simulation](http://localhost:8501/Run_Simulation)
- Test the "🎯 Run Simulation" button (primary, full width)
- Test the "🗑️ Clear Previous Results" button (danger, small)
- Both should show as Carbon buttons with appropriate icons

### Running the Main App
To test the integration, run:
```bash
streamlit run app.py
```
""")

st.markdown("---")
st.subheader("Quick Integration Check")

# Show the modifications made
with st.expander("📝 Changes Made to Pages"):
    st.markdown("""
    **1. Protocol Manager** (`pages/1_Protocol_Manager.py`):
    ```python
    # Before:
    if st.button("📋 Copy Checksum"):
        
    # After:
    from utils.carbon_buttons import carbon_action_button, convert_emoji_to_icon
    
    label, icon = convert_emoji_to_icon("📋 Copy Checksum")
    if carbon_action_button(label, key="copy_checksum", kind="secondary", icon=icon, size="sm"):
    ```
    
    **2. Run Simulation** (`pages/2_Run_Simulation.py`):
    ```python
    # Before:
    if st.button("🎯 Run Simulation", type="primary", use_container_width=True):
    
    # After:
    label, icon = convert_emoji_to_icon("🎯 Run Simulation")
    if carbon_action_button(label, key="run_simulation", kind="primary", icon=icon, use_container_width=True):
    ```
    """)

with st.expander("🛡️ Fallback Mechanism"):
    st.markdown("""
    The integration includes automatic fallback to standard Streamlit buttons if:
    - Carbon component is not installed
    - Import fails
    - Runtime error occurs
    
    The fallback:
    - Preserves emoji icons
    - Maintains button functionality
    - Logs errors for debugging
    - Requires no code changes in pages
    """)

st.markdown("---")
st.info("💡 **Tip**: The Carbon buttons should have the subtle scientific styling you requested - warm grey/teal in light mode, pink-grey/darker teal in dark mode.")

# Button to launch the main app
if st.button("🚀 Launch Main App", type="primary"):
    st.info("Launching main app... Check http://localhost:8501")
    subprocess.Popen(["streamlit", "run", "app.py"])
    time.sleep(2)
    st.success("App should be running at http://localhost:8501")