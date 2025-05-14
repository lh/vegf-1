"""
Retreatment visualization panel for AMD Protocol Explorer.

This module provides detailed visualization and analysis of retreatment data,
showing retreatment rates by discontinuation type and other retreatment statistics.
"""

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Import visualization functions
try:
    from visualization.clean_nested_bar_chart import create_discontinuation_retreatment_chart
    from streamlit_app.simulation_runner import DEBUG_MODE, create_tufte_bar_chart, save_plot_for_debug
except ImportError:
    DEBUG_MODE = False

# Import the central color system
try:
    from visualization.color_system import COLORS, SEMANTIC_COLORS, ALPHAS
except ImportError:
    # Fallback if the central color system is not available
    COLORS = {
        'primary': '#4682B4',    # Steel Blue - for visual acuity data
        'secondary': '#B22222',  # Firebrick - for critical information
        'patient_counts': '#8FAD91',  # Muted Sage Green - for patient counts
    }
    ALPHAS = {
        'high': 0.8,        # High opacity for primary elements
        'medium': 0.5,      # Medium opacity for standard elements
        'low': 0.2,         # Low opacity for background elements
        'very_low': 0.1,    # Very low opacity for subtle elements
        'patient_counts': 0.5  # Consistent opacity for all patient/sample count visualizations
    }
    SEMANTIC_COLORS = {
        'acuity_data': COLORS['primary'],
        'patient_counts': COLORS['patient_counts'],
        'critical_info': COLORS['secondary'],
    }
    
    # Define fallback functions if simulation_runner imports fail
    def create_tufte_bar_chart(categories, values, title="", xlabel="", ylabel="",
                              color=None, figsize=(10, 6), horizontal=True):
        """Fallback implementation of create_tufte_bar_chart"""
        # Use patient_counts color from semantic system if available
        if color is None:
            color = SEMANTIC_COLORS['patient_counts']

        fig, ax = plt.subplots(figsize=figsize)
        if horizontal:
            ax.barh(range(len(categories)), values, color=color, alpha=ALPHAS['patient_counts'])
            ax.set_yticks(range(len(categories)))
            ax.set_yticklabels(categories)
        else:
            ax.bar(range(len(categories)), values, color=color, alpha=ALPHAS['patient_counts'])
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
        # Display basic metrics with descriptions for screen readers
        st.write(f"**Total Retreatment Events:** {total_retreatments}", help="Total number of retreatment events recorded")
        if unique_retreatments != total_retreatments:
            st.write(f"**Unique Patients Retreated:** {unique_retreatments}", help="Number of distinct patients who required retreatment")
        
        # Calculate and display retreatment rate
        discontinued_patients = results.get("total_discontinuations", 0)
        if discontinued_patients > 0:
            # Patient retreatment rate - unique patients retreated divided by discontinued
            patient_retreatment_rate = (unique_retreatments / discontinued_patients) * 100
            st.write(f"**Patient Retreatment Rate:** {patient_retreatment_rate:.1f}% of discontinued patients", 
                    help="Percentage of discontinued patients who later required retreatment")
            
            # Also show event-based retreatment rate for clarity
            event_retreatment_rate = (total_retreatments / discontinued_patients) * 100
            if event_retreatment_rate > patient_retreatment_rate:
                st.write(f"**Event/Patient Ratio:** {(total_retreatments / discontinued_patients):.2f} retreatments per discontinued patient",
                        help="Average number of retreatment events per discontinued patient")
            
            # Calculate average retreatments per patient
            if unique_retreatments > 0:
                avg_retreatments = total_retreatments / unique_retreatments
                st.write(f"**Avg Retreatments per Patient:** {avg_retreatments:.2f}",
                        help="Average number of retreatment events per unique retreated patient")
    
    # First check if we have raw_discontinuation_stats with retreatments_by_type
    if "raw_discontinuation_stats" in results and "retreatments_by_type" in results["raw_discontinuation_stats"]:
        # Use the detailed stats from the discontinuation manager
        retreatment_by_type = results["raw_discontinuation_stats"]["retreatments_by_type"]
    else:
        # Fallback to recurrence data
        retreatment_by_type = recurrence_data.get("by_type", {})

    # Get discontinuation counts for combined visualization
    if "discontinuation_counts" in results:
        disc_counts = results["discontinuation_counts"]
        type_mapping = {
            "Planned": "stable_max_interval",
            "Administrative": "random_administrative",
            "Not Renewed": "course_complete_but_not_renewed",
            "Premature": "premature"
        }

        # Create combined dataset for visualization
        combined_data = []
        for disc_type, disc_count in disc_counts.items():
            retreatment_key = type_mapping.get(disc_type, "")
            retreated_count = retreatment_by_type.get(retreatment_key, 0)

            # Estimate unique patients retreated
            if unique_retreatments > 0 and total_retreatments > 0:
                # Proportional estimation of unique patients
                est_unique_retreated = (retreated_count / total_retreatments) * unique_retreatments
                # Cap at total patients
                est_unique_retreated = min(est_unique_retreated, disc_count)
            else:
                est_unique_retreated = retreated_count

            # Add retreated patients
            combined_data.append({
                'reason': disc_type,
                'retreated': True,
                'count': int(round(est_unique_retreated))
            })

            # Add non-retreated patients
            combined_data.append({
                'reason': disc_type,
                'retreated': False,
                'count': disc_count - int(round(est_unique_retreated))
            })

        # Convert to DataFrame
        combined_df = pd.DataFrame(combined_data)

        # Create and display the combined visualization
        try:
            # Force direct implementation of the nested bar chart to guarantee the correct styling
            st.write("Note: Using direct visualization implementation for consistency")

            # Create custom implementation right here to ensure correct styling
            def create_direct_nested_chart(data, title="Discontinuation Reasons and Retreatment Status"):
                """Direct implementation of the nested bar chart with proper spacing."""
                import matplotlib.pyplot as plt
                import numpy as np

                # Calculate totals for each category
                totals = data.groupby('reason')['count'].sum().reset_index()
                totals = totals.sort_values('count', ascending=False)  # Sort by total count
                reasons = totals['reason'].tolist()
                reason_totals = totals['count'].tolist()

                # Set up plot
                fig, ax = plt.subplots(figsize=(10, 6))

                # Use log scale
                ax.set_yscale('log')
                ax.set_ylim(bottom=0.9)  # Start log scale at just below 1

                # Add grid for better readability
                ax.grid(axis='y', linestyle='--', alpha=0.3, color='#cccccc')

                # Define colors
                bg_color = '#E0E0E0'  # Light grey for background
                retreated_color = '#4682B4'  # Steel Blue for retreated
                not_retreated_color = '#8FAD91'  # Sage green for not retreated

                # Set up positions
                x = np.arange(len(reasons))
                bar_width = 0.75  # Width of background bar

                # For segments, use narrower width with spacing
                segment_width = bar_width * 0.4  # 40% of total width per segment
                segment_spacing = bar_width * 0.1  # 10% spacing between segments

                # Draw background bars for totals
                bg_bars = ax.bar(x, reason_totals, width=bar_width, color=bg_color,
                                edgecolor='none', alpha=0.8, zorder=1)

                # Add segments
                for i, reason in enumerate(reasons):
                    # Get data for this reason
                    retreated_count = data[(data['reason'] == reason) & (data['retreated'] == True)]['count'].sum()
                    not_retreated_count = data[(data['reason'] == reason) & (data['retreated'] == False)]['count'].sum()

                    # Position segments with proper spacing
                    left_pos = x[i] - (segment_width + segment_spacing/2)  # For retreated (left)
                    right_pos = x[i] + segment_spacing/2  # For not retreated (right)

                    # Draw retreated segment (blue)
                    if retreated_count > 0:
                        ax.bar(left_pos, retreated_count, width=segment_width, color=retreated_color,
                              edgecolor='white', linewidth=0.5, zorder=2,
                              label='Retreated' if i == 0 else None)

                        # Label
                        ax.text(left_pos, retreated_count/2, str(retreated_count),
                               ha='center', va='center',
                               color='white' if retreated_count >= 50 else 'black',
                               fontweight='bold')

                    # Draw not retreated segment (sage green)
                    if not_retreated_count > 0:
                        ax.bar(right_pos, not_retreated_count, width=segment_width, color=not_retreated_color,
                              edgecolor='white', linewidth=0.5, zorder=2,
                              label='Not Retreated' if i == 0 else None)

                        # Label
                        ax.text(right_pos, not_retreated_count/2, str(not_retreated_count),
                               ha='center', va='center',
                               color='white' if not_retreated_count >= 50 else 'black',
                               fontweight='bold')

                    # Add reason and total above bar
                    ax.text(x[i], reason_totals[i] * 2.0,
                           f'{reason}\n{reason_totals[i]}',
                           ha='center', va='bottom', fontweight='bold')

                # Small sample warning
                for i, (reason, total) in enumerate(zip(reasons, reason_totals)):
                    if total < 15:  # Small sample threshold
                        ax.text(x[i], 1.2, 'Small sample',
                               ha='center', va='center', color='#D81B60', fontsize=8, fontweight='bold',
                               bbox=dict(facecolor='white', alpha=0.9, pad=2,
                                        boxstyle='round,pad=0.3', edgecolor='#D81B60', linewidth=1),
                               zorder=10)

                # Configure axes
                ax.set_xticks([])  # Hide x-ticks
                ax.set_ylabel('Number of Patients (log scale)')
                ax.set_title(title)
                ax.legend(loc='upper right')

                # Remove spines
                for spine in ['top', 'right', 'bottom']:
                    ax.spines[spine].set_visible(False)

                # Add retreatment rate
                total_patients = data['count'].sum()
                retreated_patients = data[data['retreated'] == True]['count'].sum()
                rate = (retreated_patients / total_patients) * 100
                fig.text(0.5, 0.01, f'Overall retreatment rate: {rate:.1f}%',
                        ha='center', va='bottom', fontsize=10)

                plt.subplots_adjust(left=0.1, right=0.9, top=0.85, bottom=0.15)
                return fig, ax

            # Use our direct implementation instead of the imported one
            try:
                fig, ax = create_direct_nested_chart(
                    combined_df,
                    title="Discontinuation Reasons and Retreatment Status"
                )
            except Exception as e:
                st.error(f"Direct implementation failed: {str(e)}")
                # Fall back to the imported implementation
                fig, ax = create_discontinuation_retreatment_chart(
                    combined_df,
                    title="Discontinuation Reasons and Retreatment Status",
                    figsize=(10, 6),
                    use_log_scale=True,  # Use log scale for better visualization of different sizes
                    sort_by_total=True,  # Sort categories by total count (descending)
                    small_sample_threshold=10  # Show warning for categories with fewer than 10 patients
                )

            # Save for debugging
            save_plot_for_debug(fig, "discontinuation_retreatment_chart.png")

            # Show the chart in the main area
            st.pyplot(fig)
        except Exception as e:
            st.error(f"Failed to create combined visualization: {str(e)}")
            # Fallback to the old visualizations
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

                    # Try to import semantic colors if available
                    try:
                        from streamlit_app.utils.tufte_style import SEMANTIC_COLORS
                        patient_counts_color = SEMANTIC_COLORS['patient_counts']  # Use sage green for patient counts
                    except ImportError:
                        patient_counts_color = '#8FAD91'  # Fallback to sage green directly

                    # Use our helper function to create a properly formatted bar chart
                    # Use sage green for patient counts as per our semantic color system
                    fig = create_tufte_bar_chart(
                        categories=sorted_types,
                        values=sorted_counts,
                        title="GRAPHIC H: Retreatments by Type",
                        color=patient_counts_color,  # Use sage green for patient counts
                        figsize=(5, 5),
                        horizontal=True
                    )

                    # Add accessibility features to the figure
                    ax = fig.axes[0]
                    ax.set_xlabel("Number of Retreatments", fontsize=10, color="#555555")
                    ax.set_ylabel("Discontinuation Type", fontsize=10, color="#555555")

                    # Save figure for debugging
                    save_plot_for_debug(fig, "graphic_h_debug.png")

                    # Show the chart
                    st.pyplot(fig)
    else:
        # Fallback if we don't have discontinuation counts
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

                # Try to import semantic colors if available
                try:
                    from streamlit_app.utils.tufte_style import SEMANTIC_COLORS
                    patient_counts_color = SEMANTIC_COLORS['patient_counts']  # Use sage green for patient counts
                except ImportError:
                    patient_counts_color = '#8FAD91'  # Fallback to sage green directly

                # Use our helper function to create a properly formatted bar chart
                # Use sage green for patient counts as per our semantic color system
                fig = create_tufte_bar_chart(
                    categories=sorted_types,
                    values=sorted_counts,
                    title="GRAPHIC H: Retreatments by Type",
                    color=patient_counts_color,  # Use sage green for patient counts
                    figsize=(5, 5),
                    horizontal=True
                )

                # Add accessibility features to the figure
                ax = fig.axes[0]
                ax.set_xlabel("Number of Retreatments", fontsize=10, color="#555555")
                ax.set_ylabel("Discontinuation Type", fontsize=10, color="#555555")

                # Save figure for debugging
                save_plot_for_debug(fig, "graphic_h_debug.png")

                # Show the chart
                st.pyplot(fig)
        
        # Display detailed statistics in an expander
        st.markdown('<div data-test-id="detailed-retreatment-stats-marker"></div>', unsafe_allow_html=True)
        with st.expander("**Detailed Retreatment Statistics**"):
            st.write("### Retreatments by Discontinuation Type")
            st.dataframe(retreatment_df, use_container_width=True)
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
                
                st.dataframe(comparison_df, use_container_width=True)
                
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
                # Use the standard patient counts color for consistency
                try:
                    from streamlit_app.utils.tufte_style import SEMANTIC_COLORS
                    patient_counts_color = SEMANTIC_COLORS['patient_counts']  # Use sage green for patient counts
                except ImportError:
                    patient_counts_color = '#8FAD91'  # Fallback to sage green directly

                fig = create_tufte_bar_chart(
                    categories=types,
                    values=rates,
                    title="GRAPHIC I: Patient Retreatment Rate by Discontinuation Type",
                    xlabel="Retreatment Rate (%)",
                    color=patient_counts_color,  # Use sage green for patient counts
                    figsize=(10, 5),
                    horizontal=True
                )
                
                # Get the axis from the figure
                ax = fig.axes[0]
                
                # Set appropriate axis limits
                ax.set_xlim(0, max(rates) * 1.1)
                
                # Force a clear zero line as a reference
                ax.axhline(y=0, color='#cccccc', linestyle='-', linewidth=0.5, alpha=0.3)
                
                # Add accessibility features to the figure
                ax.set_xlabel("Retreatment Rate (%)", fontsize=10, color="#555555")
                ax.set_ylabel("Discontinuation Type", fontsize=10, color="#555555")
                
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

    if not (retreatment_by_type and sum(retreatment_by_type.values()) > 0):
        st.warning("No retreatment breakdown by discontinuation type available.")

    # Add explanation expander at the bottom (outside all other expanders)
    st.markdown('<div data-test-id="retreatment-explanation-marker"></div>', unsafe_allow_html=True)
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