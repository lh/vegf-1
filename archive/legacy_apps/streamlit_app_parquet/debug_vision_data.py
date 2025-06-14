"""
Debug script to check vision data in Parquet files
"""
import pandas as pd
import os
import glob

# Find the most recent Parquet files
parquet_dir = "streamlit_app_parquet/output/parquet_results"
if os.path.exists(parquet_dir):
    visit_files = glob.glob(os.path.join(parquet_dir, "*_visits.parquet"))
    if visit_files:
        # Get the most recent file
        latest_file = max(visit_files, key=os.path.getctime)
        print(f"Checking file: {latest_file}")
        
        # Load the visits DataFrame
        visits_df = pd.read_parquet(latest_file)
        
        print(f"\nDataFrame shape: {visits_df.shape}")
        print(f"Columns: {list(visits_df.columns)}")
        
        # Check for vision-related columns
        vision_cols = [col for col in visits_df.columns if 'vision' in col.lower() or 'va' in col.lower() or 'acuity' in col.lower()]
        print(f"\nVision-related columns: {vision_cols}")
        
        # Check if 'vision' column exists
        if 'vision' in visits_df.columns:
            print(f"\n'vision' column stats:")
            print(f"  - Data type: {visits_df['vision'].dtype}")
            print(f"  - Non-null count: {visits_df['vision'].notna().sum()}")
            print(f"  - Null count: {visits_df['vision'].isna().sum()}")
            print(f"  - Sample values (first 10 non-null):")
            print(visits_df[visits_df['vision'].notna()]['vision'].head(10))
        else:
            print("\n'vision' column NOT FOUND in DataFrame")
            
        # Check what columns actually have data
        print("\n\nAll columns with their non-null counts:")
        for col in visits_df.columns:
            non_null = visits_df[col].notna().sum()
            if non_null > 0:
                print(f"  {col}: {non_null} non-null values")
    else:
        print("No Parquet files found in", parquet_dir)
else:
    print(f"Directory {parquet_dir} does not exist")

# Also check the main output directory
main_output = "output/simulation_results"
if os.path.exists(main_output):
    print(f"\n\nChecking main output directory: {main_output}")
    visit_files = glob.glob(os.path.join(main_output, "*_visits.parquet"))
    if visit_files:
        latest_file = max(visit_files, key=os.path.getctime)
        print(f"Found file: {latest_file}")
        visits_df = pd.read_parquet(latest_file)
        print(f"Columns: {list(visits_df.columns)}")
        if 'vision' in visits_df.columns:
            print(f"Vision column has {visits_df['vision'].notna().sum()} non-null values")