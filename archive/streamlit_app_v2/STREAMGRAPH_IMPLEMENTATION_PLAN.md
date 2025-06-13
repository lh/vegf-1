# Streamgraph Implementation Plan - Detailed

## Overview
Implement a treatment state streamgraph visualization showing patient cohort flow over time, with pre-calculated treatment pattern data loaded automatically when simulations are accessed.

## Phase 0: Verify Existing Functionality (CRITICAL)

### 0.1 Manual Testing Protocol
**Before ANY changes**, verify current Sankey behavior:

**Testing Steps**:
1. Ask user to run a simulation (e.g., 1000 patients, 2 years)
2. Navigate to Analysis → Patient Journey Visualisation tab
3. Take screenshot of working Sankey diagram
4. Note any console errors or warnings
5. Record approximate load time

**Simple Verification Script**: `verify_sankey_works.py`
```python
# Quick script to check if treatment patterns can be extracted
import streamlit as st
from core.results.registry import ResultsRegistry

# Load latest simulation
results = ResultsRegistry.load_latest()
if results:
    from components.treatment_patterns import extract_treatment_patterns_vectorized
    transitions_df, visits_df = extract_treatment_patterns_vectorized(results)
    print(f"✓ Transitions found: {len(transitions_df)}")
    print(f"✓ Visits with states: {len(visits_df)}")
    print(f"✓ Unique states: {visits_df['treatment_state'].nunique()}")
else:
    print("❌ No simulation found")
```

### 0.2 Implement Backward Compatibility
**Key Principle**: The Sankey must work identically whether data is:
- Lazy-loaded (current behavior) 
- Pre-calculated (new behavior)
- Already cached from previous tab visit

**Implementation**:
```python
def get_cached_treatment_patterns(sim_id, include_terminals=False):
    """Existing function MUST continue to work unchanged."""
    # Check if data is already pre-calculated
    cache_key = f"treatment_patterns_{sim_id}"
    if cache_key in st.session_state:
        data = st.session_state[cache_key]
        transitions_df = data['transitions_df']
        visits_df = data['visits_df']
    else:
        # Fall back to calculating on demand (current behavior)
        if include_terminals and enhanced_available:
            transitions_df, visits_df = extract_treatment_patterns_with_terminals(results)
        else:
            transitions_df, visits_df = extract_treatment_patterns_vectorized(results)
    
    return transitions_df, visits_df
```

### 0.3 Regression Tests
**Create tests to verify**:
1. Sankey data shape remains identical
2. Transition counts match exactly
3. Color mappings are preserved
4. Performance is same or better
5. Cache keys don't conflict

### 0.4 Rollback Plan
- Keep changes isolated in feature branch
- Implement feature flag to toggle pre-calculation
- Ensure we can disable pre-calculation without code changes

### 0.5 Key Testing Checkpoints
**After each implementation phase, ask user to**:
1. Run a fresh simulation
2. Check if Sankey still loads correctly
3. Compare visual output with baseline screenshot
4. Report any performance changes
5. Check for console errors

**Red Flags to Watch For**:
- Sankey shows different data than before
- Loading takes significantly longer
- Empty or error states in Sankey
- Console errors about missing data
- Different colors or state names

## Phase 1: Data Infrastructure (Pre-calculation Strategy)

### 1.1 Modify Simulation Loading
**File**: `utils/state_helpers.py`
- Modify `get_active_simulation()` to pre-calculate treatment patterns
- Add progress indicator during calculation
- Cache results in session state with simulation

**Implementation**:
```python
def get_active_simulation():
    """Get active simulation and pre-calculate treatment patterns."""
    # ... existing code ...
    
    if results_data:
        # Pre-calculate treatment patterns if not already cached
        sim_id = results_data['results'].metadata.sim_id
        cache_key = f"treatment_patterns_{sim_id}"
        
        if cache_key not in st.session_state:
            with st.spinner("Preparing treatment pattern analysis..."):
                from components.treatment_patterns import extract_treatment_patterns_vectorized
                transitions_df, visits_df = extract_treatment_patterns_vectorized(results_data['results'])
                st.session_state[cache_key] = {
                    'transitions_df': transitions_df,
                    'visits_df': visits_df,
                    'calculated_at': time.time()
                }
    
    return results_data
```

### 1.2 Create Centralized Data Access
**New File**: `components/treatment_patterns/data_manager.py`
- Centralized function to get treatment pattern data
- Handles caching and ensures data availability
- Returns consistent data structure

**Key Functions**:
- `get_treatment_pattern_data(results) -> tuple[pd.DataFrame, pd.DataFrame]`
- `ensure_treatment_patterns_cached(sim_id: str) -> bool`
- `clear_treatment_pattern_cache(sim_id: str = None)`

## Phase 2: Streamgraph Data Processing

### 2.1 Create Time Series Generator
**New File**: `components/treatment_patterns/time_series_generator.py`

**Key Functions**:
```python
def generate_patient_state_time_series(
    visits_df: pd.DataFrame,
    time_resolution: str = 'month',
    start_time: float = 0,
    end_time: float = None
) -> pd.DataFrame:
    """
    Generate time series of patient counts by state.
    
    Returns DataFrame with columns:
    - time_point: Time in months
    - state: Treatment state name
    - patient_count: Number of patients in state
    - percentage: Percentage of total patients
    """
```

**Processing Steps**:
1. Create time points based on resolution (week/month)
2. For each time point:
   - Identify active patients (have started, not yet discontinued)
   - Get most recent visit for each patient before time point
   - Count patients by their current treatment state
3. Handle edge cases:
   - Patients not yet started (pre-treatment)
   - Patients between visits (carry forward last state)
   - Discontinued patients (no visits in 6+ months)

### 2.2 State Tracking Logic
**Key Considerations**:
- Patient state persists between visits
- Gaps >6 months trigger "No Further Visits" state
- New patients enter as cohort recruits
- Track both actual visit states and inferred states

**Algorithm**:
```python
def get_patient_state_at_time(patient_visits, time_point, sim_end_time):
    """Determine patient's state at specific time point."""
    # Get visits before time_point
    past_visits = patient_visits[patient_visits['time_days'] <= time_point * 30.44]
    
    if len(past_visits) == 0:
        return 'Pre-Treatment'
    
    last_visit = past_visits.iloc[-1]
    time_since_last = (time_point * 30.44) - last_visit['time_days']
    
    # Check if discontinued (>6 months since last visit)
    if time_since_last > 180:
        return 'No Further Visits'
    
    # Return last known treatment state
    return last_visit['treatment_state']
```

## Phase 3: Visualization Implementation

### 3.1 Create Streamgraph Component
**New File**: `visualizations/streamgraph_treatment_states.py`

**Main Function**:
```python
def create_treatment_state_streamgraph(
    results,
    time_resolution: str = 'month',
    normalize: bool = False,
    height: int = 500
) -> go.Figure:
    """Create interactive Plotly streamgraph of treatment states."""
```

**Features**:
- Plotly stacked area chart with smooth interpolation
- Semantic colors from visualization system
- Interactive hover showing exact counts
- Legend to toggle states
- Export configuration support

### 3.2 Visual Design
**Layout**:
- States ordered logically (active → gaps → terminal)
- Smooth transitions between time points
- Clear axis labels and title
- Responsive sizing

**State Ordering** (bottom to top):
1. Initial Treatment
2. Intensive (Monthly)
3. Regular (6-8 weeks)
4. Extended (12+ weeks)
5. Maximum Extension (16 weeks)
6. Restarted After Gap
7. Treatment Gap (3-6 months)
8. Extended Gap (6-12 months)
9. Long Gap (12+ months)
10. No Further Visits

## Phase 4: Integration

### 4.1 Update Analysis Page
**File**: `pages/3_Analysis_Overview.py`

**Changes**:
- Import new streamgraph function
- Replace existing streamgraph in tab4
- Remove comprehensive/simple toggle (single implementation)
- Add controls for time resolution and normalization

### 4.2 Performance Optimization
- Cache time series data by (sim_id, resolution, normalize)
- Use vectorized pandas operations throughout
- Limit maximum time points to prevent UI lag
- Progressive loading for very long simulations

## Phase 5: Testing & Validation

### 5.1 Data Validation
- Verify patient count conservation at each time point
- Check state transitions are logical
- Validate against known patterns from Sankey

### 5.2 Visual Testing
- Test with various simulation sizes (100 to 10,000 patients)
- Verify colors match semantic system
- Check responsiveness and interactivity

### 5.3 Performance Testing
- Measure calculation time for different dataset sizes
- Verify caching works correctly
- Test memory usage with large datasets

## Implementation Timeline

**Day 0**: Verify Existing Functionality
- Create Sankey regression tests
- Document current behavior
- Implement verification scripts
- Set up rollback plan

**Day 1**: Data Infrastructure
- Implement backward-compatible caching
- Add pre-calculation to state_helpers
- Create data_manager module
- Verify Sankey still works identically

**Day 2**: Time Series Generation
- Implement time_series_generator
- Create patient state tracking logic
- Validate data accuracy
- Cross-check with Sankey data

**Day 3**: Visualization
- Create streamgraph component
- Apply styling and interactivity
- Test visual output
- Ensure consistency with Sankey

**Day 4**: Integration & Testing
- Integrate into Analysis page
- Performance optimization
- Final testing and validation
- Verify all treatment pattern visualizations work

## Success Metrics

1. **Data Accuracy**
   - Patient counts conserved at all time points
   - States match visit interval definitions
   - Transitions align with Sankey diagram

2. **Performance**
   - Pre-calculation < 3 seconds for 10k patients
   - Streamgraph renders < 1 second
   - Smooth interaction with no lag

3. **User Experience**
   - Clear visual representation of patient flow
   - Intuitive controls
   - Informative hover tooltips
   - Consistent with app design language

## Risk Mitigation

1. **Memory Usage**: Implement data sampling for very large datasets
2. **Calculation Time**: Show progress indicators, allow cancellation
3. **Data Gaps**: Handle edge cases gracefully with clear messages
4. **Browser Performance**: Limit number of rendered points, use data aggregation

## Next Steps

1. Review and approve this plan
2. Create feature branch: `feature/treatment-state-streamgraph`
3. Begin Phase 1 implementation
4. Daily progress updates and testing