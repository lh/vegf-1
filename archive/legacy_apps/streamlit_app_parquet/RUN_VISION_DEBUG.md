# Vision Data Debugging Guide

The visual acuity (VA) plots are showing "Empty VA data" because the `mean_va_data` is not being populated. Here's how to debug this issue:

## Quick Tests to Run

### 1. Check existing Parquet files for vision data:
```bash
cd /Users/rose/Code/CC
python streamlit_app_parquet/debug_vision_data.py
```

This will show you:
- What columns are in your Parquet files
- If 'vision' column exists
- How many non-null vision values there are

### 2. Test the full pipeline:
```bash
python streamlit_app_parquet/debug_full_pipeline.py
```

This will:
- Run a minimal simulation
- Show the patient history structure
- Save to Parquet and check the data
- Test the VA processing

### 3. Test like Streamlit does:
```bash
python streamlit_app_parquet/test_minimal_streamlit_sim.py
```

This mimics clicking "Run Simulation" in the UI.

## What We Know So Far

1. **The simulation IS recording vision data**:
   - Line 262 in `treat_and_extend_abs_fixed.py`: `'vision': patient.current_vision`
   - The Patient class has `current_vision` and `baseline_vision` attributes

2. **The issue is likely one of**:
   - Vision values are all null/NaN
   - Column name mismatch
   - Data not being saved to Parquet correctly
   - VA processing function not finding the data

## What to Look For

When you run the debug scripts, check:

1. **In patient histories**: Does each visit have a 'vision' field with a numeric value?
2. **In Parquet DataFrame**: Is there a 'vision' column with non-null values?
3. **In VA processing**: Is `mean_va_data` being created?

## Manual Check in Streamlit

You can also enable Debug Mode in the Streamlit sidebar (Advanced Settings) to see diagnostic messages when running a simulation.

## Potential Fixes

Based on what the debug scripts show:

1. **If vision is missing from patient histories**: 
   - Check if Patient objects are initialized with vision values
   - Check if vision model is calculating changes

2. **If vision is in histories but not in Parquet**:
   - Issue in `save_results_as_parquet` function
   - Field name mismatch

3. **If vision is in Parquet but VA plot fails**:
   - Issue in VA data processing
   - Empty or all-null vision values

Let me know what the debug scripts show and we can fix the specific issue!