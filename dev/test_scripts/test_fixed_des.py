"""
Test script for the fixed DES implementation.

This script runs the fixed DES implementation and verifies that:
1. Discontinuations occur at the expected rate
2. No double counting is happening
3. Discontinuation rate is plausible (≤100%)
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from simulation.config import SimulationConfig
from treat_and_extend_des_fixed import run_treat_and_extend_des, TreatAndExtendDES

def test_fixed_des_discontinuation():
    """
    Run a test to validate that discontinuations work correctly
    in the fixed DES implementation.
    """
    print("\n" + "="*50)
    print("TESTING FIXED DES IMPLEMENTATION")
    print("="*50)
    
    # Create a config with a small number of patients and short duration
    # for quick testing
    config = SimulationConfig(
        config_name="test_des_fixed",
        num_patients=1000,
        duration_days=365*2,  # 2 years
        start_date="2023-01-01",
        parameters={
            "discontinuation": {
                "enabled": True,
                "criteria": {
                    "stable_max_interval": {
                        "probability": 0.2,
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
    
    # Run the simulation
    print("\nRunning fixed DES simulation with test configuration...")
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
    # Generally should be within 0-50% for reasonable parameters
    assert disc_rate <= 1.0, f"Discontinuation rate ({disc_rate:.2%}) exceeds 100%"
    assert disc_rate > 0.0, f"No discontinuations occurred (rate: {disc_rate:.2%})"
    
    # Print success message with rate
    print(f"\n✅ DES TEST PASSED: Discontinuation rate is {disc_rate:.2%}, which is plausible.")
    
    # Compare with retreatments
    unique_retreated = sim.stats.get("unique_retreatments", 0)
    retreatment_rate = unique_retreated / max(1, unique_discontinued)
    print(f"Retreatment rate: {retreatment_rate:.2%} ({unique_retreated}/{unique_discontinued})")
    
    return True

if __name__ == "__main__":
    # Run the test
    test_fixed_des_discontinuation()
    
    # Add option to visualize results
    print("\nWould you like to visualize patient outcomes? (y/n)")
    choice = input().strip().lower()
    
    if choice == 'y':
        # Run a larger simulation for visualization
        config = SimulationConfig(
            config_name="test_des_fixed_viz",
            num_patients=200,
            duration_days=365*3,  # 3 years
            start_date="2023-01-01",
            parameters={
                "discontinuation": {
                    "enabled": True,
                    "criteria": {
                        "stable_max_interval": {
                            "probability": 0.2,
                            "consecutive_visits": 3,
                            "interval_weeks": 16
                        }
                    }
                }
            }
        )
        
        # Run simulation
        sim = TreatAndExtendDES(config)
        patient_histories = sim.run()
        
        # Convert to DataFrame
        all_data = []
        for patient_id, visits in patient_histories.items():
            for visit in visits:
                # Extract key data from visit
                visit_data = {
                    'patient_id': patient_id,
                    'date': visit.get('date', ''),
                    'vision': visit.get('vision', None),
                    'phase': visit.get('phase', ''),
                    'type': visit.get('type', ''),
                }
                all_data.append(visit_data)
        
        df = pd.DataFrame(all_data)
        df['date'] = pd.to_datetime(df['date'])
        
        # Plot vision over time for sample patients
        sample_patients = np.random.choice(df['patient_id'].unique(), 5)
        
        plt.figure(figsize=(12, 8))
        for patient_id in sample_patients:
            patient_data = df[df['patient_id'] == patient_id]
            plt.plot(patient_data['date'], patient_data['vision'], 'o-', label=patient_id)
        
        plt.xlabel('Date')
        plt.ylabel('Visual Acuity (ETDRS letters)')
        plt.title('Visual Acuity Over Time (Sample Patients)')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.savefig('des_fixed_vision_over_time.png')
        print("Plot saved as des_fixed_vision_over_time.png")
        
        # Plot distribution of visit phases
        phase_counts = df['phase'].value_counts()
        plt.figure(figsize=(10, 6))
        phase_counts.plot(kind='bar')
        plt.title('Distribution of Visit Phases')
        plt.ylabel('Number of Visits')
        plt.savefig('des_fixed_phase_distribution.png')
        print("Plot saved as des_fixed_phase_distribution.png")