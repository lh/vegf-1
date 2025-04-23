"""Run comparative simulations between agent-based and discrete event models.

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
    python run_simulation.py

Note: The configuration file path can be modified in the main() function.
"""

from datetime import datetime, timedelta
from simulation.config import SimulationConfig
from simulation.abs import AgentBasedSimulation
from simulation.base import Event

def run_abs(config, verbose=False):
    """Run agent-based simulation using production implementation.
    
    Parameters
    ----------
    config : SimulationConfig
        Simulation configuration
    verbose : bool, optional
        Whether to print detailed output, by default False
        
    Returns
    -------
    dict
        Dictionary mapping patient IDs to their visit histories
    """
    # Initialize simulation
    start_date = datetime(2023, 1, 1)
    end_date = start_date + timedelta(days=config.duration_days)
    
    sim = AgentBasedSimulation(config, start_date)
    sim.clock.end_date = end_date  # Set end date before scheduling events
    
    # Add patients
    for i in range(1, config.num_patients + 1):
        patient_id = f"TEST{i:03d}"
        sim.add_patient(patient_id, "treat_and_extend")
        
        # Schedule initial visit
        sim.clock.schedule_event(Event(
            time=start_date + timedelta(minutes=30*(i-1)),
            event_type="visit",
            patient_id=patient_id,
            data={
                "visit_type": "injection_visit",
                "actions": ["vision_test", "oct_scan", "injection"],
                "decisions": ["nurse_vision_check", "doctor_treatment_decision"]
            },
            priority=1
        ))
    
    # Run simulation
    sim.run(end_date)
    
    # Collect results
    patient_histories = {}
    for patient_id, patient in sim.agents.items():
        patient_histories[patient_id] = patient.history
    
    # Debug print first patient's history structure
    if patient_histories:
        first_patient = next(iter(patient_histories.values()))
        print(f"\nFirst patient history structure (len={len(first_patient)}):")
        print(f"First visit object type: {type(first_patient[0])}")
        print(f"First visit contents: {first_patient[0]}")
    
    return patient_histories
from test_des_simulation import run_test_des_simulation as run_des
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
    Uses 'test_simulation.yaml' by default. Modify the config path as needed.
    
    Output Files
    -----------
    - individual_simulation_results.png
    - mean_acuity_comparison.png
    
    Console Output
    -------------
    - Progress messages during simulation
    - Summary statistics for both simulation types
    """
    # Load configuration
    standard_config = SimulationConfig.from_yaml("test_simulation")
    
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
    
    # Create individual visualizations
    plt.figure(figsize=(15, 5))
    
    plt.subplot(121)
    abs_sim_results.plot_mean_vision(title="Agent-Based Simulation Results")
    
    plt.subplot(122)
    des_sim_results.plot_mean_vision(title="Discrete Event Simulation Results")
    
    plt.tight_layout()
    plt.savefig('individual_simulation_results.png', dpi=300)
    plt.show()  # Display plot for debugging
    plt.close()
    
    # Create comparison visualization
    time_points = list(range((end_date - start_date).days + 1))
    des_data = {"All Patients": des_sim_results.get_mean_vision_over_time()}
    abs_data = {"All Patients": abs_sim_results.get_mean_vision_over_time()}
    
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
