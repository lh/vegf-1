# Next Steps to Fix Visual Acuity Visualization

## Key Findings

1. ✅ **Vision data IS being recorded** - 100% of visits have vision values
2. ✅ **Parquet files are created correctly** - All 3 files (visits, metadata, stats) exist
3. ✅ **DataFrames are loaded** - Line 642-647 loads them into results
4. ✅ **VA processing code exists** - Lines 1038-1175 process VA from visits_df
5. ✅ **Date-to-time conversion works** - Lines 1051-1056 handle the conversion

## The Problem

The issue appears to be that `process_simulation_results()` is called BEFORE the Parquet data is loaded, or the results dictionary is being modified somewhere.

## Action Plan

### 1. Fix the Data Flow Order

In `run_simulation()`, ensure the correct order:

```python
# Around line 640-655, the order should be:
1. Save to Parquet files
2. Load Parquet files into results dict
3. THEN call process_simulation_results with the updated results
```

### 2. Add Debug Checkpoints

Add these debug statements to trace where data is lost:

```python
# In run_simulation() after loading Parquet (line 647):
debug_info(f"After Parquet load - results has visits_df: {'visits_df' in results}")
if 'visits_df' in results:
    debug_info(f"  visits_df shape: {results['visits_df'].shape}")
    debug_info(f"  vision column present: {'vision' in results['visits_df'].columns}")

# Just before returning results (around line 654):
debug_info(f"Before return - results keys: {list(results.keys())}")
debug_info(f"  has visits_df: {'visits_df' in results}")
debug_info(f"  has mean_va_data: {'mean_va_data' in results}")
```

### 3. Check process_simulation_results Call

Look for where `process_simulation_results` is called and ensure it happens AFTER Parquet loading:

```python
# The flow should be:
results = process_simulation_results(sim, patient_histories, params)
# Then ADD the Parquet data to results
results["visits_df"] = pd.read_parquet(...)
# Then process VA data
```

### 4. Quick Fix to Test

As a quick fix, you could force VA processing after Parquet load:

```python
# After line 647 where Parquet is loaded:
results["visits_df"] = pd.read_parquet(f"{parquet_base_path}_visits.parquet")
results["metadata_df"] = pd.read_parquet(f"{parquet_base_path}_metadata.parquet")
results["stats_df"] = pd.read_parquet(f"{parquet_base_path}_stats.parquet")

# Force VA processing here
from streamlit_app_parquet.simulation_runner import process_va_data_from_parquet
if "visits_df" in results:
    va_results = process_va_data_from_parquet(results["visits_df"])
    results.update(va_results)
```

### 5. Verify in Test Visualizations

The Test Visualizations page works because it processes VA data directly from visits_df. Check how it does it:

```python
# In test_visualizations.py, find how it processes VA
# Copy that logic to the main simulation runner
```

## Root Cause Analysis

The most likely cause is that `process_simulation_results()` is called with the original patient_histories BEFORE the Parquet data is added to results. The function processes VA data from patient_histories (which might not have the right format) instead of from visits_df.

## Recommended Fix

1. **Move VA processing** to happen AFTER Parquet data is loaded
2. **Ensure results dict** contains visits_df before any VA processing
3. **Add defensive checks** to prefer visits_df over patient_histories for VA data

## Testing the Fix

1. Enable debug mode in Streamlit sidebar
2. Run a new simulation (even 100 patients for 1 year)
3. Watch console output for debug messages
4. Check if "mean_va_data" appears in results
5. Verify VA plots show actual data

The fix should be straightforward once we ensure the data flow order is correct!