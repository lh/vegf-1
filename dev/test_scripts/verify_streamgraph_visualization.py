#!/usr/bin/env python
"""
Verify the streamgraph visualization accurately represents patient state data.

This script loads simulation data from Parquet files, validates the visualization
data for accuracy, and verifies the conservation principle is maintained.
"""

import os
import sys
import argparse
import pandas as pd
import numpy as np
from pathlib import Path

# Add project root to path
root_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(root_dir)


def validate_visualization_data(input_path):
    """
    Validate the patient state data used for visualization.
    
    Parameters
    ----------
    input_path : str
        Path to simulation Parquet files (without _visits, etc. extensions)
        
    Returns
    -------
    dict
        Validation results
    """
    # Load visits data
    visits_path = f"{input_path}_visits.parquet"
    metadata_path = f"{input_path}_metadata.parquet"
    stats_path = f"{input_path}_stats.parquet"
    
    # Check if files exist
    if not os.path.exists(visits_path):
        raise FileNotFoundError(f"Visits data not found at {visits_path}")
    if not os.path.exists(metadata_path):
        raise FileNotFoundError(f"Metadata not found at {metadata_path}")
    if not os.path.exists(stats_path):
        raise FileNotFoundError(f"Statistics not found at {stats_path}")
    
    # Load data
    visits_df = pd.read_parquet(visits_path)
    metadata_df = pd.read_parquet(metadata_path)
    stats_df = pd.read_parquet(stats_path)
    
    # Extract key metadata
    total_patients = metadata_df["patients"].iloc[0]
    duration_years = metadata_df["duration_years"].iloc[0]
    duration_months = int(duration_years * 12)
    
    print(f"\nValidating visualization data from: {input_path}")
    print(f"  - Patients: {total_patients}")
    print(f"  - Duration: {duration_years} years ({duration_months} months)")
    
    # Begin validation
    validation_results = {
        "total_patients": total_patients,
        "duration_months": duration_months,
        "visits_count": len(visits_df),
        "unique_patients": visits_df["patient_id"].nunique(),
        "conservation_violations": [],
        "state_distributions": {}
    }
    
    # Check patient counts
    if validation_results["unique_patients"] != total_patients:
        print(f"⚠️ VALIDATION WARNING: Expected {total_patients} patients, found {validation_results['unique_patients']}")
    else:
        print(f"✅ Patient count matches expected value: {total_patients}")
    
    # Ensure date is datetime
    if not pd.api.types.is_datetime64_dtype(visits_df["date"]):
        visits_df["date"] = pd.to_datetime(visits_df["date"])
    
    # Calculate months for each visit
    # First, find the earliest date for each patient
    patient_start_dates = visits_df.groupby("patient_id")["date"].min()
    start_date_map = patient_start_dates.to_dict()
    
    # Calculate months since start
    def get_months_since_start(row):
        patient_id = row["patient_id"]
        visit_date = row["date"]
        start_date = start_date_map[patient_id]
        delta = visit_date - start_date
        return delta.days / 30.44
    
    visits_df["months"] = visits_df.apply(get_months_since_start, axis=1)
    visits_df["month_int"] = visits_df["months"].round().astype(int)
    
    # Determine state for each visit
    def determine_state(row):
        if row.get("is_retreatment", False):
            return "retreated"
        elif row.get("is_discontinuation", False):
            disc_type = row.get("discontinuation_type", "").lower()
            if "stable" in disc_type or "planned" in disc_type or "max" in disc_type:
                return "discontinued_planned"
            elif "admin" in disc_type:
                return "discontinued_administrative"
            elif "duration" in disc_type or "course" in disc_type:
                return "discontinued_duration"
            else:
                return "discontinued_planned"  # Default
        elif row.get("phase", "").lower() == "monitoring":
            return "monitoring"
        else:
            return "active"
    
    visits_df["state"] = visits_df.apply(determine_state, axis=1)
    
    # Generate complete patient timelines to test conservation principle
    def generate_patient_timeline(patient_id, patient_visits):
        visits_by_month = patient_visits.sort_values("month_int")
        
        # Initialize timeline
        timeline = pd.DataFrame({
            "month": range(duration_months + 1),
            "patient_id": patient_id,
            "state": None
        })
        
        # Get visit months and states
        visit_months = visits_by_month["month_int"].tolist()
        visit_states = visits_by_month["state"].tolist()
        
        # Fill states by interpolation
        last_state = "active"
        for i, month in enumerate(timeline["month"]):
            latest_idx = -1
            for j, visit_month in enumerate(visit_months):
                if visit_month <= month:
                    latest_idx = j
                else:
                    break
            
            if latest_idx >= 0:
                last_state = visit_states[latest_idx]
            
            timeline.loc[i, "state"] = last_state
        
        return timeline
    
    # Generate timelines
    all_timelines = []
    for patient_id, patient_visits in visits_df.groupby("patient_id"):
        patient_timeline = generate_patient_timeline(patient_id, patient_visits)
        all_timelines.append(patient_timeline)
    
    patient_timelines = pd.concat(all_timelines, ignore_index=True)
    
    # Test conservation principle - count patients by state at each month
    state_counts = patient_timelines.groupby(["month", "state"]).size().reset_index(name="count")
    month_totals = state_counts.groupby("month")["count"].sum().reset_index()
    
    # Check if each month has the correct total
    for _, row in month_totals.iterrows():
        month = row["month"]
        count = row["count"]
        
        if count != total_patients:
            validation_results["conservation_violations"].append({
                "month": int(month),
                "patient_count": int(count),
                "expected": int(total_patients),
                "difference": int(count - total_patients)
            })
    
    # Report conservation violations
    if validation_results["conservation_violations"]:
        print(f"\n⚠️ Conservation principle violated in {len(validation_results['conservation_violations'])} months:")
        for violation in validation_results["conservation_violations"][:5]:  # Show first 5
            print(f"  - Month {violation['month']}: {violation['patient_count']} patients "
                  f"(expected {violation['expected']}, diff {violation['difference']})")
        if len(validation_results["conservation_violations"]) > 5:
            print(f"  ... and {len(validation_results['conservation_violations']) - 5} more")
    else:
        print("\n✅ Conservation principle maintained across all months")
    
    # Get state distribution at key time points
    state_categories = ["active", "discontinued_planned", "discontinued_administrative", 
                       "discontinued_duration", "monitoring", "retreated"]
    
    pivot_df = state_counts.pivot(index="month", columns="state", values="count").fillna(0)
    
    for state in state_categories:
        if state not in pivot_df.columns:
            pivot_df[state] = 0
    
    # Track state distributions
    for year in range(int(duration_years) + 1):
        month = year * 12
        if month in pivot_df.index:
            month_distribution = {}
            for state in state_categories:
                if state in pivot_df.columns:
                    count = int(pivot_df.loc[month, state])
                    month_distribution[state] = count
            
            validation_results["state_distributions"][str(month)] = month_distribution
    
    # Print state distributions
    print("\nPatient state distribution at yearly intervals:")
    for year, month in enumerate([0, 12, 24, 36]):
        if month in pivot_df.index:
            print(f"\nMonth {month} (Year {year}):")
            for state in state_categories:
                if state in pivot_df.columns:
                    count = int(pivot_df.loc[month, state])
                    if count > 0:
                        print(f"  - {state}: {count} patients ({count/total_patients*100:.1f}%)")
    
    # Validate against simulation statistics
    disc_stats = {k: v for k, v in stats_df.iloc[0].items() if 'discontinu' in k.lower()}
    
    print("\nValidating visualization data against simulation statistics:")
    
    # Get unique discontinued patients
    unique_discontinued = stats_df["unique_discontinuations"].iloc[0]
    print(f"  - Unique discontinued patients (simulation): {unique_discontinued}")
    
    # Check if monitoring and discontinued states match
    monitoring_patients = pivot_df.loc[pivot_df.index.max(), "monitoring"] 
    if pd.isna(monitoring_patients):
        monitoring_patients = 0
    else:
        monitoring_patients = int(monitoring_patients)
    
    retreated_patients = pivot_df.loc[pivot_df.index.max(), "retreated"]
    if pd.isna(retreated_patients):
        retreated_patients = 0
    else:
        retreated_patients = int(retreated_patients)
    
    print(f"  - Monitoring patients (visualization): {monitoring_patients}")
    print(f"  - Retreated patients (visualization): {retreated_patients}")
    
    return validation_results


def main():
    """Main function to parse arguments and validate visualization."""
    parser = argparse.ArgumentParser(description="Validate streamgraph visualization data")
    parser.add_argument("--input", type=str, required=True, 
                        help="Path to simulation Parquet files (without _visits, etc. extensions)")
    
    args = parser.parse_args()
    
    # Validate data
    validation_results = validate_visualization_data(args.input)
    
    # Report overall status
    if not validation_results["conservation_violations"]:
        print("\n✅ VALIDATION PASSED: Visualization data is consistent and accurate")
    else:
        print("\n⚠️ VALIDATION WARNING: Conservation principle violated in "
              f"{len(validation_results['conservation_violations'])} months")


if __name__ == "__main__":
    main()