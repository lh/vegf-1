"""Debug script to check Parquet file columns."""
import pandas as pd
from pathlib import Path

# Get a sample Parquet file
parquet_dir = Path("streamlit_app_parquet/output/parquet_results")
visit_files = list(parquet_dir.glob("*_visits.parquet"))

if visit_files:
    # Read a sample visits file
    sample_file = visit_files[0]
    print(f"Reading: {sample_file.name}")
    
    df = pd.read_parquet(sample_file)
    
    print(f"\nShape: {df.shape}")
    print(f"\nColumns: {list(df.columns)}")
    print(f"\nFirst few rows:")
    print(df.head())
    
    # Check for time-related columns
    time_cols = [col for col in df.columns if 'time' in col.lower() or 'month' in col.lower() or 'week' in col.lower()]
    print(f"\nTime-related columns: {time_cols}")
    
    # Check data types
    print(f"\nData types:")
    print(df.dtypes)
else:
    print("No visit parquet files found!")