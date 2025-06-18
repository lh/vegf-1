"""
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
WARNING: This script uses the DEPRECATED simulation framework (v1)

This script imports from simulation/ which is the old framework.
For new development, use scripts that import from simulation_v2/

Status: Legacy script - kept for reference
Consider: Updating to use simulation_v2 framework
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

Run comparative simulations between agent-based and discrete event models.

This script executes both simulation types (ABS and DES) using the same configuration,
compares their results, and generates visualizations showing:

1. Individual simulation results (mean vision over time)
2. Comparative results between simulation types
3. Summary statistics for both simulations

The script requires:
- A valid simulation configuration YAML file (default: test_simulation.yaml)
- All required dependencies installed (see requirements.txt)

Outputs:
- individual_simulation_results.png: Side-by-side plots of ABS and DES results
- mean_acuity_comparison.png: Direct comparison plot of mean vision trajectories
- Console output with summary statistics

Example Usage:
    python run_simulation.py                     # Uses default test_simulation.yaml
    python run_simulation.py eylea_literature_based  # Uses specified configuration

Command-line Arguments:
    config_name: Name of the configuration file (without .yaml extension)
                 Located in protocols/simulation_configs/
"""

import logging
import argparse
import os.path
from pathlib import Path
# Configure logging to reduce debug output
logging.basicConfig(level=logging.INFO)
# Set specific loggers to higher levels to reduce noise
logging.getLogger('matplotlib').setLevel(logging.WARNING)
logging.getLogger('PIL').setLevel(logging.WARNING)

from datetime import datetime, timedelta
from simulation.config import SimulationConfig
from simulation.abs import AgentBasedSimulation
from simulation.base import Event

# Use the treat-and-extend protocol implementation for ABS
from treat_and_extend_abs import run_treat_and_extend_abs as run_abs
# Use the treat-and-extend protocol implementation for DES
from treat_and_extend_des import run_treat_and_extend_des as run_des
# Previous implementations:
# from direct_des_fix import run_direct_des_fix as run_des
# from des_simulation import run_des_simulation as run_des
# from test_des_simulation import run_test_des_simulation as run_des
import matplotlib.pyplot as plt
from analysis.simulation_results import SimulationResults
from visualization.comparison_viz import plot_mean_acuity_comparison

def main():
    """Execute comparative simulation runs and generate results.
    
    This function:
    1. Loads the simulation configuration
    2. Runs both agent-based and discrete event simulations
    3. Processes and compares results
    4. Generates visualizations
    5. Prints summary statistics
    
    Configuration
    ------------
    Uses command-line argument or 'test_simulation.yaml' by default.
    
    Output Files
    -----------
    - individual_simulation_results.png
    - mean_acuity_comparison.png
    
    Console Output
    -------------
    - Progress messages during simulation
    - Summary statistics for both simulation types
    """
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Run comparative simulations between ABS and DES models.')
    parser.add_argument('config_name', nargs='?', default='test_simulation',
                        help='Name of the configuration file (without .yaml extension)')
    args = parser.parse_args()
    
    # Validate configuration file exists
    config_path = Path("protocols") / "simulation_configs" / f"{args.config_name}.yaml"
    if not config_path.exists():
        print(f"Error: Configuration file '{config_path}' not found.")
        print("Available configurations:")
        for config_file in Path("protocols/simulation_configs").glob("*.yaml"):
            print(f"  - {config_file.stem}")
        return
    
    print(f"Loading configuration from: {config_path}")
    print(f"Absolute path: {config_path.absolute()}")
    
    # Check if file exists
    if os.path.exists(config_path):
        print(f"Config file exists at {config_path}")
        with open(config_path, 'r') as f:
            print(f"File contents: {f.read()}")
    
    # Load configuration
    standard_config = SimulationConfig.from_yaml(args.config_name)
    
    print("\nRunning Agent-Based Simulation...")
    abs_results = run_abs(
        config=standard_config,
        verbose=True  # Enable verbose output to see simulation progress
    )
    
    print("\nRunning Discrete Event Simulation...")
    des_results = run_des(
        config=standard_config,
        verbose=True
    )
    
    # Setup time range
    start_date = datetime(2023, 1, 1)
    end_date = start_date + timedelta(days=365)
    
    # Process results
    abs_sim_results = SimulationResults(
        start_date=start_date,
        end_date=end_date,
        patient_histories=abs_results
    )
    
    des_sim_results = SimulationResults(
        start_date=start_date,
        end_date=end_date,
        patient_histories=des_results
    )
    
    # Dump ABS data to a file for inspection
    import json
    import pandas as pd
    
    # First, convert the ABS data to a more readable format
    abs_data_list = []
    for patient_id, history in abs_results.items():
        for visit in history:
            visit_data = {
                'patient_id': patient_id,
                'date': str(visit.get('date', '')),
                'vision': visit.get('vision', None),
                'type': visit.get('type', ''),
                'actions': str(visit.get('actions', [])),
                'disease_state': visit.get('disease_state', '')
            }
            abs_data_list.append(visit_data)
    
    # Convert to DataFrame for easier viewing
    if abs_data_list:
        abs_df = pd.DataFrame(abs_data_list)
        abs_df.to_csv('abs_data_dump.csv', index=False)
        print("\nABS data dumped to abs_data_dump.csv")
    else:
        print("\nNo ABS data to dump")
    
    # Create individual visualizations
    # Create separate figures for ABS and DES to avoid issues with subplot sharing
    
    # ABS visualization
    abs_fig = plt.figure(figsize=(8, 6))
    abs_plot = abs_sim_results.plot_mean_vision(title="Agent-Based Simulation Results")
    if abs_plot is None:
        print("Warning: No data available for ABS visualization")
        plt.close(abs_fig)
    else:
        plt.savefig('abs_mean_acuity.png', dpi=300)
        print("Saved ABS visualization to abs_mean_acuity.png")
    plt.close()
    
    # DES visualization
    des_fig = plt.figure(figsize=(8, 6))
    des_plot = des_sim_results.plot_mean_vision(title="Discrete Event Simulation Results")
    if des_plot is None:
        print("Warning: No data available for DES visualization")
        plt.close(des_fig)
    else:
        plt.savefig('des_mean_acuity.png', dpi=300)
        print("Saved DES visualization to des_mean_acuity.png")
    plt.close()
    
    # Now create a combined figure with both plots side by side
    # Use the saved images to create a combined figure
    import matplotlib.image as mpimg
    
    try:
        # Load the saved images
        abs_img = mpimg.imread('abs_mean_acuity.png')
        des_img = mpimg.imread('des_mean_acuity.png')
        
        # Create a new figure for the combined plot
        combined_fig = plt.figure(figsize=(16, 6))
        
        # Add the images as subplots
        plt.subplot(121)
        plt.imshow(abs_img)
        plt.axis('off')
        
        plt.subplot(122)
        plt.imshow(des_img)
        plt.axis('off')
        
        plt.tight_layout()
        plt.savefig('individual_simulation_results.png', dpi=300)
        print("Saved combined visualization to individual_simulation_results.png")
    except Exception as e:
        print(f"Error creating combined visualization: {e}")
    
    plt.close('all')
    
    # Create comparison visualization
    # Use weekly time points instead of daily to match the data structure
    time_points = list(range(0, 53))  # Weekly points for a year (0-52 weeks)
    
    # Get the mean vision data
    des_means = des_sim_results.get_mean_vision_over_time()
    abs_means = abs_sim_results.get_mean_vision_over_time()
    
    # Debug output to understand the data
    print("\nDES mean vision data length:", len(des_means) if des_means else 0)
    print("ABS mean vision data length:", len(abs_means) if abs_means else 0)
    
    # Create data dictionaries for the comparison plot
    des_data = {"All Patients": des_means}
    abs_data = {"All Patients": abs_means}
    
    # Plot the comparison
    plot_mean_acuity_comparison(des_data, abs_data, time_points)
    
    # Print summary statistics
    print("\nAgent-Based Simulation Summary Statistics:")
    print(abs_sim_results.get_summary_statistics())
    
    print("\nDiscrete Event Simulation Summary Statistics:")
    print(des_sim_results.get_summary_statistics())
    
    print("\nVisualization files generated:")
    print("1. individual_simulation_results.png")
    print("2. mean_acuity_comparison.png")

if __name__ == "__main__":
    main()
