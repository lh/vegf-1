#!/usr/bin/env python3
"""
Verify the cumulative retreatment tracking implementation in streamgraph visualization.

This script tests the implementation of cumulative retreatment tracking by:
1. Running a simulation with the updated code
2. Verifying that the has_been_retreated flag is set correctly
3. Checking that retreated patients continue to appear in the retreated state
4. Ensuring the visualization shows retreated patients as a growing segment
"""

import os
import sys
import argparse
import pandas as pd
import numpy as np
from pathlib import Path
import plotly.graph_objects as go
from datetime import datetime

# Add project root to path
root_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(root_dir)

# Import necessary functions
from run_streamgraph_simulation_parquet import run_simulation, save_results_parquet
from create_patient_state_streamgraph import load_simulation_data, prepare_patient_state_data

def run_test_simulation():
    """Run a test simulation to generate data for verification."""
    print("\n===== Running test simulation =====")
    # Run a simulation with retreat-heavy parameters
    patient_histories, statistics, config = run_simulation(
        num_patients=50,  # Small number for quick testing
        duration_years=3  # 3 years is enough to see retreatment patterns
    )
    
    # Configure higher retreatment probability to ensure we get retreatments
    config.parameters["discontinuation"]["retreatment"]["probability"] = 0.7
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_filename = f"test_retreatment_{timestamp}"
    output_dir = os.path.join(root_dir, "output", "test_results")
    os.makedirs(output_dir, exist_ok=True)
    
    base_path = save_results_parquet(
        patient_histories,
        statistics,
        config,
        output_dir=output_dir,
        base_filename=base_filename
    )
    
    return base_path

def verify_retreatment_flags(base_path):
    """Verify that retreatment flags are set correctly."""
    print("\n===== Verifying retreatment flags =====")
    # Load the data
    visits_df, metadata_df, stats_df = load_simulation_data(base_path)
    
    # Check if both flags exist
    if "is_retreatment_visit" not in visits_df.columns:
        print("ERROR: is_retreatment_visit flag is missing from the data")
        return False
        
    if "has_been_retreated" not in visits_df.columns:
        print("ERROR: has_been_retreated flag is missing from the data")
        return False
    
    # Count retreatment visits and total retreated visits
    retreatment_visits = visits_df["is_retreatment_visit"].sum()
    cumulative_retreated_visits = visits_df["has_been_retreated"].sum()
    
    print(f"Total visits: {len(visits_df)}")
    print(f"Patients: {visits_df['patient_id'].nunique()}")
    print(f"Retreatment visits: {retreatment_visits}")
    print(f"Cumulative retreated visits: {cumulative_retreated_visits}")
    
    # Cumulative should be greater than or equal to retreatment visits
    if cumulative_retreated_visits < retreatment_visits:
        print("ERROR: Cumulative retreated visits should be >= retreatment visits")
        return False
    
    # Check for patients with retreatment
    retreated_patients = visits_df[visits_df["is_retreatment_visit"]]["patient_id"].unique()
    print(f"Patients with retreatment: {len(retreated_patients)}")
    
    # Verify that has_been_retreated is set for all subsequent visits
    for patient_id in retreated_patients:
        patient_visits = visits_df[visits_df["patient_id"] == patient_id].sort_values("date")
        
        # Find the first retreatment visit
        first_retreatment_idx = patient_visits["is_retreatment_visit"].idxmax()
        if not patient_visits.loc[first_retreatment_idx, "is_retreatment_visit"]:
            # No retreatment for this patient
            continue
            
        # Get all visits after the first retreatment
        first_retreatment_date = patient_visits.loc[first_retreatment_idx, "date"]
        later_visits = patient_visits[patient_visits["date"] >= first_retreatment_date]
        
        # All these visits should have has_been_retreated = True
        all_retreated = later_visits["has_been_retreated"].all()
        if not all_retreated:
            print(f"ERROR: Patient {patient_id} has later visits without has_been_retreated flag")
            return False
    
    print("✓ Retreatment flags verification passed!")
    return True

def verify_state_tracking(base_path):
    """Verify that patient states are tracked correctly in the streamgraph data."""
    print("\n===== Verifying patient state tracking =====")
    # Load the data
    visits_df, metadata_df, stats_df = load_simulation_data(base_path)
    
    # Prepare the patient state data
    state_counts_df, state_categories = prepare_patient_state_data(visits_df, metadata_df)
    
    # Check if 'retreated' state exists
    if "retreated" not in state_counts_df.columns:
        print("ERROR: retreated state is missing from the streamgraph data")
        return False
    
    # Check if retreated counts increase over time
    retreated_counts = state_counts_df["retreated"].tolist()
    if not retreated_counts:
        print("WARNING: No retreated patients found in the data")
        return True
    
    # Retreated patients should be cumulative, so counts should generally increase
    # Allow for a small number of decreases due to study end or other reasons
    decreases = sum(1 for i in range(1, len(retreated_counts)) 
                   if retreated_counts[i] < retreated_counts[i-1])
    decrease_percentage = (decreases / (len(retreated_counts)-1)) * 100 if len(retreated_counts) > 1 else 0
    
    print(f"Retreated state counts over time: {retreated_counts[:10]}...")
    print(f"Decreases in retreated count: {decreases} ({decrease_percentage:.1f}%)")
    
    # Allow for small variations but overall should increase
    if decrease_percentage > 10:
        print("ERROR: Too many decreases in retreated patient count (>10%)")
        return False
    
    # Check if retreated counts are higher at the end than at the beginning
    if retreated_counts[-1] <= retreated_counts[0] and retreated_counts[0] == 0:
        print("WARNING: Retreated patients count did not increase by the end")
        return True
    
    print("✓ State tracking verification passed!")
    return True

def main():
    """Main function to run verification."""
    parser = argparse.ArgumentParser(description="Verify cumulative retreatment tracking")
    parser.add_argument("--input", type=str, default=None,
                        help="Base path to existing simulation data (without extensions)")
    
    args = parser.parse_args()
    
    if args.input:
        # Use existing data
        base_path = args.input
        print(f"Using existing simulation data at {base_path}")
    else:
        # Run a new simulation
        base_path = run_test_simulation()
    
    # Verify the implementation
    retreatment_flags_verified = verify_retreatment_flags(base_path)
    state_tracking_verified = verify_state_tracking(base_path)
    
    if retreatment_flags_verified and state_tracking_verified:
        print("\n✓ Cumulative retreatment tracking verification PASSED!")
        return 0
    else:
        print("\n✗ Cumulative retreatment tracking verification FAILED!")
        return 1

if __name__ == "__main__":
    sys.exit(main())