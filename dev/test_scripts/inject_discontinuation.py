
# Import the necessary classes first
from treat_and_extend_abs import TreatAndExtendABS
import sys

# Create a simpler version of our monkey patching
print("Applying monkey patch to patient generation...")

# Original method will be accessed within the modified_patient_generator
# We don't need to save it separately

# Create a simple patched Patient class
# This solves the issue with modifying the Patient object attributes
class PatchedPatient:
    def __init__(self, patient_id, make_discontinuation_ready=False):
        self.patient_id = patient_id
        self.current_vision = 65.0
        self.baseline_vision = 65.0
        
        if make_discontinuation_ready:
            # Set up for discontinuation
            self.current_phase = "maintenance"
            self.treatments_in_phase = 5
            self.next_visit_interval = 16
            self.disease_activity = {
                "fluid_detected": False,  # Stable disease
                "consecutive_stable_visits": 3,  # Already had 3 stable visits
                "max_interval_reached": True,  # Reached max interval
                "current_interval": 16  # At max interval
            }
        else:
            # Normal setup
            self.current_phase = "loading"
            self.treatments_in_phase = 0
            self.next_visit_interval = 4
            self.disease_activity = {
                "fluid_detected": True,  # Start with fluid detected (active disease)
                "consecutive_stable_visits": 0,
                "max_interval_reached": False,
                "current_interval": 4  # Start with loading phase interval
            }
            
        self.treatment_status = {
            "active": True,
            "recurrence_detected": False,
            "weeks_since_discontinuation": 0,
            "cessation_type": None
        }
        self.disease_characteristics = {
            "has_PED": False
        }
        self.history = []

# Define a replacement method
def patched_generate_patients(self):
    """
    Generate patients ready for discontinuation.
    """
    print("⚠️ USING PATCHED PATIENT GENERATOR - Creating discontinuation-ready patients")
    
    # Create patients with fixed settings for reproducibility
    num_patients = self.config.num_patients
    print(f"Generating {num_patients} patients...")
    
    # Calculate how many patients should be ready for discontinuation
    discontinuation_ready_count = int(num_patients * 0.5)  # 50% ready for discontinuation
    
    # Generate patients
    for i in range(1, num_patients + 1):
        patient_id = f"PATIENT{i:03d}"
        
        # Decide if this patient should be ready for discontinuation
        make_ready = i <= discontinuation_ready_count
        
        # Create patient with the appropriate state
        patient = PatchedPatient(patient_id, make_discontinuation_ready=make_ready)
        
        # Store in simulation
        self.agents[patient_id] = patient
        
        # Schedule initial visit (use index to space them out)
        from datetime import timedelta
        initial_visit_time = self.start_date + timedelta(hours=i*2)
        
        # Import Event class
        from simulation.base import Event
        
        # Create the event
        event = Event(
            time=initial_visit_time,
            event_type="visit",
            patient_id=patient_id,
            data={
                "visit_type": "injection_visit",
                "actions": ["vision_test", "oct_scan", "injection"],
                "decisions": ["nurse_vision_check", "doctor_treatment_decision"]
            },
            priority=1
        )
        
        # Schedule event using the simulation's clock
        self.clock.schedule_event(event)
    
    print(f"Created {discontinuation_ready_count} patients ready for discontinuation out of {num_patients} total patients")

# Apply the patch
TreatAndExtendABS.generate_patients = patched_generate_patients
print("⚠️ PATCHED: Modified patient generation to create patients ready for discontinuation")
