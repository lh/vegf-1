"""
Test script to verify the Streamlit app correctly integrates with the fixed implementations.

This script directly tests the simulation_runner.py module's ability to process
simulation results and generate basic visualization without relying on potentially 
synthetic data or complex streamgraphs.
"""

import sys
import os
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import json

# Add the project root directory to sys.path
root_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(root_dir)

# Import the simulation modules directly for testing
from simulation.config import SimulationConfig
from treat_and_extend_abs_fixed import TreatAndExtendABS
from treat_and_extend_des_fixed import TreatAndExtendDES

# Import the core functions from simulation_runner
from streamlit_app.simulation_runner import process_simulation_results, create_tufte_bar_chart

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
        
        config.parameters["discontinuation"]["retreatment"]["probability"] = 0.95  # High probability of retreatment
        
        # Ensure monitoring visits are scheduled
        if "monitoring" not in config.parameters["discontinuation"]:
            config.parameters["discontinuation"]["monitoring"] = {}
            
        if "cessation_types" not in config.parameters["discontinuation"]["monitoring"]:
            config.parameters["discontinuation"]["monitoring"]["cessation_types"] = {}
            
        # Set all cessation types to have "planned" monitoring
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
            try:
                results = process_simulation_results(sim, patient_histories, params)
                
                # Create output directory if it doesn't exist
                output_dir = os.path.join(os.getcwd(), "output", "debug")
                os.makedirs(output_dir, exist_ok=True)
                
                # Save the processed results for inspection
                results_file = os.path.join(output_dir, f"{sim_type.lower()}_processed_results.json")
                with open(results_file, 'w') as f:
                    # Convert complex objects to strings for JSON serialization
                    serializable_results = {}
                    for key, value in results.items():
                        if isinstance(value, (int, float, str, bool, list, dict)) or value is None:
                            serializable_results[key] = value
                        else:
                            serializable_results[key] = str(value)
                    
                    json.dump(serializable_results, f, indent=2)
                print(f"Saved processed results to {results_file}")
                
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
                    
                # Create a simple bar chart of discontinuation types using tufte_bar_chart
                if "discontinuation_counts" in results and results["discontinuation_counts"]:
                    try:
                        disc_counts = results["discontinuation_counts"]
                        types = list(disc_counts.keys())
                        counts = list(disc_counts.values())
                        
                        if sum(counts) > 0:
                            # Create the bar chart
                            fig = create_tufte_bar_chart(
                                categories=types,
                                values=counts,
                                title=f"{sim_type} Discontinuation Types",
                                xlabel="Number of Patients",
                                figsize=(10, 6),
                                horizontal=True
                            )
                            
                            # Save the figure
                            bar_chart_file = os.path.join(output_dir, f"{sim_type.lower()}_discontinuation_chart.png")
                            fig.savefig(bar_chart_file)
                            print(f"Saved bar chart to {bar_chart_file}")
                            
                            print(f"✅ {sim_type} VISUALIZATION TEST PASSED: Created bar chart")
                        else:
                            print(f"⚠️ {sim_type} VISUALIZATION TEST: No discontinuations to visualize")
                    except Exception as e:
                        print(f"❌ {sim_type} VISUALIZATION TEST FAILED: {type(e).__name__}: {e}")
                else:
                    print(f"⚠️ {sim_type} VISUALIZATION TEST: No discontinuation_counts in results")
            except Exception as e:
                print(f"❌ {sim_type} STREAMLIT PROCESSING FAILED: {type(e).__name__}: {e}")
                import traceback
                traceback.print_exc()
        
        print("\n✅ STREAMLIT INTEGRATION TESTS COMPLETED")
        
    except Exception as e:
        print(f"\n❌ ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()