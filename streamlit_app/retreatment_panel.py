"""
Retreatment visualization panel for AMD Protocol Explorer.

This module provides detailed visualization and analysis of retreatment data,
showing retreatment rates by discontinuation type and other retreatment statistics.
"""

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

def display_retreatment_panel(results):
    """
    Display detailed retreatment statistics and visualizations.
    
    Parameters
    ----------
    results : dict
        Simulation results containing retreatment data
    """
    if "recurrences" not in results or results["recurrences"].get("total", 0) == 0:
        st.warning("No retreatment data available in simulation results.")
        return
        
    st.subheader("Retreatment Analysis")
    recurrence_data = results["recurrences"]
    
    # Get retreatment count and unique count
    total_retreatments = recurrence_data.get("total", 0)
    unique_retreatments = recurrence_data.get("unique_count", total_retreatments)
    
    # Create columns for metrics
    ret_col1, ret_col2 = st.columns(2)
    
    with ret_col1:
        # Display basic metrics
        st.write(f"**Total Retreatment Events:** {total_retreatments}")
        if unique_retreatments != total_retreatments:
            st.write(f"**Unique Patients Retreated:** {unique_retreatments}")
        
        # Calculate and display retreatment rate
        discontinued_patients = results.get("total_discontinuations", 0)
        if discontinued_patients > 0:
            retreatment_rate = (unique_retreatments / discontinued_patients) * 100
            st.write(f"**Retreatment Rate:** {retreatment_rate:.1f}% of discontinued patients")
            
            # Calculate average retreatments per patient
            if unique_retreatments > 0:
                avg_retreatments = total_retreatments / unique_retreatments
                st.write(f"**Avg Retreatments per Patient:** {avg_retreatments:.2f}")
    
    # First check if we have raw_discontinuation_stats with retreatments_by_type
    if "raw_discontinuation_stats" in results and "retreatments_by_type" in results["raw_discontinuation_stats"]:
        # Use the detailed stats from the discontinuation manager
        retreatment_by_type = results["raw_discontinuation_stats"]["retreatments_by_type"]
    else:
        # Fallback to recurrence data
        retreatment_by_type = recurrence_data.get("by_type", {})
        
    if retreatment_by_type and sum(retreatment_by_type.values()) > 0:
        # Convert to DataFrame for display
        retreatment_df = pd.DataFrame({
            'Type': [key.replace('_', ' ').title() for key in retreatment_by_type.keys()],
            'Count': list(retreatment_by_type.values())
        })
        
        with ret_col2:
            # Create pie chart to show proportion
            fig, ax = plt.subplots(figsize=(5, 5))
            ax.pie(
                retreatment_df['Count'], 
                labels=retreatment_df['Type'],
                autopct='%1.1f%%',
                startangle=90
            )
            ax.axis('equal')
            ax.set_title('Retreatments by Discontinuation Type')
            st.pyplot(fig)
        
        # Display detailed statistics in an expander
        with st.expander("**Detailed Retreatment Statistics**"):
            st.write("### Retreatments by Discontinuation Type")
            st.dataframe(retreatment_df)
            st.bar_chart(retreatment_df.set_index('Type'))
            
            # Calculate and display retreatment rates by discontinuation type
            if "discontinuation_counts" in results:
                st.write("### Retreatment Rates by Discontinuation Type")
                
                # Convert discontinuation counts to same format as retreatment types
                disc_counts = results["discontinuation_counts"]
                type_mapping = {
                    "Planned": "stable_max_interval", 
                    "Administrative": "random_administrative", 
                    "Time-based": "treatment_duration", 
                    "Premature": "premature"
                }
                
                # Create a new DataFrame with both discontinuation counts and retreatment counts
                comparison_data = []
                for disc_type, count in disc_counts.items():
                    retreatment_key = type_mapping.get(disc_type, "")
                    retreatment_count = retreatment_by_type.get(retreatment_key, 0)
                    
                    # Calculate rate
                    rate = (retreatment_count / count * 100) if count > 0 else 0
                    
                    comparison_data.append({
                        "Discontinuation Type": disc_type,
                        "Patients Discontinued": count,
                        "Retreatment Events": retreatment_count,
                        "Retreatment Rate": f"{rate:.1f}%",
                        "Raw Rate": rate  # For sorting
                    })
                
                # Create DataFrame and display
                comparison_df = pd.DataFrame(comparison_data)
                comparison_df = comparison_df.sort_values(by="Raw Rate", ascending=False)
                comparison_df = comparison_df.drop(columns=["Raw Rate"])
                
                st.dataframe(comparison_df)
                
                # Create a bar chart to visualize retreatment rates
                st.write("### Retreatment Rate by Discontinuation Type")
                rate_df = pd.DataFrame({
                    'Type': [row["Discontinuation Type"] for row in comparison_data],
                    'Rate (%)': [row["Raw Rate"] for row in comparison_data]
                })
                st.bar_chart(rate_df.set_index('Type'))
    else:
        st.warning("No retreatment breakdown by discontinuation type available.")