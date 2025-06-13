"""Test Streamlit caching effectiveness for workload analysis.

This script simulates how Streamlit's caching works with the workload analysis
and identifies potential issues.
"""

import streamlit as st
import pandas as pd
import numpy as np
import time
import json
import hashlib
from typing import Dict, Any
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import workload analysis functions
from ape.components.treatment_patterns.workload_analyzer_optimized import (
    calculate_clinical_workload_attribution
)
from ape.components.treatment_patterns.workload_visualizations import (
    create_dual_bar_chart,
    create_impact_pyramid,
    create_bubble_chart
)


def create_test_visits_df(num_patients: int = 1000) -> pd.DataFrame:
    """Create test visit data."""
    visits = []
    for i in range(num_patients):
        num_visits = np.random.randint(5, 15)
        current_time = 0
        for j in range(num_visits):
            visits.append({
                'patient_id': i,
                'time_days': current_time,
                'visit_number': j
            })
            if j < num_visits - 1:
                current_time += np.random.randint(30, 90)
    
    return pd.DataFrame(visits)


@st.cache_data
def cached_workload_analysis(visit_data_json: str, sim_id: str) -> Dict[str, Any]:
    """Cached version of workload analysis - matches enhanced_tab.py implementation."""
    print(f"[CACHE MISS] Running workload analysis for sim_id: {sim_id}")
    visits_df = pd.read_json(visit_data_json)
    return calculate_clinical_workload_attribution(visits_df)


@st.cache_data
def cached_visualization(workload_data_json: str, viz_type: str, tufte_mode: bool):
    """Cached visualization creation."""
    print(f"[CACHE MISS] Creating {viz_type} visualization")
    workload_data = json.loads(workload_data_json)
    
    # Reconstruct DataFrames if present
    if 'patient_profiles' in workload_data and workload_data['patient_profiles']:
        workload_data['patient_profiles'] = pd.DataFrame(workload_data['patient_profiles'])
    if 'intensity_categories' in workload_data and workload_data['intensity_categories']:
        workload_data['intensity_categories'] = pd.DataFrame(workload_data['intensity_categories'])
    if 'visit_contributions' in workload_data and workload_data['visit_contributions']:
        workload_data['visit_contributions'] = pd.DataFrame(workload_data['visit_contributions'])
    
    if viz_type == "dual_bar":
        return create_dual_bar_chart(workload_data, tufte_mode)
    elif viz_type == "pyramid":
        return create_impact_pyramid(workload_data, tufte_mode)
    elif viz_type == "bubble":
        return create_bubble_chart(workload_data, tufte_mode)


def test_cache_effectiveness():
    """Test how well caching works with different data."""
    st.title("Streamlit Caching Test for Workload Analysis")
    
    st.header("1. Cache Key Stability Test")
    
    # Create test data
    num_patients = st.slider("Number of patients", 100, 5000, 1000, 100)
    
    if st.button("Generate New Data"):
        st.session_state.visits_df = create_test_visits_df(num_patients)
        st.session_state.data_generated = True
    
    if 'visits_df' not in st.session_state:
        st.session_state.visits_df = create_test_visits_df(num_patients)
        st.session_state.data_generated = True
    
    visits_df = st.session_state.visits_df
    
    # Test cache key generation
    st.subheader("Cache Key Analysis")
    
    # Method 1: Direct DataFrame (NOT CACHEABLE)
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Method 1: Direct DataFrame**")
        try:
            # This would fail in actual caching
            df_hash = hashlib.md5(pd.util.hash_pandas_object(visits_df).values).hexdigest()
            st.code(f"Hash: {df_hash[:16]}...")
            st.error("❌ DataFrames are not hashable for caching")
        except:
            st.error("❌ Cannot hash DataFrame directly")
    
    with col2:
        st.markdown("**Method 2: JSON Serialization**")
        visits_json = visits_df.to_json()
        json_hash = hashlib.md5(visits_json.encode()).hexdigest()
        st.code(f"Hash: {json_hash[:16]}...")
        st.success("✅ JSON is hashable and stable")
    
    # Test workload analysis caching
    st.header("2. Workload Analysis Caching")
    
    sim_id = "test_sim_001"
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Run Analysis (1st time)"):
            start = time.time()
            workload_data = cached_workload_analysis(visits_json, sim_id)
            elapsed = time.time() - start
            st.metric("Execution Time", f"{elapsed:.3f}s")
            st.session_state.workload_data = workload_data
    
    with col2:
        if st.button("Run Analysis (2nd time)"):
            start = time.time()
            workload_data = cached_workload_analysis(visits_json, sim_id)
            elapsed = time.time() - start
            st.metric("Execution Time", f"{elapsed:.3f}s")
            if elapsed < 0.01:
                st.success("✅ Cache hit!")
            else:
                st.warning("⚠️ Cache miss?")
    
    with col3:
        if st.button("Run with Different ID"):
            start = time.time()
            workload_data = cached_workload_analysis(visits_json, "different_id")
            elapsed = time.time() - start
            st.metric("Execution Time", f"{elapsed:.3f}s")
            st.info("Different sim_id = cache miss")
    
    # Test visualization caching
    st.header("3. Visualization Caching")
    
    if 'workload_data' in st.session_state:
        workload_data = st.session_state.workload_data
        
        # Prepare workload data for JSON serialization
        workload_json = json.dumps({
            'summary_stats': workload_data['summary_stats'],
            'total_patients': workload_data['total_patients'],
            'total_visits': workload_data['total_visits'],
            'category_definitions': workload_data['category_definitions']
        })
        
        viz_type = st.selectbox("Visualization Type", ["dual_bar", "pyramid", "bubble"])
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Create Viz (1st time)"):
                start = time.time()
                fig = cached_visualization(workload_json, viz_type, True)
                elapsed = time.time() - start
                st.metric("Creation Time", f"{elapsed:.3f}s")
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            if st.button("Create Viz (2nd time)"):
                start = time.time()
                fig = cached_visualization(workload_json, viz_type, True)
                elapsed = time.time() - start
                st.metric("Creation Time", f"{elapsed:.3f}s")
                if elapsed < 0.01:
                    st.success("✅ Cache hit!")
                else:
                    st.warning("⚠️ Cache miss?")
                st.plotly_chart(fig, use_container_width=True)
    
    # Cache inspection
    st.header("4. Cache Inspection")
    
    if st.button("Clear All Caches"):
        st.cache_data.clear()
        st.success("✅ All caches cleared")
    
    # Performance recommendations
    st.header("5. Performance Recommendations")
    
    st.markdown("""
    ### Key Findings:
    
    1. **DataFrame Serialization**: Always convert DataFrames to JSON for cache keys
    2. **Stable Keys**: Use consistent sim_id or hash of actual data
    3. **Visualization Caching**: Cache at the Plotly figure level, not just data
    4. **Memory Usage**: Large datasets may cause memory issues with caching
    
    ### Optimization Strategies:
    
    - ✅ **Do**: Use JSON serialization for stable cache keys
    - ✅ **Do**: Cache expensive computations (workload analysis)
    - ✅ **Do**: Cache visualization objects
    - ❌ **Don't**: Pass DataFrames directly as cache parameters
    - ❌ **Don't**: Include timestamps in cache keys unless necessary
    - ⚠️ **Consider**: Cache expiration for very large datasets
    """)
    
    # Show memory usage
    st.header("6. Memory Usage")
    
    if 'workload_data' in st.session_state:
        import sys
        
        st.markdown("**Object Sizes:**")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            df_size = visits_df.memory_usage(deep=True).sum() / 1024 / 1024
            st.metric("DataFrame Size", f"{df_size:.1f} MB")
        
        with col2:
            json_size = len(visits_json) / 1024 / 1024
            st.metric("JSON Size", f"{json_size:.1f} MB")
        
        with col3:
            workload_size = sys.getsizeof(workload_json) / 1024 / 1024
            st.metric("Workload JSON", f"{workload_size:.1f} MB")


if __name__ == "__main__":
    test_cache_effectiveness()