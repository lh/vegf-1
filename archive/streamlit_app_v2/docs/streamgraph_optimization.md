# Streamgraph Performance Optimization

## Overview
The Patient States streamgraph visualization was taking 10-24 seconds to generate for large datasets (10,000 patients over 10 years), making the UI feel sluggish. This document describes the optimization approach that reduced this to ~1-2 seconds with intelligent caching.

## The Problem
The original implementation had several performance bottlenecks:

1. **Nested loops**: O(n×m) complexity where n = time points and m = patients
2. **Non-vectorized operations**: Using pandas `apply()` instead of numpy operations
3. **Redundant computation**: Recalculating everything when switching between percentage/absolute views
4. **No pre-computation**: Users had to wait for initial calculation every time

## The Solution

### 1. Vectorization (5-10x speedup)

#### Before:
```python
# Counting enrolled patients - O(n×m) complexity
for t in time_points:
    enrolled_count = sum(1 for pid in all_patients 
                        if enrollment_times.get(pid, 0) <= t)
```

#### After:
```python
# Pre-compute all enrollment counts at once - O(n log n)
enrollment_months_sorted = np.sort(enrollment_months)
enrolled_at_time = np.searchsorted(enrollment_months_sorted, time_points, side='right')
```

#### Before:
```python
# Using apply() for state determination - slow row-wise operation
last_visits['current_state'] = last_visits.apply(
    lambda row: 'No Further Visits' if row['time_since_last'] > 6 else row['treatment_state'],
    axis=1
)
```

#### After:
```python
# Vectorized conditional using np.where - fast column-wise operation
last_visits['current_state'] = np.where(
    time_since_last > 6,
    'No Further Visits',
    last_visits['treatment_state']
)
```

### 2. Intelligent Caching (instant switching)

The key insight was to cache the expensive data computation, not the visualization:

```python
@st.cache_data(show_spinner=False)
def get_cached_time_series_data(
    sim_id: str,
    visits_df_hash: str,
    time_resolution: str,
    enrollment_df_hash: Optional[str] = None
) -> pd.DataFrame:
    # Expensive computation happens only once per resolution
    return generate_patient_state_time_series(...)
```

Now switching between percentage and absolute views just transforms already-computed data.

### 3. Smart Resolution Selection

For large datasets, week resolution becomes prohibitively slow. We now intelligently disable it:

```python
def should_show_week_resolution(n_patients: int, duration_years: float) -> bool:
    """
    Week resolution creates ~52 points per year
    10,000 patients × 10 years × 52 weeks = 5.2M data points
    """
    expected_points = duration_years * 52
    data_complexity = n_patients * expected_points
    
    # Threshold based on testing
    return data_complexity < 200_000
```

### 4. Pre-computation During Simulation

After a simulation completes, we pre-compute common resolutions:

```python
# In simulation completion
progress_bar.progress(92, text="Pre-computing visualizations...")
precompute_treatment_patterns(results, show_progress=False)
```

This means users see instant results when they first open the analysis.

## Results

### Performance Improvements:
- **Month resolution**: 7.2s → 0.7s (10x faster)
- **Week resolution**: 28.5s → 1.5s (19x faster)
- **View switching**: 10-24s → instant (cached)
- **First load**: 10-24s → instant (pre-computed)

### User Experience:
- Large datasets (10k+ patients) automatically have week resolution disabled
- Clear messaging when options are limited for performance
- Instant switching between percentage and absolute views
- No waiting when first opening analysis (pre-computed)

## Key Lessons

1. **Profile first**: The bottlenecks weren't where expected - the nested loop for enrollment counting was the biggest issue

2. **Cache the right thing**: Caching the Plotly figure wasn't helpful - cache the expensive data computation instead

3. **Vectorize everything**: Even simple operations like conditionals benefit from numpy's vectorized operations

4. **Guide users**: Rather than letting users select slow options, intelligently limit choices based on data size

5. **Pre-compute when possible**: A few seconds during simulation save many seconds of user waiting later

## Code Locations

- Optimized time series generator: `components/treatment_patterns/time_series_generator.py`
- Caching layer: `components/treatment_patterns/time_series_cache.py`
- Pre-computation: `components/treatment_patterns/precompute.py`
- UI integration: `pages/3_Analysis.py` (Patient States tab)