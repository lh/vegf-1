#!/usr/bin/env python3
"""
Run a real ABS simulation and generate a streamgraph visualization.

This script uses the same simulation approach as the Streamlit app 
but runs it from the command line and saves results.
"""

import os
import sys
import json
import argparse
import time
from datetime import datetime
from pathlib import Path

# Add the project root directory to sys.path
root_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(root_dir)

# Import necessary modules
try:
    from simulation.config import SimulationConfig
    from treat_and_extend_abs_fixed import TreatAndExtendABS
    from streamlit_app.streamgraph_fixed import generate_fixed_streamgraph
    import matplotlib.pyplot as plt
    from streamlit_app.data_normalizer import DataNormalizer
except ImportError as e:
    print(f"Failed to import required modules: {e}")
    sys.exit(1)

def run_simulation(population_size=100, duration_years=5):
    """
    Run a simulation using ABS.
    
    Parameters
    ----------
    population_size : int
        Number of patients to simulate
    duration_years : int
        Duration of simulation in years
        
    Returns
    -------
    dict
        Simulation results
    """
    print(f"Running ABS simulation with {population_size} patients for {duration_years} years")
    start_time = time.time()
    
    try:
        # Create a SimulationConfig from an existing YAML file
        config = SimulationConfig.from_yaml("test_simulation")
        
        # Override specific parameters
        config.num_patients = population_size
        config.duration_days = duration_years * 365
        
        # Ensure discontinuation is enabled
        if not hasattr(config, 'parameters'):
            config.parameters = {}
        
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
                    },
                    'premature': {
                        'min_interval_weeks': 8,
                        'probability_factor': 1.0,
                        'target_rate': 0.145
                    }
                }
            }
        else:
            # Make sure 'enabled' is True
            config.parameters['discontinuation']['enabled'] = True
        
        # Create simulation instance
        print("Initializing ABS simulation...")
        sim = TreatAndExtendABS(config)
        
        # Run simulation
        print("Running simulation...")
        patient_histories = sim.run()
        
        # Calculate runtime
        end_time = time.time()
        runtime = end_time - start_time
        print(f"Simulation completed in {runtime:.2f} seconds")
        
        # Process results
        results = process_simulation_results(sim, patient_histories, {
            'simulation_type': 'ABS',
            'population_size': population_size,
            'duration_years': duration_years,
            'enable_clinician_variation': True,
            'planned_discontinue_prob': 0.2,
            'admin_discontinue_prob': 0.05
        })
        
        results["runtime_seconds"] = runtime
        
        # Add simulation stats
        if hasattr(sim, 'stats'):
            results["simulation_stats"] = sim.stats
            
            # Ensure retreatments are properly captured
            if "retreatments" in sim.stats and sim.stats["retreatments"] > 0:
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
        
        # Store patient histories in results
        results["patient_histories"] = patient_histories
        
        return results
    
    except Exception as e:
        import traceback
        print(f"Error running simulation: {e}")
        print(traceback.format_exc())
        return {
            "error": str(e),
            "simulation_type": "ABS",
            "population_size": population_size,
            "duration_years": duration_years,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "failed": True
        }


def process_simulation_results(sim, patient_histories, params):
    """
    Process simulation results.
    
    Parameters
    ----------
    sim : TreatAndExtendABS
        The simulation object
    patient_histories : dict
        Dictionary of patient histories
    params : dict
        Simulation parameters
        
    Returns
    -------
    dict
        Processed results
    """
    # Normalize data
    patient_histories = DataNormalizer.normalize_patient_histories(patient_histories)
    
    # Create results dictionary
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
    
    # Check for discontinuation manager data
    discontinuation_manager = None
    if hasattr(sim, 'get_discontinuation_manager'):
        discontinuation_manager = sim.get_discontinuation_manager()
    elif hasattr(sim, 'discontinuation_manager'):
        discontinuation_manager = sim.discontinuation_manager
    elif hasattr(sim, 'refactored_manager'):
        discontinuation_manager = sim.refactored_manager
    else:
        print("Warning: Could not access discontinuation manager - stats will be limited")
    
    # Initialize default counts
    discontinuation_counts = {
        "Planned": 0,
        "Administrative": 0,
        "Not Renewed": 0,
        "Premature": 0
    }
    
    # Process statistics if we have a discontinuation manager
    if discontinuation_manager:
        if hasattr(discontinuation_manager, 'stats'):
            stats = discontinuation_manager.stats
            
            # Extract counts
            discontinuation_counts["Planned"] = stats.get("stable_max_interval_discontinuations", 0)
            discontinuation_counts["Administrative"] = stats.get("random_administrative_discontinuations", 0)
            
            # Handle both old and new key names for Not Renewed
            course_complete_count = stats.get("course_complete_but_not_renewed_discontinuations", 0)
            treatment_duration_count = stats.get("treatment_duration_discontinuations", 0)
            discontinuation_counts["Not Renewed"] = course_complete_count if course_complete_count > 0 else treatment_duration_count
            
            discontinuation_counts["Premature"] = stats.get("premature_discontinuations", 0)
            
            # Store discontinuation counts in results
            results["discontinuation_counts"] = discontinuation_counts
    
    # Create alias for patient data
    if "patient_histories" in results and "patient_data" not in results:
        results["patient_data"] = results["patient_histories"]
    
    return results


def main():
    """Parse command line arguments and run simulation."""
    parser = argparse.ArgumentParser(description='Run ABS simulation for streamgraph visualization')
    parser.add_argument('--patients', '-p', type=int, default=100,
                        help='Number of patients to simulate (default: 100)')
    parser.add_argument('--years', '-y', type=int, default=5,
                        help='Simulation duration in years (default: 5)')
    parser.add_argument('--output', '-o', type=str, default=None,
                        help='Output JSON file path (default: streamgraph_data_YYYYMMDD_HHMMSS.json)')
    parser.add_argument('--plot', '-g', action='store_true',
                        help='Generate streamgraph visualization')
    args = parser.parse_args()
    
    # Run simulation
    results = run_simulation(
        population_size=args.patients,
        duration_years=args.years
    )
    
    # Generate output filename if not provided
    if not args.output:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        args.output = f"streamgraph_data_{timestamp}.json"
    
    # Create output directory if it doesn't exist
    output_dir = os.path.dirname(args.output)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    # Save results to file if successful
    if not results.get("failed", False):
        # Filter patient_histories for serialization (avoid serializing complex objects)
        serializable_results = results.copy()
        
        try:
            with open(args.output, "w") as f:
                json.dump(serializable_results, f, indent=2, default=str)
            print(f"Simulation results saved to {args.output}")
        except Exception as e:
            print(f"Error saving simulation results: {e}")
    else:
        print("Simulation failed - no results to save")
        sys.exit(1)
    
    # Generate streamgraph if requested
    if args.plot and not results.get("failed", False):
        try:
            print("Generating streamgraph visualization...")
            fig = generate_fixed_streamgraph(results)
            
            # Save figure
            plot_path = os.path.splitext(args.output)[0] + "_streamgraph.png"
            fig.savefig(plot_path, dpi=300, bbox_inches="tight")
            print(f"Streamgraph saved to {plot_path}")
            
            # Show figure if running interactively
            plt.show()
        except Exception as e:
            print(f"Error generating streamgraph: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    main()