"""
Streamlit app for discontinuation and retreatment analysis.
"""
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import json
from streamlit_discontinuation_enhanced import create_enhanced_discontinuation_chart, load_sample_data

# Page configuration
st.set_page_config(
    page_title="Discontinuation Analysis",
    page_icon="📊",
    layout="wide"
)

# Header
st.title("Discontinuation and Retreatment Analysis")
st.markdown("""
This dashboard visualizes patient discontinuation reasons and retreatment status from simulation results.
""")

# Load sample data
df = load_sample_data()

# Sidebar for controls
st.sidebar.header("Visualization Controls")

# Chart options in sidebar
show_percentages = st.sidebar.checkbox("Show Retreatment Percentages", value=True)
show_totals = st.sidebar.checkbox("Show Category Totals", value=True)
color_theme = st.sidebar.selectbox(
    "Color Theme",
    ["Blue/Red (Default)", "Green/Purple", "Teal/Orange"]
)

# Custom color selection
if color_theme == "Blue/Red (Default)":
    retreated_color = "#4878A6"  # Muted blue
    not_retreated_color = "#A65C48"  # Muted red
elif color_theme == "Green/Purple":
    retreated_color = "#48A668"  # Muted green
    not_retreated_color = "#8048A6"  # Muted purple
else:  # Teal/Orange
    retreated_color = "#48A6A6"  # Muted teal
    not_retreated_color = "#A67848"  # Muted orange

# Custom title
custom_title = st.sidebar.text_input(
    "Custom Chart Title",
    "Discontinuation Reasons by Retreatment Status"
)

# Create the visualization
fig, ax = create_enhanced_discontinuation_chart(
    data=df,
    title=custom_title,
    show_percentages=show_percentages,
    show_totals=show_totals
)

# Display the chart in Streamlit
st.pyplot(fig)

# Display detailed information
st.header("Detailed Analysis")

# Calculate summary statistics
total_discontinuations = df['count'].sum()
total_retreated = df[df['retreatment_status'] == 'Retreated']['count'].sum()
total_not_retreated = df[df['retreatment_status'] == 'Not Retreated']['count'].sum()
retreat_rate = total_retreated / total_discontinuations * 100

# Create metrics row
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Discontinuations", f"{int(total_discontinuations)}")
with col2:
    st.metric("Total Retreated", f"{int(total_retreated)}")
with col3:
    st.metric("Total Not Retreated", f"{int(total_not_retreated)}")
with col4:
    st.metric("Overall Retreat Rate", f"{retreat_rate:.1f}%")

# Create a table with the data
st.subheader("Discontinuation and Retreatment Data")

# Pivot the data for display
pivot_table = df.pivot(
    index="discontinuation_reason", 
    columns="retreatment_status", 
    values="count"
).fillna(0).reset_index()

# Calculate totals and percentages
pivot_table["Total"] = pivot_table["Retreated"] + pivot_table["Not Retreated"]
pivot_table["Retreat Rate"] = (pivot_table["Retreated"] / pivot_table["Total"] * 100).round(1).astype(str) + "%"
pivot_table["% of All Discontinuations"] = (pivot_table["Total"] / total_discontinuations * 100).round(1).astype(str) + "%"

# Reorder the dataframe columns
pivot_table = pivot_table[["discontinuation_reason", "Retreated", "Not Retreated", "Total", "Retreat Rate", "% of All Discontinuations"]]
pivot_table = pivot_table.rename(columns={"discontinuation_reason": "Discontinuation Reason"})

# Display the table
st.dataframe(pivot_table, hide_index=True)

# Explanation section
st.header("About the Data")
st.write("""
This visualization shows the distribution of patient discontinuations by reason and retreatment status. 
The chart highlights patterns in retreatment for different discontinuation types:

- **Retreat Rate:** The percentage of patients with a specific discontinuation reason who were retreated
- **% of All Discontinuations:** The proportion of each discontinuation reason across all discontinued patients
""")

# Data source note
st.sidebar.markdown("---")
st.sidebar.caption("Data Source: Simulation Results")