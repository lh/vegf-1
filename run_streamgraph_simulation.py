#!/usr/bin/env python
"""
Run a real ABS simulation with parameters optimized for streamgraph visualization.

This script runs a real Agent-Based Simulation (ABS) with parameters configured
to generate a variety of discontinuation types and patient states for proper
streamgraph visualization. No synthetic data is used at any point.

The simulation results are saved to a JSON file for further analysis and visualization.
"""

import os
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path

# Add project root to path
root_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(root_dir)

# Import simulation modules
from simulation.config import SimulationConfig
from treat_and_extend_abs_fixed import TreatAndExtendABS


def configure_simulation(base_config, num_patients=100, duration_years=5):
    """
    Configure simulation with parameters optimized for discontinuation visualization.
    
    Parameters
    ----------
    base_config : SimulationConfig
        Base configuration to modify
    num_patients : int, optional
        Number of patients to simulate, by default 100
    duration_years : int, optional
        Duration of simulation in years, by default 5
        
    Returns
    -------
    SimulationConfig
        Modified configuration
    """
    # Override basic parameters
    base_config.num_patients = num_patients
    base_config.duration_days = int(duration_years * 365)

    # Ensure discontinuation is enabled
    if not hasattr(base_config, 'parameters'):
        base_config.parameters = {}
    if "discontinuation" not in base_config.parameters:
        base_config.parameters["discontinuation"] = {}
        
    base_config.parameters["discontinuation"]["enabled"] = True
    
    # Configure different discontinuation types with realistic probabilities
    if "criteria" not in base_config.parameters["discontinuation"]:
        base_config.parameters["discontinuation"]["criteria"] = {}
        
    # 1. Stable max interval (planned discontinuation)
    if "stable_max_interval" not in base_config.parameters["discontinuation"]["criteria"]:
        base_config.parameters["discontinuation"]["criteria"]["stable_max_interval"] = {}
    
    base_config.parameters["discontinuation"]["criteria"]["stable_max_interval"]["probability"] = 0.7
    base_config.parameters["discontinuation"]["criteria"]["stable_max_interval"]["consecutive_visits"] = 3
    base_config.parameters["discontinuation"]["criteria"]["stable_max_interval"]["interval_weeks"] = 16
    
    # 2. Random administrative (unplanned administrative discontinuation)
    if "random_administrative" not in base_config.parameters["discontinuation"]["criteria"]:
        base_config.parameters["discontinuation"]["criteria"]["random_administrative"] = {}
        
    base_config.parameters["discontinuation"]["criteria"]["random_administrative"]["annual_probability"] = 0.15
    
    # 3. Treatment duration (course completion)
    if "treatment_duration" not in base_config.parameters["discontinuation"]["criteria"]:
        base_config.parameters["discontinuation"]["criteria"]["treatment_duration"] = {}
        
    base_config.parameters["discontinuation"]["criteria"]["treatment_duration"]["max_duration_months"] = 24
    base_config.parameters["discontinuation"]["criteria"]["treatment_duration"]["probability"] = 0.5
    
    # Configure retreatment settings
    if "retreatment" not in base_config.parameters["discontinuation"]:
        base_config.parameters["discontinuation"]["retreatment"] = {}
    
    # High probability of retreatment for fluid detection
    base_config.parameters["discontinuation"]["retreatment"]["probability"] = 0.8
    
    # Configure vision model for higher fluid detection rate
    if "vision_model" not in base_config.parameters:
        base_config.parameters["vision_model"] = {}
    
    base_config.parameters["vision_model"]["fluid_detection_probability"] = 0.6
    
    # Configure monitoring visits
    if "monitoring" not in base_config.parameters["discontinuation"]:
        base_config.parameters["discontinuation"]["monitoring"] = {}
        
    if "cessation_types" not in base_config.parameters["discontinuation"]["monitoring"]:
        base_config.parameters["discontinuation"]["monitoring"]["cessation_types"] = {}
    
    # Set monitoring schedule for all discontinuation types
    base_config.parameters["discontinuation"]["monitoring"]["cessation_types"] = {
        "stable_max_interval": "planned",
        "random_administrative": "planned",
        "treatment_duration": "planned",
        "premature": "planned"
    }
    
    # Configure monitoring visit schedule (months)
    if "schedule" not in base_config.parameters["discontinuation"]["monitoring"]:
        base_config.parameters["discontinuation"]["monitoring"]["schedule"] = {}
    
    base_config.parameters["discontinuation"]["monitoring"]["schedule"] = {
        "year_1": 8,  # Monitor every 8 months in year 1
        "year_2_3": 12,  # Monitor every 12 months in years 2-3
        "year_4_plus": 16  # Monitor every 16 months after year 4
    }
    
    return base_config


def run_simulation(config_name="test_simulation", num_patients=100, duration_years=5):
    """
    Run a simulation and save results.
    
    Parameters
    ----------
    config_name : str, optional
        Base configuration to use, by default "test_simulation"
    num_patients : int, optional
        Number of patients to simulate, by default 100
    duration_years : int, optional
        Duration of simulation in years, by default 5
        
    Returns
    -------
    dict
        Simulation results
    """
    # Load base configuration
    try:
        config = SimulationConfig.from_yaml(config_name)
    except Exception as e:
        print(f"Error loading configuration '{config_name}': {e}")
        sys.exit(1)
    
    # Configure for visualization
    config = configure_simulation(config, num_patients, duration_years)
    
    # Print configuration details
    print(f"Running simulation with parameters:")
    print(f"  - Patients: {config.num_patients}")
    print(f"  - Duration: {config.duration_days / 365:.1f} years")
    print(f"  - Discontinuation types enabled:")
    disc_types = config.parameters.get("discontinuation", {}).get("criteria", {}).keys()
    for disc_type in disc_types:
        print(f"    - {disc_type}")
    
    # Initialize and run simulation
    try:
        print("\nInitializing TreatAndExtendABS simulation...")
        sim = TreatAndExtendABS(config)
        
        print("Running simulation...")
        start_time = datetime.now()
        patient_histories = sim.run()
        end_time = datetime.now()
        
        run_time = (end_time - start_time).total_seconds()
        print(f"Simulation completed in {run_time:.2f} seconds")
        
        # Compile results
        simulation_results = {
            "simulation_type": "ABS",
            "config": {
                "patient_count": config.num_patients,
                "duration_years": config.duration_days / 365,
                "start_date": config.start_date,
                "discontinuation_enabled": config.parameters.get("discontinuation", {}).get("enabled", False)
            },
            "statistics": sim.stats,
            "patient_histories": patient_histories
        }
        
        # Print basic statistics
        try:
            print("\nSimulation Statistics:")
            print("-" * 30)
            print(f"Total patients: {config.num_patients}")
            print(f"Total visits: {sim.stats.get('total_visits', 0)}")
            print(f"Total injections: {sim.stats.get('total_injections', 0)}")
            print(f"Unique discontinued patients: {sim.stats.get('unique_discontinuations', 0)}")
            print(f"Discontinuation rate: {(sim.stats.get('unique_discontinuations', 0) / config.num_patients) * 100:.1f}%")
            
            # Print discontinuation types
            disc_counts = sim.stats.get("discontinuation_counts", {})
            if disc_counts:
                print("\nDiscontinuation Counts:")
                total_count = 0
                for disc_type, count in disc_counts.items():
                    print(f"  - {disc_type}: {count}")
                    total_count += count
                print(f"Total discontinuations: {total_count}")
            
            # Print retreatment information
            print(f"\nRetreatments: {sim.stats.get('retreatments', 0)}")
            print(f"Unique retreated patients: {sim.stats.get('unique_retreatments', 0)}")
            
            # Print retreatment by type
            retreatment_by_type = sim.stats.get("retreatments_by_type", {})
            if retreatment_by_type:
                print("\nRetreatments by Type:")
                for disc_type, count in retreatment_by_type.items():
                    print(f"  - {disc_type}: {count}")
        except Exception as e:
            print(f"Error displaying statistics: {e}")
        
        return simulation_results
    except Exception as e:
        print(f"Error running simulation: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def save_results(results, filename=None):
    """
    Save simulation results to a JSON file.
    
    Parameters
    ----------
    results : dict
        Simulation results to save
    filename : str, optional
        Filename to save to, by default auto-generated based on parameters
        
    Returns
    -------
    str
        Path to saved file
    """
    # Create output directory if it doesn't exist
    output_dir = os.path.join(os.getcwd(), "output")
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate filename if not provided
    if filename is None:
        patient_count = results["config"]["patient_count"]
        duration = int(results["config"]["duration_years"])
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"streamgraph_sim_{patient_count}p_{duration}yr_{timestamp}.json"
    
    # Ensure filename has .json extension
    if not filename.endswith(".json"):
        filename += ".json"
    
    # Full path
    filepath = os.path.join(output_dir, filename)
    
    # Save the file
    try:
        with open(filepath, "w") as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\nResults saved to: {filepath}")
        return filepath
    except Exception as e:
        print(f"Error saving results: {e}")
        return None


def main():
    """Main function to parse arguments and run simulation."""
    parser = argparse.ArgumentParser(description="Run a simulation for streamgraph visualization")
    parser.add_argument("--config", type=str, default="test_simulation", 
                        help="Base configuration name (default: test_simulation)")
    parser.add_argument("--patients", type=int, default=100, 
                        help="Number of patients (default: 100)")
    parser.add_argument("--years", type=float, default=5, 
                        help="Simulation duration in years (default: 5)")
    parser.add_argument("--output", type=str, default=None, 
                        help="Output filename (default: auto-generated)")
    
    args = parser.parse_args()
    
    # Run simulation
    results = run_simulation(
        config_name=args.config,
        num_patients=args.patients,
        duration_years=args.years
    )
    
    # Save results
    if results:
        save_results(results, args.output)


if __name__ == "__main__":
    main()