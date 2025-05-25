#!/usr/bin/env python
"""
Create streamgraph visualization showing CURRENT patient states over time.

This differs from the cumulative view by showing where patients actually are at each
time point, allowing transitions like: Active → Discontinued → Retreated → Discontinued.

Each cross-section represents the current distribution at that moment in time.
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
    
    raise FileNotFoundError(f"Could not find simulation data at {base_path}")


def prepare_current_state_data(visits_df, metadata_df):
    """
    Prepare patient state data showing CURRENT states at each time point.
    
    This approach tracks where patients currently are, not where they've ever been.
    Patients can transition: Active → Discontinued → Retreated → Discontinued
    """
    print("\nPreparing CURRENT patient state data for visualization...")
    
    # Get basic parameters
    total_patients = metadata_df["patients"].iloc[0]
    duration_years = metadata_df["duration_years"].iloc[0]
    duration_months = int(duration_years * 12)
    
    # Ensure date column is datetime
    if not pd.api.types.is_datetime64_dtype(visits_df["date"]):
        visits_df["date"] = pd.to_datetime(visits_df["date"])
    
    # Calculate months since start for each visit
    patient_start_dates = visits_df.groupby("patient_id")["date"].min()
    start_date_map = patient_start_dates.to_dict()
    
    def months_since_start(row):
        patient_id = row["patient_id"]
        visit_date = row["date"]
        start_date = start_date_map[patient_id]
        delta = visit_date - start_date
        return delta.days / 30.44  # Average days per month
    
    # Add months column
    visits_df["months"] = visits_df.apply(months_since_start, axis=1)
    visits_df["month_int"] = visits_df["months"].round().astype(int)
    
    # Define current state determination function
    def determine_current_state(row):
        """
        Determine patient's CURRENT state at this visit based on phase and context.
        
        This represents where the patient actually is right now, not cumulative history.
        """
        phase = row.get("phase", "").lower()
        
        # Check if this is a retreatment context
        # Retreated = patient was discontinued but is now back in active treatment
        is_retreatment = row.get("is_retreatment_visit", False)
        
        # Determine current state based on phase
        if phase == "monitoring":
            # Patient is currently discontinued (being monitored, no injections)
            disc_type = row.get("discontinuation_type", "") or ""
            disc_type = disc_type.lower() if disc_type else ""
            
            # Map to clinical state names from patient_state_visualization_definitions
            if "stable_max_interval" in disc_type:
                return "untreated_remission"  # "Untreated - remission"
            elif "random_administrative" in disc_type:
                return "not_booked"  # "Not booked"
            elif "course_complete_but_not_renewed" in disc_type:
                return "not_renewed"  # "Not renewed"
            elif "poor_outcome" in disc_type:
                return "stopped_poor_outcome"  # "Stopped - poor outcome"
            else:
                return "discontinued_without_reason"  # "Discontinued without reason"
                
        elif phase in ["loading", "maintenance"]:
            # Patient is currently in active treatment
            if is_retreatment:
                return "recommencing_treatment"  # "Recommencing treatment" - transient state
            else:
                return "active"  # Regular active treatment
        
        # Default to active if phase not recognized
        return "active"
    
    # Add current state column
    visits_df["current_state"] = visits_df.apply(determine_current_state, axis=1)
    
    # Sort visits by patient and date
    visits_df = visits_df.sort_values(["patient_id", "date"])
    
    # Create timeline for each patient showing current state at each month
    def generate_current_state_timeline(patient_id, patient_visits):
        """Generate current state for all months for a patient"""
        # Sort visits by month
        visits_by_month = patient_visits.sort_values("month_int")
        
        # Initialize timeline with all months
        timeline = pd.DataFrame({
            "month": range(duration_months + 1),
            "patient_id": patient_id,
            "current_state": None
        })
        
        # Get actual visit months and states
        visit_months = visits_by_month["month_int"].tolist()
        visit_states = visits_by_month["current_state"].tolist()
        
        # Fill in current states using forward fill from latest visit
        last_state = "active"  # Default starting state
        
        for i, month in enumerate(timeline["month"]):
            # Find the latest visit state at or before this month
            latest_idx = -1
            for j, visit_month in enumerate(visit_months):
                if visit_month <= month:
                    latest_idx = j
                else:
                    break
            
            # If we have a visit at or before this month, use its current state
            if latest_idx >= 0:
                last_state = visit_states[latest_idx]
            
            # Record the current state for this month
            timeline.loc[i, "current_state"] = last_state
        
        return timeline
    
    # Generate timeline for each patient
    all_timelines = []
    
    for patient_id, patient_visits in visits_df.groupby("patient_id"):
        patient_timeline = generate_current_state_timeline(patient_id, patient_visits)
        all_timelines.append(patient_timeline)
    
    # Combine all patient timelines
    patient_timelines = pd.concat(all_timelines, ignore_index=True)
    
    # Count patients by current state and month
    state_counts = patient_timelines.groupby(["month", "current_state"]).size().reset_index(name="count")
    
    # Verify the conservation principle
    month_totals = state_counts.groupby("month")["count"].sum()
    for month, total in month_totals.items():
        if total != total_patients:
            print(f"WARNING: Month {month} has {total} patients, expected {total_patients}")
    
    # Pivot to get states as columns
    pivot_df = state_counts.pivot(index="month", columns="current_state", values="count").fillna(0)
    
    # Ensure all state categories exist (based on patient_state_visualization_definitions)
    state_categories = [
        "active",
        "recommencing_treatment",  # Transient retreatment state
        "untreated_remission",     # Stable max interval
        "not_booked",              # Administrative issues
        "not_renewed",             # Course complete
        "stopped_poor_outcome",    # Poor visual outcome (future)
        "discontinued_without_reason"  # Generic/unclear discontinuation
    ]
    
    for state in state_categories:
        if state not in pivot_df.columns:
            pivot_df[state] = 0
    
    # Print summary
    print("\nCURRENT patient state summary:")
    print(f"  - Time range: 0 to {duration_months} months")
    print(f"  - Total patients: {total_patients}")
    
    # Print states at key time points
    for year in range(int(duration_years) + 1):
        month = year * 12
        if month in pivot_df.index:
            print(f"\nMonth {month} (Year {year}) - CURRENT STATES:")
            for state in state_categories:
                if state in pivot_df.columns:
                    count = int(pivot_df.loc[month, state])
                    if count > 0:
                        print(f"  - {state}: {count} patients ({count/total_patients*100:.1f}%)")
    
    return pivot_df, state_categories


def create_current_state_streamgraph(state_counts_df, state_categories, metadata_df, stats_df):
    """
    Create a Plotly streamgraph visualization showing current states.
    """
    print("\nCreating CURRENT STATE streamgraph visualization...")
    
    # Extract key metadata
    total_patients = metadata_df["patients"].iloc[0]
    duration_years = metadata_df["duration_years"].iloc[0]
    simulation_type = metadata_df["simulation_type"].iloc[0]
    
    # Use color system for patient states (map new clinical names to existing colors)
    state_colors = {
        "active": SEMANTIC_COLORS['patient_state_active'],
        "recommencing_treatment": SEMANTIC_COLORS['patient_state_retreated'],
        "untreated_remission": SEMANTIC_COLORS['patient_state_discontinued_planned'],
        "not_booked": SEMANTIC_COLORS['patient_state_discontinued_administrative'],
        "not_renewed": SEMANTIC_COLORS['patient_state_discontinued_duration'],
        "stopped_poor_outcome": SEMANTIC_COLORS['patient_state_discontinued_premature'],
        "discontinued_without_reason": SEMANTIC_COLORS['patient_state_discontinued']
    }
    
    # Create months array
    months = state_counts_df.index.tolist()
    
    # Create figure
    fig = go.Figure()
    
    # Add traces for each state category in reverse order (for proper stacking)
    for state in reversed(state_categories):
        if state in state_counts_df.columns:
            values = state_counts_df[state].tolist()
            
            # Get color
            color = state_colors.get(state, "#grey")
            
            # Create clinical display names based on patient_state_visualization_definitions
            display_names = {
                "active": "Active",
                "recommencing_treatment": "Recommencing treatment",
                "untreated_remission": "Untreated - remission",
                "not_booked": "Not booked",
                "not_renewed": "Not renewed",
                "stopped_poor_outcome": "Stopped - poor outcome",
                "discontinued_without_reason": "Discontinued without reason"
            }
            display_name = display_names.get(state, state.replace("_", " ").title())
            
            # Add trace using proper stackgroup parameter for true streamgraph
            fig.add_trace(go.Scatter(
                x=months,
                y=values,
                mode='lines',
                line=dict(width=0.5, color=color),
                stackgroup='one',  # This enables proper stacking
                fillcolor=color,
                opacity=0.85,  # Add some transparency to make colors more subtle
                name=display_name,
                hovertemplate=f"{display_name}: %{{y:.0f}} patients<br>Month: %{{x:.0f}}<extra></extra>"
            ))
    
    # Configure layout
    fig.update_layout(
        title={
            'text': f"{simulation_type} Model: Current Patient States Over Time",
            'y': 0.95,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top'
        },
        xaxis_title="Months",
        yaxis_title="Number of Patients",
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
            # Ensure y-axis starts at 0 to show full stacked areas
            rangemode='nonnegative'
        ),
        # Add margins for readability
        margin=dict(l=50, r=50, t=80, b=120)
    )
    
    # Add annotations about the current state approach
    fig.add_annotation(
        x=0.02,
        y=1.05,
        xref="paper",
        yref="paper",
        text=f"CURRENT STATE VIEW<br>Total Patients: {total_patients}<br>Shows where patients are NOW<br>(not cumulative history)",
        showarrow=False,
        font=dict(size=10),
        align="left",
        bgcolor="rgba(255,255,255,0.8)",
        bordercolor="blue",
        borderwidth=2,
        borderpad=4
    )
    
    # Add attribution and data source info
    fig.add_annotation(
        x=0.5,
        y=-0.22,
        xref="paper",
        yref="paper",
        text=f"Current State Approach: Each cross-section shows actual patient distribution at that time point<br>Patients can transition: Active ↔ Discontinued ↔ Retreated ↔ Discontinued",
        showarrow=False,
        font=dict(size=8, color="darkgrey"),
        align="center"
    )
    
    return fig


def save_visualization(fig, input_path, output_dir=None):
    """
    Save the visualization as HTML and PNG.
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
    html_path = os.path.join(output_dir, f"{filename_base}_current_state_streamgraph.html")
    fig.write_html(html_path)
    print(f"Interactive current state visualization saved to: {html_path}")
    
    # Save as PNG (static)
    png_path = os.path.join(output_dir, f"{filename_base}_current_state_streamgraph.png")
    fig.write_image(png_path, width=1200, height=800, scale=2)
    print(f"Static current state visualization saved to: {png_path}")
    
    return {
        "html": html_path,
        "png": png_path
    }


def main():
    """Main function to parse arguments and create current state visualization."""
    parser = argparse.ArgumentParser(description="Create current state streamgraph visualization from simulation data")
    parser.add_argument("--input", type=str, required=True, 
                        help="Path to simulation data file (without _visits, etc. extensions)")
    parser.add_argument("--output-dir", type=str, default=None, 
                        help="Directory to save visualization to (default: output/visualizations)")
    
    args = parser.parse_args()
    
    # Load data
    visits_df, metadata_df, stats_df = load_simulation_data(args.input)
    
    # Prepare data
    state_counts_df, state_categories = prepare_current_state_data(visits_df, metadata_df)
    
    # Create visualization
    fig = create_current_state_streamgraph(state_counts_df, state_categories, metadata_df, stats_df)
    
    # Save visualization
    save_visualization(fig, args.input, args.output_dir)


if __name__ == "__main__":
    main()