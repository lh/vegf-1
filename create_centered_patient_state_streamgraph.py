#!/usr/bin/env python
"""
Create centered streamgraph visualization of patient states over time using real simulation data.

This script is a variant of create_patient_state_streamgraph.py that creates a centered streamgraph.
The main difference is that this visualization expands both upward and downward from a central
baseline, with active patients below and discontinued patients above, creating a more balanced
and symmetrical appearance.
"""

import os
import sys
import argparse
import pandas as pd
import numpy as np
from pathlib import Path
import plotly.graph_objects as go
from collections import defaultdict
from datetime import timedelta

# Add project root to path
root_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(root_dir)

# Import color system from visualization module
from visualization.color_system import COLORS, SEMANTIC_COLORS, ALPHAS


def load_simulation_data(base_path):
    """
    Load simulation data from Parquet files.
    
    Parameters
    ----------
    base_path : str
        Base path to the simulation results (without _visits, etc. extensions)
        
    Returns
    -------
    tuple
        (visits_df, metadata_df, stats_df) DataFrames
    """
    # Check if this is a directory with partitioned parquet files
    directory = os.path.dirname(base_path)
    basename = os.path.basename(base_path)
    
    # Try to load from partitioned files first
    visits_path = os.path.join(directory, f"{basename}_visits.parquet")
    metadata_path = os.path.join(directory, f"{basename}_metadata.parquet")
    stats_path = os.path.join(directory, f"{basename}_stats.parquet")
    
    if os.path.exists(visits_path):
        # Load from partitioned files
        try:
            visits_df = pd.read_parquet(visits_path)
            metadata_df = pd.read_parquet(metadata_path)
            stats_df = pd.read_parquet(stats_path)
            
            print(f"Loaded data from partitioned Parquet files:")
            print(f"  - Visits: {len(visits_df)} records")
            print(f"  - Patients: {visits_df['patient_id'].nunique()} unique patients")
            
            return visits_df, metadata_df, stats_df
        except Exception as e:
            print(f"Error loading partitioned Parquet files: {e}")
    
    # If partitioned files not found or failed to load, try single Parquet file
    if os.path.exists(f"{base_path}.parquet"):
        try:
            # Load from a single Parquet file (legacy format)
            print(f"Loading from single Parquet file: {base_path}.parquet")
            # This approach assumes a specific structure that would need to be defined
            raise NotImplementedError("Single Parquet file format not implemented")
        except Exception as e:
            print(f"Error loading single Parquet file: {e}")
    
    # If Parquet load failed, try JSON as last resort
    json_path = f"{base_path}.json"
    if os.path.exists(json_path):
        print(f"Falling back to JSON format: {json_path}")
        print("WARNING: JSON format loses datetime type information - this may cause issues")
        
        import json
        try:
            with open(json_path, "r") as f:
                raw_data = json.load(f)
            
            # Extract visit data
            visit_records = []
            for patient_id, visits in raw_data.get("patient_histories", {}).items():
                for visit in visits:
                    visit["patient_id"] = patient_id
                    visit_records.append(visit)
            
            visits_df = pd.DataFrame(visit_records)
            
            # Convert date strings to datetime
            if "date" in visits_df.columns:
                try:
                    visits_df["date"] = pd.to_datetime(visits_df["date"])
                except:
                    print("WARNING: Could not convert date column to datetime")
            
            # Create metadata DataFrame
            metadata = {
                "simulation_type": raw_data.get("simulation_type"),
                "patients": raw_data.get("config", {}).get("patient_count"),
                "duration_years": raw_data.get("config", {}).get("duration_years"),
                "start_date": raw_data.get("config", {}).get("start_date"),
                "discontinuation_enabled": raw_data.get("config", {}).get("discontinuation_enabled", False)
            }
            metadata_df = pd.DataFrame([metadata])
            
            # Create statistics DataFrame
            stats_df = pd.DataFrame([raw_data.get("statistics", {})])
            
            print(f"Loaded data from JSON file:")
            print(f"  - Visits: {len(visits_df)} records")
            print(f"  - Patients: {visits_df['patient_id'].nunique()} unique patients")
            
            return visits_df, metadata_df, stats_df
        except Exception as e:
            print(f"Error loading JSON file: {e}")
            import traceback
            traceback.print_exc()
    
    raise FileNotFoundError(f"Could not find simulation data at {base_path}")


def prepare_patient_state_data(visits_df, metadata_df):
    """
    Prepare patient state data for streamgraph visualization.
    
    Parameters
    ----------
    visits_df : pd.DataFrame
        DataFrame with patient visit data
    metadata_df : pd.DataFrame
        DataFrame with simulation metadata
        
    Returns
    -------
    pd.DataFrame
        DataFrame with patient counts by state and month
    """
    print("\nPreparing patient state data for visualization...")
    
    # Get basic parameters
    total_patients = metadata_df["patients"].iloc[0]
    duration_years = metadata_df["duration_years"].iloc[0]
    duration_months = int(duration_years * 12)
    
    # Check if we have all patients
    actual_patients = visits_df["patient_id"].nunique()
    if actual_patients != total_patients:
        print(f"WARNING: Expected {total_patients} patients, found {actual_patients}")
    
    # Ensure date column is datetime
    if not pd.api.types.is_datetime64_dtype(visits_df["date"]):
        visits_df["date"] = pd.to_datetime(visits_df["date"])
    
    # Calculate months since start for each visit
    # First, find the earliest date for each patient
    patient_start_dates = visits_df.groupby("patient_id")["date"].min()
    
    # Create a mapping of patient ID to start date
    start_date_map = patient_start_dates.to_dict()
    
    # Calculate months since patient's first visit
    def months_since_start(row):
        patient_id = row["patient_id"]
        visit_date = row["date"]
        start_date = start_date_map[patient_id]
        delta = visit_date - start_date
        return delta.days / 30.44  # Average days per month
    
    # Add months column
    visits_df["months"] = visits_df.apply(months_since_start, axis=1)
    visits_df["month_int"] = visits_df["months"].round().astype(int)
    
    # Define state determination function
    def determine_state(row):
        """
        Determine patient state from visit data using only explicit flags.
        
        This function relies exclusively on flags set by the simulation, without
        attempting to infer states from other data points.
        """
        # Check explicit retreatment flag or has_been_retreated flag for cumulative tracking
        if row.get("is_retreatment_visit", False) or row.get("has_been_retreated", False):
            return "retreated"
            
        # Check explicit discontinuation flags
        if row.get("is_discontinuation_visit", False):
            # Get discontinuation type for categorization
            disc_type = row.get("discontinuation_type", "").lower()
            
            # Categorize based on discontinuation type with more granular categories
            if "stable" in disc_type or "planned" in disc_type or "max_interval" in disc_type:
                return "discontinued_planned"
            elif "admin" in disc_type or "administrative" in disc_type:
                return "discontinued_administrative"
            elif "premature" in disc_type or "early" in disc_type:
                return "discontinued_premature"
            elif "duration" in disc_type or "course" in disc_type:
                return "discontinued_duration"
            else:
                # Default to planned if type not recognized
                return "discontinued_planned"
                
        # Check phase for monitoring - renamed to discontinued (monitored)
        phase = row.get("phase", "").lower()
        if phase == "monitoring":
            return "discontinued"  # Renamed from "monitoring" to "discontinued"
            
        # Default to active if no other state detected
        return "active"
    
    # Add state column
    visits_df["state"] = visits_df.apply(determine_state, axis=1)
    
    # Get state for each patient at each month
    # First, find the state at each recorded visit
    visits_df = visits_df.sort_values(["patient_id", "date"])
    
    # Create a helper function to fill in patient state for all months
    def generate_patient_timeline(patient_id, patient_visits):
        """Generate state for all months for a patient"""
        # Sort visits by month
        visits_by_month = patient_visits.sort_values("month_int")
        
        # Initialize timeline with all months
        timeline = pd.DataFrame({
            "month": range(duration_months + 1),
            "patient_id": patient_id,
            "state": None
        })
        
        # Get actual visit months and states
        visit_months = visits_by_month["month_int"].tolist()
        visit_states = visits_by_month["state"].tolist()
        
        # Fill in states
        last_state = "active"  # Default starting state
        
        for i, month in enumerate(timeline["month"]):
            # Find the latest visit state at or before this month
            latest_idx = -1
            for j, visit_month in enumerate(visit_months):
                if visit_month <= month:
                    latest_idx = j
                else:
                    break
            
            # If we have a visit at or before this month, use its state
            if latest_idx >= 0:
                last_state = visit_states[latest_idx]
            
            # Record the state for this month
            timeline.loc[i, "state"] = last_state
        
        return timeline
    
    # Generate timeline for each patient
    all_timelines = []
    
    for patient_id, patient_visits in visits_df.groupby("patient_id"):
        patient_timeline = generate_patient_timeline(patient_id, patient_visits)
        all_timelines.append(patient_timeline)
    
    # Combine all patient timelines
    patient_timelines = pd.concat(all_timelines, ignore_index=True)
    
    # Count patients by state and month
    state_counts = patient_timelines.groupby(["month", "state"]).size().reset_index(name="count")
    
    # Verify the conservation principle
    month_totals = state_counts.groupby("month")["count"].sum()
    for month, total in month_totals.items():
        if total != total_patients:
            print(f"WARNING: Month {month} has {total} patients, expected {total_patients}")
    
    # Pivot to get states as columns
    pivot_df = state_counts.pivot(index="month", columns="state", values="count").fillna(0)
    
    # Ensure all state categories exist
    state_categories = [
        "active",
        "discontinued_planned",
        "discontinued_administrative",
        "discontinued_premature",  # Added premature discontinuation state
        "discontinued_duration",
        "discontinued",  # Renamed from "monitoring" to "discontinued"
        "retreated"
    ]
    
    for state in state_categories:
        if state not in pivot_df.columns:
            pivot_df[state] = 0
    
    # Print summary
    print("\nPatient state summary:")
    print(f"  - Time range: 0 to {duration_months} months")
    print(f"  - Total patients: {total_patients}")
    
    # Print states at key time points
    for year in range(int(duration_years) + 1):
        month = year * 12
        if month in pivot_df.index:
            print(f"\nMonth {month} (Year {year}):")
            for state in state_categories:
                if state in pivot_df.columns:
                    count = int(pivot_df.loc[month, state])
                    if count > 0:
                        print(f"  - {state}: {count} patients ({count/total_patients*100:.1f}%)")
    
    return pivot_df, state_categories


def create_centered_streamgraph(state_counts_df, state_categories, metadata_df, stats_df):
    """
    Create a centered Plotly streamgraph visualization.
    
    Parameters
    ----------
    state_counts_df : pd.DataFrame
        DataFrame with patient counts by state and month (pivoted)
    state_categories : list
        List of state categories for consistent ordering
    metadata_df : pd.DataFrame
        DataFrame with simulation metadata
    stats_df : pd.DataFrame
        DataFrame with simulation statistics
        
    Returns
    -------
    plotly.graph_objects.Figure
        Plotly figure with centered streamgraph visualization
    """
    print("\nCreating centered streamgraph visualization...")
    
    # Extract key metadata
    total_patients = metadata_df["patients"].iloc[0]
    duration_years = metadata_df["duration_years"].iloc[0]
    simulation_type = metadata_df["simulation_type"].iloc[0]
    
    # Use color system for patient states
    state_colors = {
        "active": SEMANTIC_COLORS['patient_state_active'],
        "retreated": SEMANTIC_COLORS['patient_state_retreated'],
        "discontinued": SEMANTIC_COLORS['patient_state_discontinued'],  # Updated from monitoring to discontinued
        "discontinued_planned": SEMANTIC_COLORS['patient_state_discontinued_planned'],
        "discontinued_administrative": SEMANTIC_COLORS['patient_state_discontinued_administrative'],
        "discontinued_premature": SEMANTIC_COLORS['patient_state_discontinued_premature'],
        "discontinued_duration": SEMANTIC_COLORS['patient_state_discontinued_duration'],
    }
    
    # Create months array
    months = state_counts_df.index.tolist()
    
    # *** Alternative Implementation: Creating Centered Stream Manually ***
    # This approach creates a more visually balanced streamgraph by manually adjusting
    # the baseline to center the data
    
    # Create a custom baseline by dividing the range by 2
    active_patients = state_counts_df['active'].values if 'active' in state_counts_df.columns else np.zeros(len(months))
    retreated_patients = state_counts_df['retreated'].values if 'retreated' in state_counts_df.columns else np.zeros(len(months))
    
    # Group 1: active treatment (active + retreated)
    treatment_group = active_patients + retreated_patients
    
    # Group 2: all discontinued states
    discontinued_group = np.zeros(len(months))
    for state in state_categories:
        if 'discontinued' in state and state in state_counts_df.columns:
            discontinued_group += state_counts_df[state].values
    
    # Calculate the baseline as weighted average to balance the visualization
    baseline = treatment_group * 0.75  # Use 75% of treatment group as baseline
    
    # Create figure for manual approach
    fig = go.Figure()
    
    # Create a dict to track the current stack position
    current_position = {}
    for month_idx in range(len(months)):
        current_position[month_idx] = -baseline[month_idx]  # Start from negative baseline
    
    # First add the active treatment states (from bottom up)
    treatment_states = ["active", "retreated"]
    for state in treatment_states:
        if state in state_counts_df.columns:
            values = state_counts_df[state].values
            color = state_colors.get(state, "#grey")
            display_name = state.replace("_", " ").title()
            
            # Create a customized set of y-values based on stacking from the baseline
            y_values = []
            for month_idx in range(len(months)):
                start_y = current_position[month_idx]
                end_y = start_y + values[month_idx]
                current_position[month_idx] = end_y
                y_values.append(end_y)
            
            # Add filled area
            fig.add_trace(go.Scatter(
                x=months,
                y=y_values,
                mode='lines',
                line=dict(width=0.5, color=color),
                fill='tonexty' if state != treatment_states[0] else 'none',  # Fill to the trace before it
                fillcolor=color,
                opacity=0.85,
                name=display_name,
                customdata=values,  # Add raw values for hover
                hovertemplate=f"{display_name}: %{{customdata:.0f}} patients<br>Month: %{{x:.0f}}<extra></extra>"
            ))
    
    # Reset current position to start from 0 (the middle) for discontinued states
    for month_idx in range(len(months)):
        current_position[month_idx] = 0
    
    # Then add all the discontinued states (from middle up)
    discontinued_states = [s for s in state_categories if 'discontinued' in s]
    
    # Need to add an initial zero trace as a starting point for filling
    # This creates a clean separation between the treatment and discontinued groups
    fig.add_trace(go.Scatter(
        x=months,
        y=[0] * len(months),
        mode='lines',
        line=dict(width=0, color='rgba(0,0,0,0)'),
        showlegend=False,
        hoverinfo='skip'
    ))
    
    for state in discontinued_states:
        if state in state_counts_df.columns:
            values = state_counts_df[state].values
            color = state_colors.get(state, "#grey")
            display_name = state.replace("_", " ").title()
            
            # Create a customized set of y-values based on stacking from 0 (middle)
            y_values = []
            for month_idx in range(len(months)):
                start_y = current_position[month_idx]
                end_y = start_y + values[month_idx]
                current_position[month_idx] = end_y
                y_values.append(end_y)
            
            # Add filled area
            fig.add_trace(go.Scatter(
                x=months,
                y=y_values,
                mode='lines',
                line=dict(width=0.5, color=color),
                fill='tonexty',  # Fill to the trace before it
                fillcolor=color,
                opacity=0.85,
                name=display_name,
                customdata=values,  # Add raw values for hover
                hovertemplate=f"{display_name}: %{{customdata:.0f}} patients<br>Month: %{{x:.0f}}<extra></extra>"
            ))
    
    # Configure layout
    fig.update_layout(
        title={
            'text': f"{simulation_type} Model: Patient States Over Time (Centered)",
            'y': 0.95,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top'
        },
        xaxis_title="Months",
        yaxis_title="Patient Distribution",
        hovermode="x unified",
        legend=dict(
            orientation="h", 
            yanchor="bottom", 
            y=-0.2, 
            xanchor="center", 
            x=0.5
        ),
        # Apply a clean white background
        paper_bgcolor='white',
        plot_bgcolor='white',
        # Make monthly tick marks (at yearly intervals)
        xaxis=dict(
            tickmode='array',
            tickvals=[i*12 for i in range(int(duration_years) + 1)],
            ticktext=[f"{i*12}" for i in range(int(duration_years) + 1)],
            gridcolor='lightgrey',
            gridwidth=0.5
        ),
        yaxis=dict(
            gridcolor='lightgrey',
            gridwidth=0.5,
            zeroline=True,  # Show the zero line for reference
            zerolinecolor='black',
            zerolinewidth=1
        ),
        # Add margins for readability
        margin=dict(l=50, r=50, t=80, b=120)
    )
    
    # Add annotations
    # Get discontinuation and retreatment stats
    unique_discontinued = stats_df["unique_discontinuations"].iloc[0]
    unique_retreated = stats_df["unique_retreatments"].iloc[0] if "unique_retreatments" in stats_df.columns else 0
    
    disc_rate = (unique_discontinued / total_patients) * 100
    retreat_rate = (unique_retreated / unique_discontinued) * 100 if unique_discontinued > 0 else 0
    
    # Add statistics as annotations
    fig.add_annotation(
        x=0.02,
        y=1.05,
        xref="paper",
        yref="paper",
        text=f"Total Patients: {total_patients}<br>Discontinued: {unique_discontinued} ({disc_rate:.1f}%)<br>Retreated: {unique_retreated} ({retreat_rate:.1f}% of discontinued)",
        showarrow=False,
        font=dict(size=10),
        align="left",
        bgcolor="rgba(255,255,255,0.8)",
        bordercolor="black",
        borderwidth=1,
        borderpad=4
    )
    
    # Add visualization explanation
    fig.add_annotation(
        x=0.98,
        y=1.05,
        xref="paper",
        yref="paper",
        text="Centered Visualization:<br>Active states below middle line<br>Discontinued states above middle line",
        showarrow=False,
        font=dict(size=10),
        align="right",
        bgcolor="rgba(255,255,255,0.8)",
        bordercolor="black",
        borderwidth=1,
        borderpad=4
    )
    
    # Add attribution and data source info
    fig.add_annotation(
        x=0.5,
        y=-0.22,
        xref="paper",
        yref="paper",
        text=f"Source: Real patient simulation data - No synthetic data used<br>Simulation Type: {simulation_type}, Duration: {duration_years} years, Patients: {total_patients}<br>Note: This is a centered visualization with active states below and discontinued states above the center line",
        showarrow=False,
        font=dict(size=8, color="darkgrey"),
        align="center"
    )
    
    return fig


def save_visualization(fig, input_path, output_dir=None, suffix="_centered_streamgraph"):
    """
    Save the visualization as HTML and PNG.
    
    Parameters
    ----------
    fig : plotly.graph_objects.Figure
        Plotly figure to save
    input_path : str
        Path to input data file (for naming)
    output_dir : str, optional
        Directory to save visualization to, by default "output/visualizations"
    suffix : str, optional
        Suffix to add to the filename, by default "_centered_streamgraph"
    
    Returns
    -------
    dict
        Paths to saved files
    """
    # Default output directory
    if output_dir is None:
        output_dir = os.path.join(os.getcwd(), "output", "visualizations")
    
    # Create directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate filename based on input
    basename = os.path.basename(input_path)
    filename_base = os.path.splitext(basename)[0]
    
    # Save as HTML (interactive)
    html_path = os.path.join(output_dir, f"{filename_base}{suffix}.html")
    fig.write_html(html_path)
    print(f"Interactive visualization saved to: {html_path}")
    
    # Save as PNG (static)
    png_path = os.path.join(output_dir, f"{filename_base}{suffix}.png")
    fig.write_image(png_path, width=1200, height=800, scale=2)
    print(f"Static visualization saved to: {png_path}")
    
    return {
        "html": html_path,
        "png": png_path
    }


def main():
    """Main function to parse arguments and create visualization."""
    parser = argparse.ArgumentParser(description="Create centered streamgraph visualization from simulation data")
    parser.add_argument("--input", type=str, required=True, 
                        help="Path to simulation data file (without _visits, etc. extensions)")
    parser.add_argument("--output-dir", type=str, default=None, 
                        help="Directory to save visualization to (default: output/visualizations)")
    
    args = parser.parse_args()
    
    # Load data
    visits_df, metadata_df, stats_df = load_simulation_data(args.input)
    
    # Prepare data
    state_counts_df, state_categories = prepare_patient_state_data(visits_df, metadata_df)
    
    # Create centered visualization
    fig = create_centered_streamgraph(state_counts_df, state_categories, metadata_df, stats_df)
    
    # Save visualization
    save_visualization(fig, args.input, args.output_dir)


if __name__ == "__main__":
    main()