"""
Unified simulation loading functionality.

This module provides a consistent way to load simulation results from disk
and populate session state, ensuring all parts of the app stay synchronized.
"""

import streamlit as st
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any

from core.results.factory import ResultsFactory

logger = logging.getLogger(__name__)


def load_simulation_results(sim_id: str) -> bool:
    """
    Load simulation results into session state.
    
    This is the single source of truth for loading simulations. It ensures
    that whenever a simulation is selected, imported, or otherwise made current,
    all the necessary data is loaded into session state.
    
    Args:
        sim_id: The simulation ID to load
        
    Returns:
        True if loading succeeded, False otherwise
    """
    try:
        logger.info(f"Loading simulation: {sim_id}")
        
        # Load results from disk using the factory
        sim_path = ResultsFactory.DEFAULT_RESULTS_DIR / sim_id
        results = ResultsFactory.load_results(sim_path)
        
        # Load metadata to get additional info
        metadata_path = ResultsFactory.DEFAULT_RESULTS_DIR / sim_id / "metadata.json"
        
        if not metadata_path.exists():
            logger.error(f"Metadata file not found for {sim_id}")
            return False
            
        with open(metadata_path) as f:
            metadata = json.load(f)
        
        # Load protocol info if available
        protocol_info = {
            'name': metadata.get('protocol_name', 'Unknown'),
            'version': metadata.get('protocol_version', '1.0'),
            'path': metadata.get('protocol_path', '')
        }
        
        # Extract parameters
        parameters = {
            'engine': metadata.get('engine_type', 'abs'),
            'n_patients': metadata.get('n_patients', 0),
            'duration_years': metadata.get('duration_years', 0),
            'seed': metadata.get('seed', 42),
            'runtime': metadata.get('runtime_seconds', 0)
        }
        
        # Get audit trail if available
        audit_trail = metadata.get('audit_trail', [])
        
        # Set session state with all required data
        st.session_state.simulation_results = {
            'results': results,  # The actual SimulationResults object
            'protocol': protocol_info,
            'parameters': parameters,
            'audit_trail': audit_trail
        }
        
        # Also ensure current_sim_id is set
        st.session_state.current_sim_id = sim_id
        
        logger.info(f"Successfully loaded simulation {sim_id}")
        logger.debug(f"Loaded {parameters['n_patients']} patients, "
                    f"{parameters['duration_years']} years, "
                    f"protocol: {protocol_info['name']}")
        
        return True
        
    except FileNotFoundError as e:
        logger.error(f"Simulation files not found for {sim_id}: {e}")
        st.error(f"❌ Simulation files not found: {sim_id}")
        return False
        
    except json.JSONDecodeError as e:
        logger.error(f"Invalid metadata JSON for {sim_id}: {e}")
        st.error(f"❌ Corrupted metadata for simulation: {sim_id}")
        return False
        
    except Exception as e:
        logger.error(f"Failed to load simulation {sim_id}: {e}")
        st.error(f"❌ Failed to load simulation: {str(e)}")
        return False


def ensure_simulation_loaded() -> bool:
    """
    Ensure that simulation results are loaded in session state.
    
    This function checks if simulation_results exists in session state.
    If not, but current_sim_id exists, it attempts to load the simulation.
    
    Returns:
        True if simulation results are available, False otherwise
    """
    # If we already have results, we're good
    if st.session_state.get('simulation_results'):
        return True
        
    # If we have a current_sim_id but no results, try to load
    if st.session_state.get('current_sim_id'):
        logger.info("Have current_sim_id but no simulation_results, attempting to load")
        return load_simulation_results(st.session_state.current_sim_id)
        
    # No simulation selected
    return False


def get_available_simulations() -> Dict[str, Dict[str, Any]]:
    """
    Get a list of all available simulations with their metadata.
    
    Returns:
        Dictionary mapping sim_id to metadata dict
    """
    simulations = {}
    results_dir = ResultsFactory.DEFAULT_RESULTS_DIR
    
    if not results_dir.exists():
        return simulations
        
    for sim_dir in results_dir.iterdir():
        if not sim_dir.is_dir():
            continue
            
        metadata_path = sim_dir / "metadata.json"
        if metadata_path.exists():
            try:
                with open(metadata_path) as f:
                    metadata = json.load(f)
                    simulations[sim_dir.name] = metadata
            except:
                logger.warning(f"Failed to load metadata for {sim_dir.name}")
                continue
                
    return simulations


def clear_simulation_state():
    """Clear all simulation-related session state."""
    keys_to_clear = [
        'simulation_results',
        'current_sim_id',
        'imported_simulation'
    ]
    
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
            
    logger.info("Cleared simulation state")