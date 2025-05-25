#!/usr/bin/env python3
"""
Debug script to check if Parquet data has the phase field needed by visualization.
"""

import pandas as pd
import os
import sys

# Add project root to path
root_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(root_dir)

def main():
    """Check Parquet data structure."""
    # Find most recent Parquet files
    output_dir = os.path.join(root_dir, "output", "simulation_results")
    
    # List Parquet files
    parquet_files = [f for f in os.listdir(output_dir) if f.endswith("_visits.parquet")]
    
    if not parquet_files:
        print("No Parquet files found in", output_dir)
        return
    
    # Use the most recent file
    parquet_files.sort()
    latest_file = parquet_files[-1]
    visits_path = os.path.join(output_dir, latest_file)
    
    print(f"Loading visits data from: {visits_path}")
    
    # Load the data
    visits_df = pd.read_parquet(visits_path)
    
    print(f"\nDataFrame shape: {visits_df.shape}")
    print(f"Columns: {list(visits_df.columns)}")
    
    # Check for phase column
    if 'phase' in visits_df.columns:
        print("\n✓ 'phase' column exists")
        print(f"Unique phases: {visits_df['phase'].unique()}")
        print(f"Phase value counts:")
        print(visits_df['phase'].value_counts())
    else:
        print("\n✗ 'phase' column NOT found")
    
    # Check for discontinuation_type column
    if 'discontinuation_type' in visits_df.columns:
        print("\n✓ 'discontinuation_type' column exists")
        print(f"Unique types: {visits_df['discontinuation_type'].unique()}")
        print(f"Type value counts:")
        print(visits_df['discontinuation_type'].value_counts())
    else:
        print("\n✗ 'discontinuation_type' column NOT found")
    
    # Check for is_discontinuation_visit column
    if 'is_discontinuation_visit' in visits_df.columns:
        print("\n✓ 'is_discontinuation_visit' column exists")
        print(f"Discontinuation visits: {visits_df['is_discontinuation_visit'].sum()}")
    else:
        print("\n✗ 'is_discontinuation_visit' column NOT found")
    
    # Sample some discontinuation visits to see their structure
    if 'is_discontinuation_visit' in visits_df.columns:
        disc_visits = visits_df[visits_df['is_discontinuation_visit'] == True]
        if not disc_visits.empty:
            print("\nSample discontinuation visits:")
            # Show first 3 discontinuation visits
            for idx, row in disc_visits.head(3).iterrows():
                print(f"\nPatient: {row['patient_id']}")
                print(f"  Phase: {row.get('phase', 'N/A')}")
                print(f"  Discontinuation type: {row.get('discontinuation_type', 'N/A')}")
                print(f"  Date: {row.get('date', 'N/A')}")
                print(f"  Treatment status: {row.get('treatment_status', 'N/A')}")
    
    # Check if we need to infer phase from other fields
    print("\n\nChecking what fields we have to work with:")
    sample_row = visits_df.iloc[0]
    for col, val in sample_row.items():
        if not pd.isna(val):
            print(f"  {col}: {val} (type: {type(val).__name__})")

if __name__ == "__main__":
    main()