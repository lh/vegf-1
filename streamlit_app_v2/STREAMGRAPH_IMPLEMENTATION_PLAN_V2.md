# Streamgraph Implementation Plan v2 - Complete

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
6. Test other tabs that use treatment patterns:
   - Treatment Intervals tab
   - Clinical Workload Analysis tab
   - Pattern Details tab

### 0.2 Create Verification Script
**File**: `verify_sankey_works.py`

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
    
    # Test other components
    from components.treatment_patterns.interval_analyzer import calculate_interval_statistics
    stats = calculate_interval_statistics(visits_df)
    print(f"✓ Interval stats: median={stats['median']:.1f} days")
    
    # Save reference data
    import json
    reference = {
        'sim_id': results.metadata.sim_id,
        'transition_count': len(transitions_df),
        'visit_count': len(visits_df),
        'states': sorted(visits_df['treatment_state'].unique()),
        'median_interval': stats['median']
    }
    with open('sankey_reference_data.json', 'w') as f:
        json.dump(reference, f, indent=2)
    print("✓ Reference data saved to sankey_reference_data.json")
else:
    print("❌ No simulation found")
```

### 0.3 Rollback Plan
- Keep changes isolated in feature branch: `feature/treatment-state-streamgraph`
- Implement feature flag: `ENABLE_TREATMENT_PATTERN_PRECALC = True`
- Ensure we can disable pre-calculation without code changes
- Tag current working state: `git tag pre-streamgraph-baseline`

### 0.4 Testing Checkpoints
**After each phase implementation**:
1. Run fresh simulation
2. Verify Sankey loads correctly
3. Check all pattern-using tabs still work
4. Compare with reference data
5. Note performance changes
6. Check browser console for errors

**Red Flags**:
- Different data in Sankey than baseline
- Missing states or wrong colors
- Console errors about missing data
- Significantly slower performance
- Any tab showing errors or empty states

## Phase 1: Data Infrastructure (Pre-calculation Strategy)

### 1.1 Add Performance Limits
**New File**: `components/treatment_patterns/performance_config.py`

```python
"""Performance configuration for treatment pattern analysis."""

# Performance limits
MAX_PATIENTS_FOR_PRECALC = 50000  # Skip pre-calc for very large simulations
MAX_VISITS_FOR_PRECALC = 1000000  # Skip if too many visits
PRECALC_TIMEOUT_SECONDS = 10.0    # Maximum time to spend pre-calculating

# Feature flags
ENABLE_TREATMENT_PATTERN_PRECALC = True  # Master switch

def should_precalculate(results) -> bool:
    """Determine if we should pre-calculate for this simulation."""
    if not ENABLE_TREATMENT_PATTERN_PRECALC:
        return False
        
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

### 1.2 Modify Simulation Loading
**File**: `utils/state_helpers.py`

```python
def get_active_simulation():
    """Get active simulation and pre-calculate treatment patterns."""
    # ... existing code to get results_data ...
    
    if results_data:
        from components.treatment_patterns.performance_config import should_precalculate
        
        sim_id = results_data['results'].metadata.sim_id
        cache_key = f"treatment_patterns_{sim_id}"
        
        # Only pre-calculate if not already cached and within limits
        if cache_key not in st.session_state and should_precalculate(results_data['results']):
            try:
                # Check if results has required method
                if not hasattr(results_data['results'], 'get_visits_df'):
                    # Silently skip - not all simulations have visit data
                    return results_data
                
                # Time the pre-calculation
                import time
                start_time = time.time()
                
                with st.spinner("Preparing treatment pattern analysis..."):
                    from components.treatment_patterns import extract_treatment_patterns_vectorized
                    transitions_df, visits_df = extract_treatment_patterns_vectorized(results_data['results'])
                    
                    # Validate data before caching
                    if len(visits_df) == 0:
                        # No visit data - skip caching
                        return results_data
                    
                    # Check if enhanced version should also be cached
                    enhanced_data = {}
                    try:
                        from components.treatment_patterns.pattern_analyzer_enhanced import extract_treatment_patterns_with_terminals
                        transitions_enhanced, visits_enhanced = extract_treatment_patterns_with_terminals(results_data['results'])
                        enhanced_data = {
                            'transitions_df_with_terminals': transitions_enhanced,
                            'visits_df_with_terminals': visits_enhanced
                        }
                    except ImportError:
                        pass
                    
                    # Cache the data
                    st.session_state[cache_key] = {
                        'transitions_df': transitions_df,
                        'visits_df': visits_df,
                        'calculated_at': time.time(),
                        **enhanced_data
                    }
                    
                elapsed = time.time() - start_time
                if elapsed > 1.0:
                    st.caption(f"Pattern analysis took {elapsed:.1f}s")
                    
            except Exception as e:
                # Log error but don't crash - allow lazy loading to work
                import logging
                logging.warning(f"Could not pre-calculate treatment patterns: {str(e)}")
                # Clear any partial cache
                if cache_key in st.session_state:
                    del st.session_state[cache_key]
    
    return results_data
```

### 1.3 Update Backward Compatible Caching
**File**: `pages/3_Analysis_Overview.py` - Modify existing function

```python
@st.cache_data
def get_cached_treatment_patterns(sim_id, include_terminals=False):
    """Get treatment patterns with backward compatibility."""
    # First check if data was pre-calculated
    cache_key = f"treatment_patterns_{sim_id}"
    
    if cache_key in st.session_state:
        data = st.session_state[cache_key]
        # Handle enhanced terminals if requested and available
        if include_terminals and 'transitions_df_with_terminals' in data:
            return data['transitions_df_with_terminals'], data['visits_df_with_terminals']
        else:
            return data['transitions_df'], data['visits_df']
    
    # Fall back to on-demand calculation (current behavior)
    # Get results from active simulation
    results_data = get_active_simulation()
    if not results_data:
        return pd.DataFrame(), pd.DataFrame()
    
    results = results_data['results']
    
    # Calculate on demand
    if include_terminals and enhanced_available:
        transitions_df, visits_df = extract_treatment_patterns_with_terminals(results)
    else:
        transitions_df, visits_df = extract_treatment_patterns_vectorized(results)
    
    # Cache for consistency (but not in st.session_state to avoid conflicts)
    # The @st.cache_data decorator handles this caching
    
    return transitions_df, visits_df
```

### 1.4 Create Centralized Data Manager
**New File**: `components/treatment_patterns/data_manager.py`

```python
"""Centralized data management for treatment patterns."""

import streamlit as st
import pandas as pd
from typing import Tuple, Optional

def get_treatment_pattern_data(results) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Get treatment pattern data from cache or calculate."""
    sim_id = results.metadata.sim_id
    cache_key = f"treatment_patterns_{sim_id}"
    
    # Check pre-calculated cache first
    if cache_key in st.session_state:
        data = st.session_state[cache_key]
        return data['transitions_df'], data['visits_df']
    
    # Fall back to calculation
    from components.treatment_patterns import extract_treatment_patterns_vectorized
    return extract_treatment_patterns_vectorized(results)

def ensure_treatment_patterns_cached(sim_id: str) -> bool:
    """Check if treatment patterns are cached."""
    return f"treatment_patterns_{sim_id}" in st.session_state

def clear_treatment_pattern_cache(sim_id: Optional[str] = None):
    """Clear treatment pattern cache."""
    if sim_id:
        cache_key = f"treatment_patterns_{sim_id}"
        if cache_key in st.session_state:
            del st.session_state[cache_key]
    else:
        # Clear all treatment pattern caches
        keys_to_remove = [k for k in st.session_state.keys() if k.startswith("treatment_patterns_")]
        for key in keys_to_remove:
            del st.session_state[key]
```

## Phase 2: Streamgraph Data Processing

### 2.1 Create Time Series Generator
**New File**: `components/treatment_patterns/time_series_generator.py`

```python
"""Generate time series data for treatment state visualization."""

import pandas as pd
import numpy as np
from typing import Optional
import streamlit as st

def generate_patient_state_time_series(
    visits_df: pd.DataFrame,
    time_resolution: str = 'month',
    start_time: float = 0,
    end_time: Optional[float] = None
) -> pd.DataFrame:
    """
    Generate time series of patient counts by state.
    
    Args:
        visits_df: DataFrame with columns: patient_id, time_days, treatment_state
        time_resolution: 'week' or 'month'
        start_time: Start time in months
        end_time: End time in months (None = max from data)
    
    Returns:
        DataFrame with columns:
        - time_point: Time in months
        - state: Treatment state name
        - patient_count: Number of patients in state
        - percentage: Percentage of total patients
    """
    # Handle edge cases
    if len(visits_df) == 0:
        return pd.DataFrame(columns=['time_point', 'state', 'patient_count', 'percentage'])
    
    # Validate data
    if visits_df['patient_id'].nunique() == 1:
        st.warning("Streamgraph may not be meaningful with single patient")
    
    # Convert to months for consistency
    visits_df = visits_df.copy()
    visits_df['time_months'] = visits_df['time_days'] / 30.44
    
    # Determine time range
    if end_time is None:
        end_time = visits_df['time_months'].max()
    
    # Create time points based on resolution
    if time_resolution == 'week':
        time_step = 0.25  # ~1 week in months
    elif time_resolution == 'quarter':
        time_step = 3.0   # 3 months
    else:  # month
        time_step = 1.0
    
    # Limit number of time points for performance
    max_points = 500
    if (end_time - start_time) / time_step > max_points:
        time_step = (end_time - start_time) / max_points
        st.info(f"Using {time_step:.1f} month intervals for performance")
    
    time_points = np.arange(start_time, end_time + time_step, time_step)
    
    # Get all unique patients
    all_patients = visits_df['patient_id'].unique()
    total_patients = len(all_patients)
    
    # Prepare result list
    results = []
    
    # For each time point, determine each patient's state
    for t in time_points:
        # Count patients in each state at this time
        state_counts = get_patient_states_at_time(visits_df, t, end_time)
        
        # Add to results
        for state, count in state_counts.items():
            results.append({
                'time_point': t,
                'state': state,
                'patient_count': count,
                'percentage': (count / total_patients * 100) if total_patients > 0 else 0
            })
    
    return pd.DataFrame(results)

def get_patient_states_at_time(visits_df: pd.DataFrame, time_point: float, sim_end_time: float) -> dict:
    """
    Determine patient states at a specific time point.
    
    Returns dict of {state: count}
    """
    state_counts = {}
    
    # Group by patient
    for patient_id, patient_visits in visits_df.groupby('patient_id'):
        patient_visits = patient_visits.sort_values('time_months')
        
        # Get visits before or at this time point
        past_visits = patient_visits[patient_visits['time_months'] <= time_point]
        
        if len(past_visits) == 0:
            # Patient hasn't started treatment yet
            state = 'Pre-Treatment'
        else:
            # Get most recent visit
            last_visit = past_visits.iloc[-1]
            time_since_last = time_point - last_visit['time_months']
            
            # Check if patient has discontinued (>6 months since last visit)
            if time_since_last > 6:
                state = 'No Further Visits'
            else:
                # Use the treatment state from last visit
                state = last_visit['treatment_state']
        
        # Count this patient
        state_counts[state] = state_counts.get(state, 0) + 1
    
    return state_counts

def validate_time_series_data(time_series_df: pd.DataFrame, total_patients: int):
    """Validate that patient counts are conserved."""
    # Check each time point
    for time_point in time_series_df['time_point'].unique():
        point_data = time_series_df[time_series_df['time_point'] == time_point]
        total_at_point = point_data['patient_count'].sum()
        
        if abs(total_at_point - total_patients) > 1:  # Allow for rounding
            st.error(f"Patient count mismatch at t={time_point}: {total_at_point} vs {total_patients}")
            return False
    
    return True
```

## Phase 3: Visualization Implementation

### 3.1 Create Streamgraph Component
**New File**: `visualizations/streamgraph_treatment_states.py`

```python
"""Treatment state streamgraph visualization using Plotly."""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import streamlit as st
from typing import Optional

from utils.visualization_modes import get_mode_colors
from components.treatment_patterns.pattern_analyzer import STATE_COLOR_MAPPING
from components.treatment_patterns.data_manager import get_treatment_pattern_data
from components.treatment_patterns.time_series_generator import generate_patient_state_time_series

# Define state ordering (bottom to top in streamgraph)
STATE_ORDER = [
    'Pre-Treatment',
    'Initial Treatment',
    'Intensive (Monthly)',
    'Regular (6-8 weeks)', 
    'Extended (12+ weeks)',
    'Maximum Extension (16 weeks)',
    'Restarted After Gap',
    'Treatment Gap (3-6 months)',
    'Extended Gap (6-12 months)',
    'Long Gap (12+ months)',
    'No Further Visits'
]

def create_treatment_state_streamgraph(
    results,
    time_resolution: str = 'month',
    normalize: bool = False,
    height: int = 500,
    show_title: bool = True
) -> go.Figure:
    """
    Create interactive Plotly streamgraph of treatment states.
    
    Args:
        results: Simulation results object
        time_resolution: 'week', 'month', or 'quarter'
        normalize: Show as percentage vs absolute counts
        height: Chart height in pixels
        show_title: Whether to show chart title
        
    Returns:
        Plotly figure object
    """
    # Get treatment pattern data
    transitions_df, visits_df = get_treatment_pattern_data(results)
    
    if len(visits_df) == 0:
        # Return empty figure with message
        fig = go.Figure()
        fig.add_annotation(
            text="No visit data available for streamgraph",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=16)
        )
        fig.update_layout(height=height)
        return fig
    
    # Generate time series data
    with st.spinner("Generating time series data..."):
        time_series_df = generate_patient_state_time_series(
            visits_df,
            time_resolution=time_resolution
        )
    
    if len(time_series_df) == 0:
        fig = go.Figure()
        fig.add_annotation(
            text="Unable to generate time series data",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=16)
        )
        fig.update_layout(height=height)
        return fig
    
    # Get colors from semantic system
    colors = get_mode_colors()
    state_colors = {}
    for state, color_key in STATE_COLOR_MAPPING.items():
        state_colors[state] = colors.get(color_key, '#cccccc')
    
    # Add colors for states not in mapping
    state_colors['Pre-Treatment'] = '#f0f0f0'  # Light gray for pre-treatment
    
    # Pivot data for stacked area chart
    pivot_df = time_series_df.pivot(
        index='time_point',
        columns='state',
        values='patient_count' if not normalize else 'percentage'
    ).fillna(0)
    
    # Ensure all states are present in correct order
    for state in STATE_ORDER:
        if state not in pivot_df.columns:
            pivot_df[state] = 0
    
    # Reorder columns according to STATE_ORDER
    ordered_states = [s for s in STATE_ORDER if s in pivot_df.columns]
    pivot_df = pivot_df[ordered_states]
    
    # Create figure
    fig = go.Figure()
    
    # Add traces for each state
    for state in ordered_states:
        fig.add_trace(go.Scatter(
            x=pivot_df.index,
            y=pivot_df[state],
            mode='lines',
            stackgroup='one',
            name=state,
            line=dict(width=0.5, color=state_colors.get(state, '#cccccc')),
            fillcolor=state_colors.get(state, '#cccccc'),
            hovertemplate=(
                f'<b>{state}</b><br>' +
                'Time: %{x:.1f} months<br>' +
                ('Patients: %{y:,.0f}' if not normalize else 'Percentage: %{y:.1f}%') +
                '<extra></extra>'
            )
        ))
    
    # Update layout
    title = "Patient Treatment States Over Time"
    if normalize:
        title += " (Percentage)"
    
    fig.update_layout(
        title=title if show_title else None,
        xaxis_title="Time (months)",
        yaxis_title="Number of Patients" if not normalize else "Percentage of Patients",
        hovermode='x unified',
        height=height,
        showlegend=True,
        legend=dict(
            orientation="v",
            yanchor="middle",
            y=0.5,
            xanchor="left",
            x=1.02
        )
    )
    
    # Apply clean styling
    fig.update_xaxis(
        showgrid=True,
        gridwidth=1,
        gridcolor='rgba(128,128,128,0.2)',
        zeroline=True,
        zerolinewidth=1,
        zerolinecolor='rgba(128,128,128,0.5)'
    )
    
    fig.update_yaxis(
        showgrid=True,
        gridwidth=1,
        gridcolor='rgba(128,128,128,0.2)',
        zeroline=True,
        zerolinewidth=1,
        zerolinecolor='rgba(128,128,128,0.5)'
    )
    
    return fig

def create_streamgraph_with_sampling(results, max_points: int = 1000) -> go.Figure:
    """
    Create streamgraph with intelligent sampling for large datasets.
    
    Automatically adjusts time resolution based on simulation duration
    to keep visualization performant.
    """
    duration_months = results.metadata.duration_years * 12
    
    # Determine optimal time resolution
    if duration_months / max_points > 3:
        time_resolution = 'quarter'  # 3-month intervals
    elif duration_months / max_points > 1:
        time_resolution = 'month'
    else:
        time_resolution = 'week'
    
    return create_treatment_state_streamgraph(
        results, 
        time_resolution=time_resolution
    )
```

## Phase 4: Integration

### 4.1 Update Analysis Page
**File**: `pages/3_Analysis_Overview.py`

Modify the Patient States tab (tab4):

```python
with tab4:
    st.header("Patient Treatment Flow")
    st.markdown("View of patient cohort flow through different treatment states over time.")
    
    # Import the new streamgraph
    from visualizations.streamgraph_treatment_states import create_treatment_state_streamgraph
    
    # Controls
    col1, col2, col3 = st.columns([2, 2, 6])
    
    with col1:
        normalize = st.checkbox(
            "Show as Percentage",
            value=False,
            help="Display as percentage of total patients vs absolute counts"
        )
    
    with col2:
        time_resolution = st.selectbox(
            "Time Resolution",
            ["week", "month", "quarter"],
            index=1,  # Default to month
            help="Granularity of time points"
        )
    
    # Create the streamgraph
    with st.spinner("Generating treatment flow visualization..."):
        # Cache based on parameters
        @st.cache_data
        def get_streamgraph_figure(sim_id: str, time_res: str, norm: bool):
            # Results already loaded in session
            return create_treatment_state_streamgraph(
                results, 
                time_resolution=time_res,
                normalize=norm
            )
        
        fig = get_streamgraph_figure(
            results.metadata.sim_id, 
            time_resolution, 
            normalize
        )
    
    # Display with export config
    from utils.export_config import get_export_config
    config = get_export_config(filename="patient_treatment_flow")
    st.plotly_chart(fig, use_container_width=True, config=config)
    
    # Add interpretation guide
    with st.expander("Understanding the Treatment Flow"):
        st.markdown("""
        **How to read this visualization:**
        - Each colored band represents patients in a specific treatment state
        - Band thickness shows the number (or percentage) of patients
        - States are ordered from most active (bottom) to discontinued (top)
        - Hover over any point to see exact counts
        
        **Key patterns to look for:**
        - Initial growth as patients start treatment
        - Transitions from intensive to regular intervals
        - Development of treatment gaps over time
        - Accumulation in "No Further Visits" state
        
        **Treatment States:**
        - **Pre-Treatment**: Patients not yet started
        - **Initial/Intensive**: Early treatment phase with frequent visits
        - **Regular/Extended**: Stable treatment with standard intervals
        - **Gaps**: Periods of missed visits
        - **Restarted**: Return to treatment after gaps
        - **No Further Visits**: Discontinued treatment
        """)
    
    # Summary statistics
    if not normalize:
        st.subheader("Current State Distribution")
        
        # Get latest state counts
        from components.treatment_patterns.time_series_generator import get_patient_states_at_time
        
        # Need visits_df - get from cache or data manager
        from components.treatment_patterns.data_manager import get_treatment_pattern_data
        _, visits_df = get_treatment_pattern_data(results)
        
        if len(visits_df) > 0:
            end_time = visits_df['time_days'].max() / 30.44
            current_states = get_patient_states_at_time(visits_df, end_time, end_time)
            
            # Display as metrics
            col1, col2, col3, col4 = st.columns(4)
            
            # Group states for display
            active_states = ['Initial Treatment', 'Intensive (Monthly)', 
                           'Regular (6-8 weeks)', 'Extended (12+ weeks)', 
                           'Maximum Extension (16 weeks)', 'Restarted After Gap']
            gap_states = ['Treatment Gap (3-6 months)', 'Extended Gap (6-12 months)', 
                         'Long Gap (12+ months)']
            
            active_count = sum(current_states.get(s, 0) for s in active_states)
            gap_count = sum(current_states.get(s, 0) for s in gap_states)
            discontinued = current_states.get('No Further Visits', 0)
            pre_treatment = current_states.get('Pre-Treatment', 0)
            
            with col1:
                st.metric("Active Treatment", f"{active_count:,}")
            with col2:
                st.metric("In Treatment Gap", f"{gap_count:,}")
            with col3:
                st.metric("Discontinued", f"{discontinued:,}")
            with col4:
                st.metric("Pre-Treatment", f"{pre_treatment:,}")
```

### 4.2 Remove Old Streamgraph Code
- Remove imports of old streamgraph implementations
- Remove the comprehensive/simple toggle code
- Clean up any unused visualization options

## Phase 5: Testing & Validation

### 5.1 Comprehensive Test Script
**File**: `test_streamgraph_implementation.py`

```python
#!/usr/bin/env python3
"""Test the complete streamgraph implementation."""

import json
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

def run_tests():
    """Run all streamgraph implementation tests."""
    print("=" * 60)
    print("STREAMGRAPH IMPLEMENTATION TEST SUITE")
    print("=" * 60)
    
    # Test 1: Load reference data
    print("\n1. Loading reference data...")
    try:
        with open('sankey_reference_data.json', 'r') as f:
            reference = json.load(f)
        print(f"✓ Reference simulation: {reference['sim_id']}")
    except FileNotFoundError:
        print("❌ No reference data found - run verify_sankey_works.py first")
        return False
    
    # Test 2: Check pre-calculation
    print("\n2. Testing pre-calculation...")
    from utils.state_helpers import get_active_simulation
    from components.treatment_patterns.performance_config import should_precalculate
    
    results_data = get_active_simulation()
    if results_data:
        results = results_data['results']
        print(f"✓ Simulation loaded: {results.metadata.sim_id}")
        print(f"✓ Should pre-calculate: {should_precalculate(results)}")
        
        # Check if data is cached
        cache_key = f"treatment_patterns_{results.metadata.sim_id}"
        if cache_key in st.session_state:
            print("✓ Treatment patterns are pre-cached")
        else:
            print("⚠ Treatment patterns not pre-cached (may be too large)")
    
    # Test 3: Verify backward compatibility
    print("\n3. Testing backward compatibility...")
    from pages.3_Analysis_Overview import get_cached_treatment_patterns
    
    transitions_df, visits_df = get_cached_treatment_patterns(results.metadata.sim_id)
    print(f"✓ Transitions: {len(transitions_df)}")
    print(f"✓ Visits: {len(visits_df)}")
    
    # Compare with reference
    if len(transitions_df) != reference['transition_count']:
        print(f"❌ Transition count mismatch: {len(transitions_df)} vs {reference['transition_count']}")
    else:
        print("✓ Transition count matches reference")
    
    # Test 4: Generate time series
    print("\n4. Testing time series generation...")
    from components.treatment_patterns.time_series_generator import generate_patient_state_time_series
    
    time_series_df = generate_patient_state_time_series(visits_df, time_resolution='month')
    print(f"✓ Time points generated: {time_series_df['time_point'].nunique()}")
    print(f"✓ States tracked: {time_series_df['state'].nunique()}")
    
    # Test 5: Create visualization
    print("\n5. Testing visualization creation...")
    from visualizations.streamgraph_treatment_states import create_treatment_state_streamgraph
    
    fig = create_treatment_state_streamgraph(results, time_resolution='month')
    print(f"✓ Figure created with {len(fig.data)} traces")
    
    # Test 6: Data conservation
    print("\n6. Verifying data conservation...")
    total_patients = results.metadata.n_patients
    
    # Check a few time points
    for t in [0, 6, 12]:
        point_data = time_series_df[time_series_df['time_point'] == t]
        if len(point_data) > 0:
            total_at_point = point_data['patient_count'].sum()
            print(f"✓ Time {t} months: {total_at_point} patients (expected {total_patients})")
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY: All tests completed")
    print("=" * 60)
    
if __name__ == "__main__":
    run_tests()
```

### 5.2 Performance Benchmarks
Monitor and document:
- Pre-calculation time for various simulation sizes
- Streamgraph render time
- Memory usage before/after implementation
- Page load time with pre-calculation

## Implementation Timeline

**Day 0**: Verify Existing Functionality
- Run and document baseline Sankey behavior
- Create verification scripts
- Save reference data
- Test all dependent components
- Set up feature branch

**Day 1**: Data Infrastructure
- Implement performance config
- Add pre-calculation to state_helpers
- Update backward-compatible caching
- Create data_manager module
- Test Sankey still works

**Day 2**: Time Series Generation
- Implement time_series_generator
- Add state tracking logic
- Validate data conservation
- Test with various datasets
- Cross-check with Sankey

**Day 3**: Visualization
- Create streamgraph component
- Apply semantic colors
- Add interactivity
- Test visual output
- Optimize performance

**Day 4**: Integration & Testing
- Update Analysis page
- Remove old code
- Run comprehensive tests
- Document performance
- Final validation

## Success Metrics

1. **Backward Compatibility**
   - ✓ Sankey works identically before/during/after
   - ✓ All pattern-using tabs continue working
   - ✓ No performance degradation

2. **Data Accuracy**
   - ✓ Patient counts conserved at all time points
   - ✓ States match visit interval definitions
   - ✓ Transitions align with Sankey diagram

3. **Performance**
   - ✓ Pre-calculation < 3 seconds for 10k patients
   - ✓ Streamgraph renders < 1 second
   - ✓ Smooth interaction with no lag

4. **User Experience**
   - ✓ Clear visual representation of patient flow
   - ✓ Intuitive controls
   - ✓ Informative hover tooltips
   - ✓ Consistent with app design

## Next Steps

1. Get user approval on this plan
2. Run baseline tests with user
3. Create feature branch
4. Begin Phase 0 implementation
5. Proceed phase by phase with testing