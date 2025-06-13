"""Caching layer for time series data generation."""

import streamlit as st
import pandas as pd
from typing import Tuple, Optional
import hashlib

def get_cache_key(sim_id: str, time_resolution: str) -> str:
    """Generate cache key for time series data."""
    return f"time_series_{sim_id}_{time_resolution}"

@st.cache_data(show_spinner=False)
def get_cached_time_series_data(
    sim_id: str,
    visits_df_hash: str,  # Hash of visits data to detect changes
    time_resolution: str,
    enrollment_df_hash: Optional[str] = None
) -> pd.DataFrame:
    """
    Cache time series data generation which is the expensive operation.
    
    The actual computation is only done once per simulation and resolution.
    Switching between percentage/absolute is just a view change.
    """
    # Import here to avoid circular imports
    from components.treatment_patterns.time_series_generator import generate_patient_state_time_series
    from components.treatment_patterns.data_manager import get_treatment_pattern_data
    from core.results.factory import ResultsFactory
    
    # Load the actual data - this is needed because we can't pass DataFrames directly
    sim_path = ResultsFactory.DEFAULT_RESULTS_DIR / sim_id
    results = ResultsFactory.load_results(sim_path)
    
    # Get visits data
    _, visits_df = get_treatment_pattern_data(results)
    
    # Get enrollment data if available
    enrollment_df = None
    if hasattr(results, 'get_patients_df'):
        enrollment_df = results.get_patients_df()
    
    # Generate time series - this is the expensive part
    time_series_df = generate_patient_state_time_series(
        visits_df,
        time_resolution=time_resolution,
        enrollment_df=enrollment_df
    )
    
    return time_series_df

def compute_df_hash(df: pd.DataFrame) -> str:
    """Compute a hash of DataFrame to detect changes."""
    # Use shape and sample of data for quick hash
    if df is None or len(df) == 0:
        return "empty"
    
    # Create a string representation of key properties
    hash_str = f"{df.shape}_{df.columns.tolist()}_{len(df)}"
    return hashlib.md5(hash_str.encode()).hexdigest()

def should_show_week_resolution(n_patients: int, duration_years: float) -> bool:
    """
    Determine if week resolution should be offered based on data size.
    
    Week resolution creates ~52 points per year, so:
    - 10,000 patients × 10 years = 520 time points = slow
    - 1,000 patients × 5 years = 260 time points = acceptable
    - 100 patients × 2 years = 104 time points = fast
    """
    expected_points = duration_years * 52
    data_complexity = n_patients * expected_points
    
    # Threshold based on testing: 
    # Above 200,000 complexity units, week resolution becomes sluggish
    return data_complexity < 200_000