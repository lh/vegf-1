"""Test visualization with actual ABS simulation data structure"""

import os
import sys
import json
from datetime import datetime
import matplotlib.pyplot as plt

# Add the parent directory to the Python path to import from streamlit_app
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from treat_and_extend_abs_fixed import TreatAndExtendABS
from streamlit_app.simulation_runner import generate_va_over_time_plot
from simulation.config import SimulationConfig

def test_with_actual_abs():
    """Run actual ABS simulation and test visualization"""
    
    print("Running actual ABS simulation...")
    
    # Create simulation configuration
    num_patients = 100
    simulation_months = 24
    
    # Initialize parameters 
    population_params = {
        'size': num_patients,
        'ages': {
            'mean': 75,
            'std': 8,
            'min_age': 50
        },
        'sex_distribution': {
            'male': 0.4,
            'female': 0.6
        },
        'baseline_acuity': {
            'low_vision': {
                'range': (20, 39),
                'proportion': 0.25
            },
            'moderate_vision': {
                'range': (40, 69),
                'proportion': 0.65
            },
            'good_vision': {
                'range': (70, 85),
                'proportion': 0.10
            }
        }
    }
    
    # Simulation parameters
    simulation_params = {
        'duration_months': simulation_months,
        'random_seed': None
    }
    
    # Create simulation config
    config_dict = {
        'simulation_type': 'ABS',
        'population_size': num_patients,
        'duration_years': simulation_months / 12,
        'random_seed': 42,
        'scenario': {
            'scenario_type': 'Treat-and-Extend',
            'initial_interval': 30,
            'max_interval': 84,
            'min_interval': 28,
            'extension_criteria': 'stable',
            'allow_prn': False
        }
    }
    
    # Create proper config object
    config = SimulationConfig(config_dict)
    
    # Create simulation
    sim = TreatAndExtendABS(config)
    
    # Run simulation
    print("Running simulation...")
    sim.run_simulation()
    
    # Get results
    results = sim.get_results()
    
    # Analyze data structure
    print(f"\nResults keys: {list(results.keys())}")
    
    if "patient_histories" in results:
        patient_histories = results["patient_histories"]
        print(f"Number of patients with histories: {len(patient_histories)}")
        
        # Check structure of first patient
        if patient_histories:
            sample_patient_id = next(iter(patient_histories))
            sample_patient = patient_histories[sample_patient_id]
            
            print(f"\nSample patient ID: {sample_patient_id}")
            print(f"Patient data type: {type(sample_patient)}")
            
            if isinstance(sample_patient, list) and sample_patient:
                print(f"Number of visits: {len(sample_patient)}")
                print("\nFirst visit structure:")
                first_visit = sample_patient[0]
                for key, value in first_visit.items():
                    print(f"  {key}: {value} (type: {type(value).__name__})")
    
    # Generate visualization
    print("\nGenerating visualization...")
    fig = generate_va_over_time_plot(results)
    
    # Save the plot
    plot_filename = "test_abs_structure.png"
    fig.savefig(plot_filename, dpi=300, bbox_inches='tight')
    print(f"Plot saved as {plot_filename}")
    
    # Close the plot
    plt.close(fig)
    
    # Save results for debugging
    with open("test_abs_structure_data.json", 'w') as f:
        # Make JSON serializable
        json_safe = {}
        for key, value in results.items():
            try:
                json.dump({key: value}, open("/dev/null", "w"))
                json_safe[key] = value
            except:
                if key == "patient_histories":
                    # Convert to string representation
                    json_safe[key] = {
                        pid: str(patient) for pid, patient in value.items()
                    }
                else:
                    json_safe[key] = str(value)
        
        json.dump(json_safe, f, indent=2)
    print("Data saved as test_abs_structure_data.json")

if __name__ == "__main__":
    test_with_actual_abs()