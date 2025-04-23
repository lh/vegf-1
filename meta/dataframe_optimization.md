# DataFrame Optimization Strategies

## Current Issues

The current implementation of `eylea_data_analysis.py` generates multiple performance warnings related to DataFrame fragmentation:

```
PerformanceWarning: DataFrame is highly fragmented. This is usually the result of calling `frame.insert` many times, which has poor performance. Consider joining all columns at once using pd.concat(axis=1) instead. To get a de-fragmented frame, use `newframe = frame.copy()`
```

These warnings occur in several key methods:
- `handle_temporal_anomalies`: Adding the `Long_Gap` flag
- `create_patient_id`: Adding `patient_id`, `eye_standardized`, and `eye_key` columns
- `handle_missing_values`: Adding age-related columns

## Technical Background

### Why DataFrame Fragmentation Occurs

Pandas DataFrames store data in contiguous memory blocks for efficiency. When columns are added incrementally using `df['new_col'] = ...`, pandas:
1. Creates a new memory block for each column
2. Must reallocate memory and copy data repeatedly
3. Creates a fragmented memory layout with non-contiguous blocks

This fragmentation leads to:
- Increased memory usage
- Slower operations due to cache misses
- Degraded performance for large datasets

## Optimization Strategies

### Short-term: Batch Column Creation

The immediate fix is to batch column additions using one of these approaches:

1. **Using pd.concat**:
   ```python
   # Instead of:
   df['col1'] = values1
   df['col2'] = values2
   
   # Use:
   new_cols = pd.DataFrame({
       'col1': values1,
       'col2': values2
   })
   df = pd.concat([df, new_cols], axis=1)
   ```

2. **Using df.assign**:
   ```python
   # Instead of individual assignments:
   df = df.assign(
       col1=values1,
       col2=values2
   )
   ```

3. **Strategic DataFrame copying**:
   ```python
   # After major processing steps:
   df = df.copy()
   ```

### Medium-term: Pre-allocation Strategy

For a more comprehensive solution, we can pre-allocate columns:

1. Define all expected columns upfront
2. Create an empty DataFrame with the full schema
3. Fill in values as they become available

This approach requires:
- Knowing all column names in advance
- Defining appropriate data types
- Handling conditional columns carefully

### Long-term: Alternative DataFrame Libraries

For future projects, consider these alternatives to pandas:

#### Polars

[Polars](https://pola.rs/) is a modern DataFrame library written in Rust with Python bindings that offers:

- **Performance**: 10-100x faster than pandas for many operations
- **Memory Efficiency**: Uses Apache Arrow memory model
- **Lazy Evaluation**: Optimizes query plans before execution
- **API Similarity**: Familiar API for pandas users

Example conversion:
```python
# Pandas:
df = pd.read_csv("data.csv")
result = df.filter(df["col"] > 0).groupby("category").agg({"value": "mean"})

# Polars:
df = pl.read_csv("data.csv")
result = df.filter(pl.col("col") > 0).groupby("category").agg(pl.col("value").mean())
```

#### Other Alternatives

- **Modin**: Drop-in replacement for pandas with distributed computing
- **Vaex**: Out-of-core DataFrames for larger-than-memory datasets
- **cuDF**: GPU-accelerated DataFrames (NVIDIA RAPIDS)

## Implementation Plan

1. **Immediate**: Apply batch column creation in problematic methods
2. **Short-term**: Add strategic DataFrame copying after major processing steps
3. **Medium-term**: Consider schema pre-allocation for new analysis modules
4. **Long-term**: Evaluate Polars for new data analysis components

## Expected Benefits

- **Performance**: 30-50% reduction in memory usage, 2-3x speedup in column creation
- **Stability**: More predictable memory footprint
- **Scalability**: Better handling of larger datasets

## References

1. [Pandas Performance Optimization](https://pandas.pydata.org/pandas-docs/stable/user_guide/enhancingperf.html)
2. [Polars Documentation](https://pola.rs/docs/)
3. [Apache Arrow Memory Model](https://arrow.apache.org/docs/format/Columnar.html)
