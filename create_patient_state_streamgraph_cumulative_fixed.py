#!/usr/bin/env python3
"""
Create a patient state streamgraph showing CUMULATIVE patient states.
This shows what patients have EVER experienced, not just their current state.
Uses the enrichment flags from Parquet pipeline.
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os
import sys
import argparse

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import central color system
from visualization.color_system import COLORS, SEMANTIC_COLORS

def load_simulation_data(base_path):
    """Load simulation results from Parquet files."""
    visits_df = pd.read_parquet(f"{base_path}_visits.parquet")
    metadata_df = pd.read_parquet(f"{base_path}_metadata.parquet")
    stats_df = pd.read_parquet(f"{base_path}_stats.parquet")
    
    return visits_df, metadata_df, stats_df

def prepare_cumulative_state_data(visits_df, metadata_df):
    """
    Prepare patient state data showing CUMULATIVE states.
    
    This shows what patients have EVER experienced, using the cumulative flags
    like has_been_retreated and has_been_discontinued.
    """
    print("\nPreparing CUMULATIVE patient state data for visualization...")
    
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
    
    # Define cumulative state determination function
    def determine_cumulative_state(row):
        """
        Determine patient's cumulative state using enrichment flags.
        
        This represents what the patient has EVER experienced.
        Priority order: retreated > discontinued > active
        """
        # Retreatment takes precedence - once retreated, always in retreated category
        if row.get("has_been_retreated", False):
            return "retreated"
            
        # Check discontinuation - once discontinued, always in a discontinued category
        if row.get("has_been_discontinued", False):
            disc_type = row.get("discontinuation_type", "") or ""
            disc_type = disc_type.lower() if disc_type else ""
            
            # Map to cumulative state categories
            if "stable_max_interval" in disc_type:
                return "discontinued_planned"  # Good outcome
            elif "random_administrative" in disc_type:
                return "discontinued_administrative"
            elif "course_complete_but_not_renewed" in disc_type:
                return "discontinued_duration"
            elif "premature" in disc_type:
                return "discontinued_premature"
            elif "poor_outcome" in disc_type:
                return "discontinued_poor_outcome"
            else:
                return "discontinued_other"
                
        # Otherwise, patient is still active (never discontinued or retreated)
        return "active"
    
    # Add cumulative state column
    visits_df["cumulative_state"] = visits_df.apply(determine_cumulative_state, axis=1)
    
    # Sort visits by patient and date
    visits_df = visits_df.sort_values(["patient_id", "date"])
    
    # Debug: Print state distribution
    print("\nCumulative state distribution in visits:")
    print(visits_df["cumulative_state"].value_counts())
    
    # Create timeline showing cumulative states at each month
    def generate_cumulative_timeline(patient_id, patient_visits):
        """Generate cumulative state for all months for a patient"""
        visits_by_month = patient_visits.sort_values("month_int")
        
        timeline = pd.DataFrame({
            "month": range(duration_months + 1),
            "patient_id": patient_id,
            "cumulative_state": None
        })
        
        # Get actual visit months and states
        visit_months = visits_by_month["month_int"].tolist()
        visit_states = visits_by_month["cumulative_state"].tolist()
        
        # Fill in cumulative states
        last_state = "active"  # Default starting state
        
        for i, month in enumerate(timeline["month"]):
            # Find the latest visit state at or before this month
            latest_idx = -1
            for j, visit_month in enumerate(visit_months):
                if visit_month <= month:
                    latest_idx = j
                else:
                    break
            
            # Use the latest cumulative state
            if latest_idx >= 0:
                last_state = visit_states[latest_idx]
            
            timeline.loc[i, "cumulative_state"] = last_state
        
        return timeline
    
    # Generate timeline for each patient
    all_timelines = []
    
    for patient_id, patient_visits in visits_df.groupby("patient_id"):
        patient_timeline = generate_cumulative_timeline(patient_id, patient_visits)
        all_timelines.append(patient_timeline)
    
    # Combine all patient timelines
    patient_timelines = pd.concat(all_timelines, ignore_index=True)
    
    # Count patients by cumulative state and month
    state_counts = patient_timelines.groupby(["month", "cumulative_state"]).size().reset_index(name="count")
    
    # Verify conservation
    month_totals = state_counts.groupby("month")["count"].sum()
    for month, total in month_totals.items():
        if total != total_patients:
            print(f"WARNING: Month {month} has {total} patients, expected {total_patients}")
    
    # Pivot to get states as columns
    pivot_df = state_counts.pivot(index="month", columns="cumulative_state", values="count").fillna(0)
    
    # Define state categories in order
    state_categories = [
        "active",                        # Never discontinued
        "retreated",                     # Has been retreated at least once
        "discontinued_planned",          # Planned discontinuation (good outcome)
        "discontinued_administrative",   # Administrative discontinuation
        "discontinued_duration",         # Treatment duration complete
        "discontinued_premature",        # Premature discontinuation
        "discontinued_poor_outcome",     # Poor visual outcome
        "discontinued_other"            # Other/unclear discontinuation
    ]
    
    # Add missing categories
    for state in state_categories:
        if state not in pivot_df.columns:
            pivot_df[state] = 0
    
    # Reorder columns
    pivot_df = pivot_df[state_categories]
    
    # Reset index
    state_counts_df = pivot_df.reset_index()
    
    print(f"\nPrepared cumulative data for {len(state_counts_df)} months")
    print(f"State categories: {state_categories}")
    
    return state_counts_df, state_categories

def create_cumulative_streamgraph(state_counts_df, state_categories, metadata_df, stats_df):
    """Create an interactive cumulative streamgraph using Plotly."""
    
    # Use colors from central color system
    state_colors = {
        "active": COLORS['active'],  # Dark green
        "retreated": COLORS['recommencing'],  # Medium green (they're back in treatment)
        "discontinued_planned": COLORS['untreated_remission'],  # Amber (good outcome)
        "discontinued_administrative": COLORS['not_booked'],  # Light red
        "discontinued_duration": COLORS['not_renewed'],  # Medium red
        "discontinued_premature": COLORS['premature_discontinuation'],  # Dark red
        "discontinued_poor_outcome": COLORS['stopped_poor_outcome'],  # Gray
        "discontinued_other": COLORS['discontinued_without_reason']  # Very dark red
    }
    
    # Create the figure
    fig = go.Figure()
    
    # Add traces for each state
    for state in state_categories:
        if state in state_counts_df.columns:
            # Get clinical label
            clinical_labels = {
                "active": "Active (never discontinued)",
                "retreated": "Retreated",
                "discontinued_planned": "Discontinued - planned",
                "discontinued_administrative": "Discontinued - administrative",
                "discontinued_duration": "Discontinued - duration",
                "discontinued_premature": "Discontinued - premature",
                "discontinued_poor_outcome": "Discontinued - poor outcome",
                "discontinued_other": "Discontinued - other"
            }
            
            label = clinical_labels.get(state, state.replace("_", " ").title())
            
            fig.add_trace(go.Scatter(
                x=state_counts_df["month"],
                y=state_counts_df[state],
                name=label,
                mode='lines',
                line=dict(width=0.5, color=state_colors.get(state, "#999999")),
                fillcolor=state_colors.get(state, "#999999"),
                stackgroup='one',
                groupnorm='',  # Don't normalize
                hovertemplate=(
                    f'<b>{label}</b><br>' +
                    'Month: %{x}<br>' +
                    'Patients: %{y}<br>' +
                    '<extra></extra>'
                )
            ))
    
    # Get metadata
    total_patients = metadata_df["patients"].iloc[0]
    duration_years = metadata_df["duration_years"].iloc[0]
    
    # Update layout
    fig.update_layout(
        title={
            'text': "Cumulative Patient Experience Over Time",
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 20}
        },
        xaxis=dict(
            title="Months from Simulation Start",
            range=[0, duration_years * 12],
            showgrid=True,
            gridcolor='rgba(128,128,128,0.2)',
        ),
        yaxis=dict(
            title="Number of Patients",
            range=[0, total_patients],
            showgrid=True,
            gridcolor='rgba(128,128,128,0.2)',
        ),
        plot_bgcolor='white',
        paper_bgcolor='white',
        hovermode='x unified',
        showlegend=True,
        legend=dict(
            orientation="v",
            yanchor="middle",
            y=0.5,
            xanchor="left",
            x=1.02,
            bgcolor="rgba(255, 255, 255, 0.8)",
            bordercolor="rgba(0, 0, 0, 0.2)",
            borderwidth=1
        ),
        margin=dict(l=50, r=200, t=80, b=50),
        height=600
    )
    
    # Add annotation with key stats
    retreatment_count = stats_df.get("retreatments", [0]).iloc[0] if "retreatments" in stats_df.columns else 0
    discontinuation_count = stats_df.get("total_discontinuations", [0]).iloc[0] if "total_discontinuations" in stats_df.columns else 0
    
    annotation_text = (
        f"Total Patients: {total_patients}<br>"
        f"Ever Discontinued: {discontinuation_count}<br>"
        f"Ever Retreated: {retreatment_count}"
    )
    
    fig.add_annotation(
        text=annotation_text,
        xref="paper", yref="paper",
        x=0.02, y=0.98,
        showarrow=False,
        bgcolor="rgba(255, 255, 255, 0.8)",
        bordercolor="rgba(0, 0, 0, 0.2)",
        borderwidth=1,
        font=dict(size=12),
        align="left"
    )
    
    return fig

def main():
    parser = argparse.ArgumentParser(description="Create cumulative patient state streamgraph")
    parser.add_argument("--input", "-i", required=True, 
                        help="Base path for Parquet files (without extension)")
    parser.add_argument("--output", "-o", default=None,
                        help="Output HTML file path")
    
    args = parser.parse_args()
    
    # Load data
    visits_df, metadata_df, stats_df = load_simulation_data(args.input)
    
    # Prepare data
    state_counts_df, state_categories = prepare_cumulative_state_data(visits_df, metadata_df)
    
    # Create visualization
    fig = create_cumulative_streamgraph(state_counts_df, state_categories, metadata_df, stats_df)
    
    # Save output
    if args.output:
        output_path = args.output
    else:
        output_path = f"{args.input}_cumulative_streamgraph.html"
    
    fig.write_html(output_path)
    print(f"\nCumulative streamgraph saved to: {output_path}")

if __name__ == "__main__":
    main()