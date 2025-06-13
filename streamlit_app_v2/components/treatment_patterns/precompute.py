"""Pre-compute treatment pattern data after simulation completion."""

import streamlit as st
from typing import Optional
from pathlib import Path

def precompute_treatment_patterns(results, show_progress: bool = True) -> None:
    """
    Pre-compute and cache treatment pattern data for common resolutions.
    
    This should be called after simulation completion to make the UI responsive.
    """
    from components.treatment_patterns.time_series_cache import (
        get_cached_time_series_data, compute_df_hash, should_show_week_resolution
    )
    from components.treatment_patterns.data_manager import get_treatment_pattern_data
    
    try:
        # Get the data
        _, visits_df = get_treatment_pattern_data(results)
        if len(visits_df) == 0:
            return
        
        # Compute hashes
        visits_hash = compute_df_hash(visits_df)
        enrollment_hash = None
        if hasattr(results, 'get_patients_df'):
            enrollment_df = results.get_patients_df()
            enrollment_hash = compute_df_hash(enrollment_df)
        
        # Pre-compute for month and quarter (always available)
        resolutions = ['month', 'quarter']
        
        # Add week if appropriate
        if should_show_week_resolution(results.metadata.n_patients, results.metadata.duration_years):
            resolutions.append('week')
        
        if show_progress:
            progress_text = st.empty()
            progress_bar = st.progress(0)
        
        for i, resolution in enumerate(resolutions):
            if show_progress:
                progress_text.text(f"Pre-computing {resolution} resolution...")
                progress_bar.progress((i + 1) / len(resolutions))
            
            # This will compute and cache
            _ = get_cached_time_series_data(
                results.metadata.sim_id,
                visits_hash,
                resolution,
                enrollment_hash
            )
        
        if show_progress:
            progress_text.empty()
            progress_bar.empty()
            
    except Exception as e:
        # Don't fail simulation if pre-computation fails
        print(f"Warning: Failed to pre-compute treatment patterns: {e}")