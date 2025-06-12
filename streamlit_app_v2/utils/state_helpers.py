"""
Simple state management helpers for multi-simulation support.

Provides functions to manage simulation registry and active simulation
in Streamlit session state.
"""

import streamlit as st
from typing import Dict, Any, Optional
from datetime import datetime
import json
from pathlib import Path


def init_simulation_registry():
    """Initialize the simulation registry in session state if not present."""
    if 'simulation_registry' not in st.session_state:
        st.session_state.simulation_registry = {}
    
    # Ensure audit_trail is also initialized
    if 'audit_trail' not in st.session_state:
        st.session_state.audit_trail = None


def get_simulation_registry() -> Dict[str, Any]:
    """Get the current simulation registry."""
    init_simulation_registry()
    return st.session_state.simulation_registry


def add_simulation_to_registry(sim_id: str, simulation_data: Dict[str, Any]) -> None:
    """
    Add a simulation to the registry.
    
    Maintains a maximum of 5 simulations using FIFO eviction.
    
    Args:
        sim_id: Unique simulation identifier
        simulation_data: Complete simulation data including results, params, etc.
    """
    init_simulation_registry()
    registry = st.session_state.simulation_registry
    
    # Add timestamp if not present
    if 'added_at' not in simulation_data:
        simulation_data['added_at'] = datetime.now().isoformat()
    
    # Add to registry
    registry[sim_id] = simulation_data
    
    # Evict oldest if over limit (FIFO)
    if len(registry) > 5:
        # Find oldest by added_at timestamp
        oldest_id = min(registry.keys(), 
                       key=lambda x: registry[x].get('added_at', ''))
        del registry[oldest_id]
    
    # Update session state
    st.session_state.simulation_registry = registry


def get_active_simulation() -> Optional[Dict[str, Any]]:
    """
    Get the currently active simulation and pre-calculate treatment patterns.
    
    Returns:
        Active simulation data or None if no active simulation
    """
    # First check if there's an active_simulation_id
    results_data = None
    
    if 'active_simulation_id' in st.session_state:
        sim_id = st.session_state.active_simulation_id
        registry = get_simulation_registry()
        if sim_id in registry:
            results_data = registry[sim_id]
    
    # Fallback to legacy simulation_results for backward compatibility
    if results_data is None and 'simulation_results' in st.session_state:
        results_data = st.session_state.simulation_results
    
    if results_data:
        # Only do pre-calculation if results object exists
        if 'results' in results_data and hasattr(results_data['results'], 'metadata'):
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


def set_active_simulation(sim_id: str) -> bool:
    """
    Set the active simulation by ID.
    
    Args:
        sim_id: Simulation ID to make active
        
    Returns:
        True if successful, False if simulation not found
    """
    registry = get_simulation_registry()
    
    if sim_id not in registry:
        return False
    
    # Set active ID
    st.session_state.active_simulation_id = sim_id
    
    # Also set current_sim_id for consistency with load_simulation_results
    st.session_state.current_sim_id = sim_id
    
    # Also update legacy session state for compatibility
    st.session_state.simulation_results = registry[sim_id]
    
    # Sync audit trail if present
    if 'audit_trail' in registry[sim_id]:
        st.session_state.audit_trail = registry[sim_id]['audit_trail']
    
    return True


def get_latest_simulation_id() -> Optional[str]:
    """
    Get the ID of the most recently added simulation.
    
    Returns:
        Simulation ID or None if no simulations
    """
    registry = get_simulation_registry()
    
    if not registry:
        return None
    
    # Find most recent by added_at timestamp
    latest_id = max(registry.keys(), 
                   key=lambda x: registry[x].get('added_at', ''))
    return latest_id


def clear_simulation_registry():
    """Clear all simulations from the registry."""
    st.session_state.simulation_registry = {}
    st.session_state.active_simulation_id = None
    st.session_state.current_sim_id = None
    st.session_state.simulation_results = None
    st.session_state.audit_trail = None


def get_simulation_summary(sim_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a summary of a simulation without loading full data.
    
    Args:
        sim_id: Simulation ID
        
    Returns:
        Summary dict with key info or None if not found
    """
    registry = get_simulation_registry()
    
    if sim_id not in registry:
        return None
    
    sim_data = registry[sim_id]
    
    # Extract summary info
    return {
        'sim_id': sim_id,
        'protocol_name': sim_data.get('protocol', {}).get('name', 'Unknown'),
        'n_patients': sim_data.get('parameters', {}).get('n_patients', 0),
        'duration_years': sim_data.get('parameters', {}).get('duration_years', 0),
        'engine': sim_data.get('parameters', {}).get('engine', 'Unknown'),
        'timestamp': sim_data.get('timestamp', 'Unknown'),
        'added_at': sim_data.get('added_at', 'Unknown')
    }


def list_simulation_summaries() -> list[Dict[str, Any]]:
    """
    Get summaries of all simulations in registry.
    
    Returns:
        List of summary dicts, sorted by added_at (newest first)
    """
    registry = get_simulation_registry()
    
    summaries = []
    for sim_id in registry:
        summary = get_simulation_summary(sim_id)
        if summary:
            summaries.append(summary)
    
    # Sort by added_at, newest first
    summaries.sort(key=lambda x: x.get('added_at', ''), reverse=True)
    
    return summaries


def save_protocol_spec(sim_data: Dict[str, Any], protocol_path: Path) -> None:
    """
    Ensure protocol specification is saved with simulation data.
    
    Args:
        sim_data: Simulation data dictionary to update
        protocol_path: Path to the protocol YAML file
    """
    if protocol_path.exists():
        # Read the protocol YAML content
        with open(protocol_path, 'r') as f:
            protocol_yaml = f.read()
        
        # Store in simulation data
        if 'protocol' not in sim_data:
            sim_data['protocol'] = {}
        
        sim_data['protocol']['yaml_content'] = protocol_yaml
        sim_data['protocol']['yaml_path'] = str(protocol_path)


def load_protocol_spec(sim_data: Dict[str, Any]) -> Optional[str]:
    """
    Load protocol specification from simulation data.
    
    Args:
        sim_data: Simulation data dictionary
        
    Returns:
        Protocol YAML content or None if not found
    """
    protocol_info = sim_data.get('protocol', {})
    
    # First try to get stored YAML content
    if 'yaml_content' in protocol_info:
        return protocol_info['yaml_content']
    
    # Fallback to reading from original path if available
    if 'path' in protocol_info:
        yaml_path = Path(protocol_info['path'])
        if yaml_path.exists():
            with open(yaml_path, 'r') as f:
                return f.read()
    
    return None