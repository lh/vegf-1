"""Test the recruitment UI components."""

import streamlit as st
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

from components.simulation_ui_v2 import render_recruitment_parameters, render_preset_buttons_v2

st.set_page_config(page_title="Test Recruitment UI", layout="wide")

st.title("Test Recruitment UI Components")

# Test preset buttons
st.header("Preset Buttons")
render_preset_buttons_v2()

# Test recruitment parameters
st.header("Recruitment Parameters")
params = render_recruitment_parameters()

# Display the returned parameters
st.header("Returned Parameters")
st.json(params)

# Show what the simulation would use
st.header("Simulation Configuration")
if params['mode'] == 'Fixed Total':
    st.info(f"""
    **Fixed Total Mode**
    - Total patients: {params['n_patients']:,}
    - Duration: {params['duration_years']} years
    - Patients will be recruited throughout the entire period
    """)
else:
    st.info(f"""
    **Constant Rate Mode**  
    - Rate: {params['recruitment_rate']} patients {params['rate_unit']}
    - Duration: {params['duration_years']} years
    - Expected total: ~{params.get('expected_total', 0):,} patients
    - Actual count will vary due to random arrival times
    """)