"""Memory management for treatment pattern visualizations."""

import gc
import plotly.graph_objects as go
import streamlit as st


def clear_plotly_cache():
    """Clear Plotly figure cache to prevent memory buildup."""
    # Force garbage collection
    gc.collect()
    
    # Clear any cached Plotly figures in session state
    for key in list(st.session_state.keys()):
        if 'plotly' in key.lower() or 'sankey' in key.lower() or 'fig' in key.lower():
            del st.session_state[key]


def with_memory_cleanup(func):
    """Decorator to ensure memory cleanup after creating visualizations."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        finally:
            # Schedule garbage collection after figure creation
            gc.collect()
    return wrapper


@st.cache_data(ttl=300)  # Cache for 5 minutes
def create_cached_sankey_data(transitions_df_json):
    """Cache the processed Sankey data to avoid recomputation."""
    import pandas as pd
    transitions_df = pd.read_json(transitions_df_json)
    
    # Process data once and cache it
    flow_counts = transitions_df.groupby(['from_state', 'to_state']).size().reset_index(name='count')
    min_flow_size = max(1, len(transitions_df) * 0.001)
    is_terminal = flow_counts['to_state'].str.contains('Still in')
    flow_counts = flow_counts[(flow_counts['count'] >= min_flow_size) | is_terminal]
    
    return flow_counts.to_json()