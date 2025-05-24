"""
Simple check to see if vision is being recorded properly
"""
import sys
import os
sys.path.append(os.getcwd())

# Test 1: Check if Patient has vision attributes
from simulation.patient_state import PatientState

print("=== Testing PatientState ===")
patient = PatientState(patient_id="test_001")
print(f"Has current_vision? {hasattr(patient, 'current_vision')}")
print(f"Has baseline_vision? {hasattr(patient, 'baseline_vision')}")

if hasattr(patient, 'current_vision'):
    print(f"Current vision value: {patient.current_vision}")
if hasattr(patient, 'baseline_vision'):
    print(f"Baseline vision value: {patient.baseline_vision}")

# Check if __init__ sets these values
import inspect
print("\nPatientState __init__ signature:")
print(inspect.getsource(patient.__init__))

# Test 2: Check what fields are in a visit record
print("\n=== Sample Visit Record ===")
sample_visit = {
    'time': 0,
    'patient_id': 'test_001',
    'phase': 'loading',
    'treatment_status': {'active': True},
    'baseline_vision': 70,
    'vision': 70,
    'actions': ['injection']
}
print(f"Sample visit keys: {list(sample_visit.keys())}")
print(f"Vision field present: {'vision' in sample_visit}")
print(f"Vision value: {sample_visit.get('vision')}")