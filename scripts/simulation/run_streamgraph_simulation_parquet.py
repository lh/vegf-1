#!/usr/bin/env python3
"""
Run an ABS simulation with explicit state flags and save results in Parquet format.

This script runs an ABS simulation that explicitly sets state flags for each visit
(is_discontinuation_visit, discontinuation_type, is_retreatment_visit, etc.) and 
saves the results in Parquet format to preserve type information.

Important features:
- Uses explicit flags for state transitions rather than inferring them
- Tracks cumulative retreatment status with has_been_retreated flag
- Once a patient is retreated, they remain in the retreated state for visualization
- Preserves type information using Parquet format
- Provides diagnostic information about simulation data
"""

import os
import sys
import argparse
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path

# Add project root to path
root_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(root_dir)

# Import simulation modules
from simulation.config import SimulationConfig
from treat_and_extend_abs_fixed import TreatAndExtendABS

def run_simulation(num_patients=100, duration_years=3):
    """
    Run an ABS simulation with the fixed implementation that sets discontinuation flags.
    
    Parameters
    ----------
    num_patients : int, optional
        Number of patients to simulate, by default 100
    duration_years : int, optional
        Duration of simulation in years, by default 3
        
    Returns
    -------
    tuple
        (patient_histories, statistics, config) tuple containing simulation results
    """
    print(f"Running simulation with {num_patients} patients for {duration_years} years")
    
    # Create simulation config
    config = SimulationConfig.from_yaml("eylea_literature_based")
    config.num_patients = num_patients
    config.duration_days = int(duration_years * 365)
    
    # Ensure discontinuation is enabled with diverse types
    if not hasattr(config, 'parameters') or not config.parameters:
        config.parameters = {}
    
    if "discontinuation" not in config.parameters:
        config.parameters["discontinuation"] = {}
    
    config.parameters["discontinuation"]["enabled"] = True
    
    # Configure diverse discontinuation criteria
    config.parameters["discontinuation"]["criteria"] = {
        # Planned discontinuations (common)
        "stable_max_interval": {
            "consecutive_visits": 3,
            "probability": 0.7
        },
        # Administrative discontinuations (occasional)
        "random_administrative": {
            "annual_probability": 0.15
        },
        # Treatment duration discontinuations (occasional)
        "treatment_duration": {
            "threshold_weeks": 52,
            "probability": 0.3
        }
    }
    
    # Configure retreatment
    config.parameters["discontinuation"]["retreatment"] = {
        "probability": 0.5  # Medium probability of retreatment
    }
    
    # Run simulation
    print("Initializing simulation...")
    try:
        sim = TreatAndExtendABS(config)
        print("Running simulation...")
        patient_histories = sim.run()
        print("Simulation completed successfully")
        
        # Collect statistics
        statistics = sim.stats
        
        return patient_histories, statistics, config
    except Exception as e:
        print(f"Error running simulation: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

def save_results_parquet(patient_histories, statistics, config, output_dir=None, base_filename=None):
    """
    Save simulation results in Parquet format.
    
    Parameters
    ----------
    patient_histories : dict
        Dictionary of patient histories
    statistics : dict
        Simulation statistics
    config : SimulationConfig
        Simulation configuration
    output_dir : str, optional
        Directory to save results in, by default "output/simulation_results"
    base_filename : str, optional
        Base filename for output files, by default "streamgraph_sim_{num_patients}p_{duration_years}yr_{timestamp}"
        
    Returns
    -------
    str
        Base path of saved files (without extensions)
    """
    # Default output directory
    if output_dir is None:
        output_dir = os.path.join(root_dir, "output", "simulation_results")
    
    # Create directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate filename if not provided
    if base_filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_filename = f"streamgraph_sim_{config.num_patients}p_{config.duration_days // 365}yr_{timestamp}"
    
    # Full base path
    base_path = os.path.join(output_dir, base_filename)
    
    # Convert patient histories to DataFrame
    print(f"Converting patient histories to DataFrame format...")
    patient_data = []
    
    # Track patients who are retreated
    retreated_patients = set()
    # For each patient, track their treatment status changes
    treatment_status_changes = {}
    
    # First pass: identify retreatment events
    for patient_id, visits in patient_histories.items():
        # Initialize tracking for this patient
        treatment_status_changes[patient_id] = []
        was_active = True  # Assume starting active
        was_discontinued = False
        discontinuation_found = False
        
        # Look for retreatment events by scanning the visit type and phase transitions
        for i, visit in enumerate(visits):
            # Check for explicit retreatment markers
            visit_type = visit.get("type", "")
            phase = visit.get("phase", "")
            
            # Identify a retreatment:
            # 1. If a loading phase appears after a monitoring phase
            # 2. If a regular visit follows a monitoring visit
            if i > 0:
                prev_phase = visits[i-1].get("phase", "")
                if prev_phase == "monitoring" and phase == "loading":
                    # This is a clear retreatment indicator - back to loading after monitoring
                    retreated_patients.add(patient_id)
                    treatment_status_changes[patient_id].append(i)
                    
            # Also check treatment status transitions
            treatment_status = visit.get("treatment_status", {})
            is_active = treatment_status.get("active", True)
            
            # Track the first point when a patient becomes inactive
            if is_active == False and was_active == True:
                discontinuation_found = True
                
            # Track when a patient becomes active again after discontinuation
            if i > 0 and discontinuation_found:
                if not was_active and is_active:
                    # This is a retreatment - patient was discontinued and is now active again
                    retreated_patients.add(patient_id)
                    treatment_status_changes[patient_id].append(i)
            
            # Update tracking state
            was_active = is_active
            
    # Second pass: add all visit data with retreatment and discontinuation flags
    for patient_id, visits in patient_histories.items():
        # Get transition points for this patient
        transitions = treatment_status_changes.get(patient_id, [])
        has_been_retreated = False    # Track if this patient has been retreated
        has_been_discontinued = False # Track if this patient has been discontinued
        discontinuation_type = None   # Track the type of discontinuation
        
        for i, visit in enumerate(visits):
            # Determine if this is a retreatment visit
            is_retreatment_visit = i in transitions
            
            # Check for discontinuation (using the correct column name from simulation)
            is_discontinuation = visit.get("is_discontinuation_visit", False)
            
            # When a patient is retreated, they are no longer considered discontinued
            if is_retreatment_visit:
                has_been_retreated = True
                has_been_discontinued = False
                discontinuation_type = None
            
            # When a patient is discontinued, track the discontinuation type
            if is_discontinuation:
                has_been_discontinued = True
                discontinuation_type = visit.get("discontinuation_type", "")
            
            # Create a record for this visit with patient_id and state flags
            visit_record = {
                "patient_id": patient_id,
                "is_retreatment_visit": is_retreatment_visit,      # Flag for the actual retreatment visit
                "has_been_retreated": has_been_retreated,          # Cumulative flag for all visits after retreatment
                "is_discontinuation": is_discontinuation,          # Flag for the actual discontinuation visit
                "has_been_discontinued": has_been_discontinued,    # Cumulative flag for all visits after discontinuation
                "discontinuation_type": discontinuation_type,      # Type of discontinuation (if any)
                **visit  # Include all visit data
            }
            patient_data.append(visit_record)
    
    # Create a DataFrame
    visits_df = pd.DataFrame(patient_data)
    
    # Ensure date is datetime
    if "date" in visits_df.columns and pd.api.types.is_string_dtype(visits_df["date"]):
        visits_df["date"] = pd.to_datetime(visits_df["date"])
        
    # Add diagnostic information
    print(f"Added retreatment flags for {len(retreated_patients)} patients")
    print(f"Total retreatment visits: {sum(visits_df['is_retreatment_visit'])}")
    print(f"Total visits with cumulative retreatment flag: {sum(visits_df['has_been_retreated'])}")
    
    # Calculate the percentage of visits that have the cumulative retreatment flag
    # This shows how many patient-timepoints are in the retreated state
    if len(visits_df) > 0:
        retreatment_percentage = (sum(visits_df['has_been_retreated']) / len(visits_df)) * 100
        print(f"Percentage of visits with retreatment flag: {retreatment_percentage:.2f}%")
    
    # Create metadata DataFrame
    metadata = {
        "simulation_type": "ABS",
        "patients": config.num_patients,
        "duration_years": config.duration_days / 365,
        "start_date": config.start_date if hasattr(config, "start_date") else datetime.now().strftime("%Y-%m-%d"),
        "discontinuation_enabled": True
    }
    metadata_df = pd.DataFrame([metadata])
    
    # Create statistics DataFrame
    stats_df = pd.DataFrame([statistics])
    
    # Save DataFrames as Parquet files
    print(f"Saving results to Parquet files...")
    visits_df.to_parquet(f"{base_path}_visits.parquet")
    metadata_df.to_parquet(f"{base_path}_metadata.parquet")
    stats_df.to_parquet(f"{base_path}_stats.parquet")
    
    print(f"Results saved to:")
    print(f"  - Visits: {base_path}_visits.parquet")
    print(f"  - Metadata: {base_path}_metadata.parquet")
    print(f"  - Statistics: {base_path}_stats.parquet")
    
    return base_path

def main():
    """Main function to run simulation and save results."""
    parser = argparse.ArgumentParser(description="Run simulation with explicit state flags and save as Parquet")
    parser.add_argument("--patients", "-p", type=int, default=100,
                        help="Number of patients to simulate")
    parser.add_argument("--years", "-y", type=int, default=3,
                        help="Duration of simulation in years")
    parser.add_argument("--output-dir", "-o", type=str, default=None,
                        help="Directory to save results in")
    
    args = parser.parse_args()
    
    # Run simulation
    patient_histories, statistics, config = run_simulation(
        num_patients=args.patients, 
        duration_years=args.years
    )
    
    # Save results
    base_path = save_results_parquet(
        patient_histories, 
        statistics, 
        config, 
        output_dir=args.output_dir
    )
    
    print(f"\nSimulation and data export completed successfully.")
    print(f"You can now visualize the results using create_patient_state_streamgraph.py")
    print(f"Example command: python create_patient_state_streamgraph.py --input {base_path}")

if __name__ == "__main__":
    main()