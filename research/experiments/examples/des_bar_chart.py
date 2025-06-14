"""
Create a simple bar chart visualization of DES discontinuation results.

This script runs the DES simulation with enhanced discontinuation and creates
a simple bar chart showing the discontinuation counts.
"""

import os
import sys
import matplotlib.pyplot as plt
import numpy as np

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from simulation.config import SimulationConfig
from treat_and_extend_des import run_treat_and_extend_des

def create_discontinuation_chart(results):
    """
    Create a bar chart showing discontinuation counts.
    
    Parameters
    ----------
    results : dict
        Adapted DES results
    
    Returns
    -------
    matplotlib.figure.Figure
        The generated figure
    """
    # Extract discontinuation counts
    disc_counts = results.get("discontinuation_counts", {})
    
    # Define colors
    colors = {
        "Planned": "#FFA500",  # Amber
        "Administrative": "#DC143C",  # Red
        "Not Renewed": "#B22222",  # Dark red
        "Premature": "#8B0000"  # Darker red
    }
    
    # Create the plot
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Plot as horizontal bars
    types = list(disc_counts.keys())
    counts = [disc_counts[t] for t in types]
    y_pos = np.arange(len(types))
    
    bars = ax.barh(y_pos, counts, align='center', alpha=0.8)
    
    # Color the bars
    for i, bar in enumerate(bars):
        bar.set_color(colors.get(types[i], "#808080"))
    
    # Add labels
    ax.set_yticks(y_pos)
    ax.set_yticklabels(types)
    ax.invert_yaxis()  # Labels read top-to-bottom
    ax.set_xlabel('Number of Patients')
    ax.set_title('Discontinuations by Type in Enhanced DES Model')
    
    # Add count labels on the bars
    for i, v in enumerate(counts):
        if v > 0:
            ax.text(v + 0.5, i, str(v), va='center')
    
    # Add total as text annotation
    total_disc = sum(counts)
    ax.text(0.9, 0.05, f"Total: {total_disc}", transform=ax.transAxes, 
            bbox=dict(facecolor='white', alpha=0.5))
    
    # Clean styling
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    plt.tight_layout()
    return fig

def run_enhanced_des_simulation():
    """Run DES simulation with enhanced discontinuation."""
    print("Running enhanced DES simulation...")
    
    # Create a test config
    config = SimulationConfig.from_yaml("eylea_literature_based")
    config.duration_days = 365  # 1 year
    config.num_patients = 200   # Small number of patients
    
    # Enable various discontinuation types for testing
    config.parameters["discontinuation"] = {
        "enabled": True,
        "criteria": {
            "stable_max_interval": {
                "consecutive_visits": 3,
                "probability": 0.5,  # Higher probability for testing
                "interval_weeks": 16
            },
            "random_administrative": {
                "annual_probability": 0.1
            },
            "treatment_duration": {
                "threshold_weeks": 26,
                "probability": 0.1
            },
            "premature": {
                "min_interval_weeks": 8,
                "probability_factor": 1.0
            }
        }
    }
    
    # Run the simulation with Streamlit-compatible output
    results = run_treat_and_extend_des(
        config=config,
        verbose=False,
        streamlit_compatible=True
    )
    
    return results

def main():
    """Run DES simulation and create visualization."""
    # Run the simulation
    results = run_enhanced_des_simulation()
    
    # Print summary statistics
    print("\nSimulation Results:")
    print(f"Population Size: {results['population_size']}")
    print(f"Duration (years): {results['duration_years']}")
    
    # Print discontinuation counts
    print("\nDiscontinuation Counts:")
    disc_counts = results.get("discontinuation_counts", {})
    for reason, count in disc_counts.items():
        print(f"  {reason}: {count}")
    
    # Create visualization
    print("\nGenerating discontinuation chart...")
    fig = create_discontinuation_chart(results)
    
    # Save the figure
    output_file = "des_discontinuation_chart.png"
    fig.savefig(output_file, dpi=150, bbox_inches="tight")
    print(f"Chart saved to {output_file}")
    
    # Display the figure
    plt.show()

if __name__ == "__main__":
    main()