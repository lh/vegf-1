"""Debug patient data structure from simulation."""

from simulation.config import SimulationConfig
from treat_and_extend_abs_fixed import TreatAndExtendABS
import json

# Create a small test simulation
config = SimulationConfig.from_yaml("test_simulation")
config.num_patients = 2
config.duration_days = 30  # Very short for testing

print("Running simulation...")
sim = TreatAndExtendABS(config)
patient_histories = sim.run()

print(f"\nDebug: patient_histories type: {type(patient_histories)}")
print(f"Debug: Number of patients: {len(patient_histories)}")

if patient_histories:
    # patient_histories is a dict, not a list
    patient_id = list(patient_histories.keys())[0]
    patient = patient_histories[patient_id]
    print(f"\nDebug: First patient ID: {patient_id}")
    print(f"Debug: First patient type: {type(patient)}")
    
    # Check if it's a dict
    if isinstance(patient, dict):
        print("Patient is a dict with keys:")
        for key in patient.keys():
            print(f"  - {key}: {type(patient[key])}")
        
        # Check for visit_history key
        if 'visit_history' in patient:
            vh = patient['visit_history']
            print(f"\nvisit_history found! Type: {type(vh)}, Length: {len(vh) if hasattr(vh, '__len__') else 'N/A'}")
            if vh:
                print(f"First visit: {vh[0]}")
    
    # Check if it's a list
    elif isinstance(patient, list):
        print(f"Patient is a list with {len(patient)} items")
        if patient:
            print("\nFirst few items in the list:")
            for i, item in enumerate(patient[:3]):
                print(f"  [{i}] type: {type(item)}")
                if isinstance(item, dict):
                    print(f"      keys: {list(item.keys())[:5]}")
                elif isinstance(item, str):
                    print(f"      value: {item}")
    # Check if it's an object with attributes
    else:
        print("Patient is an object with attributes:")
        attrs = [attr for attr in dir(patient) if not attr.startswith('_')]
        for attr in attrs[:20]:  # Show first 20 attributes
            print(f"  - {attr}")
        
        # Check for specific attributes
        if hasattr(patient, 'state'):
            state = patient.state
            print(f"\nstate attribute found! Type: {type(state)}")
            if isinstance(state, dict):
                print("state is a dict with keys:")
                for key in list(state.keys())[:10]:
                    print(f"  - {key}: {type(state[key])}")
                if 'visit_history' in state:
                    vh = state['visit_history']
                    print(f"\nvisit_history in state! Type: {type(vh)}, Length: {len(vh) if hasattr(vh, '__len__') else 'N/A'}")
        
        if hasattr(patient, 'visit_history'):
            vh = patient.visit_history
            print(f"\nvisit_history attribute found! Type: {type(vh)}, Length: {len(vh) if hasattr(vh, '__len__') else 'N/A'}")

# Let's also check what sim.patients looks like
if hasattr(sim, 'patients'):
    print(f"\n\nsim.patients type: {type(sim.patients)}")
    if sim.patients:
        patient = list(sim.patients.values())[0] if isinstance(sim.patients, dict) else sim.patients[0]
        print(f"sim.patients patient type: {type(patient)}")
        if hasattr(patient, 'state'):
            print(f"sim.patients patient has state: {type(patient.state)}")
            if hasattr(patient.state, 'visit_history'):
                print("sim.patients patient.state has visit_history")
            elif isinstance(patient.state, dict) and 'visit_history' in patient.state:
                print("sim.patients patient.state['visit_history'] exists")