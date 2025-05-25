#!/usr/bin/env python3
"""
Run a simulation with enhanced discontinuation probabilities to ensure
all 6 patient states appear clearly in the streamgraph.

This version explicitly increases the probability of administrative
and not_renewed discontinuations to make them more visible.
"""

import os
import sys
import json
import argparse
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# Add project root to path
root_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(root_dir)

# Import necessary modules
try:
    from simulation.config import SimulationConfig
    from treat_and_extend_abs_fixed import TreatAndExtendABS
    from streamgraph_fixed_phase_tracking import generate_phase_tracking_streamgraph
    from streamlit_app.data_normalizer import DataNormalizer
except ImportError as e:
    print(f"Failed to import required modules: {e}")
    sys.exit(1)

def run_simulation(population_size=500, duration_years=5):
    """
    Run a simulation with balanced discontinuation probabilities for all types.
    
    This configuration ensures we get sufficient discontinuations of 
    each type to be visible in the visualization.
    """
    print(f"Running simulation with {population_size} patients for {duration_years} years")
    
    # Create SimulationConfig
    config = SimulationConfig.from_yaml("test_simulation")
    
    # Override parameters
    config.num_patients = population_size
    config.duration_days = duration_years * 365
    
    # Configure discontinuation with balanced probabilities across all types
    # Explicitly increase administrative and not_renewed probabilities
    # to ensure they appear in sufficient numbers
    config.parameters = {
        'discontinuation': {
            'enabled': True,
            'criteria': {
                # Planned discontinuations (amber)
                'stable_max_interval': {
                    'consecutive_visits': 3,
                    'probability': 0.15
                },
                # Administrative discontinuations (red)
                'random_administrative': {
                    'annual_probability': 0.10  # Increased to ensure visibility
                },
                # Not renewed discontinuations (dark red)
                'treatment_duration': {
                    'threshold_weeks': 52,
                    'probability': 0.15  # Increased to ensure visibility
                },
                # Premature discontinuations (darkest red)
                'premature': {
                    'min_interval_weeks': 8,
                    'probability_factor': 1.0,
                    'target_rate': 0.15
                }
            }
        }
    }
    
    print("Initializing ABS simulation...")
    sim = TreatAndExtendABS(config)
    
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

def main():
    """Parse command line arguments and run simulation."""
    parser = argparse.ArgumentParser(description='Run ABS simulation with balanced discontinuation types')
    parser.add_argument('--patients', '-p', type=int, default=500,
                        help='Number of patients to simulate (default: 500)')
    parser.add_argument('--years', '-y', type=int, default=5,
                        help='Simulation duration in years (default: 5)')
    parser.add_argument('--output', '-o', type=str, default=None,
                        help='Output JSON file path (default: streamgraph_all_types_YYYYMMDD_HHMMSS.json)')
    parser.add_argument('--timeout', '-t', type=int, default=20,
                        help='Seconds to display the visualization before closing (default: 20)')
    args = parser.parse_args()
    
    # Run simulation
    results = run_simulation(
        population_size=args.patients,
        duration_years=args.years
    )
    
    # Print discontinuation stats
    print("\nDiscontinuation statistics:")
    disc_counts = results.get("discontinuation_counts", {})
    if disc_counts:
        for type_name, count in disc_counts.items():
            percent = (count / args.patients) * 100
            print(f"  {type_name}: {count} ({percent:.1f}%)")
    
    # Generate output filename if not provided
    if not args.output:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        args.output = f"streamgraph_all_types_{timestamp}.json"
    
    # Save results
    print(f"\nSaving simulation results to {args.output}")
    try:
        with open(args.output, "w") as f:
            json.dump(results, f, indent=2, default=str)
    except Exception as e:
        print(f"Error saving results: {e}")
    
    # Generate visualization
    print("\nGenerating streamgraph visualization...")
    fig = generate_phase_tracking_streamgraph(results)
    
    # Save figure
    plot_path = os.path.splitext(args.output)[0] + ".png"
    fig.savefig(plot_path, dpi=300, bbox_inches="tight")
    print(f"Streamgraph saved to {plot_path}")
    
    # Show figure with auto-close timer
    def close_figure(frame):
        plt.close()
    
    # Create timer animation
    ani = FuncAnimation(fig, close_figure, frames=[0], interval=args.timeout * 1000, repeat=False)
    
    print(f"Showing figure (will automatically close after {args.timeout} seconds)...")
    plt.show()

if __name__ == "__main__":
    main()