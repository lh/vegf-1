#!/usr/bin/env python3
"""
Run a large-scale simulation (5000 patients for 10 years) and generate
a streamgraph visualization with all 6 patient states.

This script uses the same parameters as the original streamlit app
to ensure consistency with the production environment.
"""

import os
import sys
import json
import time
import argparse
from datetime import datetime
import matplotlib.pyplot as plt

# Add the project root directory to sys.path
root_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(root_dir)

# Import necessary modules
try:
    from simulation.config import SimulationConfig
    from treat_and_extend_abs_fixed import TreatAndExtendABS
    from streamgraph_fixed_phase_tracking import generate_phase_tracking_streamgraph
    import matplotlib.pyplot as plt
    from streamlit_app.data_normalizer import DataNormalizer
except ImportError as e:
    print(f"Failed to import required modules: {e}")
    sys.exit(1)

def run_large_simulation(population_size=5000, duration_years=10):
    """
    Run a simulation with a large population over a long duration.
    
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
    print(f"Running large-scale simulation with {population_size} patients for {duration_years} years")
    print(f"This may take several minutes to complete...")
    start_time = time.time()
    
    try:
        # Create a SimulationConfig from an existing YAML file - using the eylea_literature_based
        # as it matches the streamlit app parameters
        config = SimulationConfig.from_yaml("eylea_literature_based")
        
        # Override population and duration
        config.num_patients = population_size
        config.duration_days = duration_years * 365
        
        # Make sure discontinuation is enabled with original parameters
        # These are the parameters used in the streamlit app
        if hasattr(config, 'parameters') and 'discontinuation' in config.parameters:
            # Make sure enabled is True but preserve original settings
            config.parameters['discontinuation']['enabled'] = True
            print("Using original discontinuation parameters from config")
        else:
            # If for some reason the config doesn't have discontinuation params,
            # add standard ones based on literature
            config.parameters['discontinuation'] = {
                'enabled': True,
                'criteria': {
                    'stable_max_interval': {
                        'consecutive_visits': 3,
                        'probability': 0.7  # High probability for planned discontinuations
                    },
                    'random_administrative': {
                        'annual_probability': 0.05  # Standard probability for administrative
                    },
                    'treatment_duration': {
                        'threshold_weeks': 52,
                        'probability': 0.15  # Moderate for not renewed
                    },
                    'premature': {
                        'min_interval_weeks': 8,
                        'probability_factor': 1.0,
                        'target_rate': 0.15  # Standard for premature
                    }
                }
            }
        
        # Initialize simulation
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
        results = {
            "simulation_type": "ABS",
            "population_size": population_size,
            "duration_years": duration_years,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "patient_count": len(patient_histories),
            "runtime_seconds": runtime
        }
        
        # Extract discontinuation stats
        if hasattr(sim, 'discontinuation_manager'):
            dm = sim.discontinuation_manager
            if hasattr(dm, 'stats'):
                stats = dm.stats
                results["raw_discontinuation_stats"] = stats
                
                # Extract counts by type
                results["discontinuation_counts"] = {
                    "Planned": stats.get("stable_max_interval_discontinuations", 0),
                    "Administrative": stats.get("random_administrative_discontinuations", 0),
                    "Not Renewed": (
                        stats.get("course_complete_but_not_renewed_discontinuations", 0) + 
                        stats.get("treatment_duration_discontinuations", 0)
                    ),
                    "Premature": stats.get("premature_discontinuations", 0)
                }
        
        # Extract retreatment stats
        if hasattr(sim, 'stats'):
            stats = sim.stats
            
            # Store retreatment stats
            if "retreatments" in stats:
                if "raw_discontinuation_stats" not in results:
                    results["raw_discontinuation_stats"] = {}
                    
                results["raw_discontinuation_stats"]["retreatments"] = stats["retreatments"]
                if "unique_retreatments" in stats:
                    results["raw_discontinuation_stats"]["unique_patient_retreatments"] = stats["unique_retreatments"]
                
                # Add recurrences structure
                results["recurrences"] = {
                    "total": stats["retreatments"],
                    "by_type": {},
                    "unique_count": stats.get("unique_retreatments", 0)
                }
        
        # Normalize data
        normalized_histories = DataNormalizer.normalize_patient_histories(patient_histories)
        results["patient_histories"] = normalized_histories
        
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

def main():
    """Parse command line arguments and run simulation."""
    parser = argparse.ArgumentParser(description='Run a large-scale simulation and generate streamgraph')
    parser.add_argument('--patients', '-p', type=int, default=5000,
                        help='Number of patients to simulate (default: 5000)')
    parser.add_argument('--years', '-y', type=int, default=10,
                        help='Simulation duration in years (default: 10)')
    parser.add_argument('--timeout', '-t', type=int, default=10,
                        help='Visualization display timeout in seconds (default: 10)')
    args = parser.parse_args()
    
    # Run simulation
    results = run_large_simulation(
        population_size=args.patients,
        duration_years=args.years
    )
    
    # Save results to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"large_streamgraph_data_{timestamp}.json"
    
    try:
        print(f"\nSaving simulation results to {output_file}")
        with open(output_file, "w") as f:
            json.dump(results, f, indent=2, default=str)
    except Exception as e:
        print(f"Error saving results: {e}")
    
    # Print statistics
    print("\n=== Simulation Statistics ===")
    print(f"Population size: {results.get('population_size', 'unknown')}")
    print(f"Duration: {results.get('duration_years', 'unknown')} years")
    print(f"Patient count: {results.get('patient_count', 'unknown')}")
    print(f"Runtime: {results.get('runtime_seconds', 'unknown'):.2f} seconds")
    
    # Discontinuation counts
    disc_counts = results.get("discontinuation_counts", {})
    if disc_counts:
        total_patients = results.get("patient_count", 1)  # Avoid division by zero
        print("\nDiscontinuation counts:")
        for type_name, count in disc_counts.items():
            percent = (count / total_patients) * 100
            print(f"  {type_name}: {count} ({percent:.1f}%)")
    
    # Retreatment stats
    retreat_stats = results.get("raw_discontinuation_stats", {})
    if "retreatments" in retreat_stats:
        print("\nRetreatment statistics:")
        print(f"  Total retreatments: {retreat_stats['retreatments']}")
        if "unique_patient_retreatments" in retreat_stats:
            print(f"  Unique patients retreated: {retreat_stats['unique_patient_retreatments']}")
    
    # Generate visualization
    if not results.get("failed", False):
        print("\nGenerating streamgraph visualization...")
        fig = generate_phase_tracking_streamgraph(results)
        
        # Save figure
        plot_path = f"large_streamgraph_{timestamp}.png"
        fig.savefig(plot_path, dpi=300, bbox_inches="tight")
        print(f"Streamgraph saved to {plot_path}")
        
        # Show figure with timer
        print(f"Showing figure (will close after {args.timeout} seconds)...")
        
        # Use a safer timer approach
        timer = fig.canvas.new_timer(interval=args.timeout * 1000)
        timer.add_callback(plt.close)
        timer.start()
        
        plt.show()

if __name__ == "__main__":
    main()