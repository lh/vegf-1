"""
Session state management utilities for the APE Streamlit application.

This module provides functions for managing session state variables
consistently across the application.
"""

import streamlit as st

def get_simulation_results():
    """Get simulation results from session state.
    
    Returns
    -------
    dict or None
        Simulation results dictionary or None if not available
    """
    return st.session_state.get("simulation_results")

def set_simulation_results(results):
    """Store simulation results in session state.
    
    Parameters
    ----------
    results : dict
        Simulation results to store
    """
    st.session_state["simulation_results"] = results
    st.session_state["simulation_complete"] = True
    
    # Store patient histories in session state if available
    if "patient_histories" in results:
        st.session_state["patient_histories"] = results["patient_histories"]

def get_staggered_results():
    """Get staggered simulation results from session state.
    
    Returns
    -------
    dict or None
        Staggered simulation results dictionary or None if not available
    """
    return st.session_state.get("staggered_results")

def set_staggered_results(results):
    """Store staggered simulation results in session state.
    
    Parameters
    ----------
    results : dict
        Staggered simulation results to store
    """
    st.session_state["staggered_results"] = results

def get_simulation_parameters():
    """Get simulation parameters from session state.
    
    Returns
    -------
    dict
        Dictionary of simulation parameters
    """
    return {
        "simulation_type": st.session_state.get("simulation_type", "ABS"),
        "duration_years": st.session_state.get("duration_years", 5),
        "population_size": st.session_state.get("population_size", 1000),
        "enable_clinician_variation": st.session_state.get("enable_clinician_variation", True),
        "planned_discontinue_prob": st.session_state.get("planned_discontinue_prob", 0.2),
        "admin_discontinue_prob": st.session_state.get("admin_discontinue_prob", 0.05),
        "premature_discontinue_prob": st.session_state.get("premature_discontinue_prob", 2.0),
        "consecutive_stable_visits": st.session_state.get("consecutive_stable_visits", 3),
        "monitoring_schedule": st.session_state.get("monitoring_schedule", [12, 24, 36]),
        "no_monitoring_for_admin": st.session_state.get("no_monitoring_for_admin", True),
        "recurrence_risk_multiplier": st.session_state.get("recurrence_risk_multiplier", 1.0)
    }

def set_simulation_parameters(params):
    """Store simulation parameters in session state.
    
    Parameters
    ----------
    params : dict
        Dictionary of simulation parameters
    """
    for key, value in params.items():
        st.session_state[key] = value

def is_simulation_running():
    """Check if a simulation is currently running.
    
    Returns
    -------
    bool
        True if a simulation is running, False otherwise
    """
    return st.session_state.get("simulation_running", False)

def set_simulation_running(running=True):
    """Set the simulation running status.
    
    Parameters
    ----------
    running : bool, optional
        Whether the simulation is running, by default True
    """
    st.session_state["simulation_running"] = running

def is_simulation_complete():
    """Check if a simulation has completed.
    
    Returns
    -------
    bool
        True if a simulation has completed, False otherwise
    """
    return st.session_state.get("simulation_complete", False)

def get_debug_mode():
    """Get the debug mode status.
    
    Returns
    -------
    bool
        True if debug mode is enabled, False otherwise
    """
    return st.session_state.get("debug_mode_toggle", False)