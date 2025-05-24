"""
Fixed Treat-and-extend protocol implementation for Discrete Event Simulation (DES).

This module provides a corrected implementation of treat_and_extend_des.py that
properly handles discontinuation statistics by using the refactored discontinuation
manager. Key improvements include:
- Clear separation of concerns for discontinuation logic
- Proper handling of discontinuation statistics
- Prevention of double-counting discontinuations
- Tracking of unique patient discontinuations

To use this fixed version, simply import from treat_and_extend_des_fixed instead of
treat_and_extend_des.
"""

from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import logging
from simulation.config import SimulationConfig
from simulation import DiscreteEventSimulation, Event
from simulation.patient_state import PatientState
from simulation.clinical_model import ClinicalModel
from simulation.scheduler import ClinicScheduler
from simulation.vision_models import RealisticVisionModel, create_vision_model
from simulation.clinician import Clinician, ClinicianManager

# Import the refactored discontinuation manager
from simulation.refactored_discontinuation_manager import (
    RefactoredDiscontinuationManager, 
    CompatibilityDiscontinuationManager,
    DiscontinuationDecision,
    RetreatmentDecision
)

# Set up logger
logger = logging.getLogger(__name__)

class TreatAndExtendDES:
    """
    Fixed implementation of the Treat-and-extend protocol for Discrete Event Simulation.
    
    This class implements the treat-and-extend protocol according to the
    Veeramani pathway diagram, ensuring that patients receive injections
    at every visit, with proper discontinuation handling.
    """
    
    def __init__(self, config=None):
        """
        Initialize the simulation with the specified configuration.
        
        Parameters
        ----------
        config : str or SimulationConfig, optional
            Configuration name or object, by default None (uses "eylea_literature_based")
        """
        # Handle different types of config parameter
        if config is None:
            self.config = SimulationConfig.from_yaml("eylea_literature_based")
        elif isinstance(config, str):
            self.config = SimulationConfig.from_yaml(config)
        else:
            self.config = config
            
        self.start_date = datetime.strptime(self.config.start_date, "%Y-%m-%d") if isinstance(self.config.start_date, str) else self.config.start_date
        self.end_date = self.start_date + timedelta(days=self.config.duration_days)
        
        # Initialize components
        self.scheduler = ClinicScheduler(
            daily_capacity=20,
            days_per_week=5
        )
        
        # Initialize vision model
        vision_model_type = self.config.parameters.get('vision_model_type', 'realistic')
        if vision_model_type == 'simplified':
            self.vision_model = create_vision_model('simplified', self.config)
        else:
            self.vision_model = create_vision_model('realistic', self.config)
        
        # Initialize clinician manager
        clinician_config = self.config.parameters.get("clinicians", {})
        clinician_enabled = clinician_config.get("enabled", False)
        self.clinician_manager = ClinicianManager(self.config.parameters, enabled=clinician_enabled)
        
        # Initialize the refactored discontinuation manager
        self._initialize_discontinuation_manager()
        
        # Patient state management
        self.patients = {}
        
        # Statistics with improved tracking
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
        
        # Event queue
        self.events = []
        self.current_time = self.start_date
    
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
                logger.error(f"Error loading discontinuation parameters: {str(e)}")
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
            logger.info("Using EnhancedDiscontinuationManager which supports premature discontinuations")
            self.discontinuation_manager = EnhancedDiscontinuationManager(config_dict)
        except ImportError:
            # Fall back to the compatibility wrapper if enhanced manager not available
            logger.info("EnhancedDiscontinuationManager not found, using compatibility wrapper")
            self.discontinuation_manager = CompatibilityDiscontinuationManager(config_dict)
        
        # Store a direct reference to the manager as well
        self.refactored_manager = self.discontinuation_manager
        
        logger.info(f"Initialized Discontinuation Manager with enabled={self.discontinuation_manager.enabled}")
    
    def run(self):
        """
        Run the simulation.
        """
        print("Initializing fixed treat-and-extend DES simulation...")
        
        # Generate patients
        self._generate_patients()
        
        # Process events
        print("Processing events...")
        event_count = 0
        while self.events:
            # Sort events by time
            self.events.sort(key=lambda e: e["time"])
            
            # Get next event
            event = self.events.pop(0)
            
            # Update current time
            self.current_time = event["time"]
            
            # Process event
            if event["type"] == "visit":
                self._process_visit(event)
            
            # Print progress
            event_count += 1
            if event_count % 1000 == 0:
                print(f"Processed {event_count} events...")
        
        print(f"Simulation complete after {event_count} events")
        
        # Print statistics
        self._print_statistics()
        
        # Return patient histories
        return {pid: patient["visit_history"] for pid, patient in self.patients.items()}
    
    def _generate_patients(self):
        """
        Generate patients and schedule their initial visits.
        """
        num_patients = self.config.num_patients
        print(f"Generating {num_patients} patients...")
        
        # Calculate arrival rate to distribute patients over simulation period
        simulation_weeks = self.config.duration_days / 7
        distribution_weeks = max(1, simulation_weeks / 2)
        rate_per_week = num_patients / distribution_weeks
        
        # Generate arrival times
        arrival_times = []
        week = 0
        patient_num = 1
        
        while patient_num <= num_patients and week < simulation_weeks:
            # Determine patients this week using Poisson distribution
            patients_this_week = min(
                np.random.poisson(rate_per_week),
                num_patients - patient_num + 1
            )
            
            # Distribute patients throughout the week
            for i in range(patients_this_week):
                # Random time within the week
                day_offset = np.random.uniform(0, 7)
                arrival_time = self.start_date + timedelta(days=week*7 + day_offset)
                
                # Ensure arrival time is before end date
                if arrival_time < self.end_date:
                    arrival_times.append((arrival_time, patient_num))
                    patient_num += 1
            
            week += 1
        
        # Create patients and schedule initial visits
        for arrival_time, patient_num in arrival_times:
            patient_id = f"PATIENT{patient_num:03d}"
            
            # Initialize patient
            vision_params = self.config.get_vision_params()
            initial_vision = vision_params.get("baseline_mean", 65)
            
            # Add randomness to initial vision
            if vision_params.get("baseline_std"):
                initial_vision = np.random.normal(
                    initial_vision, 
                    vision_params.get("baseline_std", 10)
                )
                # Clamp vision between 0-85 ETDRS letters
                initial_vision = min(max(initial_vision, 0), 85)
            
            # Create patient
            self.patients[patient_id] = {
                "id": patient_id,  # Store ID in the patient dict for tracking
                "current_vision": initial_vision,
                "baseline_vision": initial_vision,
                "current_phase": "loading",
                "treatments_in_phase": 0,
                "next_visit_interval": 4,  # Initial loading phase interval
                "disease_activity": {
                    "fluid_detected": True,  # Start with fluid detected (active disease)
                    "consecutive_stable_visits": 0,
                    "max_interval_reached": False,
                    "current_interval": 4  # Start with loading phase interval
                },
                "treatment_status": {
                    "active": True,
                    "recurrence_detected": False,
                    "weeks_since_discontinuation": 0,
                    "cessation_type": None,
                    "discontinuation_date": None,  # Track date for statistics
                },
                "disease_characteristics": {
                    "has_PED": np.random.random() < 0.3,  # 30% of patients have PED
                },
                "visit_history": [],
                "treatment_start": arrival_time  # Store treatment start date for duration calculations
            }
            
            # Schedule initial visit
            self.events.append({
                "time": arrival_time,
                "type": "visit",
                "patient_id": patient_id,
                "actions": ["vision_test", "oct_scan", "injection"]
            })
    
    def _process_visit(self, event):
        """
        Process a patient visit with proper discontinuation handling.
        
        Parameters
        ----------
        event : dict
            Event containing:
            - time: datetime - Visit time
            - patient_id: str - Patient ID
            - actions: list - Actions to perform
        """
        patient_id = event["patient_id"]
        if patient_id not in self.patients:
            return
        
        patient = self.patients[patient_id]
        
        # Get the assigned clinician for this visit
        clinician_id = self.clinician_manager.assign_clinician(patient_id, event["time"])
        clinician = self.clinician_manager.get_clinician(clinician_id)
        event["clinician_id"] = clinician_id  # Store for reference
        
        # Check if this is a monitoring visit for a discontinued patient
        is_monitoring = event.get("is_monitoring", False)
        
        # Update statistics
        self.stats["total_visits"] += 1
        if is_monitoring:
            self.stats["monitoring_visits"] += 1
        if "injection" in event["actions"]:
            self.stats["total_injections"] += 1
        if "oct_scan" in event["actions"]:
            self.stats["total_oct_scans"] += 1
        
        # Handle monitoring visit differently
        if is_monitoring and not patient["treatment_status"]["active"]:
            # First, update the fluid_detected status based on OCT scan
            if "oct_scan" in event["actions"]:
                # Create state dictionary for vision model
                state = {
                    "patient_id": patient_id,
                    "fluid_detected": patient["disease_activity"]["fluid_detected"],
                    "treatments_in_phase": 0,  # Not in treatment phase
                    "interval": 0,  # Not relevant for monitoring visits
                    "current_vision": patient["current_vision"],
                }
                
                # Use vision model to determine fluid status
                # Use 0 for vision change as we're only interested in fluid detection
                _, fluid_detected = self.vision_model.calculate_vision_change(
                    state=state,
                    actions=event["actions"],
                    phase="monitoring"
                )
                
                # Update patient's disease activity with new fluid status
                patient["disease_activity"]["fluid_detected"] = fluid_detected
            
            # Evaluate retreatment using the refactored manager approach
            result = self.refactored_manager.evaluate_retreatment(
                patient_state=patient,
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
                logger.warning(f"Unexpected return type from evaluate_retreatment: {type(result)}")
                should_retreat = False
                probability = 0.0
            
            # Record monitoring visit
            visit_record = {
                'date': event["time"],
                'actions': event["actions"],
                'vision': patient["current_vision"],
                'baseline_vision': patient["baseline_vision"],
                'phase': "monitoring",
                'type': 'monitoring_visit',
                'disease_state': 'stable' if not patient["disease_activity"]["fluid_detected"] else 'active',
                'treatment_status': patient["treatment_status"].copy(),
                'clinician_id': clinician_id,
                'fluid_detected': patient["disease_activity"]["fluid_detected"]  # Add explicit fluid status
            }
            patient["visit_history"].append(visit_record)
            
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
                patient["treatment_status"]["active"] = True
                patient["treatment_status"]["recurrence_detected"] = True
                patient["current_phase"] = "loading"  # Restart with loading phase
                patient["treatments_in_phase"] = 0
                patient["next_visit_interval"] = 4  # Initial loading phase interval
                patient["disease_activity"]["current_interval"] = 4
                
                # Register the retreatment with the manager
                self.refactored_manager.register_retreatment(patient_id)
                
                # Schedule next treatment visit
                next_visit_time = event["time"] + timedelta(weeks=4)  # Start with 4-week interval
                if next_visit_time <= self.end_date:
                    self.events.append({
                        "time": next_visit_time,
                        "type": "visit",
                        "patient_id": patient_id,
                        "actions": ["vision_test", "oct_scan", "injection"]
                    })
            
            return
        
        # Regular visit processing
        
        # Record baseline vision for this visit
        baseline_vision = patient["current_vision"]
        
        # Create state dictionary for vision model
        state = {
            "fluid_detected": patient["disease_activity"]["fluid_detected"],
            "treatments_in_phase": patient["treatments_in_phase"],
            "interval": patient["disease_activity"]["current_interval"],
            "current_vision": patient["current_vision"],
            "treatment_status": patient["treatment_status"]
        }
        
        # Calculate vision change using vision model
        vision_change, fluid_detected = self.vision_model.calculate_vision_change(
            state=state,
            actions=event["actions"],
            phase=patient["current_phase"]
        )
        
        # Update vision
        new_vision = min(max(baseline_vision + vision_change, 0), 85)
        patient["current_vision"] = new_vision
        
        # Update vision statistics
        if new_vision > baseline_vision:
            self.stats["vision_improvements"] += 1
        elif new_vision < baseline_vision:
            self.stats["vision_declines"] += 1
        
        # Update disease activity
        patient["disease_activity"]["fluid_detected"] = fluid_detected
        
        # Record visit
        visit_record = {
            'date': event["time"],
            'actions': event["actions"],
            'vision': new_vision,
            'baseline_vision': baseline_vision,
            'phase': patient["current_phase"],
            'type': 'regular_visit',
            'disease_state': 'stable' if not fluid_detected else 'active',
            'treatment_status': patient["treatment_status"].copy(),
            'clinician_id': clinician_id
        }
        patient["visit_history"].append(visit_record)
        
        # Process based on current phase
        current_phase = patient["current_phase"]
        treatments_in_phase = patient["treatments_in_phase"] + 1
        patient["treatments_in_phase"] = treatments_in_phase
        
        if current_phase == "loading":
            # Check if loading phase is complete (3 injections)
            if treatments_in_phase >= 3:
                # Transition to maintenance phase
                patient["current_phase"] = "maintenance"
                patient["treatments_in_phase"] = 0
                
                # Set initial maintenance interval to 8 weeks per Veeramani pathway
                patient["next_visit_interval"] = 8
                patient["disease_activity"]["current_interval"] = 8
                
                # Update statistics
                self.stats["protocol_completions"] += 1
            else:
                # Continue loading phase with 4-week intervals
                patient["next_visit_interval"] = 4
                patient["disease_activity"]["current_interval"] = 4
        
        elif current_phase == "maintenance":
            current_interval = patient["disease_activity"]["current_interval"]
            
            if fluid_detected:
                # Decrease interval by 2 weeks, but not below 8 weeks
                new_interval = max(8, current_interval - 2)
                patient["disease_activity"]["consecutive_stable_visits"] = 0
                patient["disease_activity"]["max_interval_reached"] = False
            else:
                # Increase interval by 2 weeks, up to 16 weeks maximum
                new_interval = min(16, current_interval + 2)
                patient["disease_activity"]["consecutive_stable_visits"] += 1
                
                # Check if max interval reached
                if new_interval >= 16:
                    patient["disease_activity"]["max_interval_reached"] = True
                    
                # Use ONE discontinuation evaluation instead of two
                # Evaluate discontinuation using the refactored manager
                result = self.refactored_manager.evaluate_discontinuation(
                    patient_state=patient,
                    current_time=event["time"],
                    patient_id=patient_id,
                    clinician_id=clinician_id,
                    treatment_start_time=patient["treatment_start"],
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
                    logger.warning(f"Unexpected return type from evaluate_discontinuation: {type(result)}")
                    should_discontinue = False
                    reason = ""
                    probability = 0.0
                    cessation_type = ""
                
                # If discontinuation is recommended
                if should_discontinue:
                    # Update patient state
                    patient["treatment_status"]["active"] = False
                    patient["treatment_status"]["discontinuation_date"] = event["time"]
                    patient["treatment_status"]["discontinuation_reason"] = reason
                    patient["treatment_status"]["cessation_type"] = cessation_type
                    
                    # Only increment stats if this is a new discontinuation for this patient
                    if patient_id not in self.discontinued_patients:
                        self.stats["protocol_discontinuations"] += 1
                        self.stats["unique_discontinuations"] += 1
                        self.discontinued_patients.add(patient_id)
                    else:
                        # Do not increment stats for re-discontinuations
                        logger.warning(f"Patient {patient_id} already discontinued previously")
                    
                    # Apply vision changes specific to this type of discontinuation
                    # Convert patient dictionary to expected format for discontinuation manager
                    patient_state = {
                        "disease_activity": patient["disease_activity"],
                        "treatment_status": patient["treatment_status"],
                        "disease_characteristics": patient["disease_characteristics"],
                        "vision": {
                            "current_va": patient["current_vision"]
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
                            patient["current_vision"] = updated_patient_state["vision"]["current_va"]
                    
                    # Register the discontinuation with the manager
                    self.refactored_manager.register_discontinuation(
                        patient_id, 
                        cessation_type
                    )
                    
                    # Schedule monitoring visits
                    monitoring_events = self.refactored_manager.schedule_monitoring(
                        event["time"],
                        cessation_type=cessation_type,
                        clinician=clinician,
                        patient_id=patient_id
                    )
                    
                    for monitoring_event in monitoring_events:
                        if monitoring_event["time"] <= self.end_date:
                            self.events.append({
                                "time": monitoring_event["time"],
                                "type": "visit",
                                "patient_id": patient_id,
                                "actions": monitoring_event["actions"],
                                "is_monitoring": True,
                                "cessation_type": monitoring_event.get("cessation_type")
                            })
                    
                    return  # No more regular visits
            
            # Update interval for next visit
            patient["next_visit_interval"] = new_interval
            patient["disease_activity"]["current_interval"] = new_interval
        
        # Schedule next visit
        next_interval = patient["next_visit_interval"]
        next_visit_time = event["time"] + timedelta(weeks=next_interval)
        
        # Only schedule next visit if treatment is active and we haven't reached the end date
        if patient["treatment_status"]["active"] and next_visit_time <= self.end_date:
            # Always include injection in treat-and-extend protocol
            next_actions = ["vision_test", "oct_scan", "injection"]
            
            self.events.append({
                "time": next_visit_time,
                "type": "visit",
                "patient_id": patient_id,
                "actions": next_actions
            })
    
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
        total_patients = len(self.patients)
        disc_rate = unique_discontinued / total_patients if total_patients > 0 else 0
        print(f"Discontinuation rate: {disc_rate:.2%} ({unique_discontinued}/{total_patients} patients)")
        
        # Print patient summary
        print("\nPatient Summary:")
        print("-" * 20)
        total_patients = len(self.patients)
        total_visits = sum(len(patient["visit_history"]) for patient in self.patients.values())
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
        for patient in self.patients.values():
            for visit in patient["visit_history"]:
                if visit["phase"] == "maintenance":
                    maintenance_visits += 1
                    if "injection" in visit["actions"]:
                        maintenance_injections += 1
        
        if maintenance_visits > 0:
            maintenance_injection_rate = (maintenance_injections / maintenance_visits) * 100
            print(f"Maintenance Phase Injection Rate: {maintenance_injection_rate:.1f}%")

def run_treat_and_extend_des(config=None, verbose=False):
    """
    Run a DES simulation with the fixed treat-and-extend protocol.
    
    Parameters
    ----------
    config : SimulationConfig or str, optional
        Simulation configuration or name, by default None
    verbose : bool, optional
        Whether to print verbose output, by default False
        
    Returns
    -------
    Dict[str, List[Dict]]
        Dictionary mapping patient IDs to their visit histories
    """
    # Create and run simulation
    config_name = "custom_config"
    if isinstance(config, str):
        config_name = config
    elif config and hasattr(config, 'config_name'):
        config_name = config.config_name
    else:
        config_name = "eylea_literature_based"
        
    print(f"Running fixed DES simulation with config: {config_name}")
    sim = TreatAndExtendDES(config)
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
                'treatment_status': str(visit.get('treatment_status', {}))
            }
            all_data.append(visit_data)
    
    # Create DataFrame
    df = pd.DataFrame(all_data)
    
    # Save all data to CSV
    df.to_csv('treat_and_extend_des_fixed_data.csv', index=False)
    print(f"Saved data for {len(patient_histories)} patients to treat_and_extend_des_fixed_data.csv")
    
    # Print final stats summary
    total_patients = len(sim.patients)
    unique_discontinuations = sim.stats.get("unique_discontinuations", 0)
    disc_rate = unique_discontinuations / total_patients if total_patients > 0 else 0
    
    print("\nFinal Statistics Summary:")
    print(f"Total Patients: {total_patients}")
    print(f"Unique Discontinued Patients: {unique_discontinuations}")
    print(f"Discontinuation Rate: {disc_rate:.2%}")
    
    # Sample a few patients to check their visit patterns
    if verbose:
        sample_patients = np.random.choice(list(patient_histories.keys()), min(3, len(patient_histories)))
        
        for patient_id in sample_patients:
            patient_data = [visit for visit in patient_histories[patient_id]]
            patient_data.sort(key=lambda v: v['date'])
            
            print(f"\nPatient {patient_id} visits:")
            for visit in patient_data:
                print(f"  {visit['date']} - Phase: {visit['phase']} - Actions: {visit['actions']}")
    
    return patient_histories

if __name__ == "__main__":
    run_treat_and_extend_des(verbose=True)