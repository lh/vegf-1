#!/usr/bin/env python3
"""
Debug script to examine the actual structure of simulation results and patient histories.
"""

import json
import pandas as pd
from pathlib import Path
import sys
from datetime import datetime

# Add the parent directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from simulation.base import SimulationBase
from simulation_runner import run_simulation_with_config
from protocols.config_parser import parse_config


def run_small_simulation():
    """Run a small simulation and return the results."""
    print("Running small simulation...")
    config_path = Path("protocols/simulation_configs/enhanced_discontinuation.yaml")
    
    if not config_path.exists():
        print(f"Config file not found: {config_path}")
        return None
    
    # Parse the config
    simulation, params = parse_config(config_path)
    
    # Override to use fewer patients for debugging
    sim_params = params.get('simulation_parameters', {})
    sim_params['num_patients'] = 10
    sim_params['warmup_time'] = 0
    sim_params['simulation_time'] = 365 * 2  # 2 years
    
    # Run the simulation
    simulation.reset()
    simulation.run()
    
    # Generate results
    results = simulation.generate_results()
    
    # Add patient histories if available
    results['patient_histories'] = {}
    for patient_id, patient in simulation.patients.items():
        results['patient_histories'][str(patient_id)] = patient.get_history()
    
    return results


def examine_patient_histories(results):
    """Examine the structure of patient histories."""
    if 'patient_histories' not in results:
        print("No patient_histories field in results")
        return
    
    histories = results['patient_histories']
    print(f"\nNumber of patients: {len(histories)}")
    
    # Examine a few sample patients
    for i, (patient_id, history) in enumerate(histories.items()):
        if i >= 3:  # Look at first 3 patients
            break
        
        print(f"\n--- Patient {patient_id} ---")
        print(f"History type: {type(history)}")
        
        if isinstance(history, dict):
            print(f"Keys: {list(history.keys())}")
            
            # Check structure of each key
            for key, value in history.items():
                print(f"\n  {key}:")
                print(f"    Type: {type(value)}")
                
                if isinstance(value, list) and len(value) > 0:
                    print(f"    Length: {len(value)}")
                    print(f"    First item: {value[0]}")
                    print(f"    Last item: {value[-1]}")
                    
                    # Check for time format
                    if key in ['visit_times', 'treatment_times', 'vision_updates']:
                        if isinstance(value[0], dict) and 'time' in value[0]:
                            time_val = value[0]['time']
                            print(f"    Time format: {type(time_val)} = {time_val}")
                        elif isinstance(value[0], (int, float)):
                            print(f"    Time format: {type(value[0])} = {value[0]}")
                
                elif isinstance(value, pd.DataFrame):
                    print(f"    Shape: {value.shape}")
                    print(f"    Columns: {list(value.columns)}")
                    if not value.empty:
                        print(f"    First row:\n{value.iloc[0]}")
                
                else:
                    print(f"    Value: {value}")


def check_streamgraph_processing():
    """Check how the actual streamgraph is processing the data."""
    print("\n--- Checking Streamgraph Processing ---")
    
    # Import the actual streamgraph function
    try:
        from visualization.visualization_templates import create_realistic_acuity_streamgraph
        print("Successfully imported create_realistic_acuity_streamgraph")
        
        # Look at the function to understand expected data format
        import inspect
        print("\nFunction signature:")
        print(inspect.signature(create_realistic_acuity_streamgraph))
        
        # Get the source code
        print("\nFunction documentation:")
        print(create_realistic_acuity_streamgraph.__doc__)
        
    except ImportError as e:
        print(f"Could not import streamgraph function: {e}")


def save_debug_output(results):
    """Save the results for further inspection."""
    output_dir = Path("output/debug")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save raw results
    with open(output_dir / "simulation_results_debug.json", "w") as f:
        # Convert results to JSON-serializable format
        json_results = {}
        for key, value in results.items():
            if key == 'patient_histories':
                json_results[key] = {}
                for pid, hist in value.items():
                    json_results[key][pid] = {
                        k: v.tolist() if isinstance(v, pd.DataFrame) else v
                        for k, v in hist.items()
                    }
            else:
                json_results[key] = value
        
        json.dump(json_results, f, indent=2, default=str)
    
    print(f"\nResults saved to {output_dir / 'simulation_results_debug.json'}")


def main():
    """Main debug function."""
    print("Debug Script: Examining Simulation Results Structure")
    print("=" * 50)
    
    # Run the simulation
    results = run_small_simulation()
    
    if results:
        # Examine the structure
        examine_patient_histories(results)
        
        # Check streamgraph processing
        check_streamgraph_processing()
        
        # Save for further inspection
        save_debug_output(results)
        
        # Try to create a simple streamgraph if possible
        try:
            from visualization.visualization_templates import create_realistic_acuity_streamgraph
            
            # Find a patient with some history
            for patient_id, history in results['patient_histories'].items():
                if 'vision_updates' in history and len(history['vision_updates']) > 5:
                    print(f"\nTrying to create streamgraph for patient {patient_id}")
                    
                    # Extract history in expected format
                    patient_history = []
                    for update in history['vision_updates']:
                        if isinstance(update, dict):
                            time_val = update.get('time', 0)
                            va_val = update.get('va', 0)
                        else:
                            # If it's a tuple or list
                            time_val = update[0] if len(update) > 0 else 0
                            va_val = update[1] if len(update) > 1 else 0
                        
                        patient_history.append({
                            'time': time_val,
                            'visual_acuity': va_val
                        })
                    
                    # Try to create the plot
                    fig, ax = create_realistic_acuity_streamgraph(
                        patient_history,
                        title=f"Patient {patient_id} Visual Acuity"
                    )
                    print("Successfully created streamgraph!")
                    break
                    
        except Exception as e:
            print(f"\nError creating streamgraph: {e}")
            import traceback
            traceback.print_exc()
    
    else:
        print("Failed to run simulation")


if __name__ == "__main__":
    main()