#!/usr/bin/env python3
"""
Run a full test of the streamgraph visualization with explicit discontinuation types.
This script runs a simulation and creates a visualization in headless mode.
"""

import os
import sys
import json
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
from datetime import datetime

# Add the project root directory to sys.path
root_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(root_dir)

# Import necessary modules
try:
    from simulation.config import SimulationConfig
    from treat_and_extend_abs import TreatAndExtendABS
    from streamlit_app.streamgraph_patient_states import create_streamgraph
except ImportError as e:
    print(f"Failed to import required modules: {e}")
    sys.exit(1)

def run_simulation(population_size=100, duration_years=5):
    """
    Run a simulation with enhanced discontinuation tracking.
    """
    print(f"Running ABS simulation with {population_size} patients for {duration_years} years")
    
    try:
        # Create config from YAML name
        config = SimulationConfig.from_yaml("test_simulation")
        print("Loaded config from yaml name")
        
        # Override specific parameters
        config.num_patients = population_size
        config.duration_days = duration_years * 365
        
        # Ensure discontinuation is enabled with all types
        if not hasattr(config, 'parameters'):
            config.parameters = {}
        
        config.parameters['discontinuation'] = {
            'enabled': True,
            'criteria': {
                'stable_max_interval': {
                    'consecutive_visits': 3,
                    'probability': 0.2
                },
                'random_administrative': {
                    'annual_probability': 0.1  # Increased for better representation
                },
                'treatment_duration': {
                    'threshold_weeks': 52,
                    'probability': 0.2  # Increased for better representation
                },
                'premature': {
                    'min_interval_weeks': 8,
                    'probability_factor': 1.0,
                    'target_rate': 0.2  # Increased for better representation
                }
            }
        }
        
        # Create simulation instance
        print("Initializing ABS simulation...")
        sim = TreatAndExtendABS(config)
        
        # Run simulation
        print("Running simulation...")
        patient_histories = sim.run()
        
        # Process results
        results = {
            "simulation_type": "ABS",
            "population_size": population_size,
            "duration_years": duration_years,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "patient_count": len(patient_histories)
        }
        
        # Add simulation stats
        if hasattr(sim, 'stats'):
            results["simulation_stats"] = sim.stats
            
            # Extract discontinuation counts
            discontinuation_counts = {
                "stable_max_interval": sim.stats.get("stable_max_interval_discontinuations", 0),
                "random_administrative": sim.stats.get("random_administrative_discontinuations", 0),
                "treatment_duration": sim.stats.get("treatment_duration_discontinuations", 0),
                "premature": sim.stats.get("premature_discontinuations", 0)
            }
            results["discontinuation_counts"] = discontinuation_counts
            
            # Print discontinuation stats
            total_disc = sum(discontinuation_counts.values())
            print(f"Discontinuation stats (total: {total_disc}):")
            for reason, count in discontinuation_counts.items():
                print(f"  {reason}: {count}")
        
        # Store patient histories in results
        results["patient_histories"] = patient_histories
        
        return results
    
    except Exception as e:
        import traceback
        print(f"Error running simulation: {e}")
        print(traceback.format_exc())
        return {"failed": True}

def check_discontinuation_types(results):
    """Check which discontinuation types exist in the simulation results."""
    if not results or results.get("failed", False):
        return
    
    # Analyze a sample of patients
    patient_histories = results.get("patient_histories", {})
    sample_size = min(20, len(patient_histories))
    sample_patients = list(patient_histories.items())[:sample_size]
    
    type_counts = {
        "stable_max_interval": 0,
        "random_administrative": 0,
        "treatment_duration": 0,
        "premature": 0,
        "unknown": 0
    }
    
    for pid, visits in sample_patients:
        for visit in visits:
            if visit.get("is_discontinuation_visit", False):
                disc_type = visit.get("discontinuation_type", "")
                if disc_type in type_counts:
                    type_counts[disc_type] += 1
                else:
                    type_counts["unknown"] += 1
                    print(f"Unknown discontinuation type: {disc_type}")
    
    print("\nDiscontinuation types in sample:")
    for type_name, count in type_counts.items():
        if count > 0:
            print(f"  {type_name}: {count}")

def main():
    """Run the full test."""
    # Run simulation
    population_size = 200  # Larger population for better representation
    duration_years = 5
    
    results = run_simulation(population_size, duration_years)
    
    if results.get("failed", False):
        print("Simulation failed - cannot create visualization")
        sys.exit(1)
    
    # Check discontinuation types
    check_discontinuation_types(results)
    
    # Save raw results for inspection
    output_file = "full_streamgraph_test_data.json"
    try:
        with open(output_file, "w") as f:
            json.dump(results, f, default=str)
        print(f"Raw simulation data saved to {output_file}")
    except Exception as e:
        print(f"Warning: Could not save raw data - {e}")
    
    # Create the streamgraph visualization
    try:
        print("\nCreating enhanced streamgraph visualization...")
        fig = create_streamgraph(results)
        
        # Save the figure
        plot_file = "full_streamgraph_test.png"
        fig.savefig(plot_file, dpi=300, bbox_inches="tight")
        print(f"Streamgraph saved to {plot_file}")
        
        # Close the figure
        plt.close(fig)
        print("Success! Full test complete.")
    except Exception as e:
        import traceback
        print(f"Error creating visualization: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()