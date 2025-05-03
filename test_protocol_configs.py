from datetime import datetime, timedelta
from simulation.config import SimulationConfig
from test_abs_simulation import run_test_simulation as run_abs
from test_des_simulation import run_test_des_simulation as run_des
import matplotlib.pyplot as plt
from analysis.simulation_results import SimulationResults

def test_different_protocols():
    """
    Test running simulations with different protocol configurations.
    
    This function loads a standard test configuration and runs both agent-based (ABS)
    and discrete event (DES) simulations with it. It then creates comparative
    visualizations of the mean vision outcomes and prints summary statistics.
    
    Returns
    -------
    None
        Results are visualized and printed to console
        
    Notes
    -----
    The function:
    - Loads the standard test simulation configuration
    - Runs both ABS and DES simulations with this configuration
    - Creates side-by-side plots of mean vision outcomes
    - Prints summary statistics for both simulation types
    
    This test is useful for validating that both simulation types produce
    comparable results with the same protocol configuration.
    """
    # Load different configurations
    standard_config = SimulationConfig.from_yaml("test_simulation")
    
    # Run simulations with standard config
    print("\nRunning simulations with standard configuration...")
    
    # ABS simulation
    abs_results = run_abs(
        config=standard_config,
        verbose=False
    )
    
    # DES simulation
    des_results = run_des(
        config=standard_config,
        verbose=False
    )
    
    # Create comparative visualization
    start_date = datetime(2023, 1, 1)
    end_date = start_date + timedelta(days=365)
    
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
    
    # Plot results
    plt.figure(figsize=(15, 5))
    
    plt.subplot(121)
    abs_sim_results.plot_mean_vision(title="ABS: Standard Configuration")
    
    plt.subplot(122)
    des_sim_results.plot_mean_vision(title="DES: Standard Configuration")
    
    plt.tight_layout()
    plt.show()
    
    # Print summary statistics
    print("\nABS Summary Statistics:")
    print(abs_sim_results.get_summary_statistics())
    
    print("\nDES Summary Statistics:")
    print(des_sim_results.get_summary_statistics())

if __name__ == "__main__":
    test_different_protocols()
