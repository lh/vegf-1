"""
Patient Generator with Discontinuation Ready State

This module provides functionality to initialize patients in a state that's ready
for discontinuation, making it easier to verify and debug the discontinuation system.
It works by monkey-patching the patient generation methods in both ABS and DES simulations.

Usage
-----
Import this module before running your simulation to activate the patching:

```python
import discontinuation_ready_patients

# Now run your simulation as normal
from treat_and_extend_abs import run_treat_and_extend_abs
results = run_treat_and_extend_abs()
```
"""

import random
from datetime import datetime, timedelta
import numpy as np
from functools import wraps

# Try to import simulation classes - handle gracefully if not available
try:
    from treat_and_extend_abs import TreatAndExtendABS, Patient
    from treat_and_extend_des import TreatAndExtendDES
    from simulation.base import Event
    abs_imported = True
except ImportError:
    abs_imported = False
    print("Warning: Could not import simulation classes. Patching will not be applied.")

# Global settings
DISCONTINUATION_READY_PERCENT = 0.5  # Make 50% of patients ready for discontinuation
VERBOSE = True

def log(message):
    """Print a log message if verbose mode is enabled."""
    if VERBOSE:
        print(f"[DiscontinuationPatched] {message}")

def make_patient_discontinuation_ready(patient):
    """
    Modify a patient object to be ready for discontinuation evaluation.
    This sets the necessary state that would meet the criteria for discontinuation.
    
    Parameters
    ----------
    patient : Patient
        The patient object to modify
    
    Returns
    -------
    Patient
        The modified patient object
    """
    if hasattr(patient, 'disease_activity'):
        # Set disease activity to stable with 3+ consecutive stable visits
        patient.disease_activity["fluid_detected"] = False
        patient.disease_activity["consecutive_stable_visits"] = 3
        patient.disease_activity["max_interval_reached"] = True
        patient.disease_activity["current_interval"] = 16
        
        # Set the patient's phase to maintenance
        patient.current_phase = "maintenance"
        
        # Set adequate treatments in phase
        patient.treatments_in_phase = 5
        
        # Set next visit interval to max
        patient.next_visit_interval = 16
        
        log(f"Modified patient {patient.patient_id if hasattr(patient, 'patient_id') else 'unknown'} to be ready for discontinuation")
    
    return patient

def make_des_patient_discontinuation_ready(patient_dict):
    """
    Modify a DES patient dictionary to be ready for discontinuation evaluation.
    
    Parameters
    ----------
    patient_dict : dict
        The patient dictionary to modify
    
    Returns
    -------
    dict
        The modified patient dictionary
    """
    # Set disease activity to stable with 3+ consecutive stable visits
    patient_dict["disease_activity"]["fluid_detected"] = False
    patient_dict["disease_activity"]["consecutive_stable_visits"] = 3
    patient_dict["disease_activity"]["max_interval_reached"] = True
    patient_dict["disease_activity"]["current_interval"] = 16
    
    # Set the patient's phase to maintenance
    patient_dict["current_phase"] = "maintenance"
    
    # Set adequate treatments in phase
    patient_dict["treatments_in_phase"] = 5
    
    # Set next visit interval to max
    patient_dict["next_visit_interval"] = 16
    
    log(f"Modified DES patient {patient_dict.get('id', 'unknown')} to be ready for discontinuation")
    
    return patient_dict

# Patch for ABS Patient Generation
if abs_imported:
    # Store original methods to call later
    original_abs_generate_patients = TreatAndExtendABS.generate_patients
    
    @wraps(TreatAndExtendABS.generate_patients)
    def patched_abs_generate_patients(self):
        """
        Patched version of ABS patient generation that makes some patients 
        ready for discontinuation evaluation.
        """
        log("Patching ABS patient generation")
        
        # Call original method to generate patients normally
        original_abs_generate_patients(self)
        
        # Now modify some patients to be discontinuation-ready
        for patient_id, patient in self.agents.items():
            if random.random() < DISCONTINUATION_READY_PERCENT:
                # Make this patient ready for discontinuation
                make_patient_discontinuation_ready(patient)
    
    # Apply monkey patch
    TreatAndExtendABS.generate_patients = patched_abs_generate_patients
    log("ABS patient generation successfully patched")

    # Patch DES Patient Generation
    original_des_generate_patients = TreatAndExtendDES._generate_patients
    
    @wraps(TreatAndExtendDES._generate_patients)
    def patched_des_generate_patients(self):
        """
        Patched version of DES patient generation that makes some patients
        ready for discontinuation evaluation.
        """
        log("Patching DES patient generation")
        
        # Call original method to generate patients normally
        original_des_generate_patients(self)
        
        # Now modify some patients to be discontinuation-ready and schedule visits
        for patient_id, patient in list(self.patients.items()):
            if random.random() < DISCONTINUATION_READY_PERCENT:
                # Make this patient ready for discontinuation
                make_des_patient_discontinuation_ready(patient)
                
                # Schedule a visit for this patient to ensure they're evaluated soon
                self.events.append({
                    "time": self.start_date + timedelta(days=1),  # Very soon
                    "type": "visit",
                    "patient_id": patient_id,
                    "actions": ["vision_test", "oct_scan", "injection"],
                    "priority": 1
                })
    
    # Apply monkey patch
    TreatAndExtendDES._generate_patients = patched_des_generate_patients
    log("DES patient generation successfully patched")

# Set global configuration variables for testing
def configure(discontinuation_ready_percent=0.5, verbose=True, prevent_multiple_discontinuations=True):
    """
    Configure the patching behavior.
    
    Parameters
    ----------
    discontinuation_ready_percent : float, optional
        Percentage of patients to make ready for discontinuation, by default 0.5
    verbose : bool, optional
        Whether to print verbose log messages, by default True
    prevent_multiple_discontinuations : bool, optional
        Whether to modify the discontinuation manager to prevent the same patient from being 
        discontinued multiple times, by default True
    """
    global DISCONTINUATION_READY_PERCENT, VERBOSE
    DISCONTINUATION_READY_PERCENT = discontinuation_ready_percent
    VERBOSE = verbose
    log(f"Configuration updated: {discontinuation_ready_percent*100}% discontinuation-ready, verbose={verbose}")
    
    # Add option to prevent multiple discontinuations for the same patient
    if prevent_multiple_discontinuations and abs_imported:
        try:
            from simulation.enhanced_discontinuation_manager import EnhancedDiscontinuationManager
            
            # Store the original evaluate_discontinuation method
            original_evaluate_discontinuation = EnhancedDiscontinuationManager.evaluate_discontinuation
            
            # Map from patient_id to whether they've been discontinued
            discontinued_patients = {}
            
            @wraps(EnhancedDiscontinuationManager.evaluate_discontinuation)
            def patched_evaluate_discontinuation(self, patient_state, current_time, clinician_id=None, treatment_start_time=None, clinician=None):
                """Patched version that prevents multiple discontinuations for the same patient"""
                # Extract patient ID from state if available
                patient_id = None
                
                # Try to find a patient ID somewhere in the patient state
                if hasattr(patient_state, 'patient_id'):
                    patient_id = patient_state.patient_id
                elif hasattr(patient_state, 'id'):
                    patient_id = patient_state.id
                elif isinstance(patient_state, dict):
                    # Look in common fields where ID might be stored
                    for field in ['patient_id', 'id']:
                        if field in patient_state:
                            patient_id = patient_state[field]
                            break
                
                # If we have a patient ID and they've already been discontinued, prevent another discontinuation
                if patient_id is not None and patient_id in discontinued_patients:
                    if discontinued_patients[patient_id]:
                        return False, "", 0.0, ""
                
                # Call the original method
                should_discontinue, reason, probability, cessation_type = original_evaluate_discontinuation(
                    self, patient_state, current_time, clinician_id, treatment_start_time, clinician
                )
                
                # If this patient is being discontinued, record it
                if should_discontinue and patient_id is not None:
                    discontinued_patients[patient_id] = True
                    log(f"Patient {patient_id} discontinued with reason: {reason}")
                
                return should_discontinue, reason, probability, cessation_type
            
            # Apply the patch
            EnhancedDiscontinuationManager.evaluate_discontinuation = patched_evaluate_discontinuation
            log("Patched EnhancedDiscontinuationManager to prevent multiple discontinuations for the same patient")
            
        except ImportError:
            log("Could not patch EnhancedDiscontinuationManager - prevent_multiple_discontinuations will not work")

# Print initialization message
if abs_imported:
    log("Discontinuation patient patching initialized. Import this module before running simulations to ensure some patients are ready for discontinuation.")
else:
    print("Warning: Discontinuation patient patching could not be initialized due to missing imports.")