#!/usr/bin/env python3
"""
Debug script for visual acuity data visualization

This script runs a small simulation and analyzes the patient state data structure
to help debug visual acuity visualization issues in the Streamlit app.
"""

import os
import sys
import json
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import datetime

# Add project root to path
root_dir = os.path.abspath(os.path.dirname(__file__))
sys.path.append(root_dir)

print(f"Running from: {root_dir}")

# Import simulation modules
try:
    # Only import what we need
    from simulation.abs import ABSModel
    from simulation.des import DESModel
    from simulation.config import SimulationConfig
    from streamlit_app.simulation_runner import process_simulation_results, generate_va_over_time_plot
    
    print("Successfully imported simulation modules")
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)

def debug_patient_structure(patient, prefix=""):
    """Debug print a patient object's structure"""
    if hasattr(patient, "__dict__"):
        for attr_name in dir(patient):
            # Skip private attributes and methods
            if attr_name.startswith("_") or callable(getattr(patient, attr_name)):
                continue
            
            attr = getattr(patient, attr_name)
            if attr_name in ["acuity_history", "vision_history"]:
                print(f"{prefix}{attr_name} = {type(attr).__name__} with {len(attr) if hasattr(attr, '__len__') else 'N/A'} items")
                if hasattr(attr, "__getitem__") and len(attr) > 0:
                    first_item = attr[0] if isinstance(attr, list) else list(attr.items())[0] if hasattr(attr, "items") else None
                    print(f"{prefix}  First item: {type(first_item).__name__} = {first_item}")
            else:
                print(f"{prefix}{attr_name} = {type(attr).__name__}")
    else:
        print(f"{prefix}Patient is a {type(patient).__name__} with no __dict__")
        if isinstance(patient, dict):
            for key, value in patient.items():
                print(f"{prefix}{key} = {type(value).__name__}")

def run_test_simulation(model_type="ABS", population_size=10, duration_years=1):
    """Run a test simulation and analyze visual acuity data"""
    print(f"\n=== Running {model_type} simulation with {population_size} patients for {duration_years} years ===")
    
    # Create a basic configuration
    config = SimulationConfig()
    config.simulation_type = model_type
    config.population_size = population_size
    config.duration_years = duration_years
    
    # Ensure visualization parameters are set
    config.collect_population_statistics = True 
    config.record_va_trajectories = True
    config.record_individual_outcomes = True
    
    # Create and run simulation
    if model_type == "ABS":
        sim = ABSModel(config)
    else:
        sim = DESModel(config)
    
    # Run the simulation
    print("Starting simulation...")
    sim.run()
    print("Simulation complete!")
    
    # Get patient histories
    patient_histories = sim.get_patient_histories()
    print(f"Got {len(patient_histories)} patient histories")
    
    # Check the first patient
    first_patient_id = list(patient_histories.keys())[0] if isinstance(patient_histories, dict) else 0
    first_patient = patient_histories[first_patient_id]
    
    print("\n=== First Patient Structure ===")
    debug_patient_structure(first_patient)
    
    # Process results
    print("\n=== Processing Results ===")
    results = process_simulation_results(sim, patient_histories, sim.get_simulation_config())
    
    # Check if VA data is available
    if "mean_va_data" in results:
        print(f"✅ mean_va_data available with {len(results['mean_va_data'])} time points")
        
        # Print first few data points
        print("\nFirst 3 data points:")
        for i, datapoint in enumerate(results["mean_va_data"][:3]):
            print(f"  {i}: {datapoint}")
        
        # Visualize and save
        fig = generate_va_over_time_plot(results)
        
        # Save the figure
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"debug_va_visualization_{model_type}_{timestamp}.png"
        fig.savefig(output_file, dpi=100, bbox_inches="tight")
        print(f"✅ Visualization saved to {output_file}")
        
        # Also save the data
        df = pd.DataFrame(results["mean_va_data"])
        csv_file = f"debug_va_data_{model_type}_{timestamp}.csv"
        df.to_csv(csv_file, index=False)
        print(f"✅ Data saved to {csv_file}")
    else:
        print("❌ mean_va_data NOT available in results")
        
        # Check what is in patient histories to help debug
        print("\n=== Patient History Analysis ===")
        history_found = False
        
        # Check different common attribute names
        for i, (pid, patient) in enumerate(patient_histories.items()):
            if i >= 3:  # Only check first 3 patients
                break
                
            print(f"\nPatient {pid}:")
            if isinstance(patient, list):
                print(f"  Patient record is a list with {len(patient)} visits")
                if len(patient) > 0:
                    print(f"  First visit keys: {list(patient[0].keys()) if isinstance(patient[0], dict) else 'N/A'}")
                history_found = True
            elif hasattr(patient, "acuity_history"):
                print(f"  acuity_history found: {type(patient.acuity_history).__name__} with {len(patient.acuity_history) if hasattr(patient.acuity_history, '__len__') else 'N/A'} records")
                history_found = True
            elif hasattr(patient, "vision_history"):
                print(f"  vision_history found: {type(patient.vision_history).__name__} with {len(patient.vision_history) if hasattr(patient.vision_history, '__len__') else 'N/A'} records")
                history_found = True
            elif isinstance(patient, dict) and "acuity_history" in patient:
                print(f"  acuity_history found in dict: {type(patient['acuity_history']).__name__} with {len(patient['acuity_history']) if hasattr(patient['acuity_history'], '__len__') else 'N/A'} records")
                history_found = True
            elif hasattr(patient, "history"):
                print(f"  history attribute found: {type(patient.history).__name__} with {len(patient.history) if hasattr(patient.history, '__len__') else 'N/A'} records")
                if len(patient.history) > 0:
                    print(f"  First history record keys: {list(patient.history[0].keys()) if isinstance(patient.history[0], dict) else 'N/A'}")
                history_found = True
            else:
                print("  No recognized history attribute found")
                
        if not history_found:
            print("\n❌ No patient history data found - this is likely why visualization is empty")
            
        # Create a minimal results dict with an error message
        debug_results = {
            "simulation_type": model_type,
            "population_size": population_size,
            "duration_years": duration_years
        }
        
        # Generate and save error visualization
        fig = generate_va_over_time_plot(debug_results)
        error_file = f"debug_va_error_{model_type}_{timestamp}.png"
        fig.savefig(error_file, dpi=100, bbox_inches="tight")
        print(f"✅ Error visualization saved to {error_file}")
    
    # Return results for further analysis
    return results, patient_histories

if __name__ == "__main__":
    # Run both ABS and DES tests for comparison
    abs_results, abs_patients = run_test_simulation("ABS", population_size=10, duration_years=1)
    print("\n" + "="*50 + "\n")
    des_results, des_patients = run_test_simulation("DES", population_size=10, duration_years=1)
    
    # Print summary
    print("\n=== SUMMARY ===")
    print(f"ABS mean_va_data available: {'Yes' if 'mean_va_data' in abs_results else 'No'}")
    print(f"DES mean_va_data available: {'Yes' if 'mean_va_data' in des_results else 'No'}")