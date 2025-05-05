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

# Add the project root directory to sys.path to allow importing from the main project
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root_dir)

# Also add the current working directory (important when running as a module)
sys.path.append(os.getcwd())

# Import simulation modules
try:
    from simulation.config import SimulationConfig
    
    # Import simulation classes
    from treat_and_extend_abs import TreatAndExtendABS
    from treat_and_extend_des import TreatAndExtendDES
    
    # Import parsing modules
    from protocols.protocol_parser import ProtocolParser
    from protocol_models import TreatmentProtocol
    
    # Flag that imports were successful
    simulation_imports_successful = True
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
    # Create a temporary YAML file with the configuration
    config_data = {
        "name": "APE Simulation",
        "protocol": {
            "name": "Enhanced Discontinuation Protocol",
            "description": "AMD treatment protocol with enhanced discontinuation model"
        },
        "output": {
            "type": "memory",
            "detail_level": "standard"
        },
        "simulation": {
            "type": params["simulation_type"],
            "title": "APE Simulation",
            "description": "Simulation generated from APE UI",
            "population_size": params["population_size"],
            "duration_days": params["duration_years"] * 365,
            "random_seed": params.get("random_seed", 42)
        },
        "discontinuation": {
            "enabled": True,
            "criteria": {
                "stable_max_interval": {
                    "consecutive_visits": params["consecutive_stable_visits"],
                    "probability": params["planned_discontinue_prob"],
                    "interval_weeks": 16
                },
                "random_administrative": {
                    "annual_probability": params["admin_discontinue_prob"]
                },
                "treatment_duration": {
                    "threshold_weeks": 52,
                    "probability": 0.1
                },
                "premature": {
                    "min_interval_weeks": 8,
                    "probability_factor": 2.0
                }
            },
            "monitoring": {
                "planned": {
                    "follow_up_schedule": params["monitoring_schedule"]
                },
                "unplanned": {
                    "follow_up_schedule": [8, 16, 24]
                },
                "recurrence_detection_probability": 0.87
            },
            "recurrence": {
                "planned": {
                    "base_annual_rate": 0.13,
                    "cumulative_rates": {
                        "year_1": 0.13,
                        "year_3": 0.40,
                        "year_5": 0.65
                    }
                },
                "premature": {
                    "base_annual_rate": 0.53,
                    "cumulative_rates": {
                        "year_1": 0.53,
                        "year_3": 0.85,
                        "year_5": 0.95
                    }
                },
                "administrative": {
                    "base_annual_rate": 0.30,
                    "cumulative_rates": {
                        "year_1": 0.30,
                        "year_3": 0.70,
                        "year_5": 0.85
                    }
                },
                "duration_based": {
                    "base_annual_rate": 0.32,
                    "cumulative_rates": {
                        "year_1": 0.21,
                        "year_3": 0.74,
                        "year_5": 0.88
                    }
                },
                "risk_modifiers": {
                    "with_PED": params.get("recurrence_risk_multiplier", 1.0),
                    "without_PED": 1.0
                }
            },
            "retreatment": {
                "eligibility_criteria": {
                    "detected_fluid": True,
                    "vision_loss_letters": 5
                },
                "probability": 0.95
            }
        },
        "clinicians": {
            "enabled": params["enable_clinician_variation"],
            "profiles": {
                "adherent": {
                    "protocol_adherence_rate": 0.95,
                    "probability": 0.25,
                    "characteristics": {
                        "risk_tolerance": "low",
                        "conservative_retreatment": True
                    }
                },
                "average": {
                    "protocol_adherence_rate": 0.80,
                    "probability": 0.50,
                    "characteristics": {
                        "risk_tolerance": "medium",
                        "conservative_retreatment": False
                    }
                },
                "non_adherent": {
                    "protocol_adherence_rate": 0.50,
                    "probability": 0.25,
                    "characteristics": {
                        "risk_tolerance": "high",
                        "conservative_retreatment": False
                    }
                }
            },
            "decision_biases": {
                "stability_thresholds": {
                    "adherent": 3,
                    "average": 2,
                    "non_adherent": 1
                },
                "interval_preferences": {
                    "adherent": {
                        "min_interval": 8,
                        "max_interval": 16,
                        "extension_threshold": 2
                    },
                    "average": {
                        "min_interval": 8,
                        "max_interval": 12,
                        "extension_threshold": 1
                    },
                    "non_adherent": {
                        "min_interval": 6,
                        "max_interval": 16,
                        "extension_threshold": 0
                    }
                }
            },
            "patient_assignment": {
                "mode": "fixed",
                "continuity_of_care": 0.9
            }
        }
    }
    
    # No monitoring for administrative discontinuation if specified
    if params.get("no_monitoring_for_admin", True):
        config_data["discontinuation"]["monitoring"]["administrative"] = {
            "follow_up_schedule": []
        }
    
    # Write config to a temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as temp:
        import yaml
        yaml.dump(config_data, temp)
        temp_path = temp.name
    
    # Create config object
    config = SimulationConfig.from_yaml(temp_path)
    
    # Clean up temporary file
    os.unlink(temp_path)
    
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
            st.warning("Simulation modules not available. Using sample data.")
            # Create sample data
            return generate_sample_results(params)
        
        try:
            # Create temporary YAML config file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as temp_config:
                config_path = temp_config.name
                
                # Create a valid YAML configuration
                config_data = {
                    "name": "ape_simulation",
                    "output": {
                        "directory": "output",
                        "format": "csv"
                    },
                    "simulation": {
                        "name": "APE Simulation",
                        "description": "Simulation generated from APE UI",
                        "start_date": "2025-01-01",
                        "duration_days": params["duration_years"] * 365,
                        "num_patients": params["population_size"],
                        "random_seed": params.get("random_seed", 42)
                    },
                    "protocol": {
                        "name": "Treat-and-Extend with Enhanced Discontinuation",
                        "type": "treat_and_extend",
                        "agent": f"treat_and_extend_{params['simulation_type'].lower()}",
                        "loading_phase": {
                            "injections": 3,
                            "interval_weeks": 4
                        },
                        "maintenance_phase": {
                            "min_interval_weeks": 8,
                            "max_interval_weeks": 16,
                            "extension_increment_weeks": 2,
                            "reduction_increment_weeks": 2
                        }
                    },
                    "discontinuation": {
                        "enabled": True,
                        "criteria": {
                            "stable_max_interval": {
                                "consecutive_visits": params.get("consecutive_stable_visits", 3),
                                "probability": params["planned_discontinue_prob"],
                                "interval_weeks": 16
                            },
                            "random_administrative": {
                                "annual_probability": params["admin_discontinue_prob"]
                            },
                            "treatment_duration": {
                                "threshold_weeks": 52,
                                "probability": 0.1
                            },
                            "premature": {
                                "min_interval_weeks": 8,
                                "probability_factor": 2.0
                            }
                        },
                        "monitoring": {
                            "planned": {
                                "follow_up_schedule": params.get("monitoring_schedule", [12, 24, 36])
                            },
                            "unplanned": {
                                "follow_up_schedule": [8, 16, 24]
                            },
                            "recurrence_detection_probability": 0.87
                        }
                    },
                    "clinicians": {
                        "enabled": params["enable_clinician_variation"]
                    }
                }
                
                # Add administrative monitoring configuration based on user preference
                if params.get("no_monitoring_for_admin", True):
                    config_data["discontinuation"]["monitoring"]["administrative"] = {
                        "follow_up_schedule": []
                    }
                
                # Write YAML to the temp file
                import yaml
                yaml.dump(config_data, temp_config)
            
            # Use an existing simulation configuration as base
            # Instead of creating our own, use one of the existing test configurations
            # that has all the required protocol definitions
            test_config_path = os.path.join(root_dir, "protocols", "simulation_configs", "test_simulation.yaml")
            
            st.info(f"Using configuration file: {test_config_path}")
            
            # Create a SimulationConfig from an existing YAML file
            config = SimulationConfig.from_yaml(test_config_path)
            
            # Override specific parameters based on user input
            config.num_patients = params["population_size"]
            config.duration_days = params["duration_years"] * 365
            config.simulation_type = params["simulation_type"].lower()
            
            # Delete the temporary file we created but won't use
            os.unlink(config_path)
            
            # Run appropriate simulation type
            if params["simulation_type"] == "ABS":
                sim = TreatAndExtendABS(config)
            else:  # DES
                sim = TreatAndExtendDES(config)
            
            # Remove the temporary file
            os.unlink(config_path)
            
            # Run simulation
            patient_histories = sim.run()
            
            end_time = time.time()
            
            # Process results
            results = process_simulation_results(sim, patient_histories, params)
            results["runtime_seconds"] = end_time - start_time
            
            return results
        
        except Exception as e:
            st.error(f"Error running simulation: {e}")
            st.warning("Using sample data instead.")
            # If a temp file was created, clean it up
            if 'config_path' in locals():
                try:
                    os.unlink(config_path)
                except:
                    pass
            return generate_sample_results(params)


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
    discontinuation_manager = sim.get_discontinuation_manager()
    if hasattr(discontinuation_manager, 'get_statistics'):
        disc_stats = discontinuation_manager.get_statistics()
        
        # Get discontinuation counts
        discontinuation_counts = {
            "Planned": 0,
            "Administrative": 0,
            "Time-based": 0,
            "Premature": 0
        }
        
        # Extract counts from statistics - structure depends on implementation
        if isinstance(disc_stats, dict) and "discontinuations" in disc_stats:
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
        
        results["discontinuation_counts"] = discontinuation_counts
        results["total_discontinuations"] = sum(discontinuation_counts.values())
        
        # Add other statistics if available
        if "recurrences" in disc_stats:
            results["recurrences"] = disc_stats["recurrences"]
        if "retreatments" in disc_stats:
            results["retreatments"] = disc_stats["retreatments"]
    
    # Process patient histories for visual acuity outcomes
    va_data = []
    for patient in patient_histories:
        # Structure depends on simulation implementation
        if hasattr(patient, 'acuity_history'):
            for time, va in patient.acuity_history:
                va_data.append({
                    "patient_id": patient.id,
                    "time": time,
                    "visual_acuity": va
                })
        elif isinstance(patient, dict) and "acuity_history" in patient:
            for time_point in patient["acuity_history"]:
                va_data.append({
                    "patient_id": patient.get("id", "unknown"),
                    "time": time_point.get("time", 0),
                    "visual_acuity": time_point.get("acuity", 0)
                })
    
    if va_data:
        va_df = pd.DataFrame(va_data)
        
        # Calculate mean acuity over time
        mean_va = va_df.groupby("time")["visual_acuity"].mean().reset_index()
        results["mean_va_data"] = mean_va.to_dict(orient="records")
    
    # Process injection data
    injection_data = []
    for patient in patient_histories:
        injection_count = 0
        
        # Structure depends on simulation implementation
        if hasattr(patient, 'injection_history'):
            injection_count = len(patient.injection_history)
        elif isinstance(patient, dict) and "injection_history" in patient:
            injection_count = len(patient["injection_history"])
        
        injection_data.append({
            "patient_id": patient.id if hasattr(patient, 'id') else "unknown",
            "injection_count": injection_count
        })
    
    if injection_data:
        injection_df = pd.DataFrame(injection_data)
        results["mean_injections"] = injection_df["injection_count"].mean()
        results["total_injections"] = injection_df["injection_count"].sum()
    
    # Save results to a temporary file for report generation
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp:
        json.dump(results, temp)
        results["data_path"] = temp.name
    
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
        json.dump(results, f, indent=2)
    
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
    if "mean_va_data" not in results:
        # Create sample data if real data isn't available
        months = np.arange(0, results["duration_years"] * 12)
        va = 75 + 5 * (1 - np.exp(-0.2 * months)) - 0.02 * months
        
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(months, va)
        ax.set_xlabel("Months")
        ax.set_ylabel("Visual Acuity (letters)")
        ax.set_title("Mean Visual Acuity Over Time (SAMPLE DATA)")
        ax.grid(True, linestyle='--', alpha=0.7)
        return fig
    
    # Create DataFrame from the results
    df = pd.DataFrame(results["mean_va_data"])
    
    # Convert time to months if it's in different units
    # This depends on how time is stored in your simulation
    if df["time"].max() > 1000:  # Likely in days or hours
        df["time_months"] = df["time"] / 30  # Approximate days to months
    else:
        df["time_months"] = df["time"]
    
    # Create the plot
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(df["time_months"], df["visual_acuity"])
    ax.set_xlabel("Months")
    ax.set_ylabel("Visual Acuity (letters)")
    ax.set_title("Mean Visual Acuity Over Time")
    ax.grid(True, linestyle='--', alpha=0.7)
    
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
    if "discontinuation_counts" not in results:
        # Create sample data if real data isn't available
        disc_types = ["Planned", "Administrative", "Time-based", "Premature"]
        counts = [250, 120, 180, 80]
        
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.bar(disc_types, counts)
        ax.set_xlabel("Discontinuation Type")
        ax.set_ylabel("Count")
        ax.set_title("Discontinuation by Type (SAMPLE DATA)")
        ax.grid(True, linestyle='--', alpha=0.7, axis='y')
        return fig
    
    # Create the plot from actual data
    disc_counts = results["discontinuation_counts"]
    types = list(disc_counts.keys())
    counts = list(disc_counts.values())
    
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar(types, counts)
    
    # Add percentages on top of bars
    total = sum(counts)
    for bar, count in zip(bars, counts):
        percentage = count / total * 100 if total > 0 else 0
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 5,
            f"{percentage:.1f}%",
            ha='center',
            va='bottom'
        )
    
    ax.set_xlabel("Discontinuation Type")
    ax.set_ylabel("Count")
    ax.set_title("Discontinuation by Type")
    ax.grid(True, linestyle='--', alpha=0.7, axis='y')
    
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
    params["consecutive_stable_visits"] = st.session_state.get("consecutive_stable_visits", 3)
    params["monitoring_schedule"] = st.session_state.get("monitoring_schedule", [12, 24, 36])
    params["no_monitoring_for_admin"] = st.session_state.get("no_monitoring_for_admin", True)
    params["recurrence_risk_multiplier"] = st.session_state.get("recurrence_risk_multiplier", 1.0)
    
    return params