"""
Test script to verify the fixed implementations handle discontinuation statistics correctly.

This script directly tests the fixed simulation classes and ensures that stats are tracked
properly without relying on complex visualizations or potentially synthetic data.
"""

import sys
import os
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# Add the project root directory to sys.path
root_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(root_dir)

# Import the simulation modules directly for testing
from simulation.config import SimulationConfig
from treat_and_extend_abs_fixed import TreatAndExtendABS
from treat_and_extend_des_fixed import TreatAndExtendDES

def main():
    """Test the discontinuation statistics tracking in fixed implementations."""
    print("\n" + "="*50)
    print("TESTING FIXED DISCONTINUATION IMPLEMENTATION")
    print("="*50)
    
    # Create a test configuration with high discontinuation probability
    try:
        config = SimulationConfig.from_yaml("test_simulation")
        
        # Override the parameters for a quick test
        config.num_patients = 10
        config.duration_days = 365 * 2  # 2 years
        
        # Set discontinuation parameters to ensure we get some discontinuations
        if not hasattr(config, 'parameters'):
            config.parameters = {}
        if "discontinuation" not in config.parameters:
            config.parameters["discontinuation"] = {}
            
        config.parameters["discontinuation"]["enabled"] = True
        
        # Set stability criteria with high probability
        if "criteria" not in config.parameters["discontinuation"]:
            config.parameters["discontinuation"]["criteria"] = {}
            
        if "stable_max_interval" not in config.parameters["discontinuation"]["criteria"]:
            config.parameters["discontinuation"]["criteria"]["stable_max_interval"] = {}
            
        # Set 90% probability to ensure we get discontinuations
        config.parameters["discontinuation"]["criteria"]["stable_max_interval"]["probability"] = 0.9
        config.parameters["discontinuation"]["criteria"]["stable_max_interval"]["consecutive_visits"] = 3
        config.parameters["discontinuation"]["criteria"]["stable_max_interval"]["interval_weeks"] = 16
        
        # Set some randomAdministrative too
        if "random_administrative" not in config.parameters["discontinuation"]["criteria"]:
            config.parameters["discontinuation"]["criteria"]["random_administrative"] = {}
            
        config.parameters["discontinuation"]["criteria"]["random_administrative"]["annual_probability"] = 0.2
        
        # Set higher fluid detection probability to ensure we get retreatments
        if "vision_model" not in config.parameters:
            config.parameters["vision_model"] = {}
        
        config.parameters["vision_model"]["fluid_detection_probability"] = 0.8  # Increase from default 0.3
        
        # Configure retreatment settings to ensure we get retreatments
        if "retreatment" not in config.parameters["discontinuation"]:
            config.parameters["discontinuation"]["retreatment"] = {}
        
        config.parameters["discontinuation"]["retreatment"]["probability"] = 0.95  # High probability of retreatment when fluid is detected
        
        # Ensure monitoring visits are scheduled for all cessation types
        if "monitoring" not in config.parameters["discontinuation"]:
            config.parameters["discontinuation"]["monitoring"] = {}
            
        if "cessation_types" not in config.parameters["discontinuation"]["monitoring"]:
            config.parameters["discontinuation"]["monitoring"]["cessation_types"] = {}
            
        # Set all cessation types to have "planned" monitoring (ensures monitoring visits)
        config.parameters["discontinuation"]["monitoring"]["cessation_types"] = {
            "stable_max_interval": "planned",
            "random_administrative": "planned",
            "treatment_duration": "planned",
            "premature": "planned"
        }
        
        # Run both simulation types
        for sim_type in ["ABS", "DES"]:
            print(f"\nTesting {sim_type} implementation...")
            
            # Run the appropriate simulation
            if sim_type == "ABS":
                sim = TreatAndExtendABS(config)
            else:
                sim = TreatAndExtendDES(config)
                
            # Run the simulation
            patient_histories = sim.run()
            
            # Extract the discontinuation statistics
            disc_stats = sim.stats.get("discontinuations", {})
            
            print(f"\n{sim_type} Discontinuation Statistics:")
            print("-" * 40)
            
            # Print raw discontinuation counts by type
            print("Discontinuation Counts by Type:")
            total_disc = 0
            for disc_type, count in sim.stats.get("discontinuation_counts", {}).items():
                print(f"  {disc_type}: {count}")
                total_disc += count
            
            print(f"Total Discontinuations: {total_disc}")
            print(f"Unique Discontinued Patients: {sim.stats.get('unique_discontinuations', 0)}")
            
            # Print retreatment stats if available
            total_retreatments = sim.stats.get("retreatments", 0)
            unique_retreated = sim.stats.get("unique_retreatments", 0)
            retreatment_by_type = sim.stats.get("retreatments_by_type", {})
            
            print("\nRetreatment Statistics:")
            print(f"  Total Retreatments: {total_retreatments}")
            print(f"  Unique Retreated Patients: {unique_retreated}")
                
            # Print retreatments by type if available
            if retreatment_by_type:
                print("\nRetreatments by Prior Discontinuation Type:")
                for disc_type, count in retreatment_by_type.items():
                    print(f"  {disc_type}: {count}")
            
            # Verify unique patient counts are consistent
            total_patients = len(sim.agents) if sim_type == "ABS" else len(sim.patients)
            unique_disc = sim.stats.get("unique_discontinuations", 0)
            
            if unique_disc <= total_patients:
                print(f"\n✅ {sim_type} VALIDATION PASSED: Unique discontinued patients ({unique_disc}) <= Total patients ({total_patients})")
            else:
                print(f"\n❌ {sim_type} VALIDATION FAILED: Unique discontinued patients ({unique_disc}) > Total patients ({total_patients})")
                
            # Calculate overall discontinuation rate
            disc_rate = (unique_disc / total_patients) * 100 if total_patients > 0 else 0
            print(f"Discontinuation Rate: {disc_rate:.1f}%")
        
        print("\n✅ DISCONTINUATION TESTS COMPLETED")
        
    except Exception as e:
        print(f"\n❌ ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()