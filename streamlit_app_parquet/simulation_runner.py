"""
Simulation Runner Module

This module handles running simulations from the Streamlit UI and processing results.
"""

import os
import sys
# Removed json import - Parquet only!
import tempfile
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import streamlit as st
import time
from datetime import datetime
from collections import defaultdict

# Import data normalization
from streamlit_app_parquet.data_normalizer import DataNormalizer

# Import the central color system and templates - fail fast, no fallbacks
from visualization.color_system import COLORS, SEMANTIC_COLORS, ALPHAS
from visualization.chart_templates import (
    apply_dual_axis_style, 
    apply_standard_layout, 
    apply_horizontal_legend,
    set_standard_y_axis_range,
    set_yearly_x_ticks,
    add_explanatory_note
)

# Global variable for debug mode - will be set by app.py
DEBUG_MODE = False

# This version is ALWAYS Parquet - no feature flag needed!

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

# Removed JSON utilities - Parquet only!

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
    'get_ui_parameters'
    # Removed JSON save/load from exports
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
            
            # Initialize results dictionary with basic info
            results = {
                "runtime_seconds": runtime,
                "simulation_type": params["simulation_type"],
                "population_size": params["population_size"],
                "duration_years": params["duration_years"],
                "patient_histories": patient_histories
            }
            
            # ALWAYS use Parquet pipeline in this version - BEFORE processing results
            try:
                st.info("📊 Saving results to Parquet format...")
                debug_info("Starting Parquet save process...")
                
                # Get stats for Parquet
                statistics = sim.stats if hasattr(sim, 'stats') else {}
                debug_info(f"Got statistics: {len(statistics)} keys")
                
                # Save to Parquet
                parquet_base_path = save_results_as_parquet(
                    patient_histories,
                    statistics,
                    config,
                    params
                )
                
                debug_info(f"Parquet files saved to: {parquet_base_path}")
                
                # Add Parquet path to results for downstream use
                results["parquet_base_path"] = parquet_base_path
                
                # Load the parquet files for immediate use
                results["visits_df"] = pd.read_parquet(f"{parquet_base_path}_visits.parquet")
                results["metadata_df"] = pd.read_parquet(f"{parquet_base_path}_metadata.parquet")
                results["stats_df"] = pd.read_parquet(f"{parquet_base_path}_stats.parquet")
                
                debug_info(f"Loaded DataFrames - visits shape: {results['visits_df'].shape}")
                debug_info(f"DataFrames loaded - results now has visits_df: {'visits_df' in results}")
                
            except Exception as parquet_error:
                import traceback
                st.error(f"Failed to save/load Parquet data: {parquet_error}")
                debug_info(f"Parquet error details: {traceback.format_exc()}")
            
            # NOW process results with Parquet data available
            # Pass the results dict which now contains visits_df
            processed_results = process_simulation_results(sim, patient_histories, params, results)
            
            # Merge processed results with our results dict (keeping Parquet data)
            for key, value in processed_results.items():
                if key not in ["visits_df", "metadata_df", "stats_df"]:  # Don't overwrite Parquet data
                    results[key] = value
            
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
            
            # Debug: Check if VA data was processed
            if DEBUG_MODE:
                debug_info(f"Final results check - has mean_va_data: {'mean_va_data' in results}")
                if 'mean_va_data' in results:
                    debug_info(f"  mean_va_data length: {len(results['mean_va_data'])}")
                if 'va_data_summary' in results:
                    debug_info(f"  VA summary: {results['va_data_summary']}")
            
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


def save_results_as_parquet(patient_histories, statistics, config, params):
    """
    Save simulation results in Parquet format with enrichment logic.
    Based on run_streamgraph_simulation_parquet.py
    
    Parameters
    ----------
    patient_histories : dict
        Dictionary of patient histories
    statistics : dict
        Simulation statistics
    config : SimulationConfig
        Simulation configuration
    params : dict
        UI parameters
        
    Returns
    -------
    str
        Base path of saved files (without extensions)
    """
    # Default output directory
    output_dir = os.path.join(os.path.dirname(__file__), "output", "parquet_results")
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate filename with better naming convention
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    base_filename = f"{timestamp}-sim-{params['population_size']}p-{params['duration_years']}y"
    base_path = os.path.join(output_dir, base_filename)
    
    # Convert patient histories to DataFrame with enrichment
    patient_data = []
    
    # Track patients who are retreated
    retreated_patients = set()
    treatment_status_changes = {}
    
    # First pass: identify retreatment events
    for patient_id, visits in patient_histories.items():
        treatment_status_changes[patient_id] = []
        was_active = True
        was_discontinued = False
        discontinuation_found = False
        
        for i, visit in enumerate(visits):
            visit_type = visit.get("type", "")
            phase = visit.get("phase", "")
            
            # Identify retreatment by phase transitions
            if i > 0:
                prev_phase = visits[i-1].get("phase", "")
                if prev_phase == "monitoring" and phase == "loading":
                    retreated_patients.add(patient_id)
                    treatment_status_changes[patient_id].append(i)
                    
            # Track treatment status transitions
            treatment_status = visit.get("treatment_status", {})
            is_active = treatment_status.get("active", True)
            
            if is_active == False and was_active == True:
                discontinuation_found = True
                
            if i > 0 and discontinuation_found:
                if not was_active and is_active:
                    retreated_patients.add(patient_id)
                    treatment_status_changes[patient_id].append(i)
            
            was_active = is_active
    
    # Second pass: add all visit data with enrichment flags
    for patient_id, visits in patient_histories.items():
        transitions = treatment_status_changes.get(patient_id, [])
        has_been_retreated = False
        has_been_discontinued = False
        discontinuation_type = None
        
        for i, visit in enumerate(visits):
            is_retreatment_visit = i in transitions
            is_discontinuation = visit.get("is_discontinuation_visit", False)
            
            if is_retreatment_visit:
                has_been_retreated = True
                has_been_discontinued = False
                discontinuation_type = None
            
            if is_discontinuation:
                has_been_discontinued = True
                discontinuation_type = visit.get("discontinuation_type", "")
            
            visit_record = {
                "patient_id": patient_id,
                "is_retreatment_visit": is_retreatment_visit,
                "has_been_retreated": has_been_retreated,
                "is_discontinuation": is_discontinuation,
                "has_been_discontinued": has_been_discontinued,
                "discontinuation_type": discontinuation_type,
                **visit
            }
            patient_data.append(visit_record)
    
    # Create DataFrames
    visits_df = pd.DataFrame(patient_data)
    
    # Ensure date is datetime
    if "date" in visits_df.columns and pd.api.types.is_string_dtype(visits_df["date"]):
        visits_df["date"] = pd.to_datetime(visits_df["date"])
    
    # Create metadata DataFrame
    metadata = {
        "simulation_type": params["simulation_type"],
        "patients": params["population_size"],
        "population_size": params["population_size"],  # Add for backwards compatibility
        "duration_years": params["duration_years"],
        "recruitment_mode": params.get("recruitment_mode", "Fixed Total"),
        "recruitment_rate": params.get("recruitment_rate", params["population_size"] / (params["duration_years"] * 12)),
        "start_date": config.start_date if hasattr(config, "start_date") else datetime.now().strftime("%Y-%m-%d"),
        "discontinuation_enabled": True,
        "planned_discontinue_prob": params["planned_discontinue_prob"],
        "admin_discontinue_prob": params["admin_discontinue_prob"],
        "enable_clinician_variation": params["enable_clinician_variation"],
        "timestamp": params.get("timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    }
    metadata_df = pd.DataFrame([metadata])
    
    # Create statistics DataFrame
    stats_df = pd.DataFrame([statistics])
    
    # Save DataFrames as Parquet files
    visits_df.to_parquet(f"{base_path}_visits.parquet")
    metadata_df.to_parquet(f"{base_path}_metadata.parquet")
    stats_df.to_parquet(f"{base_path}_stats.parquet")
    
    debug_info(f"Parquet files saved to: {base_path}")
    
    return base_path


def process_simulation_results(sim, patient_histories, params, existing_results=None):
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
    existing_results : dict, optional
        Existing results dictionary (may contain visits_df from Parquet)
    
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
    
    # Start with existing results if provided, otherwise create new dict
    if existing_results:
        results = existing_results.copy()
        # Update with processing params
        results.update({
            "simulation_type": params["simulation_type"],
            "population_size": params["population_size"],
            "duration_years": params["duration_years"],
            "enable_clinician_variation": params["enable_clinician_variation"],
            "planned_discontinue_prob": params["planned_discontinue_prob"],
            "admin_discontinue_prob": params["admin_discontinue_prob"],
            "timestamp": existing_results.get("timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            "patient_count": len(patient_histories)
        })
    else:
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
    
    # Process visual acuity data from Parquet DataFrame
    if "visits_df" in results:
        # Use Parquet data for VA processing
        visits_df = results["visits_df"]
        
        # Always log this important step
        debug_info("✅ Found visits_df in results - processing VA data from Parquet!")
        
        # Debug info about the DataFrame
        if DEBUG_MODE:
            debug_info(f"Processing VA data from visits_df with shape: {visits_df.shape}")
            debug_info(f"Columns in visits_df: {list(visits_df.columns)}")
            if 'vision' in visits_df.columns:
                debug_info(f"Vision column stats - non-null: {visits_df['vision'].notna().sum()}, null: {visits_df['vision'].isna().sum()}")
        
        # Convert date to time if needed
        if 'time' not in visits_df.columns and 'date' in visits_df.columns:
            # Convert date to months from simulation start
            visits_df = visits_df.copy()
            visits_df['date'] = pd.to_datetime(visits_df['date'])
            min_date = visits_df['date'].min()
            visits_df['time'] = (visits_df['date'] - min_date).dt.days / 30.44  # Average days per month
        
        # Check if we have the required columns
        required_columns = ['patient_id', 'time', 'vision']
        missing_columns = [col for col in required_columns if col not in visits_df.columns]
        
        if missing_columns:
            results["mean_va_data"] = []
            results["va_data_summary"] = {
                "datapoints_count": 0,
                "unique_timepoints": 0,
                "min_va": None,
                "max_va": None,
                "mean_va": None,
                "error": f"Missing required columns in visits DataFrame: {missing_columns}"
            }
        else:
            # Filter out rows with missing vision data
            va_df = visits_df[visits_df['vision'].notna()].copy()
            
            if len(va_df) == 0:
                # Log additional debug info
                print(f"WARNING: No visual acuity data found. Total visits: {len(visits_df)}, Vision column exists: {'vision' in visits_df.columns}")
                if 'vision' in visits_df.columns:
                    print(f"Vision column sample (first 5): {visits_df['vision'].head()}")
                    print(f"Vision column dtype: {visits_df['vision'].dtype}")
                
                results["mean_va_data"] = []
                results["va_data_summary"] = {
                    "datapoints_count": 0,
                    "unique_timepoints": 0,
                    "min_va": None,
                    "max_va": None,
                    "mean_va": None,
                    "error": "No visual acuity data found in visits DataFrame"
                }
            else:
                # Standardize time points by binning into monthly intervals
                va_df["time_month"] = va_df["time"].round().astype(int)
                
                # Calculate mean acuity over standardized time bins
                grouped = va_df.groupby("time_month")
                mean_va_by_month = grouped["vision"].mean()
                std_va_by_month = grouped["vision"].std()
                count_va_by_month = grouped["vision"].count()
                
                # Calculate standard error of the mean (SEM) for each time point
                std_error = std_va_by_month / (count_va_by_month.clip(lower=1)).apply(lambda x: x ** 0.5)
                
                # Combine statistics into a dataframe
                mean_va = pd.DataFrame({
                    "time": mean_va_by_month.index,
                    "visual_acuity": mean_va_by_month.values,
                    "std_error": std_error.values,
                    "sample_size": count_va_by_month.values
                })
                
                # Apply smoothing if we have enough data points (at least 5)
                smoothing_applied = False
                if len(mean_va) >= 5:
                    # Sort to ensure time ordering
                    mean_va = mean_va.sort_values("time").reset_index(drop=True)
                    
                    # Create a copy of the raw values
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
                            
                            # Calculate weighted average
                            weight_sum = sum(weights)
                            if weight_sum > 0:
                                weighted_sum = sum(v * w for v, w in zip(values, weights))
                                weighted_avg = weighted_sum / weight_sum
                            else:
                                weighted_avg = values[1]  # Default to center value
                            
                            smoothed_values.append(weighted_avg)
                    
                    # Set the smoothed values
                    mean_va["visual_acuity_smoothed"] = smoothed_values
                    mean_va["visual_acuity"] = mean_va["visual_acuity_smoothed"]
                    smoothing_applied = True
                
                # Convert to records for storage
                results["mean_va_data"] = mean_va.to_dict(orient="records")
                
                # Store some additional stats about the VA data
                results["va_data_summary"] = {
                    "datapoints_count": len(va_df),
                    "unique_timepoints": len(mean_va),
                    "patients_with_data": va_df["patient_id"].nunique(),
                    "min_va": float(va_df["vision"].min()),
                    "max_va": float(va_df["vision"].max()),
                    "mean_va": float(va_df["vision"].mean()),
                    "time_range_months": int(mean_va["time"].max() - mean_va["time"].min()) if len(mean_va) > 1 else 0,
                    "smoothing_applied": smoothing_applied
                }
                
                # Debug info
                if DEBUG_MODE:
                    debug_info(f"VA data processed from Parquet: {len(va_df)} records from {va_df['patient_id'].nunique()} patients")
                    debug_info(f"Time range: {va_df['time'].min():.1f} to {va_df['time'].max():.1f} months")
    else:
        # No Parquet data available
        debug_info("❌ No visits_df found in results - VA processing skipped!")
        debug_info(f"Available keys in results: {list(results.keys())}")
        
        results["mean_va_data"] = []
        results["va_data_summary"] = {
            "datapoints_count": 0,
            "unique_timepoints": 0,
            "min_va": None,
            "max_va": None,
            "mean_va": None,
            "error": "No Parquet data available - this version requires Parquet format"
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
    
    # Removed JSON save - using Parquet instead
    # Data path will be set by Parquet save in run_simulation
    # Note: Report generation may need updating to use Parquet files
    
    return results


# Removed JSON save/load functions - Parquet only!


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
    # Import the central color system - fail fast, no fallbacks
    from visualization.color_system import COLORS, SEMANTIC_COLORS, ALPHAS
    
    # Check if we have valid data - handle all error cases gracefully
    if results.get("failed", False) or "mean_va_data" not in results or not results.get("mean_va_data"):
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
        elif not results.get("mean_va_data"):
            ax.text(0.5, 0.5, "Visual acuity data array is empty",
                    ha='center', va='center', fontsize=12, color=SEMANTIC_COLORS['critical_info'], transform=ax.transAxes)
            
            # Add VA data summary if available
            if "va_data_summary" in results:
                summary = results["va_data_summary"]
                if "error" in summary:
                    ax.text(0.5, 0.45, f"Error: {summary['error']}",
                            ha='center', va='center', fontsize=10, color=SEMANTIC_COLORS['critical_info'], 
                            transform=ax.transAxes)

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
    
    # Use the appropriate time column - fail early if not found
    if "time_months" in df.columns:
        time_col = "time_months"
    elif "time" in df.columns:
        time_col = "time"
    else:
        raise ValueError(f"No time column found in data. Available columns: {list(df.columns)}")
    
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
    if "time" in df.columns:
        if df["time"].max() > 1000:  # Likely in days or hours
            df["time_months"] = df["time"] / 30  # Approximate days to months
        else:
            df["time_months"] = df["time"]
    elif "time_months" not in df.columns:
        # If neither time nor time_months exists, this is an error
        raise ValueError(f"Missing time column in data. Available columns: {list(df.columns)}")
    
    # Sort by time to ensure proper plotting
    df = df.sort_values("time_months")
    
    # Determine if we have sample size data
    has_sample_sizes = "sample_size" in df.columns
    sample_size_variation = False
    sample_sizes = None  # Initialize to prevent UnboundLocalError
    
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
                            width=0.8,
                            label='Number of Measurements')
        
        # Set up left y-axis for measurement counts - increased font size and alpha for better legibility
        ax_counts.set_ylabel("Number of Measurements", 
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
    
    # Set consistent y-axis range per design principles
    ax_acuity.set_ylim(0, 85)  # Always use 0-85 ETDRS range for consistency
    
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
    
    # Set yearly x-axis ticks
    set_yearly_x_ticks(ax_counts)
    
    # Add title
    fig.suptitle("Mean Visual Acuity and Number of Measurements Over Time", 
               fontsize=12, 
               color=COLORS['text'], 
               x=0.1,  # Left-aligned
               y=0.98,  # Near the top
               ha='left')
    
    # Use light gray tick labels for x-axis
    ax_counts.tick_params(axis='x', colors=COLORS['text_secondary'])
    
    # Show combined legend for both axes with clean styling (no frame) at top center
    lines1, labels1 = ax_counts.get_legend_handles_labels()
    lines2, labels2 = ax_acuity.get_legend_handles_labels()
    ax_acuity.legend(lines1 + lines2, labels1 + labels2, 
                     frameon=False, fontsize=9, loc='upper center', bbox_to_anchor=(0.5, 1.05), 
                     ncol=3)  # Use ncol=3 to arrange items appropriately
    
    # Add explanatory text about the confidence interval
    fig.text(0.5, 0.01, 
            "Note: The 95% confidence interval shows our statistical confidence in the mean value, not the range of patient vision scores.",
            ha='center', va='bottom', fontsize=9, color=COLORS['text_secondary'],
            style='italic', wrap=True)
    
    # Optimize spacing around the chart for better Streamlit rendering
    # Add extra space on the right for the baseline annotation and bottom for the note
    fig.subplots_adjust(left=0.12, right=0.88, top=0.92, bottom=0.15)
    plt.tight_layout(rect=[0, 0.03, 1, 0.95]) 
    
    return fig


def generate_va_distribution_plot(results):
    """
    Generate a percentile bands plot showing the distribution of visual acuity over time.
    
    This plot shows the actual range of patient vision values, not statistical confidence.
    It displays multiple percentile bands to show how the distribution evolves over time.
    
    Parameters
    ----------
    results : dict
        Simulation results containing patient-level visual acuity data
    
    Returns
    -------
    matplotlib.figure.Figure
        Plot figure showing VA distribution over time
    
    Raises
    ------
    ValueError
        If patient data is not available in the results
    """
    # Import the central color system - fail fast, no fallbacks
    from visualization.color_system import COLORS, SEMANTIC_COLORS, ALPHAS
    
    # Get the raw patient data
    if "patient_data" not in results and "patient_histories" not in results:
        # Since we're generating the data, this should never happen
        raise ValueError("Patient-level data is required for distribution plot but not found in results. "
                        "This indicates a data generation error since we control the simulation output.")
    
    patient_histories = results.get("patient_data", results.get("patient_histories", {}))
    
    # Extract all patient VA values at each time point
    time_va_map = defaultdict(list)  # time -> list of VA values
    
    for patient_id, patient in patient_histories.items() if isinstance(patient_histories, dict) else enumerate(patient_histories):
        # Extract VA data based on patient structure (similar to aggregate_vision_data)
        if isinstance(patient, list):
            # Patient is a list of visits
            cumulative_time = 0
            baseline_time = None
            
            for i, visit in enumerate(patient):
                if isinstance(visit, dict) and 'vision' in visit:
                    # Calculate time from baseline
                    if i == 0:
                        baseline_time = visit.get('date')
                        visit_time = 0
                    else:
                        if baseline_time and 'date' in visit:
                            visit_time = (visit['date'] - baseline_time).days / 30.44
                        else:
                            visit_time = i  # fallback to visit index
                    
                    # Round to nearest month
                    time_month = round(visit_time)
                    time_va_map[time_month].append(visit['vision'])
        
        elif hasattr(patient, 'acuity_history'):
            # Use acuity_history attribute
            for record in patient.acuity_history:
                time_month = round(record.get('time', 0))
                va_value = record.get('visual_acuity', record.get('vision', 0))
                time_va_map[time_month].append(va_value)
    
    # Calculate percentiles at each time point
    percentile_data = []
    percentiles_to_calculate = [5, 10, 25, 50, 75, 90, 95]
    
    for time_month in sorted(time_va_map.keys()):
        va_values = time_va_map[time_month]
        if len(va_values) >= 5:  # Need minimum sample size for reliable percentiles
            percentile_results = {
                'time': time_month,
                'count': len(va_values),
                'mean': np.mean(va_values)
            }
            
            for p in percentiles_to_calculate:
                percentile_results[f'p{p}'] = np.percentile(va_values, p)
            
            percentile_data.append(percentile_results)
    
    if not percentile_data:
        # Not enough data
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.text(0.5, 0.5, "Insufficient data points for distribution plot",
                ha='center', va='center', fontsize=14, transform=ax.transAxes)
        return fig
    
    # Convert to DataFrame for easier plotting
    df = pd.DataFrame(percentile_data)
    
    # Create the plot with dual axes for consistency
    fig = plt.figure(figsize=(10, 6))
    ax_counts = fig.add_subplot(111)  # Primary axis for patient counts
    ax_acuity = ax_counts.twinx()  # Secondary axis for visual acuity
    
    # Use consistent colors from the color system
    counts_color = COLORS.get('patient_counts', '#8FAD91')  # Muted Sage Green
    
    # Plot measurement counts as bars on the left axis
    sample_sizes = df['count'].values
    bar_width = 0.8 if len(df) > 1 else 1.0
    bars = ax_counts.bar(df["time"], sample_sizes, 
                        alpha=ALPHAS.get('patient_counts', 0.35),
                        color=counts_color, width=bar_width,
                        label='Number of Measurements', zorder=1)
    
    # Plot percentile bands from widest to narrowest on the right axis
    # 90% band (5th to 95th percentile) - lightest
    ax_acuity.fill_between(df['time'], df['p5'], df['p95'], 
                   color=COLORS['primary'], alpha=0.15, 
                   label='90% of patients (5th-95th percentile)')
    
    # 80% band (10th to 90th percentile)
    ax_acuity.fill_between(df['time'], df['p10'], df['p90'], 
                   color=COLORS['primary'], alpha=0.25, 
                   label='80% of patients (10th-90th percentile)')
    
    # 50% band (25th to 75th percentile) - interquartile range
    ax_acuity.fill_between(df['time'], df['p25'], df['p75'], 
                   color=COLORS['primary'], alpha=0.4, 
                   label='50% of patients (25th-75th percentile)')
    
    # Median line
    ax_acuity.plot(df['time'], df['p50'], 
           color=COLORS['primary_dark'], linewidth=2.5, 
           label='Median', zorder=5)
    
    # Mean line (for comparison)
    ax_acuity.plot(df['time'], df['mean'], '--',
           color=COLORS['primary_dark'], linewidth=1.5, alpha=0.7,
           label='Mean', zorder=4)
    
    # Configure axes labels with consistent styling from first chart
    ax_counts.set_xlabel("Months", fontsize=10, color=COLORS['text_secondary'])
    ax_counts.set_ylabel("Number of Measurements", fontsize=10, color=counts_color)
    
    # Set yearly x-axis ticks
    set_yearly_x_ticks(ax_counts)
    
    # Use the same blue for acuity as the first chart
    acuity_color = SEMANTIC_COLORS.get('acuity_data', COLORS['primary'])
    ax_acuity.set_ylabel("Visual Acuity (letters)", fontsize=10, color=acuity_color)
    ax_acuity.set_ylim(0, 85)  # Standard ETDRS range
    
    # Apply light spine styling from first chart
    light_spine_color = '#cccccc'  # Light gray
    light_spine_alpha = 0.3
    light_spine_width = 0.5
    
    # Remove top spines as they're not needed
    ax_counts.spines['top'].set_visible(False)
    ax_acuity.spines['top'].set_visible(False)
    
    # Configure left spine for patient counts
    ax_counts.spines['left'].set_visible(True)
    ax_counts.spines['left'].set_linewidth(light_spine_width)
    ax_counts.spines['left'].set_alpha(light_spine_alpha)
    ax_counts.spines['left'].set_color(light_spine_color)
    
    # Configure bottom spine
    ax_counts.spines['bottom'].set_visible(True)
    ax_counts.spines['bottom'].set_linewidth(light_spine_width)
    ax_counts.spines['bottom'].set_alpha(light_spine_alpha)
    ax_counts.spines['bottom'].set_color(light_spine_color)
    
    # Configure right spine for visual acuity 
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
    
    # Tick parameters - matching first chart
    ax_counts.tick_params(axis='y', colors=counts_color)
    ax_counts.tick_params(axis='x', colors=COLORS['text_secondary'])
    ax_acuity.tick_params(axis='y', colors=acuity_color)
    
    # Add title with same positioning as first chart
    fig.suptitle("Distribution of Patient Visual Acuity Over Time", 
                fontsize=12, 
                color=COLORS['text'], 
                x=0.1,  # Left-aligned  
                y=0.98,  # Near the top
                ha='left')
    
    # Combined legend for both axes - use 2 rows to avoid compression
    lines1, labels1 = ax_counts.get_legend_handles_labels()
    lines2, labels2 = ax_acuity.get_legend_handles_labels()
    ax_acuity.legend(lines1 + lines2, labels1 + labels2, 
                    frameon=False, fontsize=9, 
                    loc='upper center', bbox_to_anchor=(0.5, 1.08),
                    ncol=3,  # Use 3 columns, will wrap to 2 rows
                    columnspacing=1.5)
    
    # Add explanatory text
    fig.text(0.5, 0.01, 
            "This plot shows the actual distribution of patient vision scores, not statistical confidence intervals.",
            ha='center', va='bottom', fontsize=9, color=COLORS['text_secondary'],
            style='italic', wrap=True)
    
    # Optimize spacing around the chart for better Streamlit rendering - match first chart
    fig.subplots_adjust(left=0.12, right=0.88, top=0.88, bottom=0.15)
    plt.tight_layout(rect=[0, 0.03, 1, 0.92])
    
    return fig


def generate_va_over_time_thumbnail(results):
    """
    Generate a thumbnail version of the mean VA plot without labels.
    
    Parameters
    ----------
    results : dict
        Simulation results
    
    Returns
    -------
    matplotlib.figure.Figure
        Thumbnail plot figure
    """
    # Import the central color system - fail fast, no fallbacks
    from visualization.color_system import COLORS, SEMANTIC_COLORS, ALPHAS
    
    # Check if we have valid data - handle gracefully instead of raising errors
    if results.get("failed", False) or "mean_va_data" not in results or not results["mean_va_data"]:
        fig, ax = plt.subplots(figsize=(3, 2))
        
        # Determine specific message
        if results.get("failed", False):
            message = "Failed"
        elif "mean_va_data" not in results:
            message = "No VA data"
        elif not results["mean_va_data"]:
            message = "Empty VA data"  
        else:
            message = "No data"
            
        ax.text(0.5, 0.5, message, ha='center', va='center', fontsize=8, transform=ax.transAxes)
        ax.set_xticks([])
        ax.set_yticks([])
        
        # Style the placeholder
        for spine in ax.spines.values():
            spine.set_visible(False)
            
        return fig
    
    # Create DataFrame from the results
    df = pd.DataFrame(results["mean_va_data"])
    
    # Debug info for troubleshooting
    if DEBUG_MODE:
        print(f"Thumbnail: DataFrame columns: {list(df.columns)}")
        if len(df) > 0:
            print(f"Thumbnail: First row data: {df.iloc[0].to_dict()}")
    
    # Filter out data points beyond simulation duration
    duration_years = results.get("duration_years", 5)
    max_months = duration_years * 12
    
    # Determine the time column - fail fast if invalid
    if "time_months" in df.columns:
        time_col = "time_months"
    elif "time" in df.columns:
        time_col = "time"
        df["time_months"] = df["time"]
    else:
        raise ValueError(f"No time column found in data. Available columns: {list(df.columns)}")
    
    # Ensure we have visual_acuity column
    if "visual_acuity" not in df.columns:
        raise ValueError(f"No visual_acuity column found in data. Available columns: {list(df.columns)}")
    
    # Filter to simulation duration
    df["time_months"] = pd.to_numeric(df[time_col], errors='coerce')
    df = df.dropna(subset=["time_months", "visual_acuity"])
    df = df[df["time_months"] <= max_months]
    
    if df.empty:
        raise ValueError("No valid data points after filtering")
    
    # Create small figure
    fig, ax = plt.subplots(figsize=(3, 2))
    
    # Plot mean line
    ax.plot(df["time_months"], df["visual_acuity"], '-',
           color=SEMANTIC_COLORS['acuity_data'], 
           linewidth=2, alpha=0.8)
    
    # Plot confidence interval if available
    if "std_error" in df.columns:
        ci_factor = 1.96
        upper_ci = df["visual_acuity"] + ci_factor * df["std_error"]
        lower_ci = df["visual_acuity"] - ci_factor * df["std_error"]
        
        ax.fill_between(df["time_months"], lower_ci, upper_ci,
                       color=SEMANTIC_COLORS['acuity_data'], 
                       alpha=ALPHAS['very_low'])
    
    # Set limits per guidelines
    ax.set_xlim(0, max_months)
    ax.set_ylim(0, 85)
    
    # Add minimal but informative axes
    # X-axis: show 0 and max time
    ax.set_xticks([0, max_months])
    ax.set_xticklabels(['0', f'{max_months}'], fontsize=7)
    ax.set_xlabel('Months', fontsize=8)
    
    # Y-axis: show key values
    ax.set_yticks([0, 40, 85])
    ax.set_yticklabels(['0', '40', '85'], fontsize=7)
    ax.set_ylabel('VA (letters)', fontsize=8)
    
    # Add a title
    ax.set_title('Mean VA + 95% CI', fontsize=9, pad=3)
    
    # Keep spines but make them subtle
    for spine in ax.spines.values():
        spine.set_linewidth(0.5)
        spine.set_color('#cccccc')
    
    # Remove top and right spines for cleaner look
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    plt.tight_layout(pad=0.1)
    return fig


def generate_va_distribution_thumbnail(results):
    """
    Generate a thumbnail version of the distribution plot without labels.
    
    Parameters
    ----------
    results : dict
        Simulation results
    
    Returns
    -------
    matplotlib.figure.Figure
        Thumbnail plot figure
        
    Raises
    ------
    ValueError
        If patient data is not available in the results
    """
    # Import the central color system - fail fast, no fallbacks
    from visualization.color_system import COLORS, SEMANTIC_COLORS, ALPHAS
    
    # Get the raw patient data
    if "patient_data" not in results and "patient_histories" not in results:
        # Since we're generating the data, this should never happen
        raise ValueError("Patient-level data is required for distribution thumbnail but not found in results.")
    
    patient_histories = results.get("patient_data", results.get("patient_histories", {}))
    
    # Extract all patient VA values at each time point
    time_va_map = defaultdict(list)
    
    for patient_id, patient in patient_histories.items() if isinstance(patient_histories, dict) else enumerate(patient_histories):
        if isinstance(patient, list):
            baseline_time = None
            
            for i, visit in enumerate(patient):
                if isinstance(visit, dict) and 'vision' in visit:
                    if i == 0:
                        baseline_time = visit.get('date')
                        visit_time = 0
                    else:
                        if baseline_time and 'date' in visit:
                            visit_time = (visit['date'] - baseline_time).days / 30.44
                        else:
                            visit_time = i
                    
                    time_month = round(visit_time)
                    time_va_map[time_month].append(visit['vision'])
    
    # Calculate percentiles at each time point
    percentile_data = []
    
    for time_month in sorted(time_va_map.keys()):
        va_values = time_va_map[time_month]
        if len(va_values) >= 5:
            percentile_results = {
                'time': time_month,
                'p5': np.percentile(va_values, 5),
                'p25': np.percentile(va_values, 25),
                'p50': np.percentile(va_values, 50),
                'p75': np.percentile(va_values, 75),
                'p95': np.percentile(va_values, 95),
            }
            percentile_data.append(percentile_results)
    
    if not percentile_data:
        fig, ax = plt.subplots(figsize=(3, 2))
        ax.text(0.5, 0.5, "Insufficient data", ha='center', va='center', fontsize=8, transform=ax.transAxes)
        ax.set_xticks([])
        ax.set_yticks([])
        return fig
    
    # Convert to DataFrame
    df = pd.DataFrame(percentile_data)
    
    # Create small figure
    fig, ax = plt.subplots(figsize=(3, 2))
    
    # Plot percentile bands
    ax.fill_between(df['time'], df['p5'], df['p95'], 
                   color=COLORS['primary'], alpha=0.15)
    
    ax.fill_between(df['time'], df['p25'], df['p75'], 
                   color=COLORS['primary'], alpha=0.4)
    
    # Median line
    ax.plot(df['time'], df['p50'], 
           color=COLORS['primary_dark'], linewidth=2)
    
    # Set limits and styling
    duration_years = results.get("duration_years", 5)
    max_months = duration_years * 12
    ax.set_xlim(0, max_months)
    ax.set_ylim(0, 85)
    
    # Add minimal but informative axes
    # X-axis: show 0 and max time
    ax.set_xticks([0, max_months])
    ax.set_xticklabels(['0', f'{max_months}'], fontsize=7)
    ax.set_xlabel('Months', fontsize=8)
    
    # Y-axis: show key values
    ax.set_yticks([0, 40, 85])
    ax.set_yticklabels(['0', '40', '85'], fontsize=7)
    ax.set_ylabel('VA (letters)', fontsize=8)
    
    # Add a title
    ax.set_title('Patient Distribution', fontsize=9, pad=3)
    
    # Keep spines but make them subtle
    for spine in ax.spines.values():
        spine.set_linewidth(0.5)
        spine.set_color('#cccccc')
    
    # Remove top and right spines for cleaner look
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    plt.tight_layout(pad=0.1)
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
    # Use the patient state streamgraph and enhanced bar chart
    try:
        # Import our patient state streamgraph function which uses real data
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        from create_current_state_streamgraph_fixed import create_patient_state_streamgraph
        
        # Create the streamgraph if we have Parquet data
        if "visits_df" in results:
            try:
                streamgraph_fig = create_patient_state_streamgraph(
                    results, 
                    output_file=None,  # Don't save to file
                    show_title=True
                )
            except Exception as e:
                # If streamgraph fails, log the error but don't fail completely
                print(f"Warning: Could not create streamgraph: {e}")
                streamgraph_fig = None
        else:
            streamgraph_fig = None

        # Also create the enhanced bar chart
        from streamlit_app_parquet.discontinuation_chart import generate_enhanced_discontinuation_plot
        bar_chart_fig = generate_enhanced_discontinuation_plot(results)

        # Return both figures as a list if we have both, otherwise just the bar chart
        if streamgraph_fig:
            return [streamgraph_fig, bar_chart_fig]
        else:
            return bar_chart_fig
    except ImportError as e:
        # Fall back to just the bar chart
        from streamlit_app_parquet.discontinuation_chart import generate_enhanced_discontinuation_plot
        return generate_enhanced_discontinuation_plot(results)


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