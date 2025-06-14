# Visual Acuity Visualization Fix Guide

## Problem Summary

The Patient State Visualization is working correctly, but the Visual Acuity plots are showing "Empty VA data" or "No visual acuity data available". This is happening because:

1. The VA processing code in `simulation_runner.py` (lines 1038-1175) is correctly implemented for Parquet data
2. However, the results might not contain the `visits_df` DataFrame needed for processing
3. The issue appears to be in how data flows from the simulation to the visualization functions

## Root Cause Analysis

After debugging with Playwright and examining the code:

1. **VA Processing Logic is Correct**: The `simulation_runner.py` has proper Parquet-based VA processing (lines 1038-1175)
2. **Visualization Functions Work**: The `generate_va_over_time_plot` function handles empty data gracefully
3. **Data Flow Issue**: The problem is that `visits_df` might not be passed into the results dictionary properly

## Action Plan for Fix

### Priority 1: Verify Data Flow in `run_simulation`

1. **Check `run_simulation` function** in `simulation_runner.py`:
   - Ensure it loads Parquet files into DataFrames
   - Verify `visits_df`, `metadata_df`, and `stats_df` are added to results
   - Look for any code that might be removing these DataFrames before VA processing

2. **Debug the data pipeline**:
   ```python
   # Add debug logging at key points:
   # After loading Parquet files
   print(f"Loaded visits_df shape: {visits_df.shape}")
   print(f"Vision column present: {'vision' in visits_df.columns}")
   
   # Before VA processing
   print(f"Results has visits_df: {'visits_df' in results}")
   ```

### Priority 2: Fix Vision Data Recording

The debug output suggests the `vision` column might be missing or empty:

1. **Check simulation output**:
   - Verify new simulations are recording vision data
   - Check if the `vision` column exists in the Parquet files
   - Ensure vision values are not all null

2. **Add data validation**:
   ```python
   # In simulation_runner.py after loading Parquet
   if 'vision' not in visits_df.columns:
       print("WARNING: No vision column in visits data!")
   else:
       non_null_vision = visits_df['vision'].notna().sum()
       print(f"Vision data: {non_null_vision} non-null out of {len(visits_df)} visits")
   ```

### Priority 3: Fix the enable_clinician_variation Parameter

The error suggests a missing parameter in simulation config:

1. **Update simulation configuration** to include all required parameters
2. **Add default values** for any missing parameters in the simulation runner

### Debugging Steps to Run

1. **Start Streamlit app**:
   ```bash
   cd streamlit_app_parquet
   streamlit run app.py --server.port 8503
   ```

2. **Use Playwright to inspect**:
   ```bash
   node playwright_debug_configurable.js 8503
   ```

3. **Run a test simulation** and check the console/terminal output for:
   - Parquet file creation messages
   - Vision data statistics
   - Any error messages during VA processing

4. **Inspect the Parquet files directly**:
   ```python
   import pandas as pd
   
   # Check a recent simulation's data
   visits_df = pd.read_parquet("path/to/visits.parquet")
   print(f"Columns: {visits_df.columns.tolist()}")
   print(f"Vision data: {visits_df['vision'].describe()}")
   ```

### Quick Fix to Test

If you need a quick fix to verify the visualization code works:

1. **Add debug output** in `simulation_runner.py` around line 1040:
   ```python
   if "visits_df" in results:
       print(f"DEBUG: Processing VA from visits_df")
       print(f"DEBUG: visits_df shape: {results['visits_df'].shape}")
       print(f"DEBUG: Columns: {list(results['visits_df'].columns)}")
   else:
       print(f"DEBUG: No visits_df in results!")
       print(f"DEBUG: Available keys: {list(results.keys())}")
   ```

2. **Ensure Parquet data is loaded** in the `run_simulation` function

3. **Verify the simulation is generating vision data** by checking the clinical model

## Expected Outcome

After these fixes:
- Visual Acuity plots should show real trend data
- The plots should display smoothed lines with confidence intervals
- Patient count bars should appear on the left axis
- All visualizations should use the Parquet data structure

## Key Files to Focus On

1. `streamlit_app_parquet/simulation_runner.py` - Check data flow in `run_simulation`
2. `simulation/vision_models.py` - Verify vision data generation
3. `simulation/clinical_model.py` - Check vision recording logic

The core issue appears to be a data pipeline problem where the Parquet DataFrames aren't making it to the VA processing code, rather than an issue with the visualization logic itself.