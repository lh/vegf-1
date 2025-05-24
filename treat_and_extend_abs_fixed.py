"""
Fixed Treat-and-extend protocol implementation for Agent-Based Simulation (ABS).

This module provides a corrected implementation of treat_and_extend_abs.py that
properly handles discontinuation statistics by using the refactored discontinuation
manager. Key improvements include:
- Clear separation of concerns for discontinuation logic
- Proper handling of discontinuation statistics
- Prevention of double-counting discontinuations
- Tracking of unique patient discontinuations

To use this fixed version, simply import from treat_and_extend_abs_fixed instead of
treat_and_extend_abs.
"""

# Import all the standard imports from the original file
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from simulation.config import SimulationConfig
from simulation.base import BaseSimulation, Event, SimulationClock
from simulation.clinical_model import ClinicalModel, DiseaseState
from simulation.scheduler import ClinicScheduler
from simulation.vision_models import RealisticVisionModel, create_vision_model
from simulation.clinician import Clinician, ClinicianManager

# Import the original classes for extension
from treat_and_extend_abs import Patient, TreatAndExtendABS as OriginalTreatAndExtendABS
from simulation.refactored_discontinuation_manager import (
    RefactoredDiscontinuationManager, 
    CompatibilityDiscontinuationManager,
    DiscontinuationDecision,
    RetreatmentDecision
)

class TreatAndExtendABS(OriginalTreatAndExtendABS):
    """
    Fixed implementation of the Treat-and-extend protocol for Agent-Based Simulation.
    
    This class extends the original implementation to use the refactored
    discontinuation manager, ensuring proper handling of discontinuation statistics.
    """
    
    def __init__(self, config, start_date=None):
        """
        Initialize the simulation with the specified configuration.
        
        Parameters
        ----------
        config : SimulationConfig or str
            Simulation configuration or name of configuration file
        start_date : datetime, optional
            Start date for the simulation, by default None (uses config start_date)
        """
        # Load configuration if string is provided
        if isinstance(config, str):
            self.config = SimulationConfig.from_yaml(config)
        else:
            self.config = config
        
        # Initialize components
        self.agents = {}
        self.clinical_model = ClinicalModel(self.config)
        
        # Set start and end dates
        if start_date is None:
            self.start_date = datetime.strptime(self.config.start_date, "%Y-%m-%d") if isinstance(self.config.start_date, str) else self.config.start_date
        else:
            self.start_date = start_date
            
        self.end_date = self.start_date + timedelta(days=self.config.duration_days)
        
        # Use the new RealisticVisionModel instead of SimplifiedVisionModel
        # Or use the factory function to allow configuration-based model selection
        vision_model_type = self.config.parameters.get('vision_model_type', 'realistic')
        if vision_model_type == 'simplified':
            self.vision_model = create_vision_model('simplified', self.config)
        else:
            self.vision_model = create_vision_model('realistic', self.config)
        
        # Initialize clinician manager
        clinician_config = self.config.parameters.get("clinicians", {})
        clinician_enabled = clinician_config.get("enabled", False)
        self.clinician_manager = ClinicianManager(self.config.parameters, enabled=clinician_enabled)
        
        # Initialize scheduler and clock
        self.scheduler = ClinicScheduler(
            daily_capacity=20,
            days_per_week=5
        )
        self.clock = SimulationClock(self.start_date)
        self.clock.end_date = self.end_date
        
        # Initialize the refactored discontinuation manager
        self._initialize_discontinuation_manager()
        
        # Statistics
        self.stats = {
            "total_visits": 0,
            "total_injections": 0,
            "total_oct_scans": 0,
            "vision_improvements": 0,
            "vision_declines": 0,
            "protocol_completions": 0,
            "protocol_discontinuations": 0,  # Will be unique patient count
            "unique_discontinuations": 0,    # Explicitly track unique patients
            "monitoring_visits": 0,
            "retreatments": 0,               # Will be unique patient count
            "unique_retreatments": 0,        # Explicitly track unique patients
            "clinician_decisions": {
                "protocol_followed": 0,
                "protocol_overridden": 0
            }
        }
        
        # Track unique patients for discontinuation and retreatment
        self.discontinued_patients = set()
        self.retreated_patients = set()
    
    def _initialize_discontinuation_manager(self):
        """
        Initialize the refactored discontinuation manager.
        
        Uses the same configuration logic as the original but creates
        a RefactoredDiscontinuationManager instead.
        """
        # Get the parameter file path from the config
        discontinuation_config = self.config.parameters.get("discontinuation", {})
        parameter_file = discontinuation_config.get("parameter_file", "")
        
        # Create a proper discontinuation config dictionary
        config_dict = {"discontinuation": {}}
        
        if parameter_file:
            try:
                # Directly load the discontinuation parameters from the file
                with open(parameter_file, 'r') as f:
                    import yaml
                    discontinuation_params = yaml.safe_load(f)
                    config_dict = discontinuation_params
            except Exception as e:
                print(f"Error loading discontinuation parameters: {str(e)}")
                # Fall back to empty dict with enabled=True
                config_dict = {"discontinuation": {"enabled": True}}
        else:
            # If no parameter file specified, use the discontinuation config from the parameters
            discontinuation_params = self.config.get_treatment_discontinuation_params()
            
            # Ensure enabled flag is present and set to True
            if "enabled" not in discontinuation_params:
                discontinuation_params["enabled"] = True
            else:
                discontinuation_params["enabled"] = True
                
            config_dict = {"discontinuation": discontinuation_params}
        
        # Try to use the enhanced discontinuation manager if available
        try:
            from simulation.enhanced_discontinuation_manager import EnhancedDiscontinuationManager
            print("Using EnhancedDiscontinuationManager which supports premature discontinuations")
            self.discontinuation_manager = EnhancedDiscontinuationManager(config_dict)
        except ImportError:
            # Fall back to the compatibility wrapper if enhanced manager not available
            print("EnhancedDiscontinuationManager not found, using compatibility wrapper")
            self.discontinuation_manager = CompatibilityDiscontinuationManager(config_dict)
        
        # Store a direct reference to the manager as well
        self.refactored_manager = self.discontinuation_manager
    
    def process_event(self, event):
        """
        Process a simulation event with proper discontinuation handling.
        
        Parameters
        ----------
        event : Event
            Event to process
        """
        if event.event_type == "visit":
            patient_id = event.patient_id
            if patient_id not in self.agents:
                return
                
            patient = self.agents[patient_id]
            
            # Update statistics
            self.stats["total_visits"] += 1
            if "injection" in event.data["actions"]:
                self.stats["total_injections"] += 1
            if "oct_scan" in event.data["actions"]:
                self.stats["total_oct_scans"] += 1
            
            # Get the assigned clinician for this visit
            clinician_id = self.clinician_manager.assign_clinician(patient_id, event.time)
            clinician = self.clinician_manager.get_clinician(clinician_id)
            event.data["clinician_id"] = clinician_id  # Store for reference
            
            # Check if this is a monitoring visit for a discontinued patient
            is_monitoring = event.data.get("is_monitoring", False)
            
            if is_monitoring:
                self.stats["monitoring_visits"] += 1
                
                # First, update the fluid_detected status based on OCT scan
                if "oct_scan" in event.data["actions"]:
                    # Create state dictionary for vision model
                    state = {
                        "patient_id": patient_id,
                        "fluid_detected": patient.disease_activity["fluid_detected"],
                        "treatments_in_phase": 0,  # Not in treatment phase
                        "interval": 0,  # Not relevant for monitoring visits
                        "current_vision": patient.current_vision,
                    }
                    
                    # Use vision model to determine fluid status
                    # Use 0 for vision change as we're only interested in fluid detection
                    _, fluid_detected = self.vision_model.calculate_vision_change(
                        state=state,
                        actions=event.data["actions"],
                        phase="monitoring"
                    )
                    
                    # Update patient's disease activity with new fluid status
                    patient.disease_activity["fluid_detected"] = fluid_detected
                
                # Process monitoring visit
                # Convert Patient object to dictionary for discontinuation manager
                patient_state = {
                    "id": patient_id,  # Include patient ID for proper tracking
                    "disease_activity": patient.disease_activity,
                    "treatment_status": patient.treatment_status,
                    "disease_characteristics": patient.disease_characteristics
                }
                
                # Evaluate retreatment using refactored manager (gets decision only)
                result = self.refactored_manager.evaluate_retreatment(
                    patient_state=patient_state,
                    patient_id=patient_id,
                    clinician=clinician
                )
                
                # Handle different return types
                if isinstance(result, tuple) and len(result) >= 2:
                    should_retreat, probability = result
                elif hasattr(result, 'should_retreat'):
                    # RetreatmentDecision object
                    should_retreat = result.should_retreat
                    probability = result.probability
                else:
                    # Unexpected return type, default to no retreatment
                    print(f"Unexpected return type from evaluate_retreatment: {type(result)}")
                    should_retreat = False
                    probability = 0.0
                
                # Record monitoring visit
                visit_record = {
                    'date': event.time,
                    'type': 'monitoring_visit',
                    'actions': event.data["actions"],
                    'baseline_vision': patient.baseline_vision,
                    'vision': patient.current_vision,
                    'disease_state': 'active' if patient.disease_activity["fluid_detected"] else 'stable',
                    'phase': 'monitoring',
                    'interval': None,
                    'clinician_id': clinician_id,
                    'fluid_detected': patient.disease_activity["fluid_detected"]  # Add explicit fluid status
                }
                patient.history.append(visit_record)
                
                # If retreatment is recommended, restart treatment
                if should_retreat:
                    # Only increment stats if this is a new retreatment for this patient
                    if patient_id not in self.retreated_patients:
                        self.stats["retreatments"] += 1
                        self.stats["unique_retreatments"] += 1
                        self.retreated_patients.add(patient_id)
                    else:
                        # Still increment retreatment but not unique count
                        self.stats["retreatments"] += 1
                    
                    # Update patient state
                    patient.treatment_status["active"] = True
                    patient.treatment_status["recurrence_detected"] = True
                    patient.current_phase = "loading"  # Restart with loading phase
                    patient.treatments_in_phase = 0
                    patient.next_visit_interval = 4  # Initial loading phase interval
                    patient.disease_activity["current_interval"] = 4
                    
                    # Register the retreatment with the manager
                    self.refactored_manager.register_retreatment(patient_id)
                    
                    # Schedule next treatment visit
                    next_visit = self.schedule_next_visit(patient_id, event.time)
                    if next_visit:
                        self.clock.schedule_event(next_visit)
                
                return
            
            # Process regular visit
            visit_data = patient.process_visit(
                event.time,
                event.data["actions"],
                self.vision_model
            )
            
            # Update vision statistics
            if patient.current_vision > patient.history[-1]["baseline_vision"]:
                self.stats["vision_improvements"] += 1
            elif patient.current_vision < patient.history[-1]["baseline_vision"]:
                self.stats["vision_declines"] += 1
            
            # Check if loading phase was completed
            if patient.current_phase == "maintenance" and patient.treatments_in_phase == 0:
                self.stats["protocol_completions"] += 1
            
            # Check if patient is in maintenance phase and at max interval
            if (patient.current_phase == "maintenance" and 
                patient.disease_activity["max_interval_reached"] and
                patient.disease_activity["consecutive_stable_visits"] >= 3):
                
                # Use discontinuation manager to evaluate discontinuation
                # Convert Patient object to dictionary for discontinuation manager
                patient_state = {
                    "id": patient_id,  # Include patient ID for proper tracking
                    "disease_activity": patient.disease_activity,
                    "treatment_status": patient.treatment_status,
                    "disease_characteristics": patient.disease_characteristics
                }
                
                # Get a single discontinuation decision (no longer calling evaluate twice)
                result = self.refactored_manager.evaluate_discontinuation(
                    patient_state=patient_state,
                    current_time=event.time,
                    patient_id=patient_id,
                    clinician_id=clinician_id,
                    treatment_start_time=patient.treatment_start,
                    clinician=clinician
                )
                
                # Handle different return types (compatibility layer returns tuple)
                if isinstance(result, tuple) and len(result) >= 4:
                    should_discontinue, reason, probability, cessation_type = result
                elif hasattr(result, 'should_discontinue'):
                    # DiscontinuationDecision object
                    should_discontinue = result.should_discontinue
                    reason = result.reason
                    probability = result.probability 
                    cessation_type = result.cessation_type
                else:
                    # Unexpected return type, default to no discontinuation
                    print(f"Unexpected return type from evaluate_discontinuation: {type(result)}")
                    should_discontinue = False
                    reason = ""
                    probability = 0.0
                    cessation_type = ""
                
                # Process the decision
                if should_discontinue:
                    # Update patient state
                    patient.treatment_status["active"] = False
                    patient.treatment_status["discontinuation_date"] = event.time
                    patient.treatment_status["discontinuation_reason"] = reason
                    patient.treatment_status["cessation_type"] = cessation_type
                    
                    # Mark the most recent visit record as a discontinuation visit
                    if patient.history and len(patient.history) > 0:
                        latest_visit = patient.history[-1]
                        latest_visit['is_discontinuation_visit'] = True
                        latest_visit['discontinuation_type'] = cessation_type
                    
                    # Only increment stats if this is a new discontinuation for this patient
                    if patient_id not in self.discontinued_patients:
                        self.stats["protocol_discontinuations"] += 1
                        self.stats["unique_discontinuations"] += 1
                        self.discontinued_patients.add(patient_id)
                    else:
                        # Do not increment stats for re-discontinuations
                        print(f"Patient {patient_id} already discontinued previously")
                    
                    # Apply vision changes specific to this type of discontinuation
                    # Convert Patient object to dictionary for discontinuation manager
                    patient_state = {
                        "disease_activity": patient.disease_activity,
                        "treatment_status": patient.treatment_status,
                        "disease_characteristics": patient.disease_characteristics,
                        "vision": {
                            "current_va": patient.current_vision
                        }
                    }
                    
                    # Apply vision changes based on cessation type
                    # Try to use the enhanced manager if available
                    if hasattr(self.discontinuation_manager, 'apply_vision_changes_after_discontinuation'):
                        updated_patient_state = self.discontinuation_manager.apply_vision_changes_after_discontinuation(
                            patient_state=patient_state,
                            cessation_type=cessation_type
                        )
                        
                        # Update patient with any vision changes
                        if "vision" in updated_patient_state and "current_va" in updated_patient_state["vision"]:
                            patient.current_vision = updated_patient_state["vision"]["current_va"]
                    
                    # Register the discontinuation with the refactored manager
                    self.refactored_manager.register_discontinuation(
                        patient_id, 
                        cessation_type
                    )
                    
                    # Schedule monitoring visits
                    monitoring_events = self.refactored_manager.schedule_monitoring(
                        event.time, 
                        cessation_type=cessation_type,
                        clinician=clinician,
                        patient_id=patient_id  # Pass patient ID for tracking
                    )
                    
                    for monitoring_event in monitoring_events:
                        if monitoring_event["time"] <= self.end_date:
                            self.clock.schedule_event(Event(
                                time=monitoring_event["time"],
                                event_type="visit",
                                patient_id=patient_id,
                                data={
                                    "visit_type": "monitoring_visit",
                                    "actions": monitoring_event["actions"],
                                    "is_monitoring": True,
                                    "cessation_type": monitoring_event.get("cessation_type")
                                },
                                priority=1
                            ))
                    
                    return  # No more regular visits
            
            # Check if treatment was already discontinued
            if not patient.treatment_status["active"] and patient.treatment_status["discontinuation_date"] is None:
                patient.treatment_status["discontinuation_date"] = event.time
                
                # Mark the most recent visit record as a discontinuation visit (likely administrative discontinuation)
                if patient.history and len(patient.history) > 0:
                    latest_visit = patient.history[-1]
                    latest_visit['is_discontinuation_visit'] = True
                    latest_visit['discontinuation_type'] = "administrative"  # Default to administrative reason
                
                # Only increment stats if this is a new discontinuation for this patient
                if patient_id not in self.discontinued_patients:
                    self.stats["protocol_discontinuations"] += 1
                    self.stats["unique_discontinuations"] += 1
                    self.discontinued_patients.add(patient_id)
                
                return  # No more visits
            
            # Schedule next visit
            next_visit = self.schedule_next_visit(patient_id, event.time)
            if next_visit:
                self.clock.schedule_event(next_visit)
    
    def _print_statistics(self):
        """
        Print simulation statistics with accurate discontinuation counts.
        """
        print("\nSimulation Statistics:")
        print("-" * 20)
        
        # Print basic stats
        formatted_stats = {}
        for stat, value in self.stats.items():
            # Special handling for nested dictionary
            if isinstance(value, dict):
                print(f"{stat}: {value}")
            else:
                formatted_stats[stat] = value
                print(f"{stat}: {value}")
        
        # Add discontinuation manager statistics
        discontinuation_stats = self.refactored_manager.get_statistics()
        print("\nDiscontinuation Statistics:")
        print("-" * 20)
        
        # Ensure unique counts are correct
        unique_discontinued = len(self.discontinued_patients)
        unique_retreated = len(self.retreated_patients)
        
        # Print actual stats
        print(f"unique_discontinued_patients: {unique_discontinued}")
        print(f"unique_retreated_patients: {unique_retreated}")
        
        # If there's a discrepancy, show warning
        dm_unique = discontinuation_stats.get("unique_discontinued_patients", 0)
        if dm_unique != unique_discontinued:
            print(f"WARNING: Discrepancy in unique discontinued patients: simulation={unique_discontinued}, manager={dm_unique}")
        
        # Print other stats
        for stat, value in discontinuation_stats.items():
            if stat not in ["unique_discontinued_patients", "unique_retreated_patients"]:
                print(f"{stat}: {value}")
        
        # Calculate discontinuation rate
        total_patients = len(self.agents)
        disc_rate = unique_discontinued / total_patients if total_patients > 0 else 0
        print(f"Discontinuation rate: {disc_rate:.2%} ({unique_discontinued}/{total_patients} patients)")
        
        # Print patient summary
        print("\nPatient Summary:")
        print("-" * 20)
        total_patients = len(self.agents)
        total_visits = sum(len(agent.history) for agent in self.agents.values())
        avg_visits = total_visits / max(1, total_patients)
        print(f"Total Patients: {total_patients}")
        print(f"Total Visits: {total_visits}")
        print(f"Average Visits per Patient: {avg_visits:.1f}")
        
        # Calculate loading phase completion rate
        loading_completions = self.stats["protocol_completions"]
        loading_completion_rate = (loading_completions / max(1, total_patients)) * 100
        print(f"Loading Phase Completion Rate: {loading_completion_rate:.1f}%")
        
        # Calculate maintenance phase injection rate
        maintenance_visits = 0
        maintenance_injections = 0
        for agent in self.agents.values():
            for visit in agent.history:
                if visit["phase"] == "maintenance":
                    maintenance_visits += 1
                    if "injection" in visit["actions"]:
                        maintenance_injections += 1
        
        if maintenance_visits > 0:
            maintenance_injection_rate = (maintenance_injections / maintenance_visits) * 100
            print(f"Maintenance Phase Injection Rate: {maintenance_injection_rate:.1f}%")
        
        # Sample a few patients to check their visit patterns
        sample_patients = np.random.choice(list(self.agents.keys()), min(3, len(self.agents)))
        
        for patient_id in sample_patients:
            patient = self.agents[patient_id]
            patient_data = patient.history
            
            print(f"\nPatient {patient_id} visits:")
            for visit in patient_data:
                print(f"  {visit['date']} - Phase: {visit['phase']} - Actions: {visit['actions']}")

def run_treat_and_extend_abs(config=None, verbose=False):
    """
    Run an ABS simulation with the fixed treat-and-extend protocol.
    
    Parameters
    ----------
    config : SimulationConfig or str, optional
        Simulation configuration or name of configuration file, by default None
    verbose : bool, optional
        Whether to print verbose output, by default False
        
    Returns
    -------
    dict
        Dictionary mapping patient IDs to their visit histories
    """
    # Create and run simulation using the fixed implementation
    config_name = config
    if isinstance(config, SimulationConfig) and hasattr(config, 'config_name'):
        config_name = config.config_name
    
    if config_name is None:
        config_name = "eylea_literature_based"
    
    print(f"Running fixed ABS simulation with config: {config_name}")
    sim = TreatAndExtendABS(config_name)
    patient_histories = sim.run()
    
    # Convert patient histories to DataFrame for analysis
    all_data = []
    for patient_id, visits in patient_histories.items():
        for visit in visits:
            # Extract key data from visit
            visit_data = {
                'patient_id': patient_id,
                'date': visit.get('date', ''),
                'vision': visit.get('vision', None),
                'baseline_vision': visit.get('baseline_vision', None),
                'phase': visit.get('phase', ''),
                'type': visit.get('type', ''),
                'actions': str(visit.get('actions', [])),
                'disease_state': str(visit.get('disease_state', '')),
                'interval': visit.get('interval', None)
            }
            all_data.append(visit_data)
    
    # Create DataFrame
    df = pd.DataFrame(all_data)
    
    # Save all data to CSV
    df.to_csv('treat_and_extend_abs_fixed_data.csv', index=False)
    print(f"Saved data for {len(patient_histories)} patients to treat_and_extend_abs_fixed_data.csv")
    
    # Print final stats summary
    total_patients = sim.stats.get("total_patients", len(sim.agents))
    unique_discontinuations = sim.stats.get("unique_discontinuations", 0)
    disc_rate = unique_discontinuations / total_patients if total_patients > 0 else 0
    
    print("\nFinal Statistics Summary:")
    print(f"Total Patients: {total_patients}")
    print(f"Unique Discontinued Patients: {unique_discontinuations}")
    print(f"Discontinuation Rate: {disc_rate:.2%}")
    
    return patient_histories

if __name__ == "__main__":
    run_treat_and_extend_abs(verbose=True)