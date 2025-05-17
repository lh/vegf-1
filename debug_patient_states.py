"""Debug patient state transitions in simulation data."""

from simulation.config import SimulationConfig
from treat_and_extend_abs_fixed import TreatAndExtendABS
import json

# Create a test simulation with higher discontinuation rates
config = SimulationConfig.from_yaml("test_simulation")
config.num_patients = 10
config.duration_days = 365

# Increase discontinuation probabilities to see transitions
if hasattr(config, 'parameters') and 'discontinuation' in config.parameters:
    disc_params = config.parameters['discontinuation']
    disc_params['planned_discontinue_prob'] = 0.5  # 50% chance
    disc_params['admin_discontinue_prob'] = 0.3    # 30% chance

print("Running simulation with higher discontinuation rates...")
sim = TreatAndExtendABS(config)
patient_histories = sim.run()

print(f"\nSimulation complete with {len(patient_histories)} patients")

# Check a patient with visits
patient_id = list(patient_histories.keys())[0]
visits = patient_histories[patient_id]

print(f"\n=== Patient {patient_id} Visit Details ===")
for i, visit in enumerate(visits):
    print(f"\nVisit {i}:")
    print(f"  Date: {visit.get('date')}")
    print(f"  Phase: {visit.get('phase')}")
    print(f"  Type: {visit.get('type')}")
    print(f"  Actions: {visit.get('actions')}")
    
    # Look for treatment status
    if 'treatment_status' in visit:
        status = visit['treatment_status']
        print(f"  Treatment Status: {status}")
    
    # Look for discontinuation info
    if 'discontinuation' in visit:
        disc = visit['discontinuation']
        print(f"  Discontinuation: {disc}")
    
    # Look for any other state info
    state_keys = [k for k in visit.keys() if 'state' in k.lower() or 'status' in k.lower()]
    if state_keys:
        print(f"  State-related keys: {state_keys}")

# Check simulation statistics
print("\n=== Simulation Statistics ===")
if hasattr(sim, 'stats'):
    print(f"Discontinuation stats: {sim.stats.get('discontinuations', {})}")
    print(f"Retreatment stats: {sim.stats.get('retreatments', {})}")

# Check patient objects directly if accessible
if hasattr(sim, 'patients'):
    print("\n=== Direct Patient State Check ===")
    for pid, patient in list(sim.patients.items())[:2]:  # Check first 2 patients
        print(f"\nPatient {pid}:")
        if hasattr(patient, 'state'):
            state = patient.state
            if isinstance(state, dict):
                print(f"  Current status: {state.get('treatment_status', 'Unknown')}")
                print(f"  Visit history length: {len(state.get('visit_history', []))}")
                
                # Check last few visits for state transitions
                visit_history = state.get('visit_history', [])
                if visit_history:
                    print("  Last 3 visits:")
                    for visit in visit_history[-3:]:
                        print(f"    - {visit.get('date')}: {visit.get('treatment_status', {})}")