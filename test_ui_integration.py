#!/usr/bin/env python3
"""
Test the actual UI integration to make sure thumbnails work in Streamlit.
"""

import streamlit as st
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from test_va_distribution_plot import generate_mock_patient_data
from streamlit_app.simulation_runner import (
    generate_va_over_time_thumbnail, 
    generate_va_distribution_thumbnail,
    generate_va_over_time_plot,
    generate_va_distribution_plot
)
import numpy as np
from collections import defaultdict

# Page config
st.set_page_config(page_title="VA Visualization Test", layout="wide")

st.title("Visual Acuity Visualization Test")

# Generate mock data
patient_data = generate_mock_patient_data()

# Create mock results structure
results = {
    'patient_data': patient_data,
    'simulation_type': 'ABS',
    'population_size': len(patient_data),
    'duration_years': 5
}

# Add mean_va_data for the standard plot
time_va_map = defaultdict(list)
for patient_id, visits in patient_data.items():
    for visit in visits:
        time_month = round(visit['time'])
        time_va_map[time_month].append(visit['vision'])

mean_va_data = []
for time_month in sorted(time_va_map.keys()):
    va_values = time_va_map[time_month]
    if va_values:
        mean_va_data.append({
            'time': time_month,
            'time_months': time_month,
            'visual_acuity': np.mean(va_values),
            'std_error': np.std(va_values) / np.sqrt(len(va_values)),
            'sample_size': len(va_values)
        })

results['mean_va_data'] = mean_va_data

# Show visual acuity over time (copied from run_simulation.py)
st.subheader("Visual Acuity Over Time")

# Show thumbnail previews
st.write("**Quick Comparison**")
thumb_col1, thumb_col2 = st.columns([1, 1])

with thumb_col1:
    thumb_fig1 = generate_va_over_time_thumbnail(results)
    st.pyplot(thumb_fig1)
    st.caption("Mean + 95% CI", unsafe_allow_html=True)

with thumb_col2:
    if "patient_data" in results or "patient_histories" in results:
        thumb_fig2 = generate_va_distribution_thumbnail(results)
        st.pyplot(thumb_fig2)
        st.caption("Patient Distribution", unsafe_allow_html=True)
    else:
        st.info("No distribution data")

# Add some spacing
st.write("")

# Show full plots stacked
st.write("**Mean Visual Acuity with Confidence Intervals**")
fig1 = generate_va_over_time_plot(results)
st.pyplot(fig1)

# Only show distribution plot if we have patient-level data
if "patient_data" in results or "patient_histories" in results:
    st.write("**Distribution of Visual Acuity**")
    fig2 = generate_va_distribution_plot(results)
    st.pyplot(fig2)
else:
    st.info("Individual patient data not available for distribution plot.")

# Test the error conditions
st.divider()
st.subheader("Testing Error Conditions")

# Test with no patient data
test_col1, test_col2 = st.columns(2)

with test_col1:
    st.write("**Test: No patient data**")
    empty_results = {'mean_va_data': mean_va_data}
    try:
        thumb_empty = generate_va_distribution_thumbnail(empty_results)
        st.pyplot(thumb_empty)
    except Exception as e:
        st.error(f"Error: {e}")

with test_col2:
    st.write("**Test: No mean data**")
    no_mean_results = {'patient_data': patient_data}
    try:
        thumb_no_mean = generate_va_over_time_thumbnail(no_mean_results)
        st.pyplot(thumb_no_mean)
    except Exception as e:
        st.error(f"Error: {e}")

st.write("Run this with: `streamlit run test_ui_integration.py`")