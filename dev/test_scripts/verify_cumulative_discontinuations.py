#!/usr/bin/env python3
"""
Verification script to check if discontinued patients remain in their discontinued state
across all future time points unless explicitly retreated.
"""

import argparse
import pandas as pd
import os
import sys
from pathlib import Path

def verify_cumulative_discontinuations(input_path):
    """
    Verify that discontinued states are cumulative in the patient data.
    A patient should remain in their discontinued state until/unless they are retreated.
    """
    print(f"\nVerifying cumulative discontinuation tracking in: {input_path}")
    
    # Load the visits dataset
    if input_path.endswith('.parquet'):
        visits_file = input_path
    else:
        # Try different naming conventions
        visits_file = os.path.join(input_path, "visits.parquet")
        if not os.path.exists(visits_file):
            visits_file = f"{input_path}_visits.parquet"
        
    if not os.path.exists(visits_file):
        print(f"ERROR: Visits file not found at {visits_file}")
        return False
    
    visits_df = pd.read_parquet(visits_file)
    print(f"Loaded {len(visits_df)} visits for {visits_df['patient_id'].nunique()} patients")
    
    # Find all patients who were discontinued at any point
    # First look for standard discontinuation flags
    discontinued_markers = [col for col in visits_df.columns if 'discontinued' in col]
    
    # Check if we have an is_discontinuation column (without the 'visit' suffix)
    if 'is_discontinuation' in visits_df.columns:
        print("Found 'is_discontinuation' column")
        discontinued_mask = visits_df['is_discontinuation'] == True
    elif discontinued_markers:
        print(f"Found discontinuation markers: {discontinued_markers}")
        # Combine all discontinuation markers
        discontinued_mask = False
        for marker in discontinued_markers:
            discontinued_mask = discontinued_mask | (visits_df[marker] == True)
    elif 'state' in visits_df.columns:
        print("Falling back to 'state' column for discontinuation detection")
        discontinued_mask = visits_df['state'].str.contains('discontinued', na=False)
    else:
        print("WARNING: No standard discontinuation markers found in the data")
        print(f"Available columns: {list(visits_df.columns)}")
        print("ERROR: Cannot identify discontinued patients - no suitable columns found")
        return False
    
    discontinued_visits = visits_df[discontinued_mask]
    discontinued_patients = discontinued_visits['patient_id'].unique()
    
    print(f"Found {len(discontinued_patients)} patients with at least one discontinuation visit")
    
    # Analyze each discontinued patient's timeline
    errors_found = False
    
    for patient_id in discontinued_patients:
        print(f"\nAnalyzing Patient {patient_id}:")
        
        # Get all visits for this patient, sorted by date
        patient_visits = visits_df[visits_df['patient_id'] == patient_id].sort_values('date')
        
        # Find the first discontinuation visit
        first_discontinuation_idx = None
        discontinuation_date = None
        
        # Try to find the first discontinuation using specific markers if available
        for marker in discontinued_markers:
            if any(patient_visits[marker]):
                first_marker_idx = patient_visits[marker].idxmax()
                if first_discontinuation_idx is None or first_marker_idx < first_discontinuation_idx:
                    first_discontinuation_idx = first_marker_idx
                    discontinuation_date = patient_visits.loc[first_discontinuation_idx, 'date']
        
        # Fallback to 'state' column if no specific markers were found
        if first_discontinuation_idx is None and 'state' in patient_visits.columns:
            # Find first visit with state containing 'discontinued'
            discontinued_visits = patient_visits[patient_visits['state'].str.contains('discontinued', na=False)]
            if not discontinued_visits.empty:
                first_discontinuation_idx = discontinued_visits.index[0]
                discontinuation_date = discontinued_visits.iloc[0]['date']
        
        if discontinuation_date is None:
            print(f"WARNING: Could not determine first discontinuation date for Patient {patient_id}")
            continue
        
        print(f"  First discontinuation date: {discontinuation_date}")
        
        # Find any retreatment visits after discontinuation
        retreatment_after_discontinuation = False
        retreatment_date = None
        
        # Check for retreatment using is_retreatment_visit or state column
        later_visits = patient_visits[patient_visits['date'] > discontinuation_date]
        
        if 'is_retreatment_visit' in patient_visits.columns:
            later_retreatments = later_visits[later_visits['is_retreatment_visit'] == True]
        elif 'state' in patient_visits.columns:
            # Look for 'retreated' state
            later_retreatments = later_visits[later_visits['state'] == 'retreated']
        else:
            later_retreatments = pd.DataFrame()
        
        if len(later_retreatments) > 0:
            retreatment_after_discontinuation = True
            retreatment_date = later_retreatments.iloc[0]['date']
            print(f"  Retreated after discontinuation on: {retreatment_date}")
        else:
            print("  No retreatment after discontinuation")
        
        # Check if the patient remains in a discontinued state from discontinuation
        # until retreatment (if any) or the end of the simulation
        
        # For verification, we'll check the state field if it exists
        if 'state' in patient_visits.columns:
            later_visits = patient_visits[patient_visits['date'] > discontinuation_date]
            
            if retreatment_after_discontinuation and retreatment_date is not None:
                # Check visits between discontinuation and retreatment
                between_disc_and_retreat = later_visits[later_visits['date'] < retreatment_date]
                
                # All these visits should have a discontinued state
                non_discontinued = between_disc_and_retreat[~between_disc_and_retreat['state'].str.contains('discontinued')]
                
                if len(non_discontinued) > 0:
                    print(f"  ERROR: Found {len(non_discontinued)} visits between discontinuation and retreatment without discontinued state:")
                    print(non_discontinued[['date', 'state']].head())
                    errors_found = True
                else:
                    print(f"  VERIFIED: Patient remained in discontinued state from discontinuation until retreatment ({len(between_disc_and_retreat)} visits)")
                
                # Check visits after retreatment - they should be "retreated" state
                after_retreat = later_visits[later_visits['date'] >= retreatment_date]
                non_retreated = after_retreat[after_retreat['state'] != 'retreated']
                
                if len(non_retreated) > 0:
                    print(f"  ERROR: Found {len(non_retreated)} visits after retreatment without retreated state:")
                    print(non_retreated[['date', 'state']].head())
                    errors_found = True
                else:
                    print(f"  VERIFIED: Patient correctly marked as retreated after retreatment ({len(after_retreat)} visits)")
                
            else:
                # No retreatment - all visits after discontinuation should have discontinued state
                non_discontinued = later_visits[~later_visits['state'].str.contains('discontinued')]
                
                if len(non_discontinued) > 0:
                    print(f"  ERROR: Found {len(non_discontinued)} visits after discontinuation without discontinued state:")
                    print(non_discontinued[['date', 'state']].head())
                    errors_found = True
                else:
                    print(f"  VERIFIED: Patient remained in discontinued state for all {len(later_visits)} visits after discontinuation")
    
    if errors_found:
        print("\nVERIFICATION FAILED: Errors were found in the cumulative discontinuation tracking")
        return False
    else:
        print("\nVERIFICATION PASSED: All discontinued patients correctly maintained their states")
        return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Verify cumulative discontinuation tracking in patient data')
    parser.add_argument('--input', required=True, help='Path to the simulation results directory')
    
    args = parser.parse_args()
    
    success = verify_cumulative_discontinuations(args.input)
    
    if success:
        sys.exit(0)
    else:
        sys.exit(1)