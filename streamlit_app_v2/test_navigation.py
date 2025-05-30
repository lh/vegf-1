"""
Navigation helper for testing Carbon buttons in the app
"""

import streamlit as st

st.set_page_config(page_title="Navigation Helper", page_icon="🧭")

st.title("🧭 Navigation Helper")

st.markdown("""
## To see the Carbon buttons in action:

1. **Use the sidebar** (click ≡ if collapsed) to navigate between pages

2. **Pages with Carbon buttons:**
   - **📋 Protocol Manager** - Look for "Copy Checksum" button
   - **🚀 Run Simulation** - Look for "Run Simulation" and "Clear Previous Results" buttons

3. **Direct links** (if sidebar navigation isn't working):
   - [Protocol Manager](/Protocol_Manager)
   - [Run Simulation](/Run_Simulation)
   - [Analysis Overview](/Analysis_Overview)

## Troubleshooting:

If you don't see the sidebar:
- Click the ≡ hamburger menu in the top left
- Or press `Ctrl+B` / `Cmd+B` to toggle sidebar

If Carbon buttons appear as standard Streamlit buttons:
- Check browser console for errors (F12)
- Verify the component is installed
- Try refreshing the page
""")

# Show current URL
st.info(f"Current page URL should be: http://localhost:8501")

# Quick status check
with st.expander("🔍 Quick Status Check"):
    try:
        from briquette import carbon_button
        st.success("✅ Carbon button component is installed")
        
        from utils.carbon_buttons import CARBON_AVAILABLE
        st.success(f"✅ Carbon wrapper available: {CARBON_AVAILABLE}")
    except Exception as e:
        st.error(f"❌ Error: {e}")