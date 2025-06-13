#!/usr/bin/env python3
"""
Debug script for streamgraph visualization.
Runs a simulation and saves the results to a JSON file.
"""

import os
import sys
import json
import time
import argparse
from pathlib import Path
import matplotlib.pyplot as plt

# Add project root to path
root_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(root_dir)

# Import simulation modules
try:
    from simulation.config import SimulationConfig
    from streamlit_app.simulation_runner import run_simulation
    from streamlit_app.streamgraph_patient_states import create_streamgraph
    from streamlit_app.streamgraph_patient_states_fixed import create_streamgraph as create_streamgraph_fixed
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Make sure you're running this script from the project root directory.")
    sys.exit(1)

def save_streamgraph_to_png(simulation_results, output_file):
    """
    Generate streamgraph and save to PNG file.
    
    Args:
        simulation_results: Dictionary containing simulation results
        output_file: Path to output PNG file
    """
    try:
        print(f"Generating streamgraph using original implementation...")
        fig = create_streamgraph(simulation_results)
        # Save figure
        fig.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"Streamgraph saved to {output_file}")
        plt.close(fig)
        
        return True
    except Exception as e:
        print(f"Error generating streamgraph: {e}")
        import traceback
        traceback.print_exc()
        return False

def save_streamgraph_fixed_to_png(simulation_results, output_file):
    """
    Generate streamgraph using fixed implementation and save to PNG file.
    
    Args:
        simulation_results: Dictionary containing simulation results
        output_file: Path to output PNG file
    """
    try:
        print(f"Generating streamgraph using fixed implementation...")
        fig = create_streamgraph_fixed(simulation_results)
        # Save figure
        fig.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"Fixed streamgraph saved to {output_file}")
        plt.close(fig)
        
        return True
    except Exception as e:
        print(f"Error generating fixed streamgraph: {e}")
        import traceback
        traceback.print_exc()
        return False

def debug_patient_states(simulation_results, output_file):
    """
    Analyze patient states in the simulation results and save debug info to file.
    
    Args:
        simulation_results: Dictionary containing simulation results
        output_file: Path to output text file
    """
    try:
        with open(output_file, 'w') as f:
            f.write("PATIENT STATE ANALYSIS\n")
            f.write("====================\n\n")
            
            # Get patient histories
            patient_histories = simulation_results.get("patient_histories", {})
            f.write(f"Total patients: {len(patient_histories)}\n\n")
            
            # Count patients with different states
            state_counts = {}
            discontinuation_types = {}
            retreatment_counts = {}
            
            for patient_id, visits in patient_histories.items():
                if isinstance(visits, dict) and "visits" in visits:
                    # New format with metadata
                    patient_data = visits
                    visits = patient_data["visits"]
                    
                    # Check if any metadata about states
                    if "current_state" in patient_data:
                        current_state = patient_data["current_state"]
                        state_counts[current_state] = state_counts.get(current_state, 0) + 1
                
                # Now process visits
                has_discontinuation = False
                discontinuation_type = None
                has_retreatment = False
                
                for visit in visits:
                    if visit.get("is_discontinuation_visit", False):
                        has_discontinuation = True
                        disc_type = visit.get("discontinuation_reason", visit.get("discontinuation_type", "unknown"))
                        discontinuation_type = disc_type
                        discontinuation_types[disc_type] = discontinuation_types.get(disc_type, 0) + 1
                    
                    if visit.get("is_retreatment_visit", False) or visit.get("is_retreatment", False):
                        has_retreatment = True
                
                # Count retreatments by discontinuation type
                if has_retreatment and discontinuation_type:
                    key = f"retreated_from_{discontinuation_type}"
                    retreatment_counts[key] = retreatment_counts.get(key, 0) + 1
            
            # Write state counts
            f.write("Patient state counts:\n")
            for state, count in state_counts.items():
                f.write(f"  {state}: {count}\n")
            f.write("\n")
            
            # Write discontinuation types
            f.write("Discontinuation types:\n")
            for disc_type, count in discontinuation_types.items():
                f.write(f"  {disc_type}: {count}\n")
            f.write("\n")
            
            # Write retreatment counts
            f.write("Retreatment counts by discontinuation type:\n")
            for state, count in retreatment_counts.items():
                f.write(f"  {state}: {count}\n")
            f.write("\n")
            
            # Sample patient data
            f.write("Sample patient data:\n")
            sample_patients = list(patient_histories.keys())[:5]
            for patient_id in sample_patients:
                f.write(f"\nPatient {patient_id}:\n")
                visits = patient_histories[patient_id]
                
                # Check if new format
                if isinstance(visits, dict) and "visits" in visits:
                    patient_data = visits
                    visits = patient_data["visits"]
                    
                    # Write metadata
                    f.write("  Metadata:\n")
                    for key, value in patient_data.items():
                        if key != "visits":
                            f.write(f"    {key}: {value}\n")
                
                # Write visits
                f.write("  Visits:\n")
                for i, visit in enumerate(visits[:10]):  # Show first 10 visits
                    f.write(f"    Visit {i+1}:\n")
                    for key, value in visit.items():
                        f.write(f"      {key}: {value}\n")
            
            print(f"Patient state analysis saved to {output_file}")
            return True
    except Exception as e:
        print(f"Error analyzing patient states: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    parser = argparse.ArgumentParser(description="Run simulation and save results for streamgraph debugging")
    parser.add_argument("--population", type=int, default=100, help="Population size (default: 100)")
    parser.add_argument("--years", type=int, default=5, help="Simulation duration in years (default: 5)")
    parser.add_argument("--output-dir", type=str, default="debug_output", help="Output directory (default: debug_output)")
    
    args = parser.parse_args()
    
    # Create output directory if it doesn't exist
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Set up simulation parameters
    params = {
        "simulation_type": "ABS",  # ABS or DES
        "population_size": args.population,
        "duration_years": args.years,
        "enable_clinician_variation": True,
        "planned_discontinue_prob": 0.2,
        "admin_discontinue_prob": 0.05,
        "premature_discontinue_prob": 2.0,
        "consecutive_stable_visits": 3,
        "monitoring_schedule": [12, 24, 36],
        "no_monitoring_for_admin": True,
        "recurrence_risk_multiplier": 1.0,
        "enable_retreatment": True,
        "retreatment_probability": {
            "stable_max_interval": 0.3,
            "random_administrative": 0.5,
            "course_complete": 0.2,
            "premature": 0.7
        }
    }
    
    # Run simulation
    print(f"Running simulation with {args.population} patients over {args.years} years...")
    start_time = time.time()
    simulation_results = run_simulation(params)
    end_time = time.time()
    
    print(f"Simulation completed in {end_time - start_time:.2f} seconds")
    
    # Check if simulation succeeded
    if "error" in simulation_results or simulation_results.get("failed", False):
        print(f"Simulation failed: {simulation_results.get('error', 'Unknown error')}")
        return
    
    # Save simulation results to JSON file
    output_file = output_dir / f"simulation_{args.population}_{args.years}y.json"
    try:
        with open(output_file, "w") as f:
            json.dump(simulation_results, f)
        print(f"Simulation results saved to {output_file}")
    except Exception as e:
        print(f"Error saving simulation results: {e}")
    
    # Generate streamgraph and save to PNG
    png_file = output_dir / f"streamgraph_{args.population}_{args.years}y.png"
    save_streamgraph_to_png(simulation_results, png_file)
    
    # Generate streamgraph using fixed implementation and save to PNG
    fixed_png_file = output_dir / f"streamgraph_fixed_{args.population}_{args.years}y.png"
    save_streamgraph_fixed_to_png(simulation_results, fixed_png_file)
    
    # Debug patient states
    debug_file = output_dir / f"patient_states_{args.population}_{args.years}y.txt"
    debug_patient_states(simulation_results, debug_file)

if __name__ == "__main__":
    main()