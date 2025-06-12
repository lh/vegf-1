# Streamgraph Implementation Plan - Addendum

## Clarifications and Improvements

### 1. Corrected Backward Compatibility Implementation

The actual implementation in `pages/3_Analysis_Overview.py` should be:

```python
@st.cache_data
def get_cached_treatment_patterns(sim_id, include_terminals=False):
    """Existing function with backward compatibility."""
    # First check if data was pre-calculated
    cache_key = f"treatment_patterns_{sim_id}"
    if cache_key in st.session_state:
        data = st.session_state[cache_key]
        # Handle enhanced terminals if needed
        if include_terminals and enhanced_available and 'transitions_df_with_terminals' in data:
            return data['transitions_df_with_terminals'], data['visits_df_with_terminals']
        else:
            return data['transitions_df'], data['visits_df']
    
    # Fall back to on-demand calculation (current behavior)
    # Need to get results from session state first
    results = get_active_simulation()['results']
    
    if include_terminals and enhanced_available:
        transitions_df, visits_df = extract_treatment_patterns_with_terminals(results)
    else:
        transitions_df, visits_df = extract_treatment_patterns_vectorized(results)
    
    # Optionally cache it now for consistency
    st.session_state[cache_key] = {
        'transitions_df': transitions_df,
        'visits_df': visits_df,
        'calculated_at': time.time()
    }
    
    return transitions_df, visits_df
```

### 2. Corrected Verification Script

```python
#!/usr/bin/env python3
"""Verify Sankey functionality before making changes."""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from utils.state_helpers import get_active_simulation
from components.treatment_patterns import extract_treatment_patterns_vectorized

# Try to load from session or latest file
try:
    # If running in Streamlit context
    import streamlit as st
    results_data = get_active_simulation()
    if results_data:
        results = results_data['results']
    else:
        results = None
except:
    # Fallback to loading latest from disk
    from core.results.registry import ResultsRegistry
    results = ResultsRegistry.load_latest()

if results:
    transitions_df, visits_df = extract_treatment_patterns_vectorized(results)
    print(f"✓ Simulation ID: {results.metadata.sim_id}")
    print(f"✓ Transitions found: {len(transitions_df)}")
    print(f"✓ Visits with states: {len(visits_df)}")
    print(f"✓ Unique states: {visits_df['treatment_state'].nunique()}")
    print(f"✓ State list: {sorted(visits_df['treatment_state'].unique())}")
else:
    print("❌ No simulation found")
```

### 3. Error Handling Strategy

Add to Phase 1 implementation:

```python
def get_active_simulation():
    """Get active simulation and pre-calculate treatment patterns."""
    # ... existing code ...
    
    if results_data:
        sim_id = results_data['results'].metadata.sim_id
        cache_key = f"treatment_patterns_{sim_id}"
        
        if cache_key not in st.session_state:
            try:
                # Check if results has required method
                if not hasattr(results_data['results'], 'get_visits_df'):
                    st.warning("Treatment patterns not available for this simulation type")
                    return results_data
                
                with st.spinner("Preparing treatment pattern analysis..."):
                    from components.treatment_patterns import extract_treatment_patterns_vectorized
                    transitions_df, visits_df = extract_treatment_patterns_vectorized(results_data['results'])
                    
                    # Validate data before caching
                    if len(visits_df) == 0:
                        st.info("No visit data available for pattern analysis")
                        return results_data
                    
                    st.session_state[cache_key] = {
                        'transitions_df': transitions_df,
                        'visits_df': visits_df,
                        'calculated_at': time.time()
                    }
            except Exception as e:
                # Log error but don't crash - allow lazy loading to work
                st.warning(f"Could not pre-calculate treatment patterns: {str(e)}")
                # Clear any partial cache
                if cache_key in st.session_state:
                    del st.session_state[cache_key]
    
    return results_data
```

### 4. Performance Limits

Add these constants to `components/treatment_patterns/data_manager.py`:

```python
# Performance limits
MAX_PATIENTS_FOR_PRECALC = 50000  # Skip pre-calc for very large simulations
MAX_VISITS_FOR_PRECALC = 1000000  # Skip if too many visits
PRECALC_TIMEOUT_SECONDS = 10.0    # Maximum time to spend pre-calculating

def should_precalculate(results) -> bool:
    """Determine if we should pre-calculate for this simulation."""
    try:
        n_patients = results.metadata.n_patients
        duration_years = results.metadata.duration_years
        
        # Estimate visits (rough approximation)
        estimated_visits = n_patients * duration_years * 12  # ~monthly visits
        
        if n_patients > MAX_PATIENTS_FOR_PRECALC:
            return False
        if estimated_visits > MAX_VISITS_FOR_PRECALC:
            return False
            
        return True
    except:
        return True  # Default to trying
```

### 5. Testing Other Affected Components

Add to Phase 0:

**Components to Test**:
1. **Treatment Intervals Tab** - Uses `visits_df` for interval analysis
2. **Clinical Workload Tab** - Uses `visits_df` for workload attribution  
3. **Pattern Details Tab** - Uses `transitions_df` for statistics
4. **Treatment Summary Tab** - May use cached data

**Test Script for All Components**:
```python
def test_all_pattern_consumers():
    """Verify all components that use treatment patterns."""
    results = get_latest_results()
    
    # Test interval analyzer
    from components.treatment_patterns.interval_analyzer import calculate_interval_statistics
    stats = calculate_interval_statistics(visits_df)
    print(f"✓ Interval stats: median={stats['median']}")
    
    # Test workload analyzer (if available)
    try:
        from components.treatment_patterns.workload_analyzer import calculate_clinical_workload_attribution
        workload = calculate_clinical_workload_attribution(visits_df)
        print(f"✓ Workload categories: {len(workload['summary_stats'])}")
    except ImportError:
        print("⚠ Workload analyzer not available")
    
    # Add more component tests...
```

### 6. Edge Cases to Handle

Add to time series generator:

```python
def handle_edge_cases(visits_df: pd.DataFrame) -> pd.DataFrame:
    """Ensure data is valid for time series generation."""
    
    # Handle empty data
    if len(visits_df) == 0:
        return pd.DataFrame(columns=['time_point', 'state', 'patient_count'])
    
    # Handle single patient
    if visits_df['patient_id'].nunique() == 1:
        st.warning("Streamgraph may not be meaningful with single patient")
    
    # Handle very short simulations
    time_span_months = visits_df['time_days'].max() / 30.44
    if time_span_months < 3:
        st.info("Short simulation - streamgraph will show limited time evolution")
    
    return visits_df
```

### 7. Memory Management

For Phase 3, add memory-efficient processing:

```python
def create_streamgraph_with_sampling(results, max_points=1000):
    """Create streamgraph with intelligent sampling for large datasets."""
    visits_df = get_visits_df_from_cache(results)
    
    # Determine optimal time resolution
    duration_months = results.metadata.duration_years * 12
    
    if duration_months > max_points:
        # Use coarser resolution for very long simulations
        time_resolution = 'quarter'  # 3-month intervals
    elif duration_months > max_points / 2:
        time_resolution = 'month'
    else:
        time_resolution = 'week'
    
    return create_treatment_state_streamgraph(
        results, 
        time_resolution=time_resolution
    )
```

## Additional Recommendations

1. **Create a feature flag** in `utils/feature_flags.py`:
   ```python
   ENABLE_TREATMENT_PATTERN_PRECALC = True
   ```

2. **Add metrics collection** to understand performance impact:
   ```python
   import time
   start = time.time()
   # ... pre-calculation ...
   elapsed = time.time() - start
   if elapsed > 1.0:
       st.caption(f"Pattern analysis took {elapsed:.1f}s")
   ```

3. **Consider partial pre-calculation** for very large datasets:
   - Pre-calculate only transition counts
   - Calculate full visits_df on demand

4. **Document the data flow** clearly in a diagram showing:
   - Simulation Load → Pre-calc → Cache → Sankey/Streamgraph/Other

5. **Add a cache warming option** in settings:
   - Allow users to disable pre-calculation if it's slow
   - Show progress during pre-calculation