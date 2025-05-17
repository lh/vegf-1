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

# Import data normalization
from streamlit_app.data_normalizer import DataNormalizer

# Import the central color system
try:
    from visualization.color_system import COLORS, SEMANTIC_COLORS, ALPHAS
except ImportError:
    # Fallback if the central color system is not available
    COLORS = {
        'primary': '#4682B4',    # Steel Blue - for visual acuity data
        'secondary': '#B22222',  # Firebrick - for critical information
        'patient_counts': '#8FAD91',  # Muted Sage Green - for patient counts
    }
    ALPHAS = {
        'high': 0.8,        # High opacity for primary elements
        'medium': 0.5,      # Medium opacity for standard elements
        'low': 0.2,         # Low opacity for background elements
        'very_low': 0.1,    # Very low opacity for subtle elements
        'patient_counts': 0.5  # Consistent opacity for all patient/sample count visualizations
    }
    SEMANTIC_COLORS = {
        'acuity_data': COLORS['primary'],
        'patient_counts': COLORS['patient_counts'],
        'critical_info': COLORS['secondary'],
    }

# Global variable for debug mode - will be set by app.py
DEBUG_MODE = False

def debug_info(message):
    """
    Display info message only when debug mode is enabled
    
    Parameters
    ----------
    message : str
        The message to display
    """
    if DEBUG_MODE:
        st.info(message)

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

# Export key functions for other modules to use
__all__ = [
    'DEBUG_MODE', 
    'save_plot_for_debug', 
    'create_tufte_bar_chart',
    'run_simulation',
    'generate_va_over_time_plot',
    'generate_discontinuation_plot',
    'get_ui_parameters',
    'save_simulation_results',
    'load_simulation_results'
]


def save_plot_for_debug(fig, filename="debug_plot.png"):
    """
    Save a matplotlib figure to a file for debugging purposes.
    
    Parameters
    ----------
    fig : matplotlib.figure.Figure
        The figure to save
    filename : str
        The filename to save the figure to
    
    Returns
    -------
    str or None
        Path to the saved file if successful, None otherwise
    """
    try:
        # Create output directory if it doesn't exist
        import os
        output_dir = os.path.join(os.getcwd(), "output", "debug")
        os.makedirs(output_dir, exist_ok=True)
        
        # Save the figure
        filepath = os.path.join(output_dir, filename)
        fig.savefig(filepath, bbox_inches='tight', dpi=300)
        print(f"DEBUG: Saved plot to {filepath}")
        return filepath
    except Exception as e:
        print(f"ERROR: Failed to save debug plot: {e}")
        return None

def create_tufte_bar_chart(categories, values, title="", xlabel="", ylabel="",
                          color=None, figsize=(10, 6), horizontal=True):
    """
    Create a Tufte-inspired bar chart that avoids the half-cut bar issue.

    Parameters
    ----------
    categories : list
        List of category labels
    values : list
        List of values for each category
    title : str, optional
        Chart title, by default ""
    xlabel : str, optional
        X-axis label, by default ""
    ylabel : str, optional
        Y-axis label, by default ""
    color : str, optional
        Bar color, by default uses the patient_counts semantic color (muted sage green)
    figsize : tuple, optional
        Figure size, by default (10, 6)
    horizontal : bool, optional
        Whether to create a horizontal bar chart, by default True

    Returns
    -------
    matplotlib.figure.Figure
        The created figure
    """
    # Use the patient_counts color from semantic color system if no color specified
    if color is None:
        color = SEMANTIC_COLORS['patient_counts']

    # Create figure and axis
    fig, ax = plt.subplots(figsize=figsize)
    
    # Sort data by value in descending order
    sorted_indices = np.argsort(values)[::-1]
    sorted_categories = [categories[i] for i in sorted_indices]
    sorted_values = [values[i] for i in sorted_indices]
    
    # Create positions starting at 1 (not 0) to avoid the half-cut bar issue
    positions = np.arange(1, len(categories) + 1)
    
    # Create bars - horizontal or vertical based on parameter
    if horizontal:
        # Create horizontal bars - if patient counts, use the consistent alpha
        if color == SEMANTIC_COLORS.get('patient_counts'):
            alpha_value = ALPHAS['patient_counts']
        else:
            alpha_value = ALPHAS['medium']

        bars = ax.barh(positions, sorted_values, color=color, alpha=alpha_value, height=0.6)
        
        # Set ticks exactly at bar positions
        ax.set_yticks(positions)
        ax.set_yticklabels(sorted_categories)
        
        # Add labels with count and percentage
        total = sum(sorted_values)
        percentages = [(value / total * 100) for value in sorted_values]
        
        for i, (bar, value, pct) in enumerate(zip(bars, sorted_values, percentages)):
            # Determine label position and color
            if value > (max(sorted_values) * 0.25):
                # Inside the bar
                x_pos = bar.get_width() * 0.95
                text_color = 'white'
                ha = 'right'
            else:
                # Outside the bar
                x_pos = bar.get_width() + (max(sorted_values) * 0.02)
                text_color = 'black'
                ha = 'left'
                
            # Add text label
            ax.text(
                x_pos, 
                bar.get_y() + bar.get_height()/2, 
                f"{value} ({pct:.1f}%)", 
                va='center',
                ha=ha,
                color=text_color,
                fontsize=9
            )
        
        # Set axis limits with ample space
        ax.set_ylim(0.5, len(sorted_categories) + 1)
        
        # Add subtle horizontal lines to guide the eye
        for pos in positions:
            ax.axhline(pos, color='#f0f0f0', zorder=0, linewidth=0.8)
            
        # Set axis labels
        if xlabel:
            ax.set_xlabel(xlabel, fontsize=10, color='#555555')
        if ylabel:
            ax.set_ylabel(ylabel, fontsize=10, color='#555555')
            
    else:
        # Create vertical bars
        bars = ax.bar(positions, sorted_values, color=color, alpha=0.7, width=0.6)
        
        # Set ticks exactly at bar positions
        ax.set_xticks(positions)
        ax.set_xticklabels(sorted_categories, rotation=45, ha='right')
        
        # Add labels with count and percentage
        total = sum(sorted_values)
        percentages = [(value / total * 100) for value in sorted_values]
        
        for i, (bar, value, pct) in enumerate(zip(bars, sorted_values, percentages)):
            # Determine label position and color
            if value > (max(sorted_values) * 0.5):
                # Inside the bar
                y_pos = bar.get_height() * 0.9
                text_color = 'white'
                va = 'top'
            else:
                # Outside the bar
                y_pos = bar.get_height() + (max(sorted_values) * 0.02)
                text_color = 'black'
                va = 'bottom'
                
            # Add text label
            ax.text(
                bar.get_x() + bar.get_width()/2, 
                y_pos, 
                f"{value}\n({pct:.1f}%)", 
                ha='center',
                va=va,
                color=text_color,
                fontsize=9
            )
        
        # Set axis limits with ample space
        ax.set_xlim(0.5, len(sorted_categories) + 1)
        
        # Add subtle vertical lines to guide the eye
        for pos in positions:
            ax.axvline(pos, color='#f0f0f0', zorder=0, linewidth=0.8)
            
        # Set axis labels
        if xlabel:
            ax.set_xlabel(xlabel, fontsize=10, color='#555555')
        if ylabel:
            ax.set_ylabel(ylabel, fontsize=10, color='#555555')
    
    # Clean Tufte-inspired styling
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)
    ax.spines['left'].set_linewidth(0.5)
    ax.spines['bottom'].set_linewidth(0.5)
    
    # Remove unnecessary gridlines for cleaner look
    ax.grid(False)
    
    # Set clean title
    if title:
        ax.set_title(title, fontsize=12, color='#333333', loc='left', pad=10)
    
    # Use light gray tick labels
    ax.tick_params(colors='#555555')
    
    # Tight layout to optimize spacing
    plt.tight_layout()
    
    return fig


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
            debug_info(f"Running {params['simulation_type']} simulation with {params['population_size']} patients for {params['duration_years']} years")
            
            # Use an existing simulation configuration as base
            test_config_name = "test_simulation"
            test_config_path = os.path.join(root_dir, "protocols", "simulation_configs", f"{test_config_name}.yaml")
            
            debug_info(f"Using base configuration: {test_config_name}")
            
            # Create a SimulationConfig from an existing YAML file
            # Note: SimulationConfig.from_yaml expects the config name, not the file path
            config = SimulationConfig.from_yaml(test_config_name)
            
            # Display base config settings
            debug_info(f"Base configuration loaded with {config.num_patients} patients and {config.duration_days} days duration")
            
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
                debug_info("Created default discontinuation settings")
            else:
                # Make sure 'enabled' is True
                config.parameters['discontinuation']['enabled'] = True
                debug_info("Ensured discontinuation is enabled")
                
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
                
            # Ensure premature discontinuation settings exist
            if 'premature' not in disc_criteria:
                disc_criteria['premature'] = {
                    'min_interval_weeks': 8,
                    'probability_factor': 1.0,
                    'target_rate': 0.145,
                    'profile_multipliers': {
                        'adherent': 0.2,
                        'average': 1.0,
                        'non_adherent': 3.0
                    },
                    'mean_va_loss': -9.4,
                    'va_loss_std': 5.0
                }
                debug_info("Added premature discontinuation settings")
            
            # Ensure time-based (course complete but not renewed) settings exist
            if 'treatment_duration' not in disc_criteria:
                disc_criteria['treatment_duration'] = {
                    'threshold_weeks': 52,
                    'probability': 0.1
                }
                
            # Update stable_max_interval probability from UI
            disc_criteria['stable_max_interval']['probability'] = params["planned_discontinue_prob"]
            debug_info(f"Setting planned discontinuation probability to {params['planned_discontinue_prob']}")
            
            # Update random_administrative probability from UI
            disc_criteria['random_administrative']['annual_probability'] = params["admin_discontinue_prob"]
            debug_info(f"Setting administrative discontinuation probability to {params['admin_discontinue_prob']}")
            
            # Set premature discontinuation probability if provided in UI
            if "premature_discontinue_prob" in params:
                premature_prob = params["premature_discontinue_prob"]
                disc_criteria['premature']['probability_factor'] = premature_prob
                debug_info(f"Setting premature discontinuation probability factor to {premature_prob}")
            
            # Update consecutive stable visits requirement from UI
            if 'consecutive_stable_visits' in params:
                disc_criteria['stable_max_interval']['consecutive_visits'] = params["consecutive_stable_visits"]
                debug_info(f"Setting consecutive stable visits to {params['consecutive_stable_visits']}")
            
            # Update monitoring settings
            monitoring = config.parameters['discontinuation']['monitoring']
            
            # Ensure monitoring has follow_up_schedule
            if 'follow_up_schedule' not in monitoring:
                monitoring['follow_up_schedule'] = [12, 24, 36]
            
            # Update monitoring schedule from UI
            if 'monitoring_schedule' in params:
                monitoring['follow_up_schedule'] = params["monitoring_schedule"]
                debug_info(f"Setting monitoring schedule to {params['monitoring_schedule']}")
            
            # Create or update planned monitoring
            if 'planned' not in monitoring:
                monitoring['planned'] = {}
            monitoring['planned']['follow_up_schedule'] = monitoring['follow_up_schedule']
            
            # Create or update unplanned monitoring (for premature discontinuations)
            if 'unplanned' not in monitoring:
                monitoring['unplanned'] = {}
                monitoring['unplanned']['follow_up_schedule'] = [8, 16, 24]  # More frequent monitoring for premature
            
            # Ensure cessation_types mappings exist
            if 'cessation_types' not in monitoring:
                monitoring['cessation_types'] = {
                    'stable_max_interval': 'planned',
                    'premature': 'unplanned',
                    'treatment_duration': 'unplanned',
                    'random_administrative': 'none'
                }
                debug_info("Added cessation type mappings for monitoring")
            
            # Set no monitoring for administrative discontinuations if specified
            if params.get("no_monitoring_for_admin", True):
                if 'administrative' not in monitoring:
                    monitoring['administrative'] = {}
                monitoring['administrative']['follow_up_schedule'] = []
                monitoring['cessation_types']['random_administrative'] = 'none'
                debug_info("Disabled monitoring for administrative discontinuations")
            
            # Enable/disable clinician variation
            if hasattr(config, 'parameters') and 'clinicians' in config.parameters:
                config.parameters['clinicians']['enabled'] = params["enable_clinician_variation"]
                debug_info(f"Clinician variation {'enabled' if params['enable_clinician_variation'] else 'disabled'}")
            
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
    # Normalize data at system boundary
    patient_histories = DataNormalizer.normalize_patient_histories(patient_histories)
    
    # Validate normalization if in debug mode
    if DEBUG_MODE:
        try:
            DataNormalizer.validate_normalized_data(patient_histories)
            debug_info("Patient histories successfully normalized and validated")
        except ValueError as e:
            debug_info(f"Data normalization validation failed: {e}")
    
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
        "Not Renewed": 0,
        "Premature": 0
    }
    
    # Debug output - only shown in debug mode
    if discontinuation_manager and DEBUG_MODE:
        debug_info(f"Found discontinuation manager: {type(discontinuation_manager).__name__}")
        debug_info(f"Discontinuation manager stats: {hasattr(discontinuation_manager, 'stats')}")
        if hasattr(discontinuation_manager, 'stats'):
            debug_info(f"Stats keys: {list(discontinuation_manager.stats.keys())}")
    
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
                        elif "duration" in disc_type.lower() or "time" in disc_type.lower() or "course_complete" in disc_type.lower():
                            discontinuation_counts["Not Renewed"] = count
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
                        discontinuation_counts["Not Renewed"] = disc_stats["treatment_duration_discontinuations"]
                    if "course_complete_but_not_renewed_discontinuations" in disc_stats:
                        discontinuation_counts["Not Renewed"] = disc_stats["course_complete_but_not_renewed_discontinuations"]
                    if "premature_discontinuations" in disc_stats:
                        discontinuation_counts["Premature"] = disc_stats["premature_discontinuations"]
        
        # If we don't have data yet, try accessing the stats dictionary directly
        elif hasattr(discontinuation_manager, 'stats'):
            stats = discontinuation_manager.stats
            
            # Extract values from the stats dictionary
            discontinuation_counts["Planned"] = stats.get("stable_max_interval_discontinuations", 0)
            discontinuation_counts["Administrative"] = stats.get("random_administrative_discontinuations", 0)
            
            # Handle both old and new key names for Not Renewed
            course_complete_count = stats.get("course_complete_but_not_renewed_discontinuations", 0)
            treatment_duration_count = stats.get("treatment_duration_discontinuations", 0)
            discontinuation_counts["Not Renewed"] = course_complete_count if course_complete_count > 0 else treatment_duration_count
            
            discontinuation_counts["Premature"] = stats.get("premature_discontinuations", 0)
            
            # Collect recurrence/retreatment statistics
            # First check simulation stats for retreatment numbers - this is our primary source of truth
            sim_retreatments = stats.get("retreatments", 0)
            unique_retreatments = stats.get("unique_retreatments", 0)
            
            # Debug output for retreatment stats - only show in debug mode
            if DEBUG_MODE:
                debug_info(f"DEBUG - Simulation retreatment stats: total={sim_retreatments}, unique={unique_retreatments}")
            
            # Look for retreatment stats from discontinuation manager
            if "retreatments_by_type" in stats:
                retreatment_stats = stats["retreatments_by_type"]
                if sum(retreatment_stats.values()) == 0 and sim_retreatments > 0 and DEBUG_MODE:
                    debug_info(f"Found {sim_retreatments} retreatments in simulation but empty retreatment_by_type in manager")
            else:
                # Initialize with empty dict if not found
                retreatment_stats = {'stable_max_interval': 0, 'premature': 0, 'random_administrative': 0, 'treatment_duration': 0}
                if DEBUG_MODE:
                    debug_info("No retreatment_by_type found in stats, using empty dictionary")
                
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
                        elif disc_type == "Not Renewed":
                            type_key = "course_complete_but_not_renewed"
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
                        'course_complete_but_not_renewed': sim_retreatments - (3 * even_split)  # Remainder to course_complete
                    }
            
            # Store both the total and breakdown in results
            # CRITICAL FIX: Always use the simulation retreatment count as the source of truth
            # Even if the retreatment_by_type is empty, we need to ensure the total is correct
            results["recurrences"] = {
                "total": sim_retreatments,  # Always use sim_retreatments
                "by_type": retreatment_stats,
                "unique_count": unique_retreatments
            }
            
            # Emergency check for recurrence data - only show error in debug mode
            if sim_retreatments > 0 and results["recurrences"]["total"] != sim_retreatments:
                if DEBUG_MODE:
                    st.error(f"CRITICAL: Recurrence total mismatch! sim={sim_retreatments}, results={results['recurrences']['total']}")
                # Force fix regardless of debug mode
                results["recurrences"]["total"] = sim_retreatments
        
        # Add additional debugging for discontinuation counts
        if DEBUG_MODE:
            debug_info(f"Found discontinuation counts: {discontinuation_counts}")
            debug_info(f"Total discontinuations counted: {sum(discontinuation_counts.values())}")
        
        # Also check if we can directly extract total discontinuations from stats
        total_discontinuations = 0
        if hasattr(discontinuation_manager, 'stats') and "total_discontinuations" in discontinuation_manager.stats:
            total_discontinuations = discontinuation_manager.stats["total_discontinuations"]
            if DEBUG_MODE:
                debug_info(f"Total discontinuations from manager stats: {total_discontinuations}")
        
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
        
    # Create alias for patient data - visualization expects "patient_data" but simulation provides "patient_histories"
    if "patient_histories" in results and "patient_data" not in results:
        results["patient_data"] = results["patient_histories"]
    
    # Process patient histories for visual acuity outcomes
    va_data = []
    va_extraction_failures = {}
    patient_count_with_acuity = 0

    # Add debug info to help understand patient data structure (always collect, but only display in debug mode)
    patient_structure_info = []

    if patient_histories:
        # Examine the structure of patient_histories first
        patient_structure_info.append(f"Patient histories type: {type(patient_histories).__name__}")
        patient_structure_info.append(f"Patient histories count: {len(patient_histories)}")

        # Analyze a sample patient to understand its structure
        if isinstance(patient_histories, dict) and patient_histories:
            # Get a sample patient ID
            sample_id = next(iter(patient_histories))
            sample_patient = patient_histories[sample_id]

            patient_structure_info.append(f"Sample patient (ID {sample_id}) type: {type(sample_patient).__name__}")

            # Extract sample history
            if isinstance(sample_patient, list):
                patient_structure_info.append(f"Sample patient is a list with {len(sample_patient)} records")
                if sample_patient:
                    patient_structure_info.append(f"First record type: {type(sample_patient[0]).__name__}")
                    if isinstance(sample_patient[0], dict):
                        patient_structure_info.append(f"First record keys: {list(sample_patient[0].keys())}")
            elif hasattr(sample_patient, 'history') and sample_patient.history:
                patient_structure_info.append(f"Sample patient history length: {len(sample_patient.history)}")
                patient_structure_info.append(f"First record type: {type(sample_patient.history[0]).__name__}")
                if isinstance(sample_patient.history[0], dict):
                    patient_structure_info.append(f"First record keys: {list(sample_patient.history[0].keys())}")

            # Check for visual acuity related attributes
            va_attrs = []
            if hasattr(sample_patient, 'acuity_history'):
                va_attrs.append('acuity_history')
            if hasattr(sample_patient, 'vision_history'):
                va_attrs.append('vision_history')
            if isinstance(sample_patient, dict) and "acuity_history" in sample_patient:
                va_attrs.append('dict:acuity_history')

            patient_structure_info.append(f"Visual acuity attributes found: {va_attrs or 'None'}")

            # Show additional attributes
            additional_attrs = []
            if not isinstance(sample_patient, dict) and not isinstance(sample_patient, list):
                for attr in ['disease_activity', 'treatment_status', 'current_phase', 'visual_acuity', 'initial_acuity']:
                    if hasattr(sample_patient, attr):
                        additional_attrs.append(attr)
                if additional_attrs:
                    patient_structure_info.append(f"Patient has attributes: {additional_attrs}")
        else:
            patient_structure_info.append("Unable to extract detailed patient structure")

    # Store the structure info for debugging
    results["patient_structure_info"] = patient_structure_info

    # Display debug info if enabled
    if DEBUG_MODE:
        for info in patient_structure_info:
            debug_info(info)
    
    # Try different ways to extract visual acuity data
    for patient_id, patient in patient_histories.items() if isinstance(patient_histories, dict) else enumerate(patient_histories):
        # For dict-style patient histories
        if isinstance(patient_histories, dict):
            patient_obj = patient
            pid = patient_id
        else:
            patient_obj = patient
            pid = getattr(patient, 'id', f"patient_{patient_id}")

        # Track if we found acuity data for this patient
        patient_has_acuity = False

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
                        patient_has_acuity = True
                    elif isinstance(item, dict):
                        # Handle dict entries
                        va_data.append({
                            "patient_id": pid,
                            "time": item.get("time", 0),
                            "visual_acuity": item.get("acuity", item.get("visual_acuity", 0))
                        })
                        patient_has_acuity = True
            elif hasattr(acuity_history, 'items'):  # Dict-like
                for time, va in acuity_history.items():
                    va_data.append({
                        "patient_id": pid,
                        "time": time,
                        "visual_acuity": va
                    })
                    patient_has_acuity = True
        elif isinstance(patient_obj, dict) and "acuity_history" in patient_obj:
            for time_point in patient_obj["acuity_history"]:
                if isinstance(time_point, dict):
                    va_data.append({
                        "patient_id": pid,
                        "time": time_point.get("time", 0),
                        "visual_acuity": time_point.get("acuity", time_point.get("visual_acuity", 0))
                    })
                    patient_has_acuity = True
                elif isinstance(time_point, tuple) and len(time_point) == 2:
                    time, va = time_point
                    va_data.append({
                        "patient_id": pid,
                        "time": time,
                        "visual_acuity": va
                    })
                    patient_has_acuity = True
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
                        patient_has_acuity = True
                    elif isinstance(item, dict):
                        va_data.append({
                            "patient_id": pid,
                            "time": item.get("time", 0),
                            "visual_acuity": item.get("vision", item.get("visual_acuity", 0))
                        })
                        patient_has_acuity = True

        # Try to find acuity in regular history if available
        if not patient_has_acuity and hasattr(patient_obj, 'history') and isinstance(patient_obj.history, list):
            # Look for visual acuity in history records
            for i, record in enumerate(patient_obj.history):
                if isinstance(record, dict) and ('visual_acuity' in record or 'acuity' in record):
                    time_val = record.get('time', record.get('timestamp', i))
                    va_val = record.get('visual_acuity', record.get('acuity', 0))

                    va_data.append({
                        "patient_id": pid,
                        "time": time_val,
                        "visual_acuity": va_val
                    })
                    patient_has_acuity = True

        # Special case: If the patient is a list of visit records with vision field
        # This matches the structure found in the debug output
        if not patient_has_acuity and isinstance(patient_obj, list):
            # Track cumulative time for ordered visits
            cumulative_time = 0
            visit_times = {}
            baseline_time = None

            # First pass: Build a time series based on the visit structure
            for i, visit in enumerate(patient_obj):
                if isinstance(visit, dict) and 'vision' in visit:
                    # First record is time 0, subsequent records accumulate intervals
                    # All visits must have a date (already normalized to datetime)
                    if 'date' not in visit:
                        raise ValueError(
                            f"Visit {i} of patient {pid} is missing required 'date' field. "
                            f"Visit data: {visit}"
                        )
                    
                    # Date is already normalized to datetime by DataNormalizer
                    visit_date = visit['date']
                    
                    # First visit establishes baseline
                    if i == 0:
                        baseline_time = visit_date
                        visit_time = 0
                    else:
                        # Calculate time from baseline (both are datetime objects)
                        if baseline_time is None:
                            raise ValueError(f"No baseline time established for patient {pid}")
                        
                        visit_time = (visit_date - baseline_time).days / 30.44

                    # Store the vision value at this time point
                    visit_times[visit_time] = visit['vision']
                    patient_has_acuity = True

            # Second pass: Add the data points in time order
            for time_point in sorted(visit_times.keys()):
                va_data.append({
                    "patient_id": pid,
                    "time": time_point,
                    "visual_acuity": visit_times[time_point]
                })

        # Count patients with acuity data
        if patient_has_acuity:
            patient_count_with_acuity += 1
        else:
            # Store information about failures for debugging
            va_extraction_failures[str(pid)] = {
                "patient_type": type(patient_obj).__name__,
                "has_acuity_history": hasattr(patient_obj, 'acuity_history'),
                "has_vision_history": hasattr(patient_obj, 'vision_history'),
                "has_dict_acuity": isinstance(patient_obj, dict) and "acuity_history" in patient_obj,
                "has_history": hasattr(patient_obj, 'history'),
                "is_list": isinstance(patient_obj, list),
                "has_vision": isinstance(patient_obj, list) and len(patient_obj) > 0 and isinstance(patient_obj[0], dict) and 'vision' in patient_obj[0]
            }
    
    # Track extraction statistics
    results["va_extraction_stats"] = {
        "total_patients": len(patient_histories) if patient_histories else 0,
        "patients_with_acuity": patient_count_with_acuity,
        "total_va_datapoints": len(va_data),
        "extraction_failures": va_extraction_failures
    }

    if va_data:
        va_df = pd.DataFrame(va_data)

        # Standardize time points by binning into monthly intervals
        # This prevents excessive volatility from misaligned time points
        va_df["time_month"] = va_df["time"].round().astype(int)

        # Calculate mean acuity over standardized time bins
        # Also calculate standard error and sample size at each time point
        grouped = va_df.groupby("time_month")["visual_acuity"]
        mean_va_by_month = grouped.mean()
        std_va_by_month = grouped.std()
        count_va_by_month = grouped.count()

        # Calculate standard error of the mean (SEM) for each time point
        # Set a minimum sample size to avoid division by zero
        std_error = std_va_by_month / (count_va_by_month.clip(lower=1)).apply(lambda x: x ** 0.5)

        # Combine statistics into a dataframe
        mean_va = pd.DataFrame({
            "time": mean_va_by_month.index,
            "visual_acuity": mean_va_by_month.values,
            "std_error": std_error.values,
            "sample_size": count_va_by_month.values
        })

        # Apply a rolling window to smooth the data if we have enough points
        # Apply smoothing if we have enough data points (at least 5)
        smoothing_applied = False
        if len(mean_va) >= 5:
            # Sort to ensure time ordering
            mean_va = mean_va.sort_values("time").reset_index(drop=True)

            # Use a custom weighted smoothing approach that accounts for sample sizes
            if "sample_size" in mean_va.columns:
                # First create a copy of the raw values
                mean_va["visual_acuity_raw"] = mean_va["visual_acuity"].copy()

                # Apply a 3-point weighted moving average that respects sample sizes
                smoothed_values = []

                for i in range(len(mean_va)):
                    if i == 0 or i == len(mean_va) - 1:
                        # For first and last points, just use the raw value
                        smoothed_values.append(mean_va.iloc[i]["visual_acuity"])
                    else:
                        # Get values and weights for 3-point weighted average
                        values = [
                            mean_va.iloc[i-1]["visual_acuity"],
                            mean_va.iloc[i]["visual_acuity"],
                            mean_va.iloc[i+1]["visual_acuity"]
                        ]
                        weights = [
                            mean_va.iloc[i-1]["sample_size"],
                            mean_va.iloc[i]["sample_size"]*2,  # Double weight for center point
                            mean_va.iloc[i+1]["sample_size"]
                        ]

                        # Calculate weighted average (sum of value*weight / sum of weights)
                        # Handle division by zero
                        weight_sum = sum(weights)
                        if weight_sum > 0:
                            weighted_sum = 0
                            for j in range(len(values)):
                                weighted_sum += values[j] * weights[j]
                            weighted_avg = weighted_sum / weight_sum
                        else:
                            weighted_avg = values[1]  # Default to center value

                        smoothed_values.append(weighted_avg)

                # Set the smoothed values
                mean_va["visual_acuity_smoothed"] = smoothed_values
                mean_va["visual_acuity"] = mean_va["visual_acuity_smoothed"]
            else:
                # Simple rolling average if no sample size data
                rolling_window = 3
                # Use pandas' built-in rolling function
                mean_va["visual_acuity_smoothed"] = mean_va["visual_acuity"].rolling(
                    window=rolling_window, center=True, min_periods=1).mean()

                # Add the smoothed values to the output
                mean_va["visual_acuity_raw"] = mean_va["visual_acuity"].copy()
                mean_va["visual_acuity"] = mean_va["visual_acuity_smoothed"]

            smoothing_applied = True

        # Convert to records for storage
        results["mean_va_data"] = mean_va.to_dict(orient="records")

        # Store some additional stats about the VA data
        results["va_data_summary"] = {
            "datapoints_count": len(va_data),
            "unique_timepoints": len(mean_va),
            "patients_with_data": va_df["patient_id"].nunique(),
            "min_va": float(va_df["visual_acuity"].min()),
            "max_va": float(va_df["visual_acuity"].max()),
            "mean_va": float(va_df["visual_acuity"].mean()),
            "time_range_months": int(mean_va["time"].max() - mean_va["time"].min()) if len(mean_va) > 1 else 0,
            "smoothing_applied": smoothing_applied
        }
    else:
        # Store empty values to indicate no data was found
        results["mean_va_data"] = []
        results["va_data_summary"] = {
            "datapoints_count": 0,
            "unique_timepoints": 0,
            "min_va": None,
            "max_va": None,
            "mean_va": None,
            "error": "No visual acuity data found in patient histories"
        }

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
    Generate a Tufte-inspired plot of visual acuity over time with swapped axes.
    
    This function follows proper matplotlib isolation best practices:
    - Creates a new figure within the function
    - Uses explicit axis objects
    - Returns the complete figure
    - Uses the central color system
    - Places patient counts (green) on left axis
    - Places visual acuity (blue) on right axis
    
    Parameters
    ----------
    results : dict
        Simulation results
    
    Returns
    -------
    matplotlib.figure.Figure
        Plot figure
    """
    # Import the central color system
    try:
        from visualization.color_system import COLORS, SEMANTIC_COLORS, ALPHAS
    except ImportError:
        # Fallback if the central color system is not available
        COLORS = {
            'primary': '#4682B4',    # Steel Blue - for visual acuity data
            'primary_dark': '#2a4d6e', # Darker Steel Blue - for acuity trend lines
            'secondary': '#B22222',  # Firebrick - for critical information
            'tertiary': '#228B22',   # Forest Green - for additional data series
            'patient_counts': '#8FAD91',  # Muted Sage Green - for patient counts
            'patient_counts_dark': '#5e7260', # Darker Sage Green - for patient count trend lines
            'background': '#FFFFFF', # White background
            'grid': '#EEEEEE',       # Very light gray for grid lines
            'text': '#333333',       # Dark gray for titles and labels
            'text_secondary': '#666666',  # Medium gray for secondary text
            'border': '#CCCCCC'      # Light gray for necessary borders
        }
        ALPHAS = {
            'high': 0.8,        # High opacity for primary elements
            'medium': 0.5,      # Medium opacity for standard elements
            'low': 0.2,         # Low opacity for background elements
            'very_low': 0.1,    # Very low opacity for subtle elements
            'patient_counts': 0.35  # Consistent opacity for all patient/sample count visualizations
        }
        SEMANTIC_COLORS = {
            'acuity_data': COLORS['primary'],       # Blue for visual acuity data
            'acuity_trend': COLORS['primary_dark'],  # Darker blue for acuity trend lines
            'patient_counts': COLORS['patient_counts'],  # Sage Green for patient/sample counts
            'patient_counts_trend': COLORS['patient_counts_dark'],  # Darker sage green for patient count trend lines
            'critical_info': COLORS['secondary'],   # Red for critical information and alerts
            'additional_series': COLORS['tertiary'] # Green for any additional data series
        }
    
    # Check if we have valid data
    if results.get("failed", False) or "mean_va_data" not in results or not results["mean_va_data"]:
        # Create a NEW informative placeholder visualization with troubleshooting info
        # Use proper isolation (new figure created here)
        fig, ax = plt.subplots(figsize=(10, 6))

        # Main error message
        ax.text(0.5, 0.65, "No visual acuity data available",
                ha='center', va='center', fontsize=14, weight='bold', transform=ax.transAxes)

        # Detailed troubleshooting info
        if results.get("failed", False):
            error_msg = results.get("error", "Unknown error")
            ax.text(0.5, 0.5, f"Simulation failed: {error_msg}",
                    ha='center', va='center', fontsize=12, color=SEMANTIC_COLORS['critical_info'], transform=ax.transAxes)
        elif "mean_va_data" not in results:
            ax.text(0.5, 0.5, "Visual acuity data not found in simulation results",
                    ha='center', va='center', fontsize=12, color=SEMANTIC_COLORS['critical_info'], transform=ax.transAxes)
        elif not results["mean_va_data"]:
            ax.text(0.5, 0.5, "Visual acuity data array is empty",
                    ha='center', va='center', fontsize=12, color=SEMANTIC_COLORS['critical_info'], transform=ax.transAxes)

        # Troubleshooting tips
        tips = [
            "1. Check if simulation completed successfully",
            "2. Verify the simulation is recording visual acuity over time",
            "3. Enable Debug Mode in the sidebar for more information",
            "4. Try running the simulation again with different parameters"
        ]

        for i, tip in enumerate(tips):
            ax.text(0.5, 0.35 - (i * 0.05), tip,
                    ha='center', va='center', fontsize=10, color=SEMANTIC_COLORS['acuity_data'], transform=ax.transAxes)

        # Add available simulation info
        sim_info = [
            f"Simulation type: {results.get('simulation_type', 'Unknown')}",
            f"Population size: {results.get('population_size', 'Unknown')}",
            f"Duration: {results.get('duration_years', 'Unknown')} years"
        ]

        for i, info in enumerate(sim_info):
            ax.text(0.5, 0.15 - (i * 0.05), info,
                    ha='center', va='center', fontsize=9, color=COLORS['text_secondary'], transform=ax.transAxes)

        ax.set_xlabel("Time")
        ax.set_ylabel("Visual Acuity (letters)")
        ax.set_title("GRAPHIC A: Mean Visual Acuity Over Time", fontsize=12, color=COLORS['text'], loc='left', pad=10)

        # Remove ticks for cleaner empty visualization
        ax.set_xticks([])
        ax.set_yticks([])

        # Add simple border
        for spine in ax.spines.values():
            spine.set_visible(True)
            spine.set_color(COLORS['border'])
            spine.set_linewidth(0.5)

        return fig
    
    # Create DataFrame from the results
    df = pd.DataFrame(results["mean_va_data"])
    
    # Filter out data points beyond simulation duration
    duration_years = results.get("duration_years", 5)
    max_months = duration_years * 12
    
    # Use the appropriate time column
    time_col = "time_months" if "time_months" in df.columns else "time"
    df = df[df[time_col] <= max_months]
    
    if DEBUG_MODE:
        print(f"Filtered data to {max_months} months (simulation duration: {duration_years} years)")
        print(f"Data points before filter: {len(results['mean_va_data'])}, after filter: {len(df)}")
    
    # Make sure we have the required columns
    if time_col not in df.columns or "visual_acuity" not in df.columns:
        available_cols = list(df.columns)
        
        # Try to guess which columns might be time and visual acuity
        time_col_guess = next((col for col in available_cols if "time" in col.lower()), None)
        va_col = next((col for col in available_cols if "visual" in col.lower() or "acuity" in col.lower() or "va" == col.lower()), None)
        
        if time_col_guess and va_col:
            df[time_col] = df[time_col_guess]
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
    
    # Determine if we have sample size data
    has_sample_sizes = "sample_size" in df.columns
    sample_size_variation = False
    
    if has_sample_sizes:
        sample_sizes = df["sample_size"]
        if sample_sizes.min() > 0:
            sample_size_variation = sample_sizes.max() / sample_sizes.min() > 1.5
    
    # Select smoothing title suffix
    title_suffix = ""
    if "visual_acuity_raw" in df.columns:
        # Check if we have sample size data for weighted smoothing
        if has_sample_sizes:
            title_suffix = " (weighted 3-point average)"
        else:
            title_suffix = " (3-month rolling average)"
    
    # --------- CREATE NEW FIGURE WITH SWAPPED AXES ---------
    # Create a new figure with patient counts on left, visual acuity on right
    fig, ax_counts = plt.subplots(figsize=(10, 6))
    
    # Configure the primary (left) axis for patient counts
    patient_counts_color = SEMANTIC_COLORS['patient_counts']
    
    # Plot the sample size bars on the left axis if we have them
    if has_sample_sizes and sample_size_variation:
        bars = ax_counts.bar(df["time_months"], sample_sizes, 
                            alpha=ALPHAS['patient_counts'], 
                            color=patient_counts_color, 
                            width=0.8)
        
        # Set up left y-axis for patient counts - increased font size and alpha for better legibility
        ax_counts.set_ylabel("Sample Size (patients)", 
                           color=patient_counts_color, 
                           fontsize=10,
                           alpha=1.0)
        ax_counts.tick_params(axis='y', colors=patient_counts_color)
        ax_counts.set_ylim(bottom=0)
        
        # Removed redundant sample size text as requested
    else:
        # Hide the left axis if there are no sample sizes to show
        ax_counts.set_yticks([])
        ax_counts.spines['left'].set_visible(False)
    
    # Create the secondary (right) axis for visual acuity
    ax_acuity = ax_counts.twinx()
    
    # Get colors for visual acuity
    acuity_color = SEMANTIC_COLORS['acuity_data']
    
    # Now that simulation is running properly, we always have enough data
    # No need to show individual points anymore - just plot the mean and CI
    
    # Prepare for alpha calculations based on sample size
    has_variable_alpha = False
    alpha_values = []
    
    if sample_sizes is not None and len(sample_sizes) > 0:
        # Get peak sample size for scaling
        peak_sample_size = max(sample_sizes)
        min_sample_threshold = 100  # Below this we use minimum alpha
        
        # Calculate alpha values for variable transparency
        for size in sample_sizes:
            # Calculate alpha for variable transparency
            if peak_sample_size > min_sample_threshold:
                has_variable_alpha = True
                
                if size <= min_sample_threshold:
                    alpha_values.append(0.2)  # Minimum alpha
                else:
                    # Scale linearly between min_alpha and max_alpha
                    alpha_scale = (size - min_sample_threshold) / (peak_sample_size - min_sample_threshold)
                    alpha = 0.2 + alpha_scale * (1.0 - 0.2)  # Scale from 0.2 to 1.0
                    alpha_values.append(alpha)
            else:
                # Use constant alpha if not enough variation
                alpha_values.append(ALPHAS['high'])
    
    # Plot mean visual acuity lines for all timepoints
    if "visual_acuity_raw" in df.columns:
        if has_variable_alpha:
            # Plot smoothed data as segments with varying alpha
            for i in range(len(df) - 1):
                if i+1 < len(df):
                    segment_alpha = (alpha_values[i] + alpha_values[i+1]) / 2
                    ax_acuity.plot(df["time_months"].iloc[i:i+2], 
                                  df["visual_acuity"].iloc[i:i+2], '-',
                                  color=acuity_color, 
                                  linewidth=2.5, 
                                  alpha=segment_alpha)
            
            # Add a single entry to legend
            ax_acuity.plot([], [], '-', color=acuity_color, linewidth=2.5, 
                          alpha=1.0, label="Mean VA (smoothed)")
                
            # Plot raw data as lighter line with constant alpha
            ax_acuity.plot(df["time_months"], df["visual_acuity_raw"], '--',
                          color=acuity_color, 
                          linewidth=1.0, 
                          alpha=ALPHAS['low'], 
                          label="Mean VA (raw)")
        else:
            # Standard non-variable alpha plots
            ax_acuity.plot(df["time_months"], df["visual_acuity"], '-',
                          color=acuity_color, 
                          linewidth=2.5, 
                          alpha=ALPHAS['high'], 
                          label="Mean VA (smoothed)")

            ax_acuity.plot(df["time_months"], df["visual_acuity_raw"], '--',
                          color=acuity_color, 
                          linewidth=1.0, 
                          alpha=ALPHAS['low'], 
                          label="Mean VA (raw)")
    else:
        # Just plot the main data
        if has_variable_alpha:
            # Plot with varying alpha
            for i in range(len(df) - 1):
                if i+1 < len(df):
                    segment_alpha = (alpha_values[i] + alpha_values[i+1]) / 2
                    ax_acuity.plot(df["time_months"].iloc[i:i+2], 
                                  df["visual_acuity"].iloc[i:i+2], '-',
                                  color=acuity_color, 
                                  linewidth=2.5, 
                                  alpha=segment_alpha)
            
            # Add a single entry to legend
            ax_acuity.plot([], [], '-', color=acuity_color, linewidth=2.5, 
                          alpha=1.0, label="Mean VA")
        else:
            # Standard non-variable alpha plot
            ax_acuity.plot(df["time_months"], df["visual_acuity"], '-',
                          color=acuity_color, 
                          linewidth=2.5, 
                          alpha=ALPHAS['high'], 
                          label="Mean VA")

    # Add markers with variable alpha if applicable
    if has_variable_alpha:
        # Plot markers with varying alpha
        for i in range(len(df)):
            ax_acuity.scatter(df["time_months"].iloc[i], 
                             df["visual_acuity"].iloc[i],
                             s=40, 
                             color=acuity_color, 
                             alpha=alpha_values[i],
                             zorder=5)
    else:
        # Add subtle markers with constant alpha
        ax_acuity.scatter(df["time_months"], df["visual_acuity"],
                         s=40, 
                         color=acuity_color, 
                         alpha=ALPHAS['medium'], 
                         zorder=5)

    # Handle confidence intervals (no individual data points anymore)
    if "std_error" in df.columns:
        # Calculate 95% confidence interval (approx. 2 standard errors)
        ci_factor = 1.96  # 95% confidence
        df['upper_ci'] = df.apply(lambda row: row["visual_acuity"] + ci_factor * row["std_error"], axis=1)
        df['lower_ci'] = df.apply(lambda row: row["visual_acuity"] - ci_factor * row["std_error"], axis=1)
        
        # Plot confidence interval as shaded area for all timepoints
        ax_acuity.fill_between(df["time_months"], 
                              df['lower_ci'], 
                              df['upper_ci'],
                              color=acuity_color, 
                              alpha=ALPHAS['very_low'], 
                              label="95% Confidence Interval")
    
    # Add baseline reference as a subtle line from first point to right axis
    if len(df) > 0:
        initial_va = df.iloc[0]["visual_acuity"]
        initial_time = df.iloc[0]["time_months"]
        # Draw a thin, dark line from the first point to the right axis
        # Using transform to ensure it reaches the axis
        line = ax_acuity.axhline(y=initial_va, 
                                xmin=initial_time / max(df["time_months"]),  # Start from first point
                                xmax=1.0,  # Extend all the way to right axis
                                color=COLORS['text_secondary'],
                                linewidth=0.75,
                                alpha=0.4,
                                linestyle='--',  # Dashed for subtlety
                                clip_on=False)  # Allow line to extend to axis
    
    # Configure visual acuity axis (right) - increased font size and alpha for better legibility
    ax_acuity.set_ylabel("Visual Acuity (letters)", 
                        color=acuity_color, 
                        fontsize=10,
                        alpha=1.0)
    ax_acuity.tick_params(axis='y', colors=acuity_color)
    
    # Calculate y-axis range with padding
    if len(df) > 0:
        min_va = min(df["visual_acuity"]) - 5
        max_va = max(df["visual_acuity"]) + 5
        ax_acuity.set_ylim(max(0, min_va), min(85, max_va))  # Cap at 0-85 ETDRS range
    
    # Clean, minimalist styling - Tufte-inspired
    # Make all visible spines light but keep them for context
    
    # Remove top spines as they're not needed
    ax_counts.spines['top'].set_visible(False)
    ax_acuity.spines['top'].set_visible(False)
    
    # Make all remaining spines light gray, thin, and semi-transparent
    light_spine_color = '#cccccc'  # Light gray
    light_spine_alpha = 0.3
    light_spine_width = 0.5
    
    # Configure left spine (for patient counts)
    ax_counts.spines['left'].set_visible(True)
    ax_counts.spines['left'].set_linewidth(light_spine_width)
    ax_counts.spines['left'].set_alpha(light_spine_alpha)
    ax_counts.spines['left'].set_color(light_spine_color)
    
    # Configure bottom spine (shared x-axis)
    ax_counts.spines['bottom'].set_visible(True)
    ax_counts.spines['bottom'].set_linewidth(light_spine_width)
    ax_counts.spines['bottom'].set_alpha(light_spine_alpha)
    ax_counts.spines['bottom'].set_color(light_spine_color)
    
    # Configure right spine (for visual acuity)
    ax_acuity.spines['right'].set_visible(True)
    ax_acuity.spines['right'].set_linewidth(light_spine_width)
    ax_acuity.spines['right'].set_alpha(light_spine_alpha)
    ax_acuity.spines['right'].set_color(light_spine_color)
    
    # Hide unnecessary spines
    ax_acuity.spines['bottom'].set_visible(False)
    ax_acuity.spines['left'].set_visible(False)
    ax_counts.spines['right'].set_visible(False)
    
    # Use lighter grid lines only for visual acuity
    ax_counts.grid(False)
    ax_acuity.grid(True, axis='y', linestyle='--', alpha=ALPHAS['very_low'], color=COLORS['grid'])
    ax_acuity.grid(False, axis='x')
    
    # Set common axis labels
    ax_counts.set_xlabel("Months", fontsize=10, color=COLORS['text_secondary'])
    
    # Add title
    fig.suptitle("Mean Visual Acuity and Cohort Size Over Time", 
               fontsize=12, 
               color=COLORS['text'], 
               x=0.1,  # Left-aligned
               y=0.98,  # Near the top
               ha='left')
    
    # Use light gray tick labels for x-axis
    ax_counts.tick_params(axis='x', colors=COLORS['text_secondary'])
    
    # Show legend with clean styling (no frame) at top center
    # Only show it on the visual acuity axis
    ax_acuity.legend(frameon=False, fontsize=9, loc='upper center', bbox_to_anchor=(0.5, 1.05), 
                     ncol=4)  # Use ncol=4 to arrange items horizontally
    
    
    # Optimize spacing around the chart for better Streamlit rendering
    # Add extra space on the right for the baseline annotation
    fig.subplots_adjust(left=0.12, right=0.85, top=0.92, bottom=0.12)
    plt.tight_layout(rect=[0, 0, 1, 0.95]) 
    
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
    matplotlib.figure.Figure or list
        Plot figure or list of figures
    """
    # First try to use the enhanced implementation if available
    try:
        from streamlit_app.discontinuation_chart import generate_enhanced_discontinuation_plot

        # Create the enhanced chart showing discontinuation by retreatment status
        enhanced_fig = generate_enhanced_discontinuation_plot(results)

        # Also create the original simple bar chart for comparison
        original_fig = generate_simple_discontinuation_plot(results)

        # Return both figures as a list
        return [enhanced_fig, original_fig]
    except ImportError:
        # Fall back to the original implementation if enhanced version not available
        return generate_simple_discontinuation_plot(results)


def generate_simple_discontinuation_plot(results):
    """
    Generate a simple bar chart of discontinuation types.

    This is the original implementation without retreatment status.

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
    if results.get("failed", False) or "discontinuation_counts" not in results:
        # Create minimal placeholder visualization
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.text(0.5, 0.5, "No discontinuation data available",
                ha='center', va='center', fontsize=14, transform=ax.transAxes)
        ax.set_title("GRAPHIC B: Treatment Discontinuation by Type",
                     fontsize=12, color='#333333', loc='left', pad=10)
        return fig

    # Extract data
    disc_counts = results["discontinuation_counts"]
    types = list(disc_counts.keys())
    counts = list(disc_counts.values())

    # Check if we have any non-zero counts
    if sum(counts) == 0:
        # Create minimal placeholder visualization
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.text(0.5, 0.5, "No discontinuations recorded in simulation",
                ha='center', va='center', fontsize=14, transform=ax.transAxes)
        ax.set_title("GRAPHIC B: Treatment Discontinuation by Type",
                     fontsize=12, color='#333333', loc='left', pad=10)
        return fig

    # Use our helper function to create a properly formatted bar chart
    fig = create_tufte_bar_chart(
        categories=types,
        values=counts,
        title="GRAPHIC B: Treatment Discontinuation by Type",
        xlabel="Number of Patients",
        color='#3498db',
        figsize=(10, 6),
        horizontal=True
    )

    # Get the axis from the figure
    ax = fig.axes[0]

    # Calculate total for footer
    total = sum(counts)

    # Create space at the bottom for the footer
    plt.subplots_adjust(bottom=0.15)

    # Add footer directly within the plot
    ax.annotate(
        f"Total Discontinuation Events: {total} ({(total/results.get('patient_count', total))*100:.1f}% of patients)",
        xy=(0.5, -0.12),
        xycoords='axes fraction',
        ha='center', fontsize=9, color='#555555',
        annotation_clip=False  # Allow annotation outside the plot area
    )

    # Save for debugging
    save_plot_for_debug(fig, "graphic_b_debug_simplified.png")

    # Return the figure
    return fig


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
    params["premature_discontinue_prob"] = st.session_state.get("premature_discontinue_prob", 2.0)
    params["consecutive_stable_visits"] = st.session_state.get("consecutive_stable_visits", 3)
    params["monitoring_schedule"] = st.session_state.get("monitoring_schedule", [12, 24, 36])
    params["no_monitoring_for_admin"] = st.session_state.get("no_monitoring_for_admin", True)
    params["recurrence_risk_multiplier"] = st.session_state.get("recurrence_risk_multiplier", 1.0)
    
    return params