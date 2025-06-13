"""Test deployment issues."""
import streamlit as st

st.set_page_config(page_title="Deployment Test", page_icon="🔍")
st.title("🔍 Deployment Test")

# Test imports one by one
errors = []

try:
    from pathlib import Path
    st.success("✅ pathlib imported")
except Exception as e:
    errors.append(f"pathlib: {e}")
    
try:
    import yaml
    st.success("✅ yaml imported")
except Exception as e:
    errors.append(f"yaml: {e}")

try:
    from simulation_v2.protocols.protocol_spec import ProtocolSpecification
    st.success("✅ simulation_v2 imported")
except Exception as e:
    errors.append(f"simulation_v2: {e}")
    
try:
    from ape.core.simulation_runner import SimulationRunner
    st.success("✅ ape.core imported")
except Exception as e:
    errors.append(f"ape.core: {e}")

try:
    from ape.utils.carbon_button_helpers import navigation_button
    st.success("✅ carbon_button_helpers imported")
except Exception as e:
    errors.append(f"carbon_button_helpers: {e}")

if errors:
    st.error("Import errors found:")
    for err in errors:
        st.write(f"- {err}")
else:
    st.success("All imports successful!")
    
# Test page navigation
if st.button("Test Protocol Manager"):
    st.switch_page("pages/1_Protocol_Manager.py")
    
if st.button("Test Simulations"):
    st.switch_page("pages/2_Simulations.py")
    
if st.button("Test Analysis"):
    st.switch_page("pages/3_Analysis.py")