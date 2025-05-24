"""Debug the calendar transformation process step by step."""
import pandas as pd
from pathlib import Path
import sys
sys.path.append('streamlit_app_parquet')

from staggered_data_processor import transform_to_calendar_view

# Get sample files
parquet_dir = Path("streamlit_app_parquet/output/parquet_results")
metadata_files = list(parquet_dir.glob("*_metadata.parquet"))
visits_files = list(parquet_dir.glob("*_visits.parquet"))

if metadata_files and visits_files:
    # Pick a sample simulation
    sim_name = metadata_files[0].stem.replace("_metadata", "")
    print(f"Testing with simulation: {sim_name}")
    
    # Load the data
    print("\n1. Loading Parquet files...")
    visits_df = pd.read_parquet(parquet_dir / f"{sim_name}_visits.parquet")
    metadata_df = pd.read_parquet(parquet_dir / f"{sim_name}_metadata.parquet")
    
    print(f"\nVisits shape: {visits_df.shape}")
    print(f"Metadata shape: {metadata_df.shape}")
    
    print("\n2. Visits DataFrame columns:")
    print(list(visits_df.columns))
    
    print("\n3. Metadata DataFrame columns:")
    print(list(metadata_df.columns))
    
    print("\n4. First few rows of visits:")
    print(visits_df.head(2))
    
    print("\n5. First few rows of metadata:")
    print(metadata_df.head(2))
    
    print("\n6. Unique patient IDs in visits:")
    if 'patient_id' in visits_df.columns:
        print(f"Count: {visits_df['patient_id'].nunique()}")
        print(f"Sample: {list(visits_df['patient_id'].unique()[:5])}")
    else:
        print("ERROR: 'patient_id' column not found in visits!")
        print("Available columns:", visits_df.columns.tolist())
    
    print("\n7. Unique patient IDs in metadata:")
    if 'patient_id' in metadata_df.columns:
        print(f"Count: {metadata_df['patient_id'].nunique()}")
        print(f"Sample: {list(metadata_df['patient_id'].unique()[:5])}")
    else:
        print("ERROR: 'patient_id' column not found in metadata!")
        print("Available columns:", metadata_df.columns.tolist())
    
    # Try the transformation with minimal parameters
    print("\n8. Attempting transformation...")
    try:
        calendar_visits_df, clinic_metrics_df = transform_to_calendar_view(
            visits_df,
            metadata_df,
            enrollment_pattern="uniform",
            enrollment_months=12
        )
        print("SUCCESS! Transformation completed.")
        print(f"Calendar visits shape: {calendar_visits_df.shape}")
        print(f"Clinic metrics shape: {clinic_metrics_df.shape}")
    except Exception as e:
        print(f"ERROR during transformation: {e}")
        import traceback
        traceback.print_exc()
else:
    print("No Parquet files found!")