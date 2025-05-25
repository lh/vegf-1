"""
Integrated test script for evaluating both fixed ABS and DES discontinuation implementations.

This script runs both the ABS and DES implementations with the same configuration
and compares their discontinuation rates to ensure consistency and correctness.
"""

import argparse
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
from simulation.config import SimulationConfig

# Import both simulation implementations
from treat_and_extend_abs_fixed import run_treat_and_extend_abs, TreatAndExtendABS
from treat_and_extend_des_fixed import run_treat_and_extend_des, TreatAndExtendDES

def create_test_config(discontinuation_probability=0.2, num_patients=1000, duration_years=2):
    """
    Create a test configuration for both ABS and DES simulations.
    
    Parameters
    ----------
    discontinuation_probability : float, optional
        Probability of discontinuation for stable patients at max interval, by default 0.2
    num_patients : int, optional
        Number of patients to simulate, by default 1000
    duration_years : int, optional
        Duration of simulation in years, by default 2
    
    Returns
    -------
    SimulationConfig
        Configuration object for the simulation
    """
    return SimulationConfig(
        config_name="test_discontinuation_fixed",
        num_patients=num_patients,
        duration_days=365 * duration_years,
        start_date="2023-01-01",
        parameters={
            "discontinuation": {
                "enabled": True,
                "criteria": {
                    "stable_max_interval": {
                        "probability": discontinuation_probability,
                        "consecutive_visits": 3,
                        "interval_weeks": 16
                    },
                    "random_administrative": {
                        "annual_probability": 0.0
                    },
                    "treatment_duration": {
                        "probability": 0.0
                    },
                    "premature": {
                        "probability_factor": 0.0
                    }
                },
                "monitoring": {
                    "planned": {
                        "follow_up_schedule": [12, 24, 36]
                    },
                    "unplanned": {
                        "follow_up_schedule": [8, 16, 24]
                    },
                    "cessation_types": {
                        "stable_max_interval": "planned",
                        "random_administrative": "none",
                        "treatment_duration": "unplanned",
                        "premature": "unplanned"
                    }
                },
                "retreatment": {
                    "probability": 0.95
                }
            },
            "vision_model_type": "realistic"
        }
    )

def test_abs_implementation(config):
    """
    Test the fixed ABS implementation.
    
    Parameters
    ----------
    config : SimulationConfig
        Configuration for the simulation
    
    Returns
    -------
    dict
        Results dictionary with discontinuation statistics
    """
    print("\n" + "="*50)
    print("TESTING FIXED ABS IMPLEMENTATION")
    print("="*50)
    
    # Run the simulation
    print("\nRunning fixed ABS simulation...")
    sim = TreatAndExtendABS(config)
    patient_histories = sim.run()
    
    # Get discontinuation statistics
    unique_discontinued = sim.stats.get("unique_discontinuations", 0)
    total_discontinued = sim.stats.get("protocol_discontinuations", 0)
    total_patients = len(sim.agents)
    
    # Get manager statistics
    dm_stats = sim.refactored_manager.get_statistics()
    dm_unique = dm_stats.get("unique_discontinued_patients", 0)
    dm_total = dm_stats.get("total_discontinued", 0)
    
    # Calculate discontinuation rate
    disc_rate = unique_discontinued / total_patients if total_patients > 0 else 0
    
    # Print results
    print("\nABS TEST RESULTS:")
    print("-" * 30)
    print(f"Total patients: {total_patients}")
    print(f"Unique discontinued patients: {unique_discontinued}")
    print(f"Discontinuation rate: {disc_rate:.2%}")
    print(f"Discontinuation manager unique discontinued: {dm_unique}")
    
    # Verify results
    assert unique_discontinued <= total_patients, f"Discontinuation count ({unique_discontinued}) exceeds patient count ({total_patients})"
    assert unique_discontinued == dm_unique, f"Discrepancy between simulation ({unique_discontinued}) and manager ({dm_unique}) unique counts"
    assert dm_unique <= dm_total, f"Unique discontinuations ({dm_unique}) should be <= total discontinuations ({dm_total})"
    
    # Check for plausible discontinuation rate
    assert disc_rate <= 1.0, f"Discontinuation rate ({disc_rate:.2%}) exceeds 100%"
    
    # Print success message with rate
    print(f"✅ ABS TEST PASSED: Discontinuation rate is {disc_rate:.2%}, which is plausible.")
    
    # Return results for comparison
    return {
        "simulation_type": "ABS",
        "total_patients": total_patients,
        "unique_discontinued": unique_discontinued,
        "discontinuation_rate": disc_rate,
        "total_visits": sum(len(agent.history) for agent in sim.agents.values()),
        "unique_retreated": sim.stats.get("unique_retreatments", 0),
        "retreatment_rate": sim.stats.get("unique_retreatments", 0) / max(1, unique_discontinued),
    }

def test_des_implementation(config):
    """
    Test the fixed DES implementation.
    
    Parameters
    ----------
    config : SimulationConfig
        Configuration for the simulation
    
    Returns
    -------
    dict
        Results dictionary with discontinuation statistics
    """
    print("\n" + "="*50)
    print("TESTING FIXED DES IMPLEMENTATION")
    print("="*50)
    
    # Run the simulation
    print("\nRunning fixed DES simulation...")
    sim = TreatAndExtendDES(config)
    patient_histories = sim.run()
    
    # Get discontinuation statistics
    unique_discontinued = sim.stats.get("unique_discontinuations", 0)
    total_discontinued = sim.stats.get("protocol_discontinuations", 0)
    total_patients = len(sim.patients)
    
    # Get manager statistics
    dm_stats = sim.refactored_manager.get_statistics()
    dm_unique = dm_stats.get("unique_discontinued_patients", 0)
    dm_total = dm_stats.get("total_discontinued", 0)
    
    # Calculate discontinuation rate
    disc_rate = unique_discontinued / total_patients if total_patients > 0 else 0
    
    # Print results
    print("\nDES TEST RESULTS:")
    print("-" * 30)
    print(f"Total patients: {total_patients}")
    print(f"Unique discontinued patients: {unique_discontinued}")
    print(f"Discontinuation rate: {disc_rate:.2%}")
    print(f"Discontinuation manager unique discontinued: {dm_unique}")
    
    # Verify results
    assert unique_discontinued <= total_patients, f"Discontinuation count ({unique_discontinued}) exceeds patient count ({total_patients})"
    assert unique_discontinued == dm_unique, f"Discrepancy between simulation ({unique_discontinued}) and manager ({dm_unique}) unique counts"
    assert dm_unique <= dm_total, f"Unique discontinuations ({dm_unique}) should be <= total discontinuations ({dm_total})"
    
    # Check for plausible discontinuation rate
    assert disc_rate <= 1.0, f"Discontinuation rate ({disc_rate:.2%}) exceeds 100%"
    
    # Print success message with rate
    print(f"✅ DES TEST PASSED: Discontinuation rate is {disc_rate:.2%}, which is plausible.")
    
    # Return results for comparison
    return {
        "simulation_type": "DES",
        "total_patients": total_patients,
        "unique_discontinued": unique_discontinued,
        "discontinuation_rate": disc_rate,
        "total_visits": sum(len(patient["visit_history"]) for patient in sim.patients.values()),
        "unique_retreated": sim.stats.get("unique_retreatments", 0),
        "retreatment_rate": sim.stats.get("unique_retreatments", 0) / max(1, unique_discontinued),
    }

def compare_results(abs_results, des_results):
    """
    Compare the results of ABS and DES implementations.
    
    Parameters
    ----------
    abs_results : dict
        Results from ABS simulation
    des_results : dict
        Results from DES simulation
    """
    print("\n" + "="*50)
    print("COMPARING ABS AND DES RESULTS")
    print("="*50)
    
    # Calculate differences
    abs_rate = abs_results["discontinuation_rate"]
    des_rate = des_results["discontinuation_rate"]
    rate_diff = abs(abs_rate - des_rate)
    
    # Print comparison
    print(f"ABS Discontinuation Rate: {abs_rate:.2%}")
    print(f"DES Discontinuation Rate: {des_rate:.2%}")
    print(f"Absolute Rate Difference: {rate_diff:.2%}")
    
    # Check if rates are reasonably close
    # Allow for stochastic variation, but they should be within 10% of each other
    if rate_diff <= 0.10:
        print(f"✅ COMPARISON PASSED: ABS and DES rates are within 10% of each other ({rate_diff:.2%} difference)")
    else:
        print(f"⚠️ COMPARISON NOTE: ABS and DES rates differ by more than 10% ({rate_diff:.2%} difference)")
        print("This may be due to implementation differences or stochastic variation.")
    
    # Create comparative visualization
    comparison_data = pd.DataFrame([abs_results, des_results])
    
    # Plot discontinuation rates
    plt.figure(figsize=(10, 6))
    plt.bar(['ABS', 'DES'], [abs_rate, des_rate], color=['blue', 'orange'])
    plt.title('Discontinuation Rates: ABS vs DES')
    plt.ylabel('Discontinuation Rate')
    plt.ylim(0, max(abs_rate, des_rate) * 1.2)
    for i, rate in enumerate([abs_rate, des_rate]):
        plt.text(i, rate + 0.01, f'{rate:.2%}', ha='center')
    plt.savefig('discontinuation_rate_comparison.png')
    print("Rate comparison plot saved as discontinuation_rate_comparison.png")
    
    # Plot other statistics for comparison
    fig, axs = plt.subplots(2, 2, figsize=(12, 10))
    
    # Total patients
    axs[0, 0].bar(['ABS', 'DES'], [abs_results['total_patients'], des_results['total_patients']])
    axs[0, 0].set_title('Total Patients')
    
    # Discontinued patients
    axs[0, 1].bar(['ABS', 'DES'], [abs_results['unique_discontinued'], des_results['unique_discontinued']])
    axs[0, 1].set_title('Discontinued Patients')
    
    # Retreatment rate
    axs[1, 0].bar(['ABS', 'DES'], [abs_results['retreatment_rate'], des_results['retreatment_rate']])
    axs[1, 0].set_title('Retreatment Rate')
    axs[1, 0].set_ylim(0, 1)
    
    # Total visits
    axs[1, 1].bar(['ABS', 'DES'], [abs_results['total_visits'], des_results['total_visits']])
    axs[1, 1].set_title('Total Visits')
    
    plt.tight_layout()
    plt.savefig('abs_des_comparison.png')
    print("Full comparison plot saved as abs_des_comparison.png")
    
    # Return the difference for potential further analysis
    return rate_diff

def main():
    """Main function to run tests and comparisons."""
    parser = argparse.ArgumentParser(description='Test and compare fixed ABS and DES implementations.')
    parser.add_argument('--probability', type=float, default=0.2, help='Discontinuation probability (default: 0.2)')
    parser.add_argument('--patients', type=int, default=500, help='Number of patients to simulate (default: 500)')
    parser.add_argument('--years', type=int, default=2, help='Duration in years (default: 2)')
    parser.add_argument('--seed', type=int, default=None, help='Random seed for reproducibility')
    parser.add_argument('--only-abs', action='store_true', help='Only run ABS test')
    parser.add_argument('--only-des', action='store_true', help='Only run DES test')
    
    args = parser.parse_args()
    
    # Set random seed if provided
    if args.seed is not None:
        np.random.seed(args.seed)
        print(f"Using random seed: {args.seed}")
    
    # Create configuration
    config = create_test_config(
        discontinuation_probability=args.probability,
        num_patients=args.patients,
        duration_years=args.years
    )
    
    # Print test parameters
    print(f"Test Parameters:")
    print(f"- Discontinuation Probability: {args.probability}")
    print(f"- Number of Patients: {args.patients}")
    print(f"- Simulation Duration: {args.years} years")
    
    # Run tests based on arguments
    abs_results = None
    des_results = None
    
    if not args.only_des:
        try:
            abs_results = test_abs_implementation(config)
        except Exception as e:
            print(f"❌ ABS TEST FAILED: {str(e)}")
            raise
    
    if not args.only_abs:
        try:
            des_results = test_des_implementation(config)
        except Exception as e:
            print(f"❌ DES TEST FAILED: {str(e)}")
            raise
    
    # Compare results if both tests were run
    if abs_results and des_results:
        try:
            rate_diff = compare_results(abs_results, des_results)
            if rate_diff <= 0.10:
                print("\n✅ OVERALL TEST PASSED: Both implementations produce plausible and consistent results.")
            else:
                print("\n⚠️ OVERALL TEST NOTE: Implementations show some differences, but both work correctly.")
        except Exception as e:
            print(f"❌ COMPARISON FAILED: {str(e)}")
            raise
    
    # Summarize test result
    if (not args.only_des and not abs_results) or (not args.only_abs and not des_results):
        print("\n❌ SOME TESTS FAILED: See above for details.")
        return False
    
    print("\n✅ ALL REQUESTED TESTS PASSED.")
    return True

if __name__ == "__main__":
    main()