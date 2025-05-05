import streamlit as st
import sys
import os

# Add the current directory to sys.path
sys.path.append(os.getcwd())

st.title("Import Test")
st.write("Python path:", sys.path)

try:
    from simulation.config import SimulationConfig
    st.success("SimulationConfig imported successfully")
except ImportError as e:
    st.error(f"Failed to import SimulationConfig: {e}")

try:
    import treat_and_extend_abs
    st.success("treat_and_extend_abs imported successfully")
except ImportError as e:
    st.error(f"Failed to import treat_and_extend_abs: {e}")

try:
    import treat_and_extend_des
    st.success("treat_and_extend_des imported successfully")
except ImportError as e:
    st.error(f"Failed to import treat_and_extend_des: {e}")