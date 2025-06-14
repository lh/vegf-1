"""
Verify that patient state flags are properly implemented in the simulation.

This script runs a real simulation with the enhanced discontinuation manager 
and verifies that the required flags are present in the patient visit records.
"""

import os
import sys
import json
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import simulation modules
from simulation.abs import AgentBasedSimulation
from simulation.config import SimulationConfig
from treat_and_extend_abs_fixed import TreatAndExtendABS

# JSON encoder for datetime objects
class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

def verify_flags_in_simulation_results(patient_histories):
    """Check if the required flags are present in the patient histories."""
    flag_counts = {
        'is_discontinuation_visit': 0,
        'discontinuation_reason': 0,
        'is_retreatment': 0,
        'retreatment_reason': 0
    }
    
    for patient_id, visits in patient_histories.items():
        for visit in visits:
            for flag in flag_counts.keys():
                if flag in visit and visit[flag]:
                    flag_counts[flag] += 1
    
    print("Flag presence counts:")
    for flag, count in flag_counts.items():
        print(f"  {flag}: {count}")
    
    return flag_counts['is_discontinuation_visit'] > 0 or flag_counts['is_retreatment'] > 0

def main():
    """Run the main verification script."""
    # Load configuration from YAML
    config_path = 'protocols/simulation_configs/enhanced_discontinuation.yaml'
    
    if not os.path.exists(config_path):
        print(f"Error: Configuration file not found at {config_path}")
        return 1
    
    print(f"Loading configuration from {config_path}...")
    config = SimulationConfig.from_yaml(config_path)
    
    # Set small number of patients for quick testing
    config.num_patients = 30
    
    # Set high discontinuation probability for testing
    if hasattr(config, 'parameters') and 'discontinuation' in config.parameters:
        if 'criteria' in config.parameters['discontinuation']:
            if 'stable_max_interval' in config.parameters['discontinuation']['criteria']:
                config.parameters['discontinuation']['criteria']['stable_max_interval']['probability'] = 0.8
            if 'random_administrative' in config.parameters['discontinuation']['criteria']:
                config.parameters['discontinuation']['criteria']['random_administrative']['annual_probability'] = 0.2
    
    # Run treat and extend ABS simulation
    print(f"Running simulation with {config.num_patients} patients...")
    simulation = TreatAndExtendABS(config)
    start_date = datetime.strptime(config.start_date, "%Y-%m-%d")
    simulation.initialize_patients()
    
    # Set longer duration for testing discontinuations and retreatments
    duration_days = 730  # 2 years
    end_date = start_date + timedelta(days=duration_days)
    
    # Run simulation
    print(f"Running simulation from {start_date} to {end_date}...")
    simulation.run()
    
    # Get results
    print("Extracting simulation results...")
    results = simulation.get_results()
    
    # Save raw results
    with open('verification_results.json', 'w') as f:
        json.dump(results, f, indent=2, cls=DateTimeEncoder)
    
    # Format patient histories for analysis
    patient_histories = {}
    for patient_id, patient in simulation.patients.items():
        patient_histories[patient_id] = patient.history
    
    # Verify that the flags are present in the patient histories
    print("\nVerifying patient state flags in simulation results...")
    flags_present = verify_flags_in_simulation_results(patient_histories)
    
    if flags_present:
        print("\nSuccess: Patient state flags are present in the simulation results")
        
        # Print some example visits with flags
        print("\nExample visits with flags:")
        examples_found = 0
        for patient_id, visits in patient_histories.items():
            for visit in visits:
                if (('is_discontinuation_visit' in visit and visit['is_discontinuation_visit']) or
                    ('is_retreatment' in visit and visit['is_retreatment'])):
                    print(f"\nPatient {patient_id}, Visit:")
                    for key, value in visit.items():
                        if key in ['is_discontinuation_visit', 'discontinuation_reason', 
                                   'is_retreatment', 'retreatment_reason', 'date', 'type']:
                            print(f"  {key}: {value}")
                    examples_found += 1
                    if examples_found >= 3:  # Limit to 3 examples
                        break
            if examples_found >= 3:
                break
        
        return 0
    else:
        print("\nError: Patient state flags are missing in the simulation results")
        return 1

if __name__ == "__main__":
    sys.exit(main())