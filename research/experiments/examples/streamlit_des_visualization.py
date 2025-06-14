"""
Demonstrate using the DES adapter with Streamlit visualizations directly.

This script shows how to run a DES simulation and generate a 
visualization using the Streamlit visualization components without 
actually running the Streamlit app.
"""

import os
import sys
import matplotlib.pyplot as plt

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from simulation.config import SimulationConfig
from treat_and_extend_des import run_treat_and_extend_des
from streamlit_app.streamgraph_actual_data import generate_actual_data_streamgraph

def main():
    """
    Run a DES simulation and generate a Streamlit visualization directly.
    """
    print("Running DES simulation...")
    
    # Create a test config with shorter duration and fewer patients
    config = SimulationConfig.from_yaml("eylea_literature_based")
    config.duration_days = 365  # 1 year
    config.num_patients = 200   # Small number of patients
    
    # Enable enhanced discontinuation with higher probabilities
    config.parameters["discontinuation"] = {
        "enabled": True,
        "criteria": {
            "stable_max_interval": {
                "consecutive_visits": 3,
                "probability": 0.6,  # Higher probability for testing
                "interval_weeks": 16
            },
            "random_administrative": {
                "annual_probability": 0.1  # Include some administrative discontinuations
            },
            "treatment_duration": {
                "threshold_weeks": 26,
                "probability": 0.1  # Include some time-based discontinuations
            },
            "premature": {
                "min_interval_weeks": 8,
                "probability_factor": 1.0  # Include some premature discontinuations
            }
        },
        "monitoring": {
            "cessation_types": {
                "stable_max_interval": "planned",
                "random_administrative": "none",
                "treatment_duration": "unplanned",
                "premature": "unplanned"
            },
            "planned": {
                "follow_up_schedule": [12, 24, 36]
            },
            "unplanned": {
                "follow_up_schedule": [8, 16, 24]
            }
        }
    }
    
    # Run the simulation with Streamlit-compatible output
    results = run_treat_and_extend_des(
        config=config,
        verbose=False,
        streamlit_compatible=True
    )
    
    # Print summary of results
    print("\nSimulation Results:")
    print(f"Population Size: {results['population_size']}")
    print(f"Duration (years): {results['duration_years']}")
    
    # Print discontinuation counts
    print("\nDiscontinuation Counts:")
    disc_counts = results.get("discontinuation_counts", {})
    for reason, count in disc_counts.items():
        print(f"  {reason}: {count}")
    
    # Generate visualization using Streamlit component
    print("\nGenerating Streamlit visualization...")
    fig = generate_actual_data_streamgraph(results)
    
    # Save the visualization
    output_file = "streamlit_des_visualization.png"
    fig.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"Streamlit visualization saved to {output_file}")
    
    # Show the plot
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    main()