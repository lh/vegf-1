"""
Test script to verify the Streamlit app correctly uses the fixed implementations.

This script directly tests the simulation_runner.py module to ensure that
it correctly uses the fixed implementations and properly handles discontinuation
statistics.
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

# Import the simulation runner module to test direct integration
from streamlit_app.simulation_runner import process_simulation_results, generate_discontinuation_plot

def main():
    """Test the integration between fixed implementations and Streamlit."""
    print("\n" + "="*50)
    print("TESTING STREAMLIT INTEGRATION WITH FIXED IMPLEMENTATIONS")
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
            print(f"\nTesting {sim_type} integration with Streamlit...")
            
            # Create params dictionary for process_simulation_results
            params = {
                "simulation_type": sim_type,
                "population_size": config.num_patients,
                "duration_years": config.duration_days / 365,
                "enable_clinician_variation": True,
                "planned_discontinue_prob": 0.9,
                "admin_discontinue_prob": 0.2
            }
            
            # Run the appropriate simulation
            if sim_type == "ABS":
                sim = TreatAndExtendABS(config)
            else:
                sim = TreatAndExtendDES(config)
                
            # Run the simulation
            patient_histories = sim.run()
            
            # Calculate discontinuation rate directly from simulation
            unique_discontinued = sim.stats.get("unique_discontinuations", 0)
            total_patients = len(sim.agents) if sim_type == "ABS" else len(sim.patients)
            direct_rate = (unique_discontinued / total_patients) * 100 if total_patients > 0 else 0
            print(f"Direct discontinuation rate: {direct_rate:.1f}%")
            
            # Now process the results using the Streamlit function
            results = process_simulation_results(sim, patient_histories, params)
            
            # Check if the corrected discontinuation rate is present
            if "unique_discontinued_patients" in results:
                streamlit_unique = results["unique_discontinued_patients"]
                streamlit_rate = (streamlit_unique / total_patients) * 100 if total_patients > 0 else 0
                print(f"Streamlit processed unique patients: {streamlit_unique}")
                print(f"Streamlit processed rate: {streamlit_rate:.1f}%")
                
                # Verify the rates match
                if abs(direct_rate - streamlit_rate) < 0.1:
                    print(f"✅ {sim_type} STREAMLIT INTEGRATION TEST PASSED: Rates match")
                else:
                    print(f"⚠️ {sim_type} RATES MISMATCH: Direct={direct_rate:.1f}%, Streamlit={streamlit_rate:.1f}%")
            else:
                print(f"❌ {sim_type} STREAMLIT INTEGRATION TEST FAILED: No unique_discontinued_patients in results")
                
            # Test visualization generation
            try:
                print(f"Testing {sim_type} visualization generation...")
                figure = generate_discontinuation_plot(results)
                
                # Check if we got a figure or list of figures
                if isinstance(figure, list):
                    print(f"✅ {sim_type} VISUALIZATION TEST PASSED: Got {len(figure)} figures")
                else:
                    print(f"✅ {sim_type} VISUALIZATION TEST PASSED: Got 1 figure")
                    
                # Save the figures for inspection
                # Create output directory if it doesn't exist
                output_dir = os.path.join(os.getcwd(), "output", "debug")
                os.makedirs(output_dir, exist_ok=True)
                
                # Save the figures for inspection
                if isinstance(figure, list):
                    for i, fig in enumerate(figure):
                        filepath = os.path.join(output_dir, f"{sim_type.lower()}_disc_viz_{i}.png")
                        fig.savefig(filepath)
                        print(f"Saved {filepath}")
                else:
                    filepath = os.path.join(output_dir, f"{sim_type.lower()}_disc_viz.png")
                    figure.savefig(filepath)
                    print(f"Saved {filepath}")
            except Exception as e:
                print(f"❌ {sim_type} VISUALIZATION TEST FAILED: {type(e).__name__}: {e}")
        
        print("\n✅ STREAMLIT INTEGRATION TESTS COMPLETED")
        
    except Exception as e:
        print(f"\n❌ ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()