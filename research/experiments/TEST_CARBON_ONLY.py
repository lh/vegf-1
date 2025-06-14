"""Test only streamlit-carbon-button import."""

import streamlit as st

st.set_page_config(page_title="Carbon Button Test", page_icon="🔘")
st.title("🔘 Carbon Button Import Test")

# Test the import
try:
    from streamlit_carbon_button import carbon_button, CarbonIcons
    st.success("✅ streamlit-carbon-button imported successfully!")
    
    # Try to use it
    if carbon_button("Test Button", key="test_btn", icon=CarbonIcons.HOME):
        st.write("Button clicked!")
        
except Exception as e:
    st.error(f"❌ Import failed: {e}")
    import traceback
    st.code(traceback.format_exc())