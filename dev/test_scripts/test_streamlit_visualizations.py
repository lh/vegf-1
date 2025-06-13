"""
Test script to display all Streamlit visualizations in a consolidated format.
This allows for easy testing and review of visualization components.
"""

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import streamlit as st
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import visualization components
from streamlit_app.simulation_runner import generate_va_over_time_plot
from streamlit_app.discontinuation_chart import generate_enhanced_discontinuation_plot
from streamlit_app.retreatment_panel import display_retreatment_panel

# Set page configuration
st.set_page_config(layout="wide", page_title="Visualization Test Suite")

st.title("Visualization Test Suite")
st.markdown("This dashboard displays all visualizations in a consolidated format for easy testing.")

# Generate sample data
@st.cache_data
def generate_sample_data():
    # Time series data for VA over time
    months = list(range(0, 25))
    va_values = [65.0] + [65.0 + np.random.normal(0, 2) for _ in range(1, 25)]
    sample_sizes = [100 - i * 2 for i in range(25)]
    
    va_df = pd.DataFrame({
        "time_months": months,
        "mean_va": va_values,
        "sample_size": sample_sizes
    })
    
    # Patient data for patient explorer
    patient_ids = list(range(1, 21))
    patient_data = []
    
    for p_id in patient_ids:
        start_va = np.random.randint(50, 75)
        n_visits = np.random.randint(5, 15)
        for visit in range(n_visits):
            month = visit * 2
            va = start_va + np.random.normal(0, 3)
            received_treatment = np.random.choice([True, False], p=[0.7, 0.3])
            patient_data.append({
                "patient_id": p_id,
                "visit_month": month,
                "visual_acuity": va,
                "received_treatment": received_treatment
            })
    
    patient_df = pd.DataFrame(patient_data)
    
    # Discontinuation data
    discon_data = {
        'Patients': 100,
        'Discontinued': 35,
        'Discontinued_due_to_disease_stability': 15,
        'Discontinued_due_to_disease_worsening': 10,
        'Discontinued_due_to_other_reasons': 10,
        'Discontinued_due_to_disease_stability_and_maintain_vision': 8,
        'Discontinued_due_to_disease_stability_and_lose_vision': 7,
    }
    
    # Retreatment data
    retreatment_data = {
        'time_months': list(range(0, 25)),
        'retreatment_rates': [0.8 - 0.02 * i for i in range(25)],
        'mean_va_change': [0] + [np.random.normal(0.5, 1) for _ in range(24)],
        'treatment_counts': [85 - 3 * i for i in range(25)]
    }
    retreatment_df = pd.DataFrame(retreatment_data)
    
    return va_df, patient_df, discon_data, retreatment_df

# Get sample data
va_df, patient_df, discon_data, retreatment_df = generate_sample_data()

# Create tabs for different visualization sections
tab1, tab2, tab3, tab4 = st.tabs(["Visual Acuity Over Time", "Patient Explorer", "Discontinuation Chart", "Retreatment Chart"])

with tab1:
    st.header("Visual Acuity Over Time")
    st.markdown("This chart displays mean visual acuity and sample sizes over time.")
    
    fig = generate_va_over_time_plot(
        va_df, 
        va_df["mean_va"].iloc[0], 
        sample_sizes=va_df["sample_size"].tolist()
    )
    
    st.pyplot(fig)

with tab2:
    st.header("Patient Explorer")
    st.markdown("This chart displays individual patient visual acuity trajectories.")
    
    # Filter to just 5 patients for clarity
    subset_patients = patient_df[patient_df["patient_id"].isin(range(1, 6))]
    
    # Patient explorer is a full Streamlit component, not just a figure
    # So we'll create a simplified version for testing
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Group by patient and plot each patient's trajectory
    for patient_id, group in subset_patients.groupby("patient_id"):
        ax.plot(group["visit_month"], group["visual_acuity"], 
                marker='o', label=f"Patient {patient_id}")
    
    ax.set_xlabel("Visit Month")
    ax.set_ylabel("Visual Acuity (letters)")
    ax.set_title("Patient Visual Acuity Trajectories")
    ax.legend()
    ax.grid(alpha=0.3)
    
    st.pyplot(fig)

with tab3:
    st.header("Discontinuation Chart")
    st.markdown("This chart displays patient discontinuation statistics.")
    
    # Prepare data for the discontinuation chart
    sample_results = {
        "discontinuation_counts": {
            "Planned": 122,
            "Administrative": 14,
            "Not Renewed": 127,
            "Premature": 545
        },
        "recurrences": {
            "total": 395,
            "by_type": {
                "stable_max_interval": 73,
                "random_administrative": 3,
                "treatment_duration": 19,
                "premature": 300
            }
        }
    }
    
    fig = generate_enhanced_discontinuation_plot(sample_results)
    st.pyplot(fig)

with tab4:
    st.header("Retreatment Chart")
    st.markdown("This chart displays retreatment statistics over time.")
    
    # Create a custom retreatment visualization as the panel is a Streamlit component
    # not just a matplotlib figure
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Plot retreatment rate over time
    ax.plot(retreatment_df["time_months"], retreatment_df["retreatment_rates"], 
            marker='o', color='#5686B3', label="Retreatment Rate")
    
    # Create a twin axis for treatment counts
    ax2 = ax.twinx()
    ax2.bar(retreatment_df["time_months"], retreatment_df["treatment_counts"], 
            alpha=0.3, color='#B37866', label="Treatment Count")
    
    # Set labels and title
    ax.set_xlabel("Months")
    ax.set_ylabel("Retreatment Rate")
    ax2.set_ylabel("Treatment Count")
    ax.set_title("Retreatment Statistics Over Time")
    
    # Combine legends
    lines1, labels1 = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax.legend(lines1 + lines2, labels1 + labels2, loc='upper right')
    
    st.pyplot(fig)

st.markdown("---")
st.markdown("### Visualization Settings")
st.markdown("Use these controls to adjust visualization parameters and test different configurations.")

# Add controls for testing different aspects of visualizations
with st.expander("Visual Acuity Plot Settings"):
    baseline_va = st.slider("Baseline VA", 40.0, 80.0, 65.0, 0.5)
    show_sample_size = st.checkbox("Show Sample Size", True)
    
    if st.button("Update VA Plot"):
        with tab1:
            fig = generate_va_over_time_plot(
                va_df, 
                baseline_va, 
                sample_sizes=va_df["sample_size"].tolist() if show_sample_size else None
            )
            st.pyplot(fig)

with st.expander("Patient Explorer Settings"):
    num_patients = st.slider("Number of Patients", 1, 10, 5)
    
    if st.button("Update Patient Plot"):
        with tab2:
            subset_patients = patient_df[patient_df["patient_id"].isin(range(1, num_patients+1))]
            
            # Create updated plot
            fig, ax = plt.subplots(figsize=(10, 6))
            
            for patient_id, group in subset_patients.groupby("patient_id"):
                ax.plot(group["visit_month"], group["visual_acuity"], 
                        marker='o', label=f"Patient {patient_id}")
            
            ax.set_xlabel("Visit Month")
            ax.set_ylabel("Visual Acuity (letters)")
            ax.set_title("Patient Visual Acuity Trajectories")
            ax.legend()
            ax.grid(alpha=0.3)
            
            st.pyplot(fig)

st.markdown("---")
st.markdown("##### Instructions")
st.markdown("""
1. Review each visualization for consistency, readability, and adherence to design principles
2. Test with different parameters using the controls on the left
3. Report any visual artifacts or inconsistencies
""")

if __name__ == "__main__":
    # This enables running as a script with: streamlit run test_streamlit_visualizations.py
    pass