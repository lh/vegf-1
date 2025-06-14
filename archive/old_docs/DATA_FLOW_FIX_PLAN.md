# Data Flow Fix Plan for Visual Acuity Visualization

## Current Data Flow (Found in Code)

1. **Simulation runs** → generates patient histories
2. **Save to Parquet** → `save_results_as_parquet()` creates 3 files:
   - `visits.parquet` - Contains all visit data INCLUDING vision column
   - `metadata.parquet` - Simulation parameters
   - `stats.parquet` - Aggregated statistics

3. **Load Parquet** → Lines 642-647 in `run_simulation()`:
   ```python
   results["visits_df"] = pd.read_parquet(f"{parquet_base_path}_visits.parquet")
   results["metadata_df"] = pd.read_parquet(f"{parquet_base_path}_metadata.parquet")
   results["stats_df"] = pd.read_parquet(f"{parquet_base_path}_stats.parquet")
   ```

4. **Process results** → `process_simulation_results()` is called
5. **VA Processing** → Lines 1038-1175 check for `visits_df` and process VA data

## The Problem

The data flow appears correct, but the VA visualization still shows "Empty VA data". The issue is likely one of:

1. **Vision data not being recorded** in the simulation
2. **Vision column is empty** (all null values)
3. **Results dict is modified** between loading and VA processing

## Debugging Plan

### Step 1: Add Strategic Debug Points

Add these debug statements to trace the data flow:

```python
# In run_simulation() after line 647:
debug_info(f"Loaded DataFrames - visits shape: {results['visits_df'].shape}")
debug_info(f"Vision column in visits_df: {'vision' in results['visits_df'].columns}")
if 'vision' in results['visits_df'].columns:
    non_null = results['visits_df']['vision'].notna().sum()
    debug_info(f"Non-null vision values: {non_null}/{len(results['visits_df'])}")
    debug_info(f"Sample vision values: {results['visits_df']['vision'].dropna().head().tolist()}")
```

### Step 2: Verify Vision Data Generation

Check if the simulation is actually recording vision data:

```python
# In save_results_as_parquet() around line 754:
# After creating visits_df, add:
if "vision" in visits_df.columns:
    print(f"Vision data stats: min={visits_df['vision'].min()}, max={visits_df['vision'].max()}, mean={visits_df['vision'].mean():.1f}")
else:
    print("WARNING: No vision column in visits DataFrame!")
```

### Step 3: Trace Results Dictionary

Ensure the results dict isn't modified between loading and processing:

```python
# Before calling process_simulation_results():
print(f"Results keys before processing: {list(results.keys())}")
print(f"Has visits_df: {'visits_df' in results}")

# After process_simulation_results():
print(f"Results keys after processing: {list(results.keys())}")
print(f"Has mean_va_data: {'mean_va_data' in results}")
```

### Step 4: Check Vision Model Integration

The root cause might be that vision values aren't being recorded during simulation:

1. Check `simulation/vision_models.py` - Ensure vision changes are recorded
2. Check `simulation/clinical_model.py` - Verify visits include vision data
3. Look for where visit dictionaries are created and ensure they include:
   ```python
   visit = {
       "date": current_date,
       "time": elapsed_time,
       "vision": patient.vision,  # This MUST be included
       "type": visit_type,
       # ... other fields
   }
   ```

## Quick Test Script

Create a test script to verify the data pipeline:

```python
# test_va_data_flow.py
import pandas as pd
import os
from glob import glob

# Find latest parquet files
parquet_dir = "streamlit_app_parquet/output/parquet_results"
latest_files = sorted(glob(os.path.join(parquet_dir, "*_visits.parquet")))[-1]

if latest_files:
    visits_df = pd.read_parquet(latest_files)
    print(f"Loaded visits from: {latest_files}")
    print(f"Shape: {visits_df.shape}")
    print(f"Columns: {visits_df.columns.tolist()}")
    
    if 'vision' in visits_df.columns:
        print(f"\nVision data statistics:")
        print(f"  Non-null: {visits_df['vision'].notna().sum()}")
        print(f"  Null: {visits_df['vision'].isna().sum()}")
        print(f"  Range: {visits_df['vision'].min():.1f} to {visits_df['vision'].max():.1f}")
        print(f"  Mean: {visits_df['vision'].mean():.1f}")
        print(f"\nSample values:")
        print(visits_df[['patient_id', 'time', 'vision']].dropna(subset=['vision']).head(10))
    else:
        print("\nERROR: No vision column found!")
```

## Expected Resolution

After implementing these debug points, we'll likely find one of:

1. **Vision column missing** → Fix the simulation to record vision
2. **Vision values all null** → Fix the vision model integration
3. **Data lost in pipeline** → Fix where results dict is modified

Once we identify the exact failure point, the fix will be straightforward.

## Next Steps

1. Run a new simulation with debug mode enabled
2. Check the console output for the debug messages
3. Run the test script to inspect the Parquet files directly
4. Based on findings, implement the specific fix needed

The good news is that the infrastructure is correct - we just need to ensure vision data flows through it properly!