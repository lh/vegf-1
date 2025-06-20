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

from ape.core.results.factory import ResultsFactory

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
        
        # Try to load the full protocol specification if available
        protocol_yaml_path = ResultsFactory.DEFAULT_RESULTS_DIR / sim_id / "protocol.yaml"
        if protocol_yaml_path.exists():
            try:
                import yaml
                with open(protocol_yaml_path) as f:
                    protocol_data = yaml.safe_load(f)
                    
                # Check if this is a full protocol spec (has clinical parameters)
                if 'min_interval_days' in protocol_data and 'disease_transitions' in protocol_data:
                    # This is a full protocol spec - save it to temp file and load properly
                    from simulation_v2.protocols.protocol_spec import ProtocolSpecification
                    import tempfile
                    
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
                        yaml.dump(protocol_data, f, default_flow_style=False, sort_keys=False)
                        temp_path = Path(f.name)
                    
                    try:
                        protocol_spec = ProtocolSpecification.from_yaml(temp_path)
                        protocol_info['spec'] = protocol_spec
                        logger.info(f"Loaded full protocol specification for {sim_id}")
                    finally:
                        temp_path.unlink()  # Clean up temp file
                else:
                    # This is just basic metadata
                    logger.warning(f"Protocol file contains only basic metadata for {sim_id}")
                    raise ValueError("Full protocol specification required but not found")
                    
            except Exception as e:
                logger.error(f"Failed to load protocol spec: {e}")
                # Fail fast - protocol spec is required
                raise ValueError(f"Could not load protocol specification: {e}")
        
        # Extract parameters
        parameters = {
            'engine': metadata.get('engine_type', 'abs'),
            'n_patients': metadata.get('n_patients', 0),
            'duration_years': metadata.get('duration_years', 0),
            'seed': metadata.get('seed', 42),
            'runtime': metadata.get('runtime_seconds', 0)
        }
        
        # Load audit trail from dedicated file
        audit_log_path = ResultsFactory.DEFAULT_RESULTS_DIR / sim_id / "audit_log.json"
        if audit_log_path.exists():
            with open(audit_log_path) as f:
                audit_trail = json.load(f)
            logger.info(f"Loaded audit log with {len(audit_trail)} events")
        else:
            # No audit trail - this is expected for simulations that don't have one
            audit_trail = []
            logger.info(f"No audit log file found for {sim_id}")
        
        # Set session state with all required data
        st.session_state.simulation_results = {
            'results': results,  # The actual SimulationResults object
            'protocol': protocol_info,
            'parameters': parameters,
            'audit_trail': audit_trail
        }
        
        # Also ensure current_sim_id is set
        st.session_state.current_sim_id = sim_id
        
        # IMPORTANT: Also set active_simulation_id so get_active_simulation() works
        st.session_state.active_simulation_id = sim_id
        
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
        'active_simulation_id',
        'imported_simulation',
        'audit_trail'  # Also clear audit trail
    ]
    
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
            
    logger.info("Cleared simulation state")


def load_simulation_data(sim_id: str) -> Optional[Dict[str, Any]]:
    """
    Load simulation data without using session state.
    
    This is useful for tests and non-Streamlit contexts.
    
    Args:
        sim_id: The simulation ID to load
        
    Returns:
        Dictionary with simulation data or None if loading failed
    """
    try:
        logger.info(f"Loading simulation data: {sim_id}")
        
        # Load results from disk using the factory
        sim_path = ResultsFactory.DEFAULT_RESULTS_DIR / sim_id
        results = ResultsFactory.load_results(sim_path)
        
        # Load metadata to get additional info
        metadata_path = ResultsFactory.DEFAULT_RESULTS_DIR / sim_id / "metadata.json"
        
        if not metadata_path.exists():
            logger.error(f"Metadata file not found for {sim_id}")
            return None
            
        with open(metadata_path) as f:
            metadata = json.load(f)
        
        # Load protocol info if available
        protocol_info = {
            'name': metadata.get('protocol_name', 'Unknown'),
            'version': metadata.get('protocol_version', '1.0'),
            'path': metadata.get('protocol_path', '')
        }
        
        # Try to load the full protocol specification if available
        protocol_yaml_path = ResultsFactory.DEFAULT_RESULTS_DIR / sim_id / "protocol.yaml"
        if protocol_yaml_path.exists():
            try:
                import yaml
                with open(protocol_yaml_path) as f:
                    protocol_data = yaml.safe_load(f)
                    
                # Check if this is a full protocol spec (has clinical parameters)
                if 'min_interval_days' in protocol_data and 'disease_transitions' in protocol_data:
                    # This is a full protocol spec - save it to temp file and load properly
                    from simulation_v2.protocols.protocol_spec import ProtocolSpecification
                    import tempfile
                    
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
                        yaml.dump(protocol_data, f, default_flow_style=False, sort_keys=False)
                        temp_path = Path(f.name)
                    
                    try:
                        protocol_spec = ProtocolSpecification.from_yaml(temp_path)
                        protocol_info['spec'] = protocol_spec
                        logger.info(f"Loaded full protocol specification for {sim_id}")
                    finally:
                        temp_path.unlink()  # Clean up temp file
                else:
                    # This is just basic metadata
                    logger.warning(f"Protocol file contains only basic metadata for {sim_id}")
                    raise ValueError("Full protocol specification required but not found")
                    
            except Exception as e:
                logger.error(f"Failed to load protocol spec: {e}")
                # Don't fail for tests - just log the error
                logger.warning(f"Continuing without protocol spec: {e}")
        
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
        
        # Return the data structure
        return {
            'results': results,  # The actual SimulationResults object
            'protocol': protocol_info,
            'parameters': parameters,
            'audit_trail': audit_trail
        }
        
    except Exception as e:
        logger.error(f"Failed to load simulation data {sim_id}: {e}")
        return None