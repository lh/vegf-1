"""
Display DES simulation results with the adapter.

This script demonstrates using the adapter with a small simulated dataset
to avoid long execution times.
"""

import os
import sys
import matplotlib.pyplot as plt
import numpy as np

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from simulation.des_streamlit_adapter import adapt_des_for_streamlit

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

def run_quick_des_simulation():
    """Run a minimal DES simulation for testing."""
    print("Running a minimal DES simulation for testing...")
    
    # Import simulation components here to avoid circular imports
    import os
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    from simulation.config import SimulationConfig
    from treat_and_extend_des import run_treat_and_extend_des
    
    # Create a minimal configuration
    config = SimulationConfig.from_yaml("eylea_literature_based")
    config.duration_days = 90  # Very short duration (3 months)
    config.num_patients = 10   # Very small number of patients
    
    # Enable discontinuation with higher probabilities for testing
    config.parameters["discontinuation"] = {
        "enabled": True,
        "criteria": {
            "stable_max_interval": {
                "consecutive_visits": 2,  # Reduced requirement for testing
                "probability": 0.8,       # Higher probability for testing
                "interval_weeks": 12      # Shorter interval for testing
            },
            "random_administrative": {
                "annual_probability": 0.2  # Higher probability for testing
            }
        }
    }
    
    # Run with real simulation data
    results = run_treat_and_extend_des(
        config=config,
        verbose=False,
        streamlit_compatible=True
    )
    
    return results

def main():
    """Demonstrate DES adapter functionality."""
    print("Running simulation to generate real data...")
    results = run_quick_des_simulation()
    
    # Results are already adapted for Streamlit compatibility
    adapted_results = results
    
    # Print summary statistics
    print("\nAdapted Results:")
    print(f"Population Size: {adapted_results['population_size']}")
    print(f"Duration (years): {adapted_results['duration_years']}")
    
    # Print discontinuation counts
    print("\nDiscontinuation Counts:")
    disc_counts = adapted_results.get("discontinuation_counts", {})
    for reason, count in disc_counts.items():
        print(f"  {reason}: {count}")
    
    # Print recurrence information
    print("\nRecurrence Information:")
    recurrences = adapted_results.get("recurrences", {})
    print(f"  Total: {recurrences.get('total', 0)}")
    
    # Print patient history information
    print("\nPatient Histories:")
    patient_histories = adapted_results.get("patient_histories", {})
    for patient_id, patient_data in patient_histories.items():
        visits = patient_data.get("visits", [])
        print(f"  {patient_id}: {len(visits)} visits")
        
        # Count discontinuations and retreatments
        disc_count = sum(1 for v in visits if v.get("is_discontinuation_visit", False))
        retreat_count = sum(1 for v in visits if v.get("is_retreatment", False))
        
        print(f"    Discontinuations: {disc_count}")
        print(f"    Retreatments: {retreat_count}")
    
    # Create visualization
    print("\nGenerating discontinuation chart...")
    fig = create_discontinuation_chart(adapted_results)
    
    # Save the figure
    output_file = "des_adapted_results_chart.png"
    fig.savefig(output_file, dpi=150, bbox_inches="tight")
    print(f"Chart saved to {output_file}")
    
    # Display the figure
    plt.show()

if __name__ == "__main__":
    main()