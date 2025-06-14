"""
Script to force discontinuations to occur in the simulation
by pre-populating patient states that will trigger discontinuation.
"""

from simulation.config import SimulationConfig
from simulation.enhanced_discontinuation_manager import EnhancedDiscontinuationManager
import numpy as np
from datetime import datetime, timedelta
import yaml
import json
import os

# Ensure reproducibility
np.random.seed(42)

print("Creating discontinuation manager with default parameters...")
with open('protocols/parameter_sets/eylea/discontinuation_parameters.yaml', 'r') as f:
    file_params = yaml.safe_load(f)

# Create discontinuation manager directly from the parameters file
manager = EnhancedDiscontinuationManager(file_params)
print(f"Discontinuation manager enabled: {manager.enabled}")
print(f"Stable max interval probability: {manager.criteria.get('stable_max_interval', {}).get('probability', 0)}")

# Write a function to create a patient state that meets discontinuation criteria
def create_patient_for_discontinuation(patient_id, patient_number, phase="maintenance"):
    """
    Create a patient state that meets discontinuation criteria.
    """
    return {
        "id": patient_id,
        "current_vision": 75.0,
        "baseline_vision": 65.0,
        "current_phase": phase,
        "treatments_in_phase": 5 if phase == "maintenance" else 0,
        "next_visit_interval": 16,  # Max interval
        "disease_activity": {
            "fluid_detected": False,  # Stable disease
            "consecutive_stable_visits": 3,  # Already had 3 stable visits
            "max_interval_reached": True,  # Reached max interval
            "current_interval": 16  # At max interval
        },
        "treatment_status": {
            "active": True,
            "recurrence_detected": False,
            "weeks_since_discontinuation": 0,
            "cessation_type": None
        },
        "disease_characteristics": {
            "has_PED": False
        },
        "visit_history": []
    }

# Create a simple function to patch into the patient generation method
def modified_patient_generator(sim):
    """
    Modified patient generator to create patients ready for discontinuation.
    Patches into the simulation's generate_patients method.
    """
    # Call original generator first to set up the basics
    original_generate_patients(sim)
    
    # Now modify the patients to be ready for discontinuation
    total_patients = len(sim.agents)
    discontinuation_ready_count = int(total_patients * 0.5)  # Make 50% ready for discontinuation
    
    # Make half the patients ready for discontinuation
    patient_ids = list(sim.agents.keys())
    for i, patient_id in enumerate(patient_ids[:discontinuation_ready_count]):
        # Modify this patient to be ready for discontinuation
        sim.agents[patient_id].current_phase = "maintenance"
        sim.agents[patient_id].treatments_in_phase = 5
        sim.agents[patient_id].next_visit_interval = 16
        
        # Set disease activity to meet discontinuation criteria
        sim.agents[patient_id].disease_activity = {
            "fluid_detected": False,  # Stable disease
            "consecutive_stable_visits": 3,  # Already had 3 stable visits
            "max_interval_reached": True,  # Reached max interval
            "current_interval": 16  # At max interval
        }
    
    print(f"Modified {discontinuation_ready_count} patients to be ready for discontinuation out of {total_patients} total patients")

# Write a script to inject this into the simulation
monkeypatch_code = """
# Save reference to the original method
original_generate_patients = TreatAndExtendABS._generate_patients

# Define a replacement method
def patched_generate_patients(self):
    # Call the injected method
    from force_discontinuation import modified_patient_generator
    return modified_patient_generator(self)

# Apply the patch
TreatAndExtendABS._generate_patients = patched_generate_patients
print("⚠️ PATCHED: Modified patient generation to create patients ready for discontinuation")
"""

# Save the monkeypatch script
with open('inject_discontinuation.py', 'w') as f:
    f.write(monkeypatch_code)

print("\nCreated injection script at inject_discontinuation.py")
print("\nTo use this in a Streamlit run, do the following:")
print("1. Modify run_ape.py to include:")
print("   import inject_discontinuation  # Add this line before running Streamlit")
print("2. Run the app: ./run_ape.py")
print("3. In the Run Simulation tab, use the following parameters:")
print("   - Population Size: 1000")
print("   - Simulation Duration: 5 years")
print("   - Planned Discontinuation Probability: 0.9  (set very high to ensure discontinuations)")
print("\nThis will create patients that have already met the criteria for discontinuation.")
print("They have stable disease, 3 consecutive stable visits, and are at max treatment interval.")
print("The simulation should show a substantial number of discontinuations.")

# Make a modification to the run_ape.py file
run_ape_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "run_ape.py")
if os.path.exists(run_ape_path):
    with open(run_ape_path, 'r') as f:
        content = f.read()
    
    if "import inject_discontinuation" not in content:
        # Insert the import after other imports
        import_pos = content.find("import subprocess")
        if import_pos >= 0:
            new_content = (
                content[:import_pos + len("import subprocess")] + 
                "\nimport inject_discontinuation  # Inject discontinuation-ready patients" +
                content[import_pos + len("import subprocess"):]
            )
            
            # Backup the original file
            with open(run_ape_path + ".bak", 'w') as f:
                f.write(content)
            
            # Write the modified file
            with open(run_ape_path, 'w') as f:
                f.write(new_content)
            
            print(f"\nUpdated {run_ape_path} with the injection code")
            print(f"A backup of the original file was saved to {run_ape_path}.bak")
        else:
            print(f"\nCould not find insertion point in {run_ape_path}")
            print("Please manually add the following line after the imports:")
            print("import inject_discontinuation  # Inject discontinuation-ready patients")
    else:
        print(f"\n{run_ape_path} already contains the injection code")
else:
    print(f"\nCould not find {run_ape_path}")
    print("Please manually create a file called inject_discontinuation.py with the following content:")
    print(monkeypatch_code)