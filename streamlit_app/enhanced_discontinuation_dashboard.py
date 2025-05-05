"""
Enhanced Discontinuation Dashboard Module

This module contains the implementation of the dashboard for visualizing
the enhanced discontinuation model simulation results.
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import json
import os

# Import project modules - adjust import paths as needed
from simulation.config import SimulationConfig
from simulation.enhanced_discontinuation_manager import EnhancedDiscontinuationManager
from treat_and_extend_abs import TreatAndExtendABS
from treat_and_extend_des import TreatAndExtendDES


def run_enhanced_discontinuation_dashboard(config_path=None):
    """
    Main function to run the enhanced discontinuation dashboard.
    
    Parameters
    ----------
    config_path : str, optional
        Path to the simulation configuration file
    """
    st.title("Enhanced Discontinuation Model Dashboard")
    
    # Load configuration
    if config_path:
        config = SimulationConfig.from_yaml(config_path)
        st.success(f"Loaded configuration from {config_path}")
    else:
        st.info("No configuration file provided. Using default settings.")
        # You can load a default configuration here or create one from UI inputs
    
    # Display dashboard components
    tabs = st.tabs([
        "Overview", 
        "Discontinuation Types", 
        "Clinician Variation", 
        "Patient Outcomes"
    ])
    
    with tabs[0]:
        display_overview()
    
    with tabs[1]:
        display_discontinuation_types()
    
    with tabs[2]:
        display_clinician_variation()
    
    with tabs[3]:
        display_patient_outcomes()


def display_overview():
    """Display overview of the enhanced discontinuation model."""
    st.header("Overview")
    
    st.markdown("""
    The Enhanced Discontinuation Model extends the basic discontinuation framework
    with multiple cessation types, clinician variation, and time-dependent recurrence
    probabilities based on clinical data.
    
    ### Key Features:
    
    1. **Multiple Discontinuation Types**
       - Protocol-based (stable at max interval)
       - Administrative (random events like insurance issues)
       - Time-based (after fixed treatment duration)
       - Premature (non-adherence to protocol)
    
    2. **Time-dependent Recurrence**
       - Different recurrence rates based on discontinuation type
       - Time-dependent probability curves based on clinical data
       - Risk factor modifiers (e.g., presence of PED)
    
    3. **Clinician Variation**
       - Different adherence rates to protocol
       - Varying risk tolerance affecting discontinuation decisions
       - Different approaches to retreatment decisions
    """)
    
    # Load and display sample data or visualization
    # This would typically load actual simulation results
    st.subheader("Sample Simulation Results")
    
    # Create sample data for demonstration
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Patients", "1,000", "")
    
    with col2:
        st.metric("Discontinued Patients", "630", "63%")
    
    with col3:
        st.metric("Recurrence Rate", "32%", "-5%")
    
    # Sample visual comparison
    st.subheader("Treatment Outcomes Comparison")
    
    # Create sample data for demonstration
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # This is sample data that should be replaced with actual simulation results
    labels = ['Continuous Treatment', 'Planned Discontinuation', 'Administrative Cessation', 'Time-based Cessation', 'Premature Cessation']
    va_change = [2.5, -1.2, -3.5, -2.8, -5.5]  # VA change in letters
    std_dev = [1.2, 2.3, 3.1, 2.5, 3.5]        # Standard deviation
    
    x_pos = np.arange(len(labels))
    
    ax.bar(x_pos, va_change, yerr=std_dev, align='center', alpha=0.7, capsize=10)
    ax.set_ylabel('Visual Acuity Change (letters)')
    ax.set_xticks(x_pos)
    ax.set_xticklabels(labels, rotation=45, ha='right')
    ax.set_title('Visual Acuity Change by Treatment Pattern')
    ax.grid(True, linestyle='--', alpha=0.7)
    
    # Add a horizontal line at y=0
    ax.axhline(y=0, color='k', linestyle='-', alpha=0.3)
    
    plt.tight_layout()
    st.pyplot(fig)


def display_discontinuation_types():
    """Display information about discontinuation types."""
    st.header("Discontinuation Types")
    
    st.markdown("""
    The enhanced model supports multiple discontinuation types, each with
    different criteria, monitoring schedules, and recurrence patterns.
    """)
    
    # Create sample data for discontinuation types
    discontinuation_types = {
        "Planned (Protocol-based)": {
            "description": "Discontinuation after achieving stability at maximum treatment interval",
            "criteria": "3 consecutive stable visits at 16-week intervals",
            "monitoring": "Every 12 weeks in year 1, every 16 weeks in year 2",
            "recurrence_rate": "13% in year 1, 40% by year 3",
            "patients": 250
        },
        "Administrative": {
            "description": "Unplanned discontinuation due to administrative reasons",
            "criteria": "Random events (insurance changes, relocation, etc.)",
            "monitoring": "None (patient lost to follow-up)",
            "recurrence_rate": "30% in year 1, 70% by year 3",
            "patients": 120
        },
        "Time-based": {
            "description": "Discontinuation after a fixed treatment duration",
            "criteria": "At least 52 weeks of treatment",
            "monitoring": "Every 8 weeks in year 1, every 12 weeks in year 2",
            "recurrence_rate": "21% in year 1, 74% by year 3",
            "patients": 180
        },
        "Premature": {
            "description": "Discontinuation before reaching stability criteria",
            "criteria": "Some improvement seen, but before protocol criteria met",
            "monitoring": "Every 8 weeks in year 1, every 12 weeks in year 2",
            "recurrence_rate": "53% in year 1, 85% by year 3",
            "patients": 80
        }
    }
    
    # Display comparison table
    st.subheader("Discontinuation Type Comparison")
    
    # Convert the dictionary to a dataframe for display
    df = pd.DataFrame(discontinuation_types).T
    df = df.reset_index().rename(columns={"index": "Type"})
    st.dataframe(df, use_container_width=True)
    
    # Display discontinuation distribution
    st.subheader("Discontinuation Distribution")
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Extract data for the pie chart
    labels = list(discontinuation_types.keys())
    sizes = [d["patients"] for d in discontinuation_types.values()]
    
    # Create pie chart
    ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, shadow=True)
    ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
    
    st.pyplot(fig)
    
    # Display recurrence rates by discontinuation type
    st.subheader("Recurrence Rates by Discontinuation Type")
    
    # Create sample data for recurrence rates over time
    fig, ax = plt.subplots(figsize=(10, 6))
    
    years = np.linspace(0, 5, 100)
    
    # These curves are approximations based on the descriptions
    planned_recurrence = 0.13 * (1 - np.exp(-0.5 * years))
    admin_recurrence = 0.30 * (1 - np.exp(-0.9 * years))
    time_based_recurrence = 0.21 * (1 - np.exp(-1.1 * years))
    premature_recurrence = 0.53 * (1 - np.exp(-1.3 * years))
    
    # Scale to reach the 3-year rates mentioned
    planned_recurrence = planned_recurrence * (0.40 / planned_recurrence[60])
    admin_recurrence = admin_recurrence * (0.70 / admin_recurrence[60])
    time_based_recurrence = time_based_recurrence * (0.74 / time_based_recurrence[60])
    premature_recurrence = premature_recurrence * (0.85 / premature_recurrence[60])
    
    # Cap at sensible maximums
    planned_recurrence = np.minimum(planned_recurrence, 0.65)
    admin_recurrence = np.minimum(admin_recurrence, 0.85)
    time_based_recurrence = np.minimum(time_based_recurrence, 0.88)
    premature_recurrence = np.minimum(premature_recurrence, 0.95)
    
    ax.plot(years, planned_recurrence, label="Planned")
    ax.plot(years, admin_recurrence, label="Administrative")
    ax.plot(years, time_based_recurrence, label="Time-based")
    ax.plot(years, premature_recurrence, label="Premature")
    
    ax.set_xlabel("Years after Discontinuation")
    ax.set_ylabel("Cumulative Recurrence Probability")
    ax.set_title("Cumulative Recurrence Rates by Discontinuation Type")
    ax.legend()
    ax.grid(True, linestyle='--', alpha=0.7)
    
    st.pyplot(fig)


def display_clinician_variation():
    """Display information about clinician variation."""
    st.header("Clinician Variation")
    
    st.markdown("""
    The enhanced model includes variation in clinician adherence to protocols,
    affecting discontinuation decisions and retreatment approaches.
    """)
    
    # Clinician profiles
    st.subheader("Clinician Profiles")
    
    clinician_profiles = {
        "Adherent": {
            "Protocol Adherence": "95%",
            "Risk Tolerance": "Low",
            "Conservative Retreatment": "Yes",
            "Stability Threshold": "3 visits",
            "Max Interval": "16 weeks",
            "Population": "25%"
        },
        "Average": {
            "Protocol Adherence": "80%",
            "Risk Tolerance": "Medium",
            "Conservative Retreatment": "No",
            "Stability Threshold": "2 visits",
            "Max Interval": "12 weeks",
            "Population": "50%"
        },
        "Non-Adherent": {
            "Protocol Adherence": "50%",
            "Risk Tolerance": "High",
            "Conservative Retreatment": "No",
            "Stability Threshold": "1 visit",
            "Max Interval": "16 weeks",
            "Population": "25%"
        }
    }
    
    # Convert the dictionary to a dataframe for display
    df_clinicians = pd.DataFrame(clinician_profiles).T
    df_clinicians = df_clinicians.reset_index().rename(columns={"index": "Profile"})
    st.dataframe(df_clinicians, use_container_width=True)
    
    # Display clinician decision impact
    st.subheader("Impact on Discontinuation Decisions")
    
    # Create sample data
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Sample data - replace with actual simulation results
    profiles = list(clinician_profiles.keys())
    discontinuation_rates = {
        "Planned": [0.25, 0.18, 0.12],
        "Premature": [0.05, 0.12, 0.25],
        "Administrative": [0.05, 0.05, 0.05],  # Same for all profiles
        "Time-based": [0.15, 0.20, 0.18]
    }
    
    x = np.arange(len(profiles))
    width = 0.2
    multiplier = 0
    
    for discontinuation_type, rate in discontinuation_rates.items():
        offset = width * multiplier
        ax.bar(x + offset, rate, width, label=discontinuation_type)
        multiplier += 1
    
    ax.set_xticks(x + width * (len(discontinuation_rates) - 1) / 2)
    ax.set_xticklabels(profiles)
    ax.set_ylabel('Discontinuation Rate')
    ax.set_title('Discontinuation Rates by Clinician Profile')
    ax.legend(loc='upper right')
    ax.grid(True, linestyle='--', alpha=0.7)
    
    st.pyplot(fig)
    
    # Display variation in retreatment decisions
    st.subheader("Variation in Retreatment Decisions")
    
    # Create sample data
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Sample data - replace with actual simulation results
    criteria = ["Any Fluid", "≥5 Letter Loss", "≥10 Letter Loss", "Symptoms"]
    retreatment_rates = {
        "Adherent": [0.95, 0.90, 0.98, 0.75],
        "Average": [0.85, 0.75, 0.95, 0.80],
        "Non-Adherent": [0.70, 0.60, 0.90, 0.85]
    }
    
    x = np.arange(len(criteria))
    width = 0.25
    multiplier = 0
    
    for profile, rate in retreatment_rates.items():
        offset = width * multiplier
        ax.bar(x + offset, rate, width, label=profile)
        multiplier += 1
    
    ax.set_xticks(x + width)
    ax.set_xticklabels(criteria)
    ax.set_ylabel('Retreatment Rate')
    ax.set_title('Retreatment Rates by Recurrence Criteria and Clinician Profile')
    ax.legend(loc='lower right')
    ax.grid(True, linestyle='--', alpha=0.7)
    
    st.pyplot(fig)


def display_patient_outcomes():
    """Display information about patient outcomes."""
    st.header("Patient Outcomes")
    
    st.markdown("""
    The enhanced discontinuation model tracks detailed patient outcomes,
    including visual acuity changes, treatment patterns, and cost metrics.
    """)
    
    # Create tabs for different outcome types
    outcome_tabs = st.tabs([
        "Visual Acuity", 
        "Treatment Patterns", 
        "Cost Analysis"
    ])
    
    with outcome_tabs[0]:
        display_visual_acuity_outcomes()
    
    with outcome_tabs[1]:
        display_treatment_patterns()
    
    with outcome_tabs[2]:
        display_cost_analysis()


def display_visual_acuity_outcomes():
    """Display visual acuity outcomes."""
    st.subheader("Visual Acuity Outcomes")
    
    # Visual acuity change over time
    st.markdown("#### Visual Acuity Change Over Time")
    
    # Create sample data
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Sample data - replace with actual simulation results
    months = np.arange(0, 61)
    
    # Different treatment patterns
    continuous = 75 + 5 * (1 - np.exp(-0.2 * months)) - 0.02 * months
    planned_disc = 75 + 5 * (1 - np.exp(-0.2 * months[:24])) - 0.02 * months[:24]
    planned_disc = np.append(planned_disc, planned_disc[-1] - 0.05 * (months[24:] - months[23]))
    
    premature_disc = 75 + 3 * (1 - np.exp(-0.2 * months[:12])) - 0.02 * months[:12]
    premature_disc = np.append(premature_disc, premature_disc[-1] - 0.15 * (months[12:] - months[11]))
    
    ax.plot(months, continuous, label="Continuous Treatment")
    ax.plot(months, planned_disc, label="Planned Discontinuation")
    ax.plot(months, premature_disc, label="Premature Discontinuation")
    
    ax.set_xlabel("Months")
    ax.set_ylabel("Visual Acuity (letters)")
    ax.set_title("Visual Acuity Change by Treatment Pattern")
    ax.legend()
    ax.grid(True, linestyle='--', alpha=0.7)
    
    st.pyplot(fig)
    
    # Visual acuity distribution at end of simulation
    st.markdown("#### Final Visual Acuity Distribution")
    
    # Create sample data
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Sample data - replace with actual simulation results
    va_bins = np.arange(0, 91, 10)
    continuous_dist = np.array([0.01, 0.02, 0.05, 0.10, 0.20, 0.25, 0.20, 0.12, 0.05])
    planned_disc_dist = np.array([0.02, 0.03, 0.07, 0.15, 0.22, 0.25, 0.15, 0.08, 0.03])
    premature_disc_dist = np.array([0.05, 0.10, 0.15, 0.20, 0.25, 0.15, 0.07, 0.02, 0.01])
    
    width = 7
    
    ax.bar(va_bins[:-1], continuous_dist, width=width, label="Continuous Treatment", alpha=0.7)
    ax.bar(va_bins[:-1]+width, planned_disc_dist, width=width, label="Planned Discontinuation", alpha=0.7)
    ax.bar(va_bins[:-1]+width*2, premature_disc_dist, width=width, label="Premature Discontinuation", alpha=0.7)
    
    ax.set_xlabel("Visual Acuity (letters)")
    ax.set_ylabel("Proportion of Patients")
    ax.set_title("Final Visual Acuity Distribution by Treatment Pattern")
    ax.legend()
    ax.grid(True, linestyle='--', alpha=0.7)
    
    st.pyplot(fig)


def display_treatment_patterns():
    """Display treatment pattern outcomes."""
    st.subheader("Treatment Patterns")
    
    # Number of injections
    st.markdown("#### Number of Injections")
    
    # Create sample data
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Sample data - replace with actual simulation results
    years = np.arange(1, 6)
    continuous = [8.5, 6.2, 5.8, 5.5, 5.2]
    planned_disc = [8.5, 3.2, 1.8, 2.5, 3.2]
    premature_disc = [5.5, 1.2, 2.8, 3.5, 3.2]
    administrative = [4.5, 0.5, 1.2, 2.5, 2.2]
    
    ax.plot(years, continuous, marker='o', label="Continuous Treatment")
    ax.plot(years, planned_disc, marker='s', label="Planned Discontinuation")
    ax.plot(years, premature_disc, marker='^', label="Premature Discontinuation")
    ax.plot(years, administrative, marker='d', label="Administrative Cessation")
    
    ax.set_xlabel("Year")
    ax.set_ylabel("Mean Number of Injections")
    ax.set_title("Annual Injection Frequency by Treatment Pattern")
    ax.legend()
    ax.grid(True, linestyle='--', alpha=0.7)
    
    st.pyplot(fig)
    
    # Clinic visits
    st.markdown("#### Clinic Visits")
    
    # Create sample data
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Sample data - replace with actual simulation results
    years = np.arange(1, 6)
    continuous_visits = [10.5, 8.2, 7.8, 7.5, 7.2]
    planned_disc_visits = [10.5, 6.2, 4.8, 4.5, 4.2]
    premature_disc_visits = [7.5, 4.2, 4.8, 5.5, 5.2]
    administrative_visits = [6.5, 1.5, 2.2, 3.5, 3.2]
    
    ax.plot(years, continuous_visits, marker='o', label="Continuous Treatment")
    ax.plot(years, planned_disc_visits, marker='s', label="Planned Discontinuation")
    ax.plot(years, premature_disc_visits, marker='^', label="Premature Discontinuation")
    ax.plot(years, administrative_visits, marker='d', label="Administrative Cessation")
    
    ax.set_xlabel("Year")
    ax.set_ylabel("Mean Number of Clinic Visits")
    ax.set_title("Annual Clinic Visits by Treatment Pattern")
    ax.legend()
    ax.grid(True, linestyle='--', alpha=0.7)
    
    st.pyplot(fig)


def display_cost_analysis():
    """Display cost analysis."""
    st.subheader("Cost Analysis")
    
    st.markdown("""
    The enhanced discontinuation model includes cost tracking for different
    discontinuation types and treatment patterns.
    """)
    
    # Cumulative costs
    st.markdown("#### Cumulative Costs Over Time")
    
    # Create sample data
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Sample data - replace with actual simulation results
    years = np.linspace(0, 5, 100)
    continuous_cost = 20000 * (1 - np.exp(-0.5 * years))
    planned_disc_cost = 12000 * (1 - np.exp(-0.8 * years))
    premature_disc_cost = 10000 * (1 - np.exp(-1 * years))
    administrative_cost = 8000 * (1 - np.exp(-1.2 * years))
    
    ax.plot(years, continuous_cost, label="Continuous Treatment")
    ax.plot(years, planned_disc_cost, label="Planned Discontinuation")
    ax.plot(years, premature_disc_cost, label="Premature Discontinuation")
    ax.plot(years, administrative_cost, label="Administrative Cessation")
    
    ax.set_xlabel("Years")
    ax.set_ylabel("Cumulative Cost ($)")
    ax.set_title("Cumulative Treatment Costs by Pattern")
    ax.legend()
    ax.grid(True, linestyle='--', alpha=0.7)
    
    st.pyplot(fig)
    
    # Cost-effectiveness
    st.markdown("#### Cost-Effectiveness Analysis")
    
    # Create sample data for cost-effectiveness
    cost_effectiveness = {
        "Continuous Treatment": {
            "Total Cost": "$20,000",
            "QALY Gain": "2.8",
            "Cost per QALY": "$7,143",
            "VA Letters Preserved": "12.5",
            "Cost per Letter": "$1,600"
        },
        "Planned Discontinuation": {
            "Total Cost": "$12,000",
            "QALY Gain": "2.5",
            "Cost per QALY": "$4,800",
            "VA Letters Preserved": "8.5",
            "Cost per Letter": "$1,412"
        },
        "Premature Discontinuation": {
            "Total Cost": "$10,000",
            "QALY Gain": "1.8",
            "Cost per QALY": "$5,556",
            "VA Letters Preserved": "4.2",
            "Cost per Letter": "$2,381"
        },
        "Administrative Cessation": {
            "Total Cost": "$8,000",
            "QALY Gain": "1.2",
            "Cost per QALY": "$6,667",
            "VA Letters Preserved": "1.5",
            "Cost per Letter": "$5,333"
        }
    }
    
    # Convert the dictionary to a dataframe for display
    df_cost = pd.DataFrame(cost_effectiveness).T
    df_cost = df_cost.reset_index().rename(columns={"index": "Treatment Pattern"})
    st.dataframe(df_cost, use_container_width=True)


if __name__ == "__main__":
    run_enhanced_discontinuation_dashboard()