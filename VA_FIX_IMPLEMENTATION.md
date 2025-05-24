# Visual Acuity Fix Implementation Guide

## Problem Summary

The VA visualization shows "Empty VA data" because:
- `process_simulation_results()` is called on line 593
- Parquet data is loaded on lines 643-645
- VA processing (lines 1038-1175) needs `visits_df` which isn't available yet

## Solution

### Option 1: Re-run VA Processing After Parquet Load (Simplest)

Add this code after line 647 in `simulation_runner.py`:

```python
# After loading Parquet data, re-process VA data
if "visits_df" in results:
    debug_info("Re-processing VA data with loaded Parquet DataFrame...")
    
    # Extract the VA processing logic into a separate function
    # Or simply copy lines 1038-1175 here
    # For now, let's call process_simulation_results again with updated results
    
    # Save the existing processed data
    existing_data = {k: v for k, v in results.items() if k not in ["visits_df", "metadata_df", "stats_df"]}
    
    # Create a dummy sim object with the stats
    class DummySim:
        def __init__(self, stats):
            self.stats = stats
    
    dummy_sim = DummySim(statistics)
    
    # Re-process with Parquet data available
    updated_results = process_simulation_results(dummy_sim, patient_histories, params)
    
    # Merge results, keeping Parquet data
    results.update(updated_results)
    results["visits_df"] = pd.read_parquet(f"{parquet_base_path}_visits.parquet")
    results["metadata_df"] = pd.read_parquet(f"{parquet_base_path}_metadata.parquet")
    results["stats_df"] = pd.read_parquet(f"{parquet_base_path}_stats.parquet")
```

### Option 2: Extract VA Processing to Separate Function (Cleaner)

1. Create a new function in `simulation_runner.py`:

```python
def process_va_from_visits_df(visits_df):
    """Process visual acuity data from visits DataFrame."""
    va_results = {}
    
    # Copy the VA processing logic from lines 1050-1175
    # Convert date to time if needed
    if 'time' not in visits_df.columns and 'date' in visits_df.columns:
        visits_df = visits_df.copy()
        visits_df['date'] = pd.to_datetime(visits_df['date'])
        min_date = visits_df['date'].min()
        visits_df['time'] = (visits_df['date'] - min_date).dt.days / 30.44
    
    # ... rest of VA processing logic ...
    
    return va_results
```

2. Call it after loading Parquet:

```python
# After line 647
if "visits_df" in results:
    va_results = process_va_from_visits_df(results["visits_df"])
    results.update(va_results)
    debug_info(f"VA processing complete: {len(results.get('mean_va_data', []))} time points")
```

### Option 3: Move Parquet Loading Earlier (Most Correct)

Restructure the code flow:

1. Run simulation
2. Save to Parquet
3. Load Parquet data
4. THEN call process_simulation_results with Parquet data available

This requires more refactoring but is the cleanest solution.

## Quick Test

After implementing the fix:

1. Enable Debug Mode in Streamlit
2. Run a small simulation (100 patients, 1 year)
3. Check console for:
   - "Re-processing VA data with loaded Parquet DataFrame..."
   - "VA processing complete: X time points"
4. Verify VA plots show data

## Expected Result

- VA plots will show actual trend lines
- Mean VA over time will display properly
- No more "Empty VA data" messages

The fix is straightforward - we just need to ensure VA processing happens AFTER the Parquet data is available in the results dictionary.