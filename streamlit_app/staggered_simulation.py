"""
Staggered Simulation Module for AMD Protocol Explorer Streamlit app.

This module integrates the StaggeredABS simulation class with the Streamlit UI,
enabling visualization of realistic patient enrollment patterns using a Poisson process.
"""

import os
import sys
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import streamlit as st
import time
from datetime import datetime, timedelta

# Add the project root directory to sys.path to allow importing from the main project
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root_dir)

# Import custom modules
from streamlit_app.json_utils import APEJSONEncoder
from streamlit_app.enrollment_viz import create_simple_enrollment_histogram
from streamlit_app.r_integration import create_enrollment_visualization

# Import simulation modules
try:
    from simulation.staggered_abs import StaggeredABS
    from simulation.config import SimulationConfig
    from visualization.acuity_viz import (
        plot_patient_acuity_by_patient_time,
        plot_mean_acuity_with_sample_size,
        plot_dual_timeframe_acuity
    )
    # Flag that imports were successful
    staggered_imports_successful = True
except ImportError as e:
    print(f"Failed to import staggered simulation modules: {e}")
    staggered_imports_successful = False

def run_staggered_simulation(params):
    """
    Run a staggered patient enrollment simulation with the given parameters.
    
    Parameters
    ----------
    params : dict
        Dictionary of parameters from the UI, including:
        - simulation_type: str
            Type of simulation ('ABS' only for staggered)
        - population_size: int
            Target population size for simulation
        - duration_years: int
            Duration in years for the simulation
        - arrival_rate: float
            Patient arrival rate per week (Poisson parameter)
        - enable_clinician_variation: bool
            Whether to enable clinician variation
        - staggered_enrollment: bool
            Whether to use staggered enrollment
    
    Returns
    -------
    dict
        Simulation results with dual timeframe data
    """
    if not staggered_imports_successful:
        st.error("Staggered simulation modules not available. Please check your installation.")
        return {
            "error": "Staggered simulation modules not available",
            "failed": True
        }
    
    try:
        # Display progress indicators
        progress_text = st.empty()
        progress_bar = st.progress(0)
        
        # Display progress update before starting
        progress_text.text("Initializing staggered ABS simulation...")
        progress_bar.progress(10)
        
        # Get configuration
        test_config_name = "test_simulation"  # Use test simulation as base config
        config = SimulationConfig.from_yaml(test_config_name)
        
        # Override with user parameters
        config.num_patients = params["population_size"]
        config.duration_days = params["duration_years"] * 365
        config.simulation_type = "agent_based"  # Always agent-based for staggered
        
        # Get current date as the start date or use a fixed date for consistency
        start_date = datetime(2023, 1, 1)  # Fixed start date for consistent results
        
        # Set arrival rate (patients per week)
        arrival_rate = params.get("arrival_rate", 10.0)  # Default to 10 patients/week
        
        # Create the staggered simulation
        progress_text.text("Creating staggered simulation...")
        progress_bar.progress(20)
        
        # Initialize simulation
        sim = StaggeredABS(config, start_date)
        sim.arrival_rate = arrival_rate
        
        # Update progress
        progress_text.text("Initializing simulation...")
        progress_bar.progress(30)
        
        # Initialize the simulation
        sim.initialize_simulation()
        
        # Update progress
        progress_text.text("Running staggered simulation...")
        progress_bar.progress(40)
        
        # Run the simulation for the specified duration
        end_date = start_date + timedelta(days=config.duration_days)
        
        # Actual simulation run
        results = sim.run()
        
        # Update progress
        progress_text.text("Processing simulation results...")
        progress_bar.progress(70)
        
        # Get patient histories
        patient_histories = results.get("patient_histories", {})
        enrollment_dates = results.get("enrollment_dates", {})
        
        # Calculate statistics
        progress_text.text("Calculating statistics...")
        progress_bar.progress(80)
        
        # Basic statistics
        total_patients = len(patient_histories)
        total_visits = sum(len(visits) for visits in patient_histories.values())
        mean_visits = total_visits / total_patients if total_patients > 0 else 0
        
        # Create enrollment histogram
        progress_text.text("Creating visualizations...")
        progress_bar.progress(90)
        
        # Save enrollment histogram using the simplified version
        enrollment_hist = create_simple_enrollment_histogram(enrollment_dates)
        
        # Prepare final results
        stats = {
            "simulation_type": "staggered_abs",
            "population_size": total_patients,
            "duration_years": params["duration_years"],
            "arrival_rate": arrival_rate,
            "total_visits": total_visits,
            "mean_visits": mean_visits,
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "patient_histories": patient_histories,
            "enrollment_dates": enrollment_dates
        }
        
        # Update progress
        progress_text.text("Staggered simulation complete!")
        progress_bar.progress(100)
        
        return stats
    
    except Exception as e:
        import traceback
        st.error(f"Error in staggered simulation: {e}")
        st.code(traceback.format_exc())
        return {
            "error": str(e),
            "traceback": traceback.format_exc(),
            "failed": True
        }

def create_enrollment_histogram_disabled(enrollment_dates):
    """
    Create a truly Tufte-inspired visualization of patient enrollment.
    
    Parameters
    ----------
    enrollment_dates : dict
        Dictionary mapping patient IDs to enrollment dates
    
    Returns
    -------
    matplotlib.figure.Figure
        Figure containing the enrollment visualization
    """
    # Extract dates and convert to quarterly data
    dates = list(enrollment_dates.values())
    
    # Convert to pandas datetime
    df = pd.DataFrame({"enrollment_date": dates})
    df["enrollment_date"] = pd.to_datetime(df["enrollment_date"])
    
    # Group by quarter for cleaner visualization
    df["quarter"] = df["enrollment_date"].dt.to_period('Q')
    
    # Count enrollments by quarter
    quarterly_counts = df.groupby("quarter").size()
    
    # Create a clean, minimal figure with controlled dimensions
    fig, ax = plt.subplots(figsize=(10, 5))
    
    # Remove default styling
    plt.rcParams['axes.spines.top'] = False
    plt.rcParams['axes.spines.right'] = False
    plt.rcParams['axes.spines.left'] = False
    plt.rcParams['axes.grid'] = False
    
    # Plot as a sparse dot plot with connecting lines (Tufte-like)
    x = range(len(quarterly_counts))
    
    # Plot connecting line (subtle)
    ax.plot(x, quarterly_counts.values, color='#999999', linewidth=0.75, alpha=0.7)
    
    # Add data points
    scatter = ax.scatter(x, quarterly_counts.values, s=30, color='#3498db', alpha=0.8, zorder=3)
    
    # Keep only bottom spine
    for spine in ['top', 'right', 'left']:
        ax.spines[spine].set_visible(False)
    
    ax.spines['bottom'].set_color('#999999')
    ax.spines['bottom'].set_linewidth(0.75)
    
    # Set up minimal y-axis
    y_max = quarterly_counts.max()
    
    # Use only minimal necessary tick marks
    ax.set_yticks([0, y_max])
    ax.set_yticklabels([0, y_max], fontsize=9, color='#555555')
    ax.tick_params(axis='y', length=0)  # No tick marks
    
    # Use abbreviated quarter labels
    quarter_labels = [f"{q.year} Q{q.quarter}" for q in quarterly_counts.index]
    
    # Only show key quarters
    if len(quarter_labels) > 4:
        # Show first quarter of each year and max enrollment
        visible_indices = []
        max_idx = quarterly_counts.values.argmax()
        
        # Add first and last points
        visible_indices.extend([0, len(quarterly_counts) - 1])
        
        # Add midpoint(s)
        middle = len(quarterly_counts) // 2
        visible_indices.append(middle)
        
        # Add max if not already included
        if max_idx not in visible_indices:
            visible_indices.append(max_idx)
        
        visible_indices = sorted(list(set(visible_indices)))
        
        sparse_labels = ["" for _ in range(len(quarter_labels))]
        for idx in visible_indices:
            sparse_labels[idx] = quarter_labels[idx]
            
        ax.set_xticks(x)
        ax.set_xticklabels(sparse_labels, fontsize=9, color='#555555')
    else:
        ax.set_xticks(x)
        ax.set_xticklabels(quarter_labels, fontsize=9, color='#555555')
    
    # Add direct data labels for key points (Tufte principle)
    # Label the maximum and first/last quarters
    max_idx = quarterly_counts.values.argmax()
    
    # Add peak label
    ax.text(
        max_idx, 
        quarterly_counts.values[max_idx] + (y_max * 0.05),
        f"{quarterly_counts.values[max_idx]}",
        ha='center', 
        va='bottom', 
        fontsize=9,
        color='#333333'
    )
    
    # Add total as small annotation
    total_patients = sum(quarterly_counts.values)
    ax.text(
        len(quarterly_counts) - 1, 
        quarterly_counts.iloc[-1], 
        f"Total: {total_patients}",
        ha='right', 
        va='bottom',
        fontsize=9,
        color='#555555',
        transform=ax.get_xaxis_transform(),
        bbox=dict(facecolor='white', alpha=0.7, edgecolor='none', pad=2)
    )
    
    # Set a clear, left-aligned title
    ax.set_title("Patient Enrollment by Quarter", fontsize=12, loc='left', color='#333333')
    
    # Small data indicator on y-axis
    ax.text(
        -0.02, 
        y_max / 2,
        "Patients",
        ha='right', 
        va='center',
        fontsize=9,
        color='#555555',
        transform=ax.get_yaxis_transform()
    )
    
    # Ensure proper spacing but with controlled size
    plt.tight_layout(pad=1.5)

    # Set a fixed figure size to avoid oversized images
    fig.set_size_inches(10, 5, forward=True)

    # Save with reasonable DPI to avoid the image size limitation
    plt.savefig("patient_enrollment_histogram.png", dpi=100, bbox_inches='tight')
    
    return fig

def create_dual_timeframe_visualizations(results, output_dir="output/staggered_comparison"):
    """
    Create dual timeframe visualizations for staggered simulation results.
    
    Parameters
    ----------
    results : dict
        Staggered simulation results with patient histories and enrollment dates
    output_dir : str, optional
        Directory to save output visualizations
    
    Returns
    -------
    dict
        Dictionary with paths to generated visualizations
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Extract data
    patient_histories = results.get("patient_histories", {})
    enrollment_dates = results.get("enrollment_dates", {})
    start_date = datetime.strptime(results.get("start_date", "2023-01-01"), "%Y-%m-%d")
    end_date = datetime.strptime(results.get("end_date", "2024-01-01"), "%Y-%m-%d")
    
    # Exit if no data
    if not patient_histories or not enrollment_dates:
        return {"error": "No patient data available"}
    
    # Convert patient data to format expected by visualization functions
    patient_data = {}
    for patient_id, visits in patient_histories.items():
        patient_data[patient_id] = []
        for visit in visits:
            visit_dict = {
                'date': visit.get('date'),
                'vision': visit.get('vision')
            }
            # Add actions if available
            if 'actions' in visit:
                visit_dict['actions'] = visit.get('actions')
            patient_data[patient_id].append(visit_dict)
    
    # Create visualization paths dictionary
    viz_paths = {}
    
    # 1. Create calendar time visualization - Using Tufte styling where available
    calendar_path = os.path.join(output_dir, "calendar_time_acuity.png")
    try:
        # Use a try-except block to handle any plotting errors
        try:
            # Try to use Tufte style if available
            try:
                from streamlit_app.utils.tufte_style import create_tufte_time_series

                # First convert patient data to the format needed by the Tufte visualization
                # This requires organized time series data by calendar date

                # Initialize data structures for weekly statistics
                start_week = 0
                total_weeks = int((end_date - start_date).days / 7) + 1

                # Create weekly timeline dates
                week_dates = [start_date + timedelta(weeks=w) for w in range(total_weeks)]

                # Data structures for weekly statistics
                acuity_by_week = {w: [] for w in range(total_weeks)}  # Week index → list of acuity values

                # Process each patient's data
                for patient_id, visits in patient_data.items():
                    # Extract dates and vision values
                    for visit in visits:
                        if 'date' in visit and 'vision' in visit:
                            visit_date = visit['date']
                            # Calculate which week this falls into
                            week_index = int((visit_date - start_date).days / 7)

                            # If within our timeframe, add to the appropriate week
                            if 0 <= week_index < total_weeks:
                                acuity_by_week[week_index].append(float(visit['vision']))

                # Compute weekly means and sample sizes
                calendar_weeks = []
                calendar_acuity = []
                calendar_sample_sizes = []

                for week in range(total_weeks):
                    if acuity_by_week[week]:
                        calendar_weeks.append(week_dates[week])
                        calendar_acuity.append(sum(acuity_by_week[week]) / len(acuity_by_week[week]))
                        calendar_sample_sizes.append(len(acuity_by_week[week]))

                # Create DataFrame for Tufte visualization
                import pandas as pd
                calendar_df = pd.DataFrame({
                    'date': calendar_weeks,
                    'visual_acuity': calendar_acuity,
                    'sample_size': calendar_sample_sizes
                })

                # Process calendar data for visualization using a bar chart approach
                from streamlit_app.utils.tufte_style import set_tufte_style, style_axis, add_reference_line, add_text_annotation, TUFTE_COLORS
                import numpy as np

                # Create figure and axis
                fig, ax = plt.subplots(figsize=(10, 6), dpi=100)

                # Apply Tufte style
                set_tufte_style()

                # Process calendar data into 4-week bins
                if len(calendar_df) > 0:
                    # Make a copy to avoid warnings
                    df = calendar_df.copy()

                    # Ensure date is datetime
                    if not pd.api.types.is_datetime64_any_dtype(df['date']):
                        df['date'] = pd.to_datetime(df['date'])

                    # Get first date as reference
                    first_date = df['date'].min()

                    # Calculate days since first date
                    df['days'] = (df['date'] - first_date).dt.days

                    # Create 4-week bins
                    bin_weeks = 4
                    days_per_bin = bin_weeks * 7
                    df['bin'] = (df['days'] // days_per_bin) * days_per_bin

                    # Calculate bin centers
                    df['bin_center_days'] = df['bin'] + days_per_bin / 2
                    df['bin_center'] = first_date + pd.to_timedelta(df['bin_center_days'], unit='D')

                    # Group data by bin
                    binned_data = df.groupby('bin').agg({
                        'visual_acuity': 'mean',
                        'sample_size': 'sum',
                        'bin_center': 'first'
                    }).reset_index()

                    # Create bar chart with lighter bars matching patient time visualization
                    bars = ax.bar(
                        binned_data['bin_center'],
                        binned_data['visual_acuity'],
                        width=pd.Timedelta(days=days_per_bin * 0.8),
                        color='#a8c4e5',  # Lighter blue that matches patient time viz
                        alpha=0.3,
                        edgecolor='none'
                    )

                    # Add data points with connecting line - matching patient time visualization
                    ax.plot(
                        binned_data['bin_center'],
                        binned_data['visual_acuity'],
                        marker='o',
                        markersize=5,
                        color=TUFTE_COLORS['primary'],
                        linewidth=1.5,
                        alpha=0.8
                    )

                    # Add trend line if enough data points
                    if len(binned_data) >= 3:
                        try:
                            # Simple linear trend
                            x_numeric = np.arange(len(binned_data))
                            z = np.polyfit(x_numeric, binned_data['visual_acuity'], 1)
                            p = np.poly1d(z)

                            ax.plot(
                                binned_data['bin_center'],
                                p(x_numeric),
                                color=TUFTE_COLORS['secondary'],
                                linewidth=1.8,
                                alpha=0.9
                            )
                        except Exception as e:
                            print(f"Error creating trend line: {e}")

                    # Add baseline reference
                    baseline_va = binned_data['visual_acuity'].iloc[0]
                    add_reference_line(ax, baseline_va, 'y', TUFTE_COLORS['text_secondary'])

                    # Format x-axis with fewer labels
                    if len(binned_data) > 8:
                        step = 2 if len(binned_data) < 16 else 3
                        ticks = np.arange(0, len(binned_data), step)

                        date_labels = [binned_data['bin_center'].iloc[i].strftime('%Y-%m') for i in ticks]
                        ax.set_xticks([binned_data['bin_center'].iloc[i] for i in ticks])
                        ax.set_xticklabels(date_labels, rotation=45, ha='right')
                    else:
                        date_labels = [d.strftime('%Y-%m') for d in binned_data['bin_center']]
                        ax.set_xticks(binned_data['bin_center'])
                        ax.set_xticklabels(date_labels, rotation=45, ha='right')

                    # Add summary statistics at bottom-left to match patient time visualization
                    add_text_annotation(
                        fig,
                        f'Baseline: {baseline_va:.2f} | Mean: {binned_data["visual_acuity"].mean():.2f}',
                        position='bottom-left',
                        fontsize=8
                    )

                # Style the chart
                style_axis(ax)

                # Set y-axis limits to 0-85 for acuity
                ax.set_ylim(0, 85)

                # Add labels
                ax.set_title("Mean Visual Acuity by Calendar Time", fontsize=14, color=TUFTE_COLORS['text'])
                ax.set_ylabel("Visual Acuity (ETDRS letters)", fontsize=10, color=TUFTE_COLORS['text_secondary'])

                # Add explanation about binning
                add_text_annotation(
                    fig,
                    'Data binned in 4-week intervals to align with treatment protocol cycles',
                    position='bottom-left',
                    fontsize=8
                )

                # Save the figure
                plt.savefig(calendar_path, dpi=100, bbox_inches='tight')
                plt.close(fig)

            except ImportError:
                # Fall back to original method if Tufte style is not available
                print("Tufte style not available for calendar time, using standard visualization")
                plt.figure(figsize=(10, 6))
                plot_mean_acuity_with_sample_size(
                    patient_data=patient_data,
                    enrollment_dates=enrollment_dates,
                    start_date=start_date,
                    end_date=end_date,
                    time_unit='calendar',
                    show=False,
                    save_path=calendar_path,
                    title="Mean Visual Acuity by Calendar Time"
                )
                plt.close()

        except Exception as plot_error:
            # Create a simple error figure instead of failing completely
            plt.figure(figsize=(10, 6))
            plt.text(0.5, 0.5, f"Error creating calendar time visualization:\n{str(plot_error)}",
                    ha='center', va='center', fontsize=12, wrap=True)
            plt.savefig(calendar_path)
            plt.close()
            # Log the error but continue
            print(f"Plot error (handled): {plot_error}")

        viz_paths["calendar_time"] = calendar_path
        # Skip the combined dual timeframe view to avoid dimension errors
        st.info("Using separate visualizations for calendar and patient time")
    except Exception as e:
        st.error(f"Error creating calendar time visualization: {e}")
    
    # 2. Plot patient time visualization - Using Tufte styling
    patient_time_path = os.path.join(output_dir, "vision_by_patient_time.png")
    try:
        # Use a try-except block to handle any plotting errors
        try:
            # Import the Tufte style visualization function
            try:
                from streamlit_app.utils.tufte_style import create_tufte_patient_time_visualization

                # First convert patient data to the format needed by the Tufte visualization
                # This requires a DataFrame with time_weeks, visual_acuity, and sample_size columns

                # Initialize lists to collect data
                time_points = []
                acuity_values = []
                sample_sizes = []

                # Create weekly bins for patient time (0-52 weeks)
                max_weeks = 52
                for week in range(max_weeks + 1):
                    week_acuity = []

                    # Collect acuity values for this week across all patients
                    for patient_id, visits in patient_data.items():
                        # Get enrollment date for this patient
                        enrollment_date = enrollment_dates.get(patient_id, start_date)

                        # Find visit closest to this week
                        for visit in visits:
                            if 'date' in visit and 'vision' in visit:
                                # Calculate weeks since enrollment
                                visit_date = visit['date']
                                weeks_since_enrollment = (visit_date - enrollment_date).days / 7

                                # If this visit is within 0.5 weeks of our target, include it
                                if abs(weeks_since_enrollment - week) <= 0.5:
                                    week_acuity.append(float(visit['vision']))

                    # Only include weeks with data
                    if week_acuity:
                        time_points.append(week)
                        acuity_values.append(sum(week_acuity) / len(week_acuity))
                        sample_sizes.append(len(week_acuity))

                # Create DataFrame for Tufte visualization
                import pandas as pd
                acuity_df = pd.DataFrame({
                    'time_weeks': time_points,
                    'visual_acuity': acuity_values,
                    'sample_size': sample_sizes
                })

                # Create the Tufte-style visualization
                fig, ax = create_tufte_patient_time_visualization(
                    acuity_df,
                    title="Mean Visual Acuity by Patient Time (Weeks Since Enrollment)",
                    figsize=(10, 6)
                )

                # Save the figure
                plt.savefig(patient_time_path, dpi=100, bbox_inches='tight')
                plt.close(fig)

            except ImportError:
                # Fall back to original method if Tufte style is not available
                print("Tufte style not available, using standard visualization")
                plt.figure(figsize=(10, 6))
                plot_mean_acuity_with_sample_size(
                    patient_data=patient_data,
                    enrollment_dates=enrollment_dates,
                    start_date=start_date,
                    end_date=end_date,
                    time_unit='patient',  # Use patient time (weeks since enrollment)
                    show=False,
                    save_path=patient_time_path,
                    title="Mean Visual Acuity by Patient Time (Weeks Since Enrollment)"
                )
                plt.close()

        except Exception as plot_error:
            # Create a simple error figure instead of failing completely
            plt.figure(figsize=(10, 6))
            plt.text(0.5, 0.5, f"Error creating patient time visualization:\n{str(plot_error)}",
                    ha='center', va='center', fontsize=12, wrap=True)
            plt.savefig(patient_time_path)
            plt.close()
            # Log the error but continue
            print(f"Plot error (handled): {plot_error}")

        viz_paths["patient_time"] = patient_time_path
    except Exception as e:
        st.error(f"Error creating patient time visualization: {e}")
        
    # Return paths to visualizations
    return viz_paths

def display_staggered_enrollment_controls():
    """
    Display UI controls for staggered patient enrollment in the Streamlit app.
    
    Returns
    -------
    dict
        Parameters selected in the UI
    """
    st.subheader("Staggered Enrollment Settings")
    
    # Create a two-column layout
    col1, col2 = st.columns(2)
    
    with col1:
        # Enable/disable staggered enrollment
        staggered_enrollment = st.checkbox(
            "Enable Staggered Enrollment",
            value=True,
            help="Use realistic patient arrival patterns instead of enrolling all patients at simulation start",
            key="staggered_enrollment_checkbox"
        )
        
        # Patient arrival rate (per week)
        arrival_rate = st.slider(
            "Patient Arrival Rate (per week)",
            min_value=1.0,
            max_value=20.0,
            value=10.0,
            step=0.5,
            help="Average number of new patients per week (Poisson distribution parameter)",
            key="arrival_rate_slider"
        )
    
    with col2:
        # Tooltip to explain staggered enrollment
        st.info("""
        **Staggered Enrollment** simulates real-world patient recruitment where patients join the study over time 
        following a Poisson process, rather than all starting at once. This enables:
        
        - More realistic resource utilization visualization
        - Dual timeframe analysis (calendar time vs. patient time)
        - Better modeling of clinic capacity constraints
        """)
    
    # Return parameters
    return {
        "staggered_enrollment": staggered_enrollment,
        "arrival_rate": arrival_rate
    }

def add_staggered_parameters(params):
    """
    Add staggered enrollment parameters to the simulation parameters.
    
    Parameters
    ----------
    params : dict
        Current simulation parameters
    
    Returns
    -------
    dict
        Updated parameters with staggered enrollment settings
    """
    # Get staggered enrollment parameters from session state
    staggered_params = {}
    staggered_params["staggered_enrollment"] = st.session_state.get("staggered_enrollment_checkbox", True)
    staggered_params["arrival_rate"] = st.session_state.get("arrival_rate_slider", 10.0)
    
    # Merge with existing parameters
    params.update(staggered_params)
    
    return params