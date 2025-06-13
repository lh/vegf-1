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


def save_results(results, filename=None, save_parquet=True):
    """
    Save simulation results to JSON and optionally Parquet format.
    
    Parameters
    ----------
    results : dict
        Simulation results to save
    filename : str, optional
        Filename base to save to (without extension), by default auto-generated based on parameters
    save_parquet : bool, optional
        Whether to also save as Parquet format, by default True
        
    Returns
    -------
    tuple
        Paths to saved files (json_path, parquet_path)
    """
    # Create output directory if it doesn't exist
    output_dir = os.path.join(os.getcwd(), "output")
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate filename if not provided
    if filename is None:
        patient_count = results["config"]["patient_count"]
        duration = int(results["config"]["duration_years"])
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"streamgraph_sim_{patient_count}p_{duration}yr_{timestamp}"
    
    # Remove any extension from filename
    filename = os.path.splitext(filename)[0]
    
    # JSON path
    json_filepath = os.path.join(output_dir, f"{filename}.json")
    parquet_filepath = None
    
    # Save as JSON (legacy format, may be deprecated in future)
    try:
        with open(json_filepath, "w") as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\nJSON results saved to: {json_filepath}")
    except Exception as e:
        print(f"Error saving JSON results: {e}")
        json_filepath = None
    
    # Also save as Parquet if requested
    if save_parquet:
        try:
            import pandas as pd
            
            # Convert patient histories to a more tabular structure for efficient Parquet storage
            patient_data = []
            
            # Process patient histories
            for patient_id, visits in results["patient_histories"].items():
                for visit in visits:
                    # Create a flattened record for this visit
                    visit_record = {
                        "patient_id": patient_id,
                        # Convert common fields
                        "date": visit.get("date"),
                        "phase": visit.get("phase"),
                        "disease_state": visit.get("disease_state"),
                        "vision": visit.get("vision"),
                        "interval": visit.get("interval"),
                        # Add any discontinuation flags
                        "is_discontinuation": visit.get("is_discontinuation_visit", False),
                        "discontinuation_type": visit.get("discontinuation_type", ""),
                        "is_retreatment": visit.get("is_retreatment_visit", False)
                    }
                    
                    # Process action list
                    actions = visit.get("actions", [])
                    visit_record["has_injection"] = "injection" in actions
                    visit_record["has_oct"] = "oct_scan" in actions
                    
                    patient_data.append(visit_record)
            
            # Create a DataFrame
            visits_df = pd.DataFrame(patient_data)
            
            # Convert date column to datetime if it's a string
            if "date" in visits_df.columns and pd.api.types.is_string_dtype(visits_df["date"]):
                try:
                    visits_df["date"] = pd.to_datetime(visits_df["date"])
                except:
                    # Log but don't fail if conversion fails
                    print("Warning: Could not convert date column to datetime")
            
            # Create a top-level metadata DataFrame
            metadata = {
                "simulation_type": results.get("simulation_type"),
                "patients": results["config"]["patient_count"],
                "duration_years": results["config"]["duration_years"],
                "start_date": results["config"]["start_date"],
                "discontinuation_enabled": results["config"]["discontinuation_enabled"]
            }
            metadata_df = pd.DataFrame([metadata])
            
            # Create a statistics DataFrame
            stats_df = pd.DataFrame([results["statistics"]])
            
            # Save as a partitioned parquet dataset
            parquet_filepath = os.path.join(output_dir, f"{filename}.parquet")
            
            # Write each DataFrame to a separate partition
            visits_df.to_parquet(os.path.join(output_dir, f"{filename}_visits.parquet"))
            metadata_df.to_parquet(os.path.join(output_dir, f"{filename}_metadata.parquet"))
            stats_df.to_parquet(os.path.join(output_dir, f"{filename}_stats.parquet"))
            
            print(f"Parquet results saved to:")
            print(f"  - Visits: {os.path.join(output_dir, f'{filename}_visits.parquet')}")
            print(f"  - Metadata: {os.path.join(output_dir, f'{filename}_metadata.parquet')}")
            print(f"  - Statistics: {os.path.join(output_dir, f'{filename}_stats.parquet')}")
            
        except Exception as e:
            print(f"Error saving Parquet results: {e}")
            import traceback
            traceback.print_exc()
            parquet_filepath = None
    
    return json_filepath, parquet_filepath


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
                        help="Output filename base (default: auto-generated)")
    parser.add_argument("--no-parquet", action="store_true", 
                        help="Disable Parquet output (JSON only)")
    
    args = parser.parse_args()
    
    # Run simulation
    results = run_simulation(
        config_name=args.config,
        num_patients=args.patients,
        duration_years=args.years
    )
    
    # Save results
    if results:
        save_results(results, args.output, save_parquet=not args.no_parquet)


if __name__ == "__main__":
    main()