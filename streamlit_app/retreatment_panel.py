"""
Retreatment visualization panel for AMD Protocol Explorer.

This module provides detailed visualization and analysis of retreatment data,
showing retreatment rates by discontinuation type and other retreatment statistics.
"""

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Import DEBUG_MODE from simulation_runner if available
try:
    from streamlit_app.simulation_runner import DEBUG_MODE, create_tufte_bar_chart, save_plot_for_debug
except ImportError:
    DEBUG_MODE = False
    
    # Define fallback functions if simulation_runner imports fail
    def create_tufte_bar_chart(categories, values, title="", xlabel="", ylabel="", 
                              color='#3498db', figsize=(10, 6), horizontal=True):
        """Fallback implementation of create_tufte_bar_chart"""
        fig, ax = plt.subplots(figsize=figsize)
        if horizontal:
            ax.barh(range(len(categories)), values, color=color)
            ax.set_yticks(range(len(categories)))
            ax.set_yticklabels(categories)
        else:
            ax.bar(range(len(categories)), values, color=color)
            ax.set_xticks(range(len(categories)))
            ax.set_xticklabels(categories, rotation=45)
        return fig
        
    def save_plot_for_debug(fig, filename="debug_plot.png"):
        """Fallback implementation of save_plot_for_debug"""
        return None

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
        
    # Don't display header - we've merged this into the Discontinuation and Retreatment Analysis section
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
            # Patient retreatment rate - unique patients retreated divided by discontinued
            patient_retreatment_rate = (unique_retreatments / discontinued_patients) * 100
            st.write(f"**Patient Retreatment Rate:** {patient_retreatment_rate:.1f}% of discontinued patients")
            
            # Also show event-based retreatment rate for clarity
            event_retreatment_rate = (total_retreatments / discontinued_patients) * 100
            if event_retreatment_rate > patient_retreatment_rate:
                st.write(f"**Event/Patient Ratio:** {(total_retreatments / discontinued_patients):.2f} retreatments per discontinued patient")
            
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
            # Extract data for the chart
            sorted_indices = np.argsort(retreatment_df['Count'].values)[::-1]
            sorted_types = [retreatment_df['Type'].values[i] for i in sorted_indices]
            sorted_counts = [retreatment_df['Count'].values[i] for i in sorted_indices]
            
            # Use our helper function to create a properly formatted bar chart
            # Use a slightly different blue for this chart to distinguish it
            fig = create_tufte_bar_chart(
                categories=sorted_types,
                values=sorted_counts,
                title="GRAPHIC H: Retreatments by Type",
                color='#2980b9',  # A slightly different blue
                figsize=(5, 5),
                horizontal=True
            )
            
            # Save figure for debugging
            save_plot_for_debug(fig, "graphic_h_debug.png")
            
            # Show the chart
            st.pyplot(fig)
        
        # Display detailed statistics in an expander
        with st.expander("**Detailed Retreatment Statistics**"):
            st.write("### Retreatments by Discontinuation Type")
            st.dataframe(retreatment_df)
            # Only show this bar chart in debug mode since it's redundant with GRAPHIC H
            if "DEBUG_MODE" in globals() and DEBUG_MODE:
                st.write("GRAPHIC J: Interactive Retreatment Chart (Debug Only)")
                st.bar_chart(retreatment_df.set_index('Type'))
            
            # Calculate and display retreatment rates by discontinuation type
            if "discontinuation_counts" in results:
                st.write("### Retreatment Rates by Discontinuation Type")
                
                # Convert discontinuation counts to same format as retreatment types
                disc_counts = results["discontinuation_counts"]
                type_mapping = {
                    "Planned": "stable_max_interval", 
                    "Administrative": "random_administrative", 
                    "Not Renewed": "course_complete_but_not_renewed", 
                    "Premature": "premature"
                }
                
                # Create a new DataFrame with both discontinuation counts and retreatment counts
                comparison_data = []
                for disc_type, count in disc_counts.items():
                    retreatment_key = type_mapping.get(disc_type, "")
                    retreatment_count = retreatment_by_type.get(retreatment_key, 0)
                    
                    # Calculate rate - but we need to be careful about comparing patients vs events
                    # The count is unique patients discontinued, so to calculate proper rate
                    # we need unique patients retreated, not retreatment events
                    
                    # For proper rate calculation, we should use unique_retreatments or estimate per type
                    # Estimate unique patients retreated per type - we'll use a conservative approach
                    # assuming multiple retreatments per patient for consistency
                    
                    # If we have unique retreatment count, use it for proportional estimation
                    if unique_retreatments > 0 and total_retreatments > 0:
                        # Estimate unique patients retreated for this type (proportionally)
                        est_unique_retreatments = (retreatment_count / total_retreatments) * unique_retreatments
                        # Cap at the total number of patients for this type to prevent >100% rates
                        est_unique_retreatments = min(est_unique_retreatments, count)
                        patient_rate = (est_unique_retreatments / count * 100) if count > 0 else 0
                    else:
                        # If we don't have unique data, just cap at 100%
                        patient_rate = min(100, (retreatment_count / count * 100)) if count > 0 else 0
                    
                    # Also calculate event rate for transparency
                    event_rate = (retreatment_count / count * 100) if count > 0 else 0
                    
                    comparison_data.append({
                        "Discontinuation Type": disc_type,
                        "Patients Discontinued": count,
                        "Retreatment Events": retreatment_count,
                        "Est. Unique Patients": round(est_unique_retreatments) if 'est_unique_retreatments' in locals() else "-",
                        "Patient Retreatment Rate": f"{patient_rate:.1f}%",
                        "Event/Patient Ratio": f"{(retreatment_count / count):.2f}" if count > 0 else "0",
                        "Raw Rate": patient_rate  # For sorting
                    })
                
                # Create DataFrame and display
                comparison_df = pd.DataFrame(comparison_data)
                comparison_df = comparison_df.sort_values(by="Raw Rate", ascending=False)
                comparison_df = comparison_df.drop(columns=["Raw Rate"])
                
                st.dataframe(comparison_df)
                
                # Create a horizontal bar chart to visualize patient retreatment rates
                st.write("### Patient Retreatment Rate by Discontinuation Type")
                st.write("*Estimated unique patients retreated divided by patients discontinued*")
                
                # Create data for plotting
                types = [row["Discontinuation Type"] for row in comparison_data]
                rates = [row["Raw Rate"] for row in comparison_data]
                counts = [row["Retreatment Events"] for row in comparison_data]
                
                # Format the data for labeling
                formatted_rates = [f"{rate:.1f}% ({count})" for rate, count in zip(rates, counts)]
                
                # Use our helper function to create a properly formatted bar chart
                # Use a teal color for this chart to distinguish from the other blue charts
                fig = create_tufte_bar_chart(
                    categories=types,
                    values=rates,
                    title="GRAPHIC I: Patient Retreatment Rate by Discontinuation Type",
                    xlabel="Retreatment Rate (%)",
                    color='#16a085',  # A nice teal color
                    figsize=(10, 5),
                    horizontal=True
                )
                
                # Get the axis from the figure
                ax = fig.axes[0]
                
                # Set appropriate axis limits
                ax.set_xlim(0, max(rates) * 1.1)
                
                # Force a clear zero line as a reference
                ax.axhline(y=0, color='#cccccc', linestyle='-', linewidth=0.5, alpha=0.3)
                
                # Save for debugging
                save_plot_for_debug(fig, "graphic_i_debug.png")
                
                # Show the chart
                st.pyplot(fig)
                
                # Add the explanations directly without an expander
                st.write("### Understanding the Retreatment Metrics")
                st.info("""
                **Important Notes About Retreatment Statistics**
                
                There's an important distinction between **unique patients** and **retreatment events**:
                
                - **Patients Discontinued**: The count of unique patients who had treatment discontinued
                - **Retreatment Events**: The total number of retreatment events (one patient may have multiple retreatments)
                - **Est. Unique Patients**: Estimated number of unique patients retreated per discontinuation type
                - **Patient Retreatment Rate**: Estimated percentage of discontinued patients who were retreated
                - **Event/Patient Ratio**: Average number of retreatment events per discontinued patient
                
                When the Event/Patient Ratio exceeds 1.0, it means some patients had multiple retreatments.
                This can lead to retreatment event counts exceeding discontinued patient counts.
                
                The Patient Retreatment Rate uses estimation to account for this and provide a more accurate
                representation of the percentage of patients who experienced at least one retreatment.
                """)
    else:
        st.warning("No retreatment breakdown by discontinuation type available.")
        
    # Add explanation expander at the bottom (outside all other expanders)
    with st.expander("📊 Understanding Retreatment vs Discontinuation"):
        st.markdown("""
        ### Retreatment Statistics Explained
        
        In this dashboard, we track both discontinuations and retreatments:
        
        - **Discontinuation**: When a patient stops receiving regular treatment
        - **Retreatment**: When a previously discontinued patient resumes treatment due to disease recurrence
        
        #### Key Metrics:
        
        - **Patient Retreatment Rate**: The percentage of discontinued patients who had at least one retreatment
        - **Event/Patient Ratio**: Average number of retreatment events per patient (can exceed 1.0)
        
        #### Why Rates Can Be High:
        
        High retreatment rates indicate that many discontinued patients eventually needed to resume treatment.
        This may suggest that:
        
        1. The discontinuation criteria may need revision
        2. Monitoring after discontinuation is effectively identifying recurrences
        3. The disease has a natural tendency to recur after treatment cessation
        
        A high Event/Patient ratio (>1.0) indicates that some patients are experiencing multiple retreatments,
        suggesting a cycle of discontinuation and retreatment that might require clinical intervention.
        """)