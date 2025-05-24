#!/usr/bin/env python3
"""
Test script to verify Visual Acuity data flow in Parquet files.
This helps diagnose why VA visualizations show "Empty VA data".
"""

import pandas as pd
import os
from glob import glob
import sys

def check_va_data():
    """Check if vision data exists in recent Parquet files."""
    
    # Find parquet files
    parquet_dir = os.path.join(os.path.dirname(__file__), "output", "parquet_results")
    
    if not os.path.exists(parquet_dir):
        print(f"ERROR: Parquet directory not found: {parquet_dir}")
        return
    
    # Get all visits parquet files
    visit_files = sorted(glob(os.path.join(parquet_dir, "*_visits.parquet")))
    
    if not visit_files:
        print(f"ERROR: No visit parquet files found in {parquet_dir}")
        return
    
    print(f"Found {len(visit_files)} visit files")
    
    # Check if we have a command line argument for specific file
    if len(sys.argv) > 1:
        target_file = sys.argv[1]
        # Find matching file
        matching = [f for f in visit_files if target_file in f]
        if matching:
            visit_files = [matching[0]]
            print(f"Checking requested file: {os.path.basename(matching[0])}\n")
        else:
            print(f"File pattern '{target_file}' not found, using latest")
            print(f"Checking latest file: {os.path.basename(visit_files[-1])}\n")
    else:
        print(f"Checking latest file: {os.path.basename(visit_files[-1])}\n")
    
    # Load the latest file
    try:
        visits_df = pd.read_parquet(visit_files[-1])
        print(f"✓ Successfully loaded visits DataFrame")
        print(f"  Shape: {visits_df.shape}")
        print(f"  Columns: {', '.join(visits_df.columns.tolist())}\n")
        
        # Check for vision column
        if 'vision' in visits_df.columns:
            print("✓ Vision column found!")
            
            # Analyze vision data
            non_null = visits_df['vision'].notna().sum()
            null_count = visits_df['vision'].isna().sum()
            
            print(f"\nVision Data Statistics:")
            print(f"  Total rows: {len(visits_df)}")
            print(f"  Non-null vision: {non_null} ({non_null/len(visits_df)*100:.1f}%)")
            print(f"  Null vision: {null_count} ({null_count/len(visits_df)*100:.1f}%)")
            
            if non_null > 0:
                print(f"  Range: {visits_df['vision'].min():.1f} to {visits_df['vision'].max():.1f}")
                print(f"  Mean: {visits_df['vision'].mean():.1f}")
                print(f"  Std: {visits_df['vision'].std():.1f}")
                
                # Show sample data
                print(f"\nSample vision data (first 10 non-null):")
                # Check which time column exists
                time_col = 'time' if 'time' in visits_df.columns else 'date'
                sample_cols = ['patient_id', time_col, 'vision', 'type']
                sample_cols = [col for col in sample_cols if col in visits_df.columns]
                sample = visits_df[sample_cols].dropna(subset=['vision']).head(10)
                print(sample.to_string(index=False))
                
                # Check if all values are the same (potential bug)
                unique_values = visits_df['vision'].dropna().nunique()
                print(f"\nUnique vision values: {unique_values}")
                if unique_values < 5:
                    print("⚠️  WARNING: Very few unique vision values - possible data generation issue")
                    print(f"Unique values: {sorted(visits_df['vision'].dropna().unique())}")
                    
            else:
                print("\n❌ ERROR: All vision values are null!")
                print("This explains why VA visualization shows 'Empty VA data'")
                
        else:
            print("❌ ERROR: No vision column found in DataFrame!")
            print("This is why VA visualization fails")
            
        # Check other relevant columns
        print("\nOther relevant columns:")
        for col in ['date', 'time', 'phase', 'type', 'is_injection']:
            if col in visits_df.columns:
                non_null = visits_df[col].notna().sum()
                print(f"  {col}: {non_null} non-null values")
                
        # Load and check metadata
        metadata_file = visit_files[-1].replace('_visits.parquet', '_metadata.parquet')
        if os.path.exists(metadata_file):
            metadata_df = pd.read_parquet(metadata_file)
            print(f"\nSimulation metadata:")
            for col in metadata_df.columns:
                print(f"  {col}: {metadata_df[col].iloc[0]}")
                
    except Exception as e:
        print(f"ERROR loading parquet file: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Visual Acuity Data Flow Test")
    print("=" * 50)
    check_va_data()