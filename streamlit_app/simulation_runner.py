"""
Simulation Runner Module

This module handles running simulations from the Streamlit UI and processing results.
"""

import os
import sys
import json
import tempfile
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import streamlit as st
import time
from datetime import datetime

# Import custom JSON utilities
from streamlit_app.json_utils import APEJSONEncoder, save_json, load_json

# Add the project root directory to sys.path to allow importing from the main project
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root_dir)

# Also add the current working directory (important when running as a module)
sys.path.append(os.getcwd())

# Import simulation modules
try:
    from simulation.config import SimulationConfig
    
    # Import fixed simulation classes
    from treat_and_extend_abs_fixed import TreatAndExtendABS
    from treat_and_extend_des_fixed import TreatAndExtendDES
    
    # Import parsing modules
    from protocols.protocol_parser import ProtocolParser
    from protocol_models import TreatmentProtocol
    
    # Flag that imports were successful
    simulation_imports_successful = True
    
    # Create a flag to show the notice after the app is initialized
    USING_FIXED_IMPLEMENTATION = True
except ImportError as e:
    st.error(f"Failed to import simulation modules: {e}")
    st.info("This may be due to missing dependencies or incorrect import paths.")
    simulation_imports_successful = False


def create_simulation_config(params):
    """
    Create a simulation configuration from UI parameters.
    
    Parameters
    ----------
    params : dict
        Dictionary of parameters from the UI
    
    Returns
    -------
    SimulationConfig
        Configuration object for simulation
    """
    # Instead of creating our own config from scratch, use an existing 
    # configuration as a base
    test_config_name = "test_simulation"
    
    # Create a SimulationConfig from an existing template
    config = SimulationConfig.from_yaml(test_config_name)
    
    # Override specific parameters based on user input
    config.num_patients = params["population_size"]
    config.duration_days = params["duration_years"] * 365
    config.simulation_type = params["simulation_type"].lower()
    
    # Apply any additional parameter overrides as needed
    # For discontinuation settings, we'd need to modify the parameters dictionary
    
    return config


def run_simulation(params):
    """
    Run a simulation with the given parameters.
    
    Parameters
    ----------
    params : dict
        Dictionary of parameters from the UI
    
    Returns
    -------
    dict
        Simulation results
    """
    with st.spinner(f"Running {params['simulation_type']} simulation..."):
        start_time = time.time()
        
        # Check if simulation modules are available
        if not simulation_imports_successful:
            st.error("Simulation modules not available. Please check your installation.")
            # Return an error result
            return {
                "error": "Simulation modules not available",
                "simulation_type": params["simulation_type"],
                "population_size": params["population_size"],
                "duration_years": params["duration_years"],
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "failed": True
            }
        
        try:
            # Display simulation settings
            st.info(f"Running {params['simulation_type']} simulation with {params['population_size']} patients for {params['duration_years']} years")
            
            # Use an existing simulation configuration as base
            test_config_name = "test_simulation"
            test_config_path = os.path.join(root_dir, "protocols", "simulation_configs", f"{test_config_name}.yaml")
            
            st.info(f"Using base configuration: {test_config_name}")
            
            # Create a SimulationConfig from an existing YAML file
            # Note: SimulationConfig.from_yaml expects the config name, not the file path
            config = SimulationConfig.from_yaml(test_config_name)
            
            # Display base config settings
            st.info(f"Base configuration loaded with {config.num_patients} patients and {config.duration_days} days duration")
            
            # Override specific parameters based on user input
            config.num_patients = params["population_size"]
            config.duration_days = params["duration_years"] * 365
            config.simulation_type = params["simulation_type"].lower()
            
            # Update discontinuation settings - create the structure if it doesn't exist
            if not hasattr(config, 'parameters'):
                config.parameters = {}
            
            # Ensure the discontinuation structure exists with correct fields
            if 'discontinuation' not in config.parameters:
                config.parameters['discontinuation'] = {
                    'enabled': True,
                    'criteria': {
                        'stable_max_interval': {
                            'consecutive_visits': 3,
                            'probability': 0.2
                        },
                        'random_administrative': {
                            'annual_probability': 0.05
                        },
                        'treatment_duration': {
                            'threshold_weeks': 52,
                            'probability': 0.1
                        }
                    },
                    'monitoring': {
                        'follow_up_schedule': [12, 24, 36],
                        'recurrence_detection_probability': 0.87
                    },
                    'retreatment': {
                        'eligibility_criteria': {
                            'detected_fluid': True,
                            'vision_loss_letters': 5
                        },
                        'probability': 0.95
                    }
                }
                st.info("Created default discontinuation settings")
            else:
                # Make sure 'enabled' is True
                config.parameters['discontinuation']['enabled'] = True
                st.info("Ensured discontinuation is enabled")
                
                # Ensure criteria structure exists
                if 'criteria' not in config.parameters['discontinuation']:
                    config.parameters['discontinuation']['criteria'] = {}
                
                # Ensure monitoring structure exists
                if 'monitoring' not in config.parameters['discontinuation']:
                    config.parameters['discontinuation']['monitoring'] = {}
                
                # Ensure retreatment structure exists
                if 'retreatment' not in config.parameters['discontinuation']:
                    config.parameters['discontinuation']['retreatment'] = {}
            
            # Now update the discontinuation settings
            disc_criteria = config.parameters['discontinuation']['criteria']
            
            # Ensure stable_max_interval settings exist
            if 'stable_max_interval' not in disc_criteria:
                disc_criteria['stable_max_interval'] = {
                    'consecutive_visits': 3,
                    'probability': 0.2
                }
                
            # Ensure random_administrative settings exist
            if 'random_administrative' not in disc_criteria:
                disc_criteria['random_administrative'] = {
                    'annual_probability': 0.05
                }
                
            # Update stable_max_interval probability from UI
            disc_criteria['stable_max_interval']['probability'] = params["planned_discontinue_prob"]
            st.info(f"Setting planned discontinuation probability to {params['planned_discontinue_prob']}")
            
            # Update random_administrative probability from UI
            disc_criteria['random_administrative']['annual_probability'] = params["admin_discontinue_prob"]
            st.info(f"Setting administrative discontinuation probability to {params['admin_discontinue_prob']}")
            
            # Update consecutive stable visits requirement from UI
            if 'consecutive_stable_visits' in params:
                disc_criteria['stable_max_interval']['consecutive_visits'] = params["consecutive_stable_visits"]
                st.info(f"Setting consecutive stable visits to {params['consecutive_stable_visits']}")
            
            # Update monitoring settings
            monitoring = config.parameters['discontinuation']['monitoring']
            
            # Ensure monitoring has follow_up_schedule
            if 'follow_up_schedule' not in monitoring:
                monitoring['follow_up_schedule'] = [12, 24, 36]
            
            # Update monitoring schedule from UI
            if 'monitoring_schedule' in params:
                monitoring['follow_up_schedule'] = params["monitoring_schedule"]
                st.info(f"Setting monitoring schedule to {params['monitoring_schedule']}")
            
            # Create or update planned monitoring
            if 'planned' not in monitoring:
                monitoring['planned'] = {}
            monitoring['planned']['follow_up_schedule'] = monitoring['follow_up_schedule']
            
            # Set no monitoring for administrative discontinuations if specified
            if params.get("no_monitoring_for_admin", True):
                if 'administrative' not in monitoring:
                    monitoring['administrative'] = {}
                monitoring['administrative']['follow_up_schedule'] = []
                st.info("Disabled monitoring for administrative discontinuations")
            
            # Enable/disable clinician variation
            if hasattr(config, 'parameters') and 'clinicians' in config.parameters:
                config.parameters['clinicians']['enabled'] = params["enable_clinician_variation"]
                st.info(f"Clinician variation {'enabled' if params['enable_clinician_variation'] else 'disabled'}")
            
            # Run appropriate simulation type
            if params["simulation_type"] == "ABS":
                progress_text = st.empty()
                progress_bar = st.progress(0)
                
                # Display progress update before starting
                progress_text.text("Initializing ABS simulation...")
                progress_bar.progress(10)
                
                # Create simulation instance
                sim = TreatAndExtendABS(config)
                
                # Update progress
                progress_text.text("Generating patients...")
                progress_bar.progress(20)
                
                # Update progress during simulation (estimate 80% of time for running)
                def progress_callback(percent):
                    progress_bar.progress(20 + int(percent * 0.6))
                    progress_text.text(f"Running simulation... {int(percent)}% complete")
                
                # Run simulation
                patient_histories = sim.run()
                
                # Update progress
                progress_text.text("Processing results...")
                progress_bar.progress(80)
                
            else:  # DES
                progress_text = st.empty()
                progress_bar = st.progress(0)
                
                # Display progress update before starting
                progress_text.text("Initializing DES simulation...")
                progress_bar.progress(10)
                
                # Create simulation instance
                sim = TreatAndExtendDES(config)
                
                # Update progress
                progress_text.text("Generating patients...")
                progress_bar.progress(20)
                
                # Run simulation
                patient_histories = sim.run()
                
                # Update progress
                progress_text.text("Processing results...")
                progress_bar.progress(80)
            
            # Calculate runtime
            end_time = time.time()
            runtime = end_time - start_time
            
            # Update progress
            progress_text.text(f"Simulation completed in {runtime:.2f} seconds")
            progress_bar.progress(100)
            
            # Process results
            results = process_simulation_results(sim, patient_histories, params)
            results["runtime_seconds"] = runtime
            
            # CRITICAL FIX: Also store direct simulation stats separately to ensure we don't lose them
            if hasattr(sim, 'stats'):
                results["simulation_stats"] = sim.stats
                # Ensure retreatments are properly captured
                if "retreatments" in sim.stats and sim.stats["retreatments"] > 0:
                    # Store direct retreatment info where the UI can easily find it
                    if "raw_discontinuation_stats" not in results:
                        results["raw_discontinuation_stats"] = {}
                    results["raw_discontinuation_stats"]["retreatments"] = sim.stats["retreatments"]
                    if "unique_retreatments" in sim.stats:
                        results["raw_discontinuation_stats"]["unique_patient_retreatments"] = sim.stats["unique_retreatments"]
                    
                    # Force update recurrences data structure 
                    if "recurrences" not in results:
                        results["recurrences"] = {"total": 0, "by_type": {}, "unique_count": 0}
                    results["recurrences"]["total"] = max(results["recurrences"].get("total", 0), sim.stats["retreatments"])
                    if "unique_retreatments" in sim.stats:
                        results["recurrences"]["unique_count"] = sim.stats["unique_retreatments"]
                        
                    print(f"Fixed retreatment stats: {sim.stats['retreatments']} total, {sim.stats.get('unique_retreatments', 0)} unique")
                
            # Store patient histories in results
            results["patient_histories"] = patient_histories
            
            return results
        
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            st.error(f"Error running simulation: {e}")
            
            # Show detailed error info in an expandable section
            with st.expander("Show error details"):
                st.code(error_details)
                
            st.error("Simulation failed. Please check the error details and try again with different parameters.")
            
            # If a temp file was created, clean it up
            if 'config_path' in locals():
                try:
                    os.unlink(config_path)
                except Exception as file_error:
                    st.warning(f"Could not delete temporary file: {file_error}")
                    
            # Return a minimal error result
            return {
                "error": str(e),
                "simulation_type": params["simulation_type"],
                "population_size": params["population_size"],
                "duration_years": params["duration_years"],
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "failed": True
            }


def generate_sample_results(params):
    """
    Generate sample simulation results when actual simulation can't be run.
    
    Parameters
    ----------
    params : dict
        Dictionary of parameters from the UI
    
    Returns
    -------
    dict
        Sample simulation results
    """
    # Wait a moment to simulate processing time
    time.sleep(1)
    
    # Get parameters
    simulation_type = params.get("simulation_type", "ABS")
    population_size = params.get("population_size", 1000)
    duration_years = params.get("duration_years", 5)
    planned_discontinue_prob = params.get("planned_discontinue_prob", 0.2)
    admin_discontinue_prob = params.get("admin_discontinue_prob", 0.05)
    
    # Create sample discontinuation counts
    planned_count = int(population_size * planned_discontinue_prob * 2.5)  # Multiplier to simulate accumulation over time
    admin_count = int(population_size * admin_discontinue_prob * 5)  # Administrative events accumulate over time
    time_based_count = int(population_size * 0.2)  # Fixed percentage for sample data
    premature_count = int(population_size * 0.1)  # Fixed percentage for sample data
    
    # Create sample visual acuity data
    months = np.linspace(0, duration_years * 12, 60)
    mean_va_data = []
    
    for month in months:
        # Create a realistic VA curve that starts at 65, improves to 75, then declines slowly
        va = 65 + 10 * (1 - np.exp(-0.3 * month)) if month < 12 else 75 - 0.15 * (month - 12)
        mean_va_data.append({
            "time": float(month),
            "visual_acuity": float(va)
        })
    
    # Create sample results dictionary
    results = {
        "simulation_type": simulation_type,
        "population_size": population_size,
        "duration_years": duration_years,
        "planned_discontinue_prob": planned_discontinue_prob,
        "admin_discontinue_prob": admin_discontinue_prob,
        "enable_clinician_variation": params.get("enable_clinician_variation", True),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "patient_count": population_size,
        "is_sample": True,
        "discontinuation_counts": {
            "Planned": planned_count,
            "Administrative": admin_count,
            "Time-based": time_based_count,
            "Premature": premature_count
        },
        "total_discontinuations": planned_count + admin_count + time_based_count + premature_count,
        "recurrences": {
            "total": int((planned_count + admin_count + time_based_count + premature_count) * 0.4)
        },
        "mean_va_data": mean_va_data,
        "mean_injections": 7.2,
        "total_injections": int(7.2 * population_size),
        "runtime_seconds": 1.0
    }
    
    return results


def process_simulation_results(sim, patient_histories, params):
    """
    Process simulation results into a format for visualization.
    
    Parameters
    ----------
    sim : TreatAndExtendABS or TreatAndExtendDES
        The simulation object
    patient_histories : list
        List of patient histories
    params : dict
        Simulation parameters
    
    Returns
    -------
    dict
        Processed results for visualization
    """
    results = {
        "simulation_type": params["simulation_type"],
        "population_size": params["population_size"],
        "duration_years": params["duration_years"],
        "enable_clinician_variation": params["enable_clinician_variation"],
        "planned_discontinue_prob": params["planned_discontinue_prob"],
        "admin_discontinue_prob": params["admin_discontinue_prob"],
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "patient_count": len(patient_histories)
    }
    
    # Process discontinuation information
    discontinuation_manager = None
    
    # Try different ways to access the discontinuation manager
    if hasattr(sim, 'get_discontinuation_manager'):
        discontinuation_manager = sim.get_discontinuation_manager()
    elif hasattr(sim, 'discontinuation_manager'):
        discontinuation_manager = sim.discontinuation_manager
    elif hasattr(sim, 'refactored_manager'):  # For the fixed implementation
        discontinuation_manager = sim.refactored_manager
    else:
        st.warning("Could not access discontinuation manager - discontinuation statistics will be limited")
        
    # Check for unique discontinuation count from fixed implementation
    unique_discontinued_patients = 0
    if hasattr(sim, 'stats') and "unique_discontinuations" in sim.stats:
        unique_discontinued_patients = sim.stats["unique_discontinuations"]
        results["unique_discontinued_patients"] = unique_discontinued_patients
    
    # Initialize default counts
    discontinuation_counts = {
        "Planned": 0,
        "Administrative": 0,
        "Time-based": 0,
        "Premature": 0
    }
    
    # Debug output
    if discontinuation_manager:
        st.info(f"Found discontinuation manager: {type(discontinuation_manager).__name__}")
        st.info(f"Discontinuation manager stats: {hasattr(discontinuation_manager, 'stats')}")
        if hasattr(discontinuation_manager, 'stats'):
            st.info(f"Stats keys: {list(discontinuation_manager.stats.keys())}")
    
    # Process statistics if we have a discontinuation manager
    if discontinuation_manager:
        # First try the get_statistics method
        if hasattr(discontinuation_manager, 'get_statistics'):
            disc_stats = discontinuation_manager.get_statistics()
            
            # Extract counts from statistics - structure depends on implementation
            if isinstance(disc_stats, dict):
                # First look for discontinuations key
                if "discontinuations" in disc_stats:
                    for disc_type, count in disc_stats["discontinuations"].items():
                        # Map to standardized types
                        if "stable" in disc_type.lower():
                            discontinuation_counts["Planned"] = count
                        elif "admin" in disc_type.lower():
                            discontinuation_counts["Administrative"] = count
                        elif "duration" in disc_type.lower() or "time" in disc_type.lower():
                            discontinuation_counts["Time-based"] = count
                        elif "premature" in disc_type.lower():
                            discontinuation_counts["Premature"] = count
                # Also look for specific discontinuation type counts
                else:
                    # Look for specific stat keys (more common in EnhancedDiscontinuationManager)
                    if "stable_max_interval_discontinuations" in disc_stats:
                        discontinuation_counts["Planned"] = disc_stats["stable_max_interval_discontinuations"]
                    if "random_administrative_discontinuations" in disc_stats:
                        discontinuation_counts["Administrative"] = disc_stats["random_administrative_discontinuations"]
                    if "treatment_duration_discontinuations" in disc_stats:
                        discontinuation_counts["Time-based"] = disc_stats["treatment_duration_discontinuations"]
                    if "premature_discontinuations" in disc_stats:
                        discontinuation_counts["Premature"] = disc_stats["premature_discontinuations"]
        
        # If we don't have data yet, try accessing the stats dictionary directly
        elif hasattr(discontinuation_manager, 'stats'):
            stats = discontinuation_manager.stats
            
            # Extract values from the stats dictionary
            discontinuation_counts["Planned"] = stats.get("stable_max_interval_discontinuations", 0)
            discontinuation_counts["Administrative"] = stats.get("random_administrative_discontinuations", 0)
            discontinuation_counts["Time-based"] = stats.get("treatment_duration_discontinuations", 0)
            discontinuation_counts["Premature"] = stats.get("premature_discontinuations", 0)
            
            # Collect recurrence/retreatment statistics
            # First check simulation stats for retreatment numbers - this is our primary source of truth
            sim_retreatments = stats.get("retreatments", 0)
            unique_retreatments = stats.get("unique_retreatments", 0)
            
            # Emergency debug output - force display of simulation stats
            st.info(f"DEBUG - Simulation retreatment stats: total={sim_retreatments}, unique={unique_retreatments}")
            
            # Look for retreatment stats from discontinuation manager
            if "retreatments_by_type" in stats:
                retreatment_stats = stats["retreatments_by_type"]
                if sum(retreatment_stats.values()) == 0 and sim_retreatments > 0:
                    st.warning(f"Found {sim_retreatments} retreatments in simulation but empty retreatment_by_type in manager")
            else:
                # Initialize with empty dict if not found
                retreatment_stats = {'stable_max_interval': 0, 'premature': 0, 'random_administrative': 0, 'treatment_duration': 0}
                st.warning("No retreatment_by_type found in stats, using empty dictionary")
                
            # Override the zeros in retreatment_stats if we have better data from the simulation
            if sim_retreatments > 0 and sum(retreatment_stats.values()) == 0:
                # Since we don't have the breakdown by type, distribute proportionally
                # based on discontinuation counts to estimate distribution
                total_discontinuations = sum(discontinuation_counts.values())
                if total_discontinuations > 0:
                    for disc_type, count in discontinuation_counts.items():
                        if disc_type == "Planned":
                            type_key = "stable_max_interval"
                        elif disc_type == "Administrative":
                            type_key = "random_administrative"
                        elif disc_type == "Time-based":
                            type_key = "treatment_duration"
                        elif disc_type == "Premature":
                            type_key = "premature"
                        else:
                            continue
                            
                        # Distribute retreatments proportionally
                        proportion = count / total_discontinuations
                        retreatment_stats[type_key] = int(sim_retreatments * proportion)
                else:
                    # If no discontinuation counts, split evenly
                    even_split = sim_retreatments // 4
                    retreatment_stats = {
                        'stable_max_interval': even_split,
                        'premature': even_split,
                        'random_administrative': even_split,
                        'treatment_duration': sim_retreatments - (3 * even_split)  # Remainder to treatment_duration
                    }
            
            # Store both the total and breakdown in results
            # CRITICAL FIX: Always use the simulation retreatment count as the source of truth
            # Even if the retreatment_by_type is empty, we need to ensure the total is correct
            results["recurrences"] = {
                "total": sim_retreatments,  # Always use sim_retreatments
                "by_type": retreatment_stats,
                "unique_count": unique_retreatments
            }
            
            # Emergency check for recurrence data
            if sim_retreatments > 0 and results["recurrences"]["total"] != sim_retreatments:
                st.error(f"CRITICAL: Recurrence total mismatch! sim={sim_retreatments}, results={results['recurrences']['total']}")
                # Force fix
                results["recurrences"]["total"] = sim_retreatments
        
        # Add additional debugging for discontinuation counts
        st.info(f"Found discontinuation counts: {discontinuation_counts}")
        st.info(f"Total discontinuations counted: {sum(discontinuation_counts.values())}")
        
        # Also check if we can directly extract total discontinuations from stats
        total_discontinuations = 0
        if hasattr(discontinuation_manager, 'stats') and "total_discontinuations" in discontinuation_manager.stats:
            total_discontinuations = discontinuation_manager.stats["total_discontinuations"]
            st.info(f"Total discontinuations from manager stats: {total_discontinuations}")
        
        # Store the discontinuation data in results
        results["discontinuation_counts"] = discontinuation_counts
        results["total_discontinuations"] = max(sum(discontinuation_counts.values()), total_discontinuations)
        
        # Add other statistics if available
        if "recurrences" in disc_stats:
            results["recurrences"] = disc_stats["recurrences"]
        if "retreatments" in disc_stats:
            results["retreatments"] = disc_stats["retreatments"]
            
        # Add raw stats for debugging
        results["raw_discontinuation_stats"] = disc_stats
    
    # Process patient histories for visual acuity outcomes
    va_data = []
    
    # Add debug info to help understand patient data structure
    if patient_histories:
        # Examine the structure of patient_histories first
        st.info(f"Patient histories type: {type(patient_histories).__name__}")
        st.info(f"Patient histories count: {len(patient_histories)}")
        
        # Analyze a sample patient to understand its structure
        if isinstance(patient_histories, dict) and patient_histories:
            # Get a sample patient ID
            sample_id = next(iter(patient_histories))
            sample_patient = patient_histories[sample_id]
            
            st.info(f"Sample patient (ID {sample_id}) type: {type(sample_patient).__name__}")
            
            # Extract sample history
            if isinstance(sample_patient, list):
                st.info(f"Sample patient is a list with {len(sample_patient)} records")
                if sample_patient:
                    st.info(f"First record type: {type(sample_patient[0]).__name__}")
                    if isinstance(sample_patient[0], dict):
                        st.info(f"First record keys: {list(sample_patient[0].keys())}")
            elif hasattr(sample_patient, 'history') and sample_patient.history:
                st.info(f"Sample patient history length: {len(sample_patient.history)}")
                st.info(f"First record type: {type(sample_patient.history[0]).__name__}")
                if isinstance(sample_patient.history[0], dict):
                    st.info(f"First record keys: {list(sample_patient.history[0].keys())}")
            
            # Show additional attributes
            additional_attrs = []
            if not isinstance(sample_patient, dict) and not isinstance(sample_patient, list):
                for attr in ['disease_activity', 'treatment_status', 'current_phase']:
                    if hasattr(sample_patient, attr):
                        additional_attrs.append(attr)
                if additional_attrs:
                    st.info(f"Patient has attributes: {additional_attrs}")
        else:
            st.warning("Unable to extract detailed patient structure")
    
    # Try different ways to extract visual acuity data
    for patient_id, patient in patient_histories.items() if isinstance(patient_histories, dict) else enumerate(patient_histories):
        # For dict-style patient histories
        if isinstance(patient_histories, dict):
            patient_obj = patient
            pid = patient_id
        else:
            patient_obj = patient
            pid = getattr(patient, 'id', f"patient_{patient_id}")
        
        # Try different attribute/key names for acuity history
        if hasattr(patient_obj, 'acuity_history'):
            # Check what type the acuity_history is
            acuity_history = patient_obj.acuity_history
            if isinstance(acuity_history, list):
                for item in acuity_history:
                    if isinstance(item, tuple) and len(item) == 2:
                        # Handle (time, va) tuples
                        time, va = item
                        va_data.append({
                            "patient_id": pid,
                            "time": time,
                            "visual_acuity": va
                        })
                    elif isinstance(item, dict):
                        # Handle dict entries
                        va_data.append({
                            "patient_id": pid,
                            "time": item.get("time", 0),
                            "visual_acuity": item.get("acuity", item.get("visual_acuity", 0))
                        })
            elif hasattr(acuity_history, 'items'):  # Dict-like
                for time, va in acuity_history.items():
                    va_data.append({
                        "patient_id": pid,
                        "time": time,
                        "visual_acuity": va
                    })
        elif isinstance(patient_obj, dict) and "acuity_history" in patient_obj:
            for time_point in patient_obj["acuity_history"]:
                if isinstance(time_point, dict):
                    va_data.append({
                        "patient_id": pid,
                        "time": time_point.get("time", 0),
                        "visual_acuity": time_point.get("acuity", time_point.get("visual_acuity", 0))
                    })
                elif isinstance(time_point, tuple) and len(time_point) == 2:
                    time, va = time_point
                    va_data.append({
                        "patient_id": pid,
                        "time": time,
                        "visual_acuity": va
                    })
        elif hasattr(patient_obj, 'vision_history'):
            # Alternative attribute name
            vision_history = patient_obj.vision_history
            if isinstance(vision_history, list):
                for item in vision_history:
                    if isinstance(item, tuple) and len(item) == 2:
                        time, va = item
                        va_data.append({
                            "patient_id": pid,
                            "time": time,
                            "visual_acuity": va
                        })
                    elif isinstance(item, dict):
                        va_data.append({
                            "patient_id": pid,
                            "time": item.get("time", 0),
                            "visual_acuity": item.get("vision", item.get("visual_acuity", 0))
                        })
    
    if va_data:
        va_df = pd.DataFrame(va_data)
        
        # Calculate mean acuity over time
        mean_va = va_df.groupby("time")["visual_acuity"].mean().reset_index()
        results["mean_va_data"] = mean_va.to_dict(orient="records")
    
    # Process injection data
    injection_data = []
    
    # Check if we can get injection stats directly from sim
    if hasattr(sim, 'stats') and "total_injections" in sim.stats:
        # Get statistics directly from simulation object
        total_injections = sim.stats.get("total_injections", 0)
        total_patients = len(patient_histories)
        mean_injections = total_injections / total_patients if total_patients > 0 else 0
        
        # Add to results
        results["mean_injections"] = mean_injections
        results["total_injections"] = total_injections
        
        # Add some sample injection data for visualization
        for i in range(min(100, total_patients)):
            injection_data.append({
                "patient_id": f"patient_{i}",
                "injection_count": mean_injections  # Use mean for all patients when we don't have individual data
            })
    else:
        # Process injections from patient histories
        # Try different ways to extract injection data
        for patient_id, patient in patient_histories.items() if isinstance(patient_histories, dict) else enumerate(patient_histories):
            injection_count = 0
            
            # For dict-style patient histories
            if isinstance(patient_histories, dict):
                patient_obj = patient
                pid = patient_id
            else:
                patient_obj = patient
                pid = getattr(patient_obj, 'id', f"patient_{patient_id}")
            
            # Check if we have a history with actions
            if isinstance(patient_obj, list) or (hasattr(patient_obj, 'history') and isinstance(patient_obj.history, list)):
                # Get the history
                history = patient_obj if isinstance(patient_obj, list) else patient_obj.history
                
                # Count injections in history
                for visit in history:
                    if isinstance(visit, dict) and 'actions' in visit:
                        actions = visit['actions']
                        if isinstance(actions, list) and 'injection' in actions:
                            injection_count += 1
                        elif isinstance(actions, str) and 'injection' in actions:
                            injection_count += 1
            # Try different attribute/key names
            elif hasattr(patient_obj, 'injection_history'):
                injection_count = len(patient_obj.injection_history)
            elif hasattr(patient_obj, 'injections'):
                injection_count = len(patient_obj.injections)
            elif hasattr(patient_obj, 'injection_count'):
                injection_count = patient_obj.injection_count
            elif isinstance(patient_obj, dict):
                if "injection_history" in patient_obj:
                    injection_count = len(patient_obj["injection_history"])
                elif "injections" in patient_obj:
                    injection_count = len(patient_obj["injections"])
                elif "injection_count" in patient_obj:
                    injection_count = patient_obj["injection_count"]
            
            injection_data.append({
                "patient_id": pid,
                "injection_count": injection_count
            })
    
    if injection_data:
        injection_df = pd.DataFrame(injection_data)
        results["mean_injections"] = injection_df["injection_count"].mean()
        results["total_injections"] = injection_df["injection_count"].sum()
    
    # Save results to a temporary file for report generation
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp:
            json.dump(results, temp, cls=APEJSONEncoder)
            results["data_path"] = temp.name
    except TypeError as e:
        st.warning(f"Could not save results to file: {e}")
        st.info("This won't affect visualization but report generation may not work.")
        
        # Try to convert any numpy values to Python native types
        for key, value in list(results.items()):
            try:
                # Test if the value is JSON serializable
                json.dumps(value)
            except (TypeError, OverflowError):
                # If not, try to convert it to a basic Python type or remove it
                import numpy as np
                if isinstance(value, (np.integer, np.int64, np.int32)):
                    results[key] = int(value)
                elif isinstance(value, (np.floating, np.float64, np.float32)):
                    results[key] = float(value)
                elif isinstance(value, np.ndarray):
                    results[key] = value.tolist()
                else:
                    # If we can't easily convert, just convert to string
                    results[key] = str(value)
    
    return results


def save_simulation_results(results, filename=None):
    """
    Save simulation results to a file.
    
    Parameters
    ----------
    results : dict
        Simulation results
    filename : str, optional
        Filename to save as, by default None (auto-generated)
    
    Returns
    -------
    str
        Path to the saved file
    """
    if filename is None:
        sim_type = results["simulation_type"]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"ape_simulation_{sim_type}_{timestamp}.json"
    
    save_path = os.path.join(os.getcwd(), "output", "simulation_results", filename)
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    
    with open(save_path, 'w') as f:
        json.dump(results, f, indent=2, cls=APEJSONEncoder)
    
    return save_path


def load_simulation_results(filepath):
    """
    Load simulation results from a file.
    
    Parameters
    ----------
    filepath : str
        Path to the results file
    
    Returns
    -------
    dict
        Simulation results
    """
    with open(filepath, 'r') as f:
        results = json.load(f)
    
    return results


def generate_va_over_time_plot(results):
    """
    Generate a plot of visual acuity over time.
    
    Parameters
    ----------
    results : dict
        Simulation results
    
    Returns
    -------
    matplotlib.figure.Figure
        Plot figure
    """
    # Check if we have valid data
    if results.get("failed", False) or "mean_va_data" not in results or not results["mean_va_data"]:
        # Create minimal placeholder visualization
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.text(0.5, 0.5, "No visual acuity data available", 
                ha='center', va='center', fontsize=14, transform=ax.transAxes)
        ax.set_xlabel("Time")
        ax.set_ylabel("Visual Acuity (letters)")
        ax.set_title("Visual Acuity Over Time")
        return fig
    
    # Create DataFrame from the results
    df = pd.DataFrame(results["mean_va_data"])
    
    # Make sure we have the required columns
    if "time" not in df.columns or "visual_acuity" not in df.columns:
        available_cols = list(df.columns)
        
        # Try to guess which columns might be time and visual acuity
        time_col = next((col for col in available_cols if "time" in col.lower()), None)
        va_col = next((col for col in available_cols if "visual" in col.lower() or "acuity" in col.lower() or "va" == col.lower()), None)
        
        if time_col and va_col:
            df["time"] = df[time_col]
            df["visual_acuity"] = df[va_col]
        else:
            # Create minimal placeholder visualization
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.text(0.5, 0.5, f"Missing required columns. Available: {available_cols}", 
                    ha='center', va='center', fontsize=14, transform=ax.transAxes)
            return fig
    
    # Convert time to months if it's in different units
    # This depends on how time is stored in your simulation
    if "time" in df.columns and df["time"].max() > 1000:  # Likely in days or hours
        df["time_months"] = df["time"] / 30  # Approximate days to months
    else:
        df["time_months"] = df["time"]
    
    # Sort by time to ensure proper plotting
    df = df.sort_values("time_months")
    
    # Create the plot
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Plot the visual acuity
    ax.plot(df["time_months"], df["visual_acuity"], marker='o', markersize=4)
    
    # Add a baseline reference line at initial VA
    if len(df) > 0:
        initial_va = df.iloc[0]["visual_acuity"]
        ax.axhline(y=initial_va, color='r', linestyle='--', alpha=0.5, label=f"Baseline VA: {initial_va:.1f}")
    
    # Add labels and grid
    ax.set_xlabel("Months")
    ax.set_ylabel("Visual Acuity (letters)")
    ax.set_title("Mean Visual Acuity Over Time")
    ax.grid(True, linestyle='--', alpha=0.7)
    ax.legend()
    
    # Add starting and ending VA annotations
    if len(df) > 0:
        ax.annotate(f"Start: {df.iloc[0]['visual_acuity']:.1f}", 
                    xy=(df.iloc[0]["time_months"], df.iloc[0]["visual_acuity"]),
                    xytext=(10, 10), textcoords="offset points")
        
        ax.annotate(f"End: {df.iloc[-1]['visual_acuity']:.1f}", 
                    xy=(df.iloc[-1]["time_months"], df.iloc[-1]["visual_acuity"]),
                    xytext=(10, -15), textcoords="offset points")
    
    return fig


def generate_discontinuation_plot(results):
    """
    Generate a plot of discontinuation types.
    
    Parameters
    ----------
    results : dict
        Simulation results
    
    Returns
    -------
    matplotlib.figure.Figure
        Plot figure
    """
    # Debug output to help diagnose issues
    st.info(f"Generating discontinuation plot with data: {results.get('discontinuation_counts', 'None')}")
    st.info(f"Total discontinuations: {results.get('total_discontinuations', 0)}")
    
    # Check if we have valid data
    if results.get("failed", False) or "discontinuation_counts" not in results:
        # Create minimal placeholder visualization
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.text(0.5, 0.5, "No discontinuation data available", 
                ha='center', va='center', fontsize=14, transform=ax.transAxes)
        ax.set_xlabel("Discontinuation Type")
        ax.set_ylabel("Count")
        ax.set_title("Discontinuation by Type")
        return fig
    
    # Create the plot from actual data
    disc_counts = results["discontinuation_counts"]
    types = list(disc_counts.keys())
    counts = list(disc_counts.values())
    
    # Check if we have any non-zero counts
    if sum(counts) == 0:
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.text(0.5, 0.5, "No discontinuations recorded in simulation", 
                ha='center', va='center', fontsize=14, transform=ax.transAxes)
        ax.set_xlabel("Discontinuation Type")
        ax.set_ylabel("Count")
        ax.set_title("Discontinuation by Type")
        
        # Test with direct display of discontinuation counts
        st.info("Trying alternative display method for discontinuation data")
        st.bar_chart(data=pd.DataFrame({
            'Type': list(disc_counts.keys()),
            'Count': list(disc_counts.values())
        }).set_index('Type'))
        
        # Also try to display raw stats if available
        if "raw_discontinuation_stats" in results:
            st.info("Raw discontinuation stats from manager:")
            st.json(results["raw_discontinuation_stats"])
        
        return fig
    
    # Create plot with actual data
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Use a colormap to make the bars more visually appealing
    colors = plt.cm.viridis(np.linspace(0.1, 0.9, len(types)))
    bars = ax.bar(types, counts, color=colors)
    
    # Add percentages on top of bars
    total = sum(counts)
    for bar, count, color in zip(bars, counts, colors):
        if count > 0:  # Only add text if count is non-zero
            percentage = count / total * 100 if total > 0 else 0
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.1,  # Small offset
                f"{percentage:.1f}%",
                ha='center',
                va='bottom',
                fontweight='bold',
                color='black'
            )
            
            # Add count inside bar if it's tall enough
            if count > total * 0.05:  # If at least 5% of total
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_height() / 2,
                    str(count),
                    ha='center',
                    va='center',
                    color='white',
                    fontweight='bold'
                )
    
    ax.set_xlabel("Discontinuation Type")
    ax.set_ylabel("Count")
    ax.set_title("Treatment Discontinuation by Type")
    ax.grid(True, linestyle='--', alpha=0.3, axis='y')
    
    # Calculate patient count and add context to the total
    patient_count = results.get("patient_count", total)  # Fallback to total if patient count missing
    
    # Use unique discontinued patients if available, otherwise fall back to total events
    unique_discontinued = results.get("unique_discontinued_patients", 0)
    if unique_discontinued > 0:
        # We have unique patient data from the fixed implementation
        corrected_rate = (unique_discontinued / patient_count) * 100 if patient_count > 0 else 0
        event_rate = (total / patient_count) * 100 if patient_count > 0 else 0
        
        if event_rate > 100:
            # Show both event count and unique patient count
            footer_text = f"Events: {total} | Unique Patients: {unique_discontinued} | Corrected Rate: {corrected_rate:.1f}%"
            
            # Add message to the plot
            plt.figtext(0.5, 0.02, "⚠️ Some patients discontinued multiple times - unique patient count is used for rate calculation", 
                         ha="center", fontsize=8, style='italic', color='red')
        else:
            footer_text = f"Total Discontinuation Events: {total} ({corrected_rate:.1f}% of patients)"
    else:
        # Fall back to original calculation for backward compatibility
        discontinuation_rate = (total / patient_count) * 100 if patient_count > 0 else 0
        
        if discontinuation_rate > 100:
            # We have retreatments and multiple discontinuations
            footer_text = f"Total Discontinuation Events: {total} ({discontinuation_rate:.1f}% of patients - includes multiple discontinuations per patient)"
        else:
            footer_text = f"Total Discontinuation Events: {total} ({discontinuation_rate:.1f}% of patients)"
        
    fig.text(0.5, 0.01, footer_text, ha='center')
    
    # Ensure y-axis starts at zero
    ax.set_ylim(bottom=0)
    
    # Make y-axis integers only
    from matplotlib.ticker import MaxNLocator
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))
    
    # Force tight layout to ensure everything is visible
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])  # Leave room for footer
    
    # Add unique patient discontinuation information if available
    unique_discontinued = results.get("unique_discontinued_patients", 0)
    if unique_discontinued > 0:
        # Create a secondary figure to compare event count vs. unique patient count
        fig2, ax2 = plt.subplots(figsize=(10, 6))
        
        # Create comparison data
        compare_labels = ['Total Events', 'Unique Patients']
        compare_counts = [total, unique_discontinued]
        
        # Calculate corrected rate
        patient_count = results.get("patient_count", 0)
        if patient_count > 0:
            corrected_rate = (unique_discontinued / patient_count) * 100
            event_rate = (total / patient_count) * 100
            
            # Add rates to labels
            compare_labels = ['Total Events\n({:.1f}%)'.format(event_rate), 
                              'Unique Patients\n({:.1f}%)'.format(corrected_rate)]
        
        # Create bar chart
        bars = ax2.bar(compare_labels, compare_counts, color=['#FFC107', '#4CAF50'])
        
        # Add count annotations
        for bar, count in zip(bars, compare_counts):
            ax2.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.1,
                str(count),
                ha='center',
                va='bottom',
                fontweight='bold'
            )
        
        ax2.set_title('Discontinuation Events vs. Unique Patient Discontinuations')
        ax2.set_ylabel('Count')
        ax2.grid(True, linestyle='--', alpha=0.3, axis='y')
        
        # Add explanation if event count > unique count
        if total > unique_discontinued:
            plt.figtext(0.5, 0.01, 
                        "Some patients discontinued multiple times during the simulation",
                        ha='center', fontsize=10, style='italic')
        
        # Return a list of figures
        return [fig, fig2]
    
    # Return the original figure if we don't have unique patient data
    if unique_discontinued <= 0:
        # Display the interactive streamlit chart
        st.info("Interactive discontinuation chart:")
        
        # Create a simplified chart with just the discontinuation types
        chart_data = pd.DataFrame({
            'Type': types,
            'Count': counts
        })
        
        # Display the chart
        st.bar_chart(data=chart_data.set_index('Type'))
        
        # Count unique patients directly if available
        if "patient_histories" in results:
            # Count unique patient discontinuations
            unique_patient_discontinuations = set()
            retreated_patients = set()
            multiple_discontinuations = set()
            
            for patient_id, history in results["patient_histories"].items():
                # Track when discontinuations happen
                discontinuation_count = 0
                
                for visit in history:
                    if isinstance(visit, dict) and "treatment_status" in visit:
                        treatment_status = visit.get("treatment_status", {})
                        
                        # Check if this visit marks a discontinuation
                        if not treatment_status.get("active", True) and treatment_status.get("cessation_type"):
                            discontinuation_count += 1
                            unique_patient_discontinuations.add(patient_id)
                            
                            # Track multiple discontinuations
                            if discontinuation_count > 1:
                                multiple_discontinuations.add(patient_id)
                        
                        # Check for retreatment
                        if treatment_status.get("active", False) and treatment_status.get("recurrence_detected", False):
                            retreated_patients.add(patient_id)
            
            # Display unique patient statistics
            unique_count = len(unique_patient_discontinuations)
            retreated_count = len(retreated_patients)
            multiple_count = len(multiple_discontinuations)
            
            if unique_count > 0:
                patient_count = results.get("patient_count", len(results["patient_histories"]))
                st.success(f"Unique patients discontinued: {unique_count} ({(unique_count / patient_count) * 100:.1f}% of patients)")
                
                if multiple_count > 0:
                    st.warning(f"Patients with multiple discontinuations: {multiple_count} ({(multiple_count / unique_count) * 100:.1f}% of discontinued patients)")
                
                if retreated_count > 0:
                    st.info(f"Patients retreated after discontinuation: {retreated_count} ({(retreated_count / unique_count) * 100:.1f}% of discontinued patients)")
                
                # Create a pie chart to show the proportion of multiple discontinuations
                if multiple_count > 0:
                    fig3, ax3 = plt.subplots(figsize=(6, 6))
                    labels = ['Single Discontinuation', 'Multiple Discontinuations']
                    sizes = [unique_count - multiple_count, multiple_count]
                    colors = ['#4CAF50', '#FF5722']
                    
                    ax3.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
                    ax3.axis('equal')
                    plt.title("Proportion of Patients with Multiple Discontinuations")
                    st.pyplot(fig3)
        
        return fig
    
    # Display both charts if we have unique patient data
    else:
        # Create a DataFrame for the streamlit chart
        chart_data = pd.DataFrame({
            'Type': types + ['UNIQUE PATIENTS'],
            'Count': counts + [unique_discontinued]
        })
        
        # Display the chart
        st.info("Interactive discontinuation chart:")
        st.bar_chart(data=chart_data.set_index('Type'))
        
        # Calculate patient rate and add context
        patient_count = results.get("patient_count", 0)
        if patient_count > 0:
            corrected_rate = (unique_discontinued / patient_count) * 100
            event_rate = (total / patient_count) * 100
            
            # Display information about the corrected rate
            if event_rate > 100:
                st.success(f"✅ CORRECTED RATE: {corrected_rate:.1f}% ({unique_discontinued} unique patients of {patient_count} total)")
                st.warning(f"⚠️ RAW EVENT RATE: {event_rate:.1f}% ({total} events for {patient_count} patients)")
                
                # Add explanation
                st.info("""
                ### Why the Difference?
                
                The **raw event rate** counts each discontinuation event separately, even if the same patient discontinues multiple times.
                
                The **corrected rate** counts each patient only once, which is the medically relevant metric.
                
                Multiple discontinuations per patient can occur when:
                1. A patient discontinues treatment
                2. Disease recurs and they are retreated
                3. They discontinue again
                """)
            else:
                st.success(f"Discontinuation rate: {corrected_rate:.1f}% ({unique_discontinued} patients of {patient_count} total)")
        
        # Return both figures
        return [fig, fig2]


def get_ui_parameters():
    """
    Get parameters from the Streamlit UI.
    
    Returns
    -------
    dict
        UI parameters
    """
    params = {}
    
    # Get values from session state or use defaults
    params["simulation_type"] = st.session_state.get("simulation_type", "ABS")
    params["duration_years"] = st.session_state.get("duration_years", 5)
    params["population_size"] = st.session_state.get("population_size", 1000)
    params["enable_clinician_variation"] = st.session_state.get("enable_clinician_variation", True)
    params["planned_discontinue_prob"] = st.session_state.get("planned_discontinue_prob", 0.2)
    params["admin_discontinue_prob"] = st.session_state.get("admin_discontinue_prob", 0.05)
    params["consecutive_stable_visits"] = st.session_state.get("consecutive_stable_visits", 3)
    params["monitoring_schedule"] = st.session_state.get("monitoring_schedule", [12, 24, 36])
    params["no_monitoring_for_admin"] = st.session_state.get("no_monitoring_for_admin", True)
    params["recurrence_risk_multiplier"] = st.session_state.get("recurrence_risk_multiplier", 1.0)
    
    return params