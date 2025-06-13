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
    from ape.components.treatment_patterns import extract_treatment_patterns_vectorized
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