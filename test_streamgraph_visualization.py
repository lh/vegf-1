#!/usr/bin/env python3
"""
Test script for the enhanced streamgraph visualization.

This script tests the streamgraph visualization on simulation results stored in Parquet format,
verifying that the visualization properly stacks different patient states.
"""

import os
import sys
import json
import argparse
import pandas as pd
from datetime import datetime
from pathlib import Path

# Add project root to path
root_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(root_dir)

# Import visualization functions
from create_patient_state_streamgraph import (
    load_simulation_data,
    prepare_patient_state_data,
    create_streamgraph,
    save_visualization
)

def test_parquet_visualization(input_base_path):
    """
    Test the streamgraph visualization using data from Parquet files.
    
    Parameters
    ----------
    input_base_path : str
        Base path to the simulation results (without _visits, etc. extensions)
        
    Returns
    -------
    dict
        Visualization output paths
    """
    print(f"\nTesting streamgraph visualization with Parquet data from: {input_base_path}")
    
    # Load data from Parquet files
    visits_df, metadata_df, stats_df = load_simulation_data(input_base_path)
    
    # Verify the data
    print("\nData verification:")
    print(f"  - Total patients: {metadata_df['patients'].iloc[0]}")
    print(f"  - Duration (years): {metadata_df['duration_years'].iloc[0]}")
    print(f"  - Simulation type: {metadata_df['simulation_type'].iloc[0]}")
    print(f"  - Total visits: {len(visits_df)}")
    print(f"  - Unique patients: {visits_df['patient_id'].nunique()}")
    
    # Check for discontinuation visits
    disc_visits = visits_df[visits_df['is_discontinuation_visit'] == True]
    print(f"  - Discontinuation visits: {len(disc_visits)}")
    
    # Count the different types of discontinuation
    if len(disc_visits) > 0 and 'discontinuation_type' in disc_visits.columns:
        disc_types = disc_visits['discontinuation_type'].value_counts()
        print("\nDiscontinuation types:")
        for dtype, count in disc_types.items():
            print(f"  - {dtype}: {count}")
    
    # Prepare data for visualization
    print("\nPreparing patient state data...")
    state_counts_df, state_categories = prepare_patient_state_data(visits_df, metadata_df)
    
    # Display the state categories
    print("\nState categories found in data:")
    for state in state_categories:
        if state in state_counts_df.columns and state_counts_df[state].max() > 0:
            max_count = int(state_counts_df[state].max())
            print(f"  - {state}: max {max_count} patients")
    
    # Create the visualization
    print("\nCreating streamgraph...")
    fig = create_streamgraph(state_counts_df, state_categories, metadata_df, stats_df)
    
    # Save visualization to test directory
    print("\nSaving visualization...")
    output_dir = os.path.join(root_dir, "output", "test_visualizations")
    os.makedirs(output_dir, exist_ok=True)
    
    # Use base filename for the output
    base_filename = os.path.basename(input_base_path)
    output_paths = save_visualization(fig, input_base_path, output_dir=output_dir)
    
    return output_paths

def test_json_visualization(json_filepath):
    """
    Test the streamgraph visualization on the simulation results from a JSON file.
    
    Parameters
    ----------
    json_filepath : str
        Path to simulation results JSON file
        
    Returns
    -------
    dict
        Visualization output paths
    """
    # Load simulation results from JSON
    try:
        print(f"\nLoading simulation results from JSON: {json_filepath}")
        with open(json_filepath, "r") as f:
            results = json.load(f)
    except Exception as e:
        print(f"Error loading simulation results: {e}")
        sys.exit(1)
    
    # Convert results to DataFrames
    import pandas as pd
    
    # Extract configuration
    config = results.get("config", {})
    
    # Create metadata DataFrame
    metadata = {
        "simulation_type": results.get("simulation_type", "Unknown"),
        "patients": config.get("patient_count", 0),
        "duration_years": config.get("duration_years", 0),
        "start_date": config.get("start_date", datetime.now().strftime("%Y-%m-%d")),
        "discontinuation_enabled": True
    }
    metadata_df = pd.DataFrame([metadata])
    
    # Create statistics DataFrame
    stats = results.get("statistics", {})
    stats_df = pd.DataFrame([stats])
    
    # Process patient histories
    patient_histories = results.get("patient_histories", {})
    visit_records = []
    
    print(f"Processing {len(patient_histories)} patient histories...")
    
    for patient_id, visits in patient_histories.items():
        for visit in visits:
            # Add patient_id to each visit
            visit["patient_id"] = patient_id
            # Append to records
            visit_records.append(visit)
    
    # Create visits DataFrame
    visits_df = pd.DataFrame(visit_records)
    print(f"Created DataFrame with {len(visits_df)} visit records")
    
    # Check if we have date column
    if "date" in visits_df.columns:
        if pd.api.types.is_string_dtype(visits_df["date"]):
            visits_df["date"] = pd.to_datetime(visits_df["date"])
    
    # Save data to temporary files
    output_dir = os.path.join(root_dir, "output", "temp")
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_path = os.path.join(output_dir, f"streamgraph_test_{timestamp}")
    
    # Save to Parquet for future use
    visits_df.to_parquet(f"{base_path}_visits.parquet")
    metadata_df.to_parquet(f"{base_path}_metadata.parquet")
    stats_df.to_parquet(f"{base_path}_stats.parquet")
    
    print(f"Saved data to Parquet files with base path: {base_path}")
    
    # Prepare data for visualization
    print("\nPreparing patient state data...")
    state_counts_df, state_categories = prepare_patient_state_data(visits_df, metadata_df)
    
    # Create the visualization
    print("\nCreating streamgraph...")
    fig = create_streamgraph(state_counts_df, state_categories, metadata_df, stats_df)
    
    # Save visualization
    print("\nSaving visualization...")
    output_paths = save_visualization(fig, base_path, 
                                     output_dir=os.path.join(root_dir, "output", "test_visualizations"))
    
    return output_paths, base_path

def main():
    parser = argparse.ArgumentParser(description="Test the streamgraph visualization with proper stacking")
    parser.add_argument("--input", "-i", type=str, required=True,
                        help="Path to simulation results (either JSON file or base path for Parquet files)")
    args = parser.parse_args()
    
    # Determine if input is JSON or Parquet
    input_path = args.input
    
    if input_path.endswith(".json"):
        # JSON path
        output_paths, base_path = test_json_visualization(input_path)
        print(f"\nCreated temporary Parquet files at: {base_path}")
    else:
        # Assume Parquet files
        output_paths = test_parquet_visualization(input_path)
    
    # Print output paths
    print("\nVisualization completed successfully.")
    print(f"Interactive HTML: {output_paths['html']}")
    print(f"Static PNG: {output_paths['png']}")
    print("\nThe visualization should now properly stack all patient states.")

if __name__ == "__main__":
    main()