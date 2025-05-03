"""
Treat-and-extend protocol implementation for Agent-Based Simulation (ABS).

This module provides a production-ready implementation of the treat-and-extend protocol
for AMD treatment modeling using Agent-Based Simulation. It ensures patients receive
injections at every visit as required by the protocol and follows the Veeramani pathway
for interval adjustments.

Key Features
-----------
- Complete implementation of treat-and-extend protocol
- Injections at every visit (loading and maintenance phases)
- Proper phase transitions (loading → maintenance)
- Interval adjustments based on disease activity (8→10→12→14→16 weeks)
- Accurate patient generation based on configuration

Functions
---------
run_treat_and_extend_abs
    Main entry point for running an ABS simulation with the treat-and-extend protocol
"""

from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from simulation.config import SimulationConfig
from simulation.base import BaseSimulation, Event, SimulationClock
from simulation.clinical_model import ClinicalModel, DiseaseState
from simulation.scheduler import ClinicScheduler
from simulation.vision_models import SimplifiedVisionModel
from simulation.discontinuation_manager import DiscontinuationManager
from simulation.enhanced_discontinuation_manager import EnhancedDiscontinuationManager
from simulation.clinician import Clinician, ClinicianManager

class Patient:
    """Patient agent in the treat-and-extend ABS simulation.
    
    Represents a single patient in the agent-based simulation, maintaining their
    current state and history of visits and treatments.

    Parameters
    ----------
    patient_id : str
        Unique identifier for the patient
    initial_vision : float
        Initial visual acuity in ETDRS letters
    start_date : datetime
        Date when treatment starts

    Attributes
    ----------
    patient_id : str
        Unique identifier for the patient
    current_vision : float
        Current visual acuity in ETDRS letters
    baseline_vision : float
        Baseline visual acuity at treatment start
    current_phase : str
        Current treatment phase ('loading' or 'maintenance')
    treatments_in_phase : int
        Number of treatments received in current phase
    next_visit_interval : int
        Weeks until next scheduled visit
    disease_activity : dict
        Information about disease activity including:
        - fluid_detected: Whether fluid was detected at last visit
        - consecutive_stable_visits: Count of consecutive visits without fluid
        - max_interval_reached: Whether maximum interval (16 weeks) was reached
        - current_interval: Current treatment interval in weeks
    treatment_status : dict
        Information about treatment status including:
        - active: Whether treatment is active
        - recurrence_detected: Whether disease recurrence was detected
        - discontinuation_date: Date when treatment was discontinued (if applicable)
        - cessation_type: Type of discontinuation (if applicable)
    disease_characteristics : dict
        Information about disease characteristics including:
        - has_PED: Whether patient has pigment epithelial detachment
    history : list
        List of historical visit records
    """

    def __init__(self, patient_id, initial_vision, start_date):
        self.patient_id = patient_id
        self.current_vision = initial_vision
        self.baseline_vision = initial_vision
        self.current_phase = "loading"
        self.treatments_in_phase = 0
        self.next_visit_interval = 4  # Initial loading phase interval
        self.disease_activity = {
            "fluid_detected": True,  # Start with fluid detected (active disease)
            "consecutive_stable_visits": 0,
            "max_interval_reached": False,
            "current_interval": 4  # Start with loading phase interval
        }
        self.treatment_status = {
            "active": True,
            "recurrence_detected": False,
            "discontinuation_date": None,
            "cessation_type": None
        }
        # Add disease characteristics including risk factors
        self.disease_characteristics = {
            "has_PED": np.random.random() < 0.3,  # 30% of patients have PED
        }
        self.history = []
        self.treatment_start = start_date

    def process_visit(self, visit_time, actions, vision_model):
        """
        Process a patient visit.
        
        Parameters
        ----------
        visit_time : datetime
            Time of the visit
        actions : list
            List of actions performed during the visit
        vision_model : SimplifiedVisionModel
            Model for vision changes
            
        Returns
        -------
        dict
            Visit data including:
            - visit_type: Type of visit
            - baseline_vision: Baseline visual acuity
            - new_vision: Updated visual acuity
            - disease_state: Disease state after visit
        """
        # Record baseline vision for this visit
        baseline_vision = self.current_vision
        
        # Create state dictionary for vision model
        state = {
            "fluid_detected": self.disease_activity["fluid_detected"],
            "treatments_in_phase": self.treatments_in_phase,
            "interval": self.disease_activity["current_interval"],
            "current_vision": self.current_vision,
            "treatment_status": self.treatment_status
        }
        
        # Calculate vision change using vision model
        vision_change, fluid_detected = vision_model.calculate_vision_change(
            state=state,
            actions=actions,
            phase=self.current_phase
        )
        
        # Update vision
        new_vision = min(max(self.current_vision + vision_change, 0), 85)
        self.current_vision = new_vision
        
        # Update disease activity
        self.disease_activity["fluid_detected"] = fluid_detected
        
        # Update treatment phase and intervals
        self._update_treatment_phase(actions)
        
        # Create visit record
        visit_record = {
            'date': visit_time,
            'type': 'regular_visit',
            'actions': actions,
            'baseline_vision': self.baseline_vision,
            'vision': new_vision,
            'disease_state': 'active' if fluid_detected else 'stable',
            'phase': self.current_phase,
            'interval': self.disease_activity["current_interval"]
        }
        
        # Add to history
        self.history.append(visit_record)
        
        # Return visit data
        return {
            'visit_type': 'regular_visit',
            'baseline_vision': self.baseline_vision,
            'new_vision': new_vision,
            'disease_state': 'active' if fluid_detected else 'stable'
        }
    
    def _update_treatment_phase(self, actions):
        """
        Update treatment phase and intervals based on visit actions.
        
        Parameters
        ----------
        actions : list
            List of actions performed during the visit
        """
        if "injection" in actions:
            # Increment treatments in current phase
            self.treatments_in_phase += 1
            
            # Check if loading phase is complete (3 injections)
            if self.current_phase == "loading" and self.treatments_in_phase >= 3:
                # Transition to maintenance phase
                self.current_phase = "maintenance"
                self.treatments_in_phase = 0
                
                # Set initial maintenance interval to 8 weeks per Veeramani pathway
                self.next_visit_interval = 8
                self.disease_activity["current_interval"] = 8
            elif self.current_phase == "loading":
                # Continue loading phase with 4-week intervals
                self.next_visit_interval = 4
                self.disease_activity["current_interval"] = 4
            elif self.current_phase == "maintenance":
                # Update maintenance phase intervals based on disease activity
                current_interval = self.disease_activity["current_interval"]
                
                if self.disease_activity["fluid_detected"]:
                    # Decrease interval by 2 weeks, but not below 8 weeks
                    new_interval = max(8, current_interval - 2)
                    self.disease_activity["consecutive_stable_visits"] = 0
                    self.disease_activity["max_interval_reached"] = False
                else:
                    # Increase interval by 2 weeks, up to 16 weeks maximum
                    new_interval = min(16, current_interval + 2)
                    self.disease_activity["consecutive_stable_visits"] += 1
                    
                    # Check if max interval reached
                    if new_interval >= 16:
                        self.disease_activity["max_interval_reached"] = True
                        # Note: Discontinuation decision will be handled by the simulation class
                
                # Update interval for next visit
                self.next_visit_interval = new_interval
                self.disease_activity["current_interval"] = new_interval

class TreatAndExtendABS(BaseSimulation):
    """
    Treat-and-extend protocol implementation for Agent-Based Simulation.
    
    This class implements the treat-and-extend protocol according to the
    Veeramani pathway diagram, ensuring that patients receive injections
    at every visit.
    
    Parameters
    ----------
    config : SimulationConfig
        Simulation configuration
    start_date : datetime, optional
        Start date for the simulation, by default None (uses config start_date)
        
    Attributes
    ----------
    config : SimulationConfig
        Simulation configuration
    start_date : datetime
        Start date of the simulation
    end_date : datetime
        End date of the simulation
    agents : dict
        Dictionary mapping patient IDs to Patient objects
    clinical_model : ClinicalModel
        Clinical model for disease progression and treatment effects
    vision_model : SimplifiedVisionModel
        Model for vision changes
    scheduler : ClinicScheduler
        Scheduler for clinic visits
    clock : SimulationClock
        Simulation clock for event scheduling
    stats : dict
        Simulation statistics
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
        
        # Initialize base simulation
        super().__init__(self.config)
        
        # Set start and end dates
        if start_date is None:
            self.start_date = datetime.strptime(self.config.start_date, "%Y-%m-%d") if isinstance(self.config.start_date, str) else self.config.start_date
        else:
            self.start_date = start_date
            
        self.end_date = self.start_date + timedelta(days=self.config.duration_days)
        
        # Initialize components
        self.agents = {}
        self.clinical_model = ClinicalModel(self.config)
        self.vision_model = SimplifiedVisionModel(self.config)
        
        # Initialize clinician manager
        clinician_config = self.config.parameters.get("clinicians", {})
        clinician_enabled = clinician_config.get("enabled", False)
        self.clinician_manager = ClinicianManager(self.config.parameters, enabled=clinician_enabled)
        
        # Initialize enhanced discontinuation manager
        # Get the parameter file path from the config
        discontinuation_config = self.config.parameters.get("discontinuation", {})
        parameter_file = discontinuation_config.get("parameter_file", "")
        
        if parameter_file:
            try:
                # Directly load the discontinuation parameters from the file
                with open(parameter_file, 'r') as f:
                    import yaml
                    discontinuation_params = yaml.safe_load(f)
                    self.discontinuation_manager = EnhancedDiscontinuationManager(discontinuation_params)
            except Exception as e:
                print(f"Error loading discontinuation parameters: {str(e)}")
                # Fall back to empty dict with enabled=True
                self.discontinuation_manager = EnhancedDiscontinuationManager({"discontinuation": {"enabled": True}})
        else:
            # If no parameter file specified, use the discontinuation config from the parameters
            self.discontinuation_manager = EnhancedDiscontinuationManager({"discontinuation": {"enabled": True}})
        
        self.scheduler = ClinicScheduler(
            daily_capacity=20,
            days_per_week=5
        )
        self.clock = SimulationClock(self.start_date)
        self.clock.end_date = self.end_date
        
        # Statistics
        self.stats = {
            "total_visits": 0,
            "total_injections": 0,
            "total_oct_scans": 0,
            "vision_improvements": 0,
            "vision_declines": 0,
            "protocol_completions": 0,
            "protocol_discontinuations": 0,
            "monitoring_visits": 0,
            "retreatments": 0,
            "clinician_decisions": {
                "protocol_followed": 0,
                "protocol_overridden": 0
            }
        }
    
    def generate_patients(self):
        """
        Generate patients and schedule their initial visits.
        """
        num_patients = self.config.num_patients
        print(f"Generating {num_patients} patients...")
        
        # Generate patients with initial visits spread across first week
        for i in range(1, num_patients + 1):
            patient_id = f"PATIENT{i:03d}"
            
            # Initialize patient with random initial vision
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
            self.agents[patient_id] = Patient(patient_id, initial_vision, self.start_date)
            
            # Schedule initial visit - spread patients across first week
            initial_visit_time = self.start_date + timedelta(hours=i*2)  # Space patients out by 2 hours
            
            # Schedule initial visit
            self.clock.schedule_event(Event(
                time=initial_visit_time,
                event_type="visit",
                patient_id=patient_id,
                data={
                    "visit_type": "injection_visit",
                    "actions": ["vision_test", "oct_scan", "injection"],
                    "decisions": ["nurse_vision_check", "doctor_treatment_decision"]
                },
                priority=1
            ))
    
    def run(self):
        """
        Run the simulation.
        
        Returns
        -------
        dict
            Dictionary mapping patient IDs to their visit histories
        """
        print("Initializing treat-and-extend ABS simulation...")
        
        # Generate patients
        self.generate_patients()
        
        # Process events
        print("Processing events...")
        event_count = 0
        
        while self.clock.current_time <= self.end_date:
            event = self.clock.get_next_event()
            if event is None:
                break
                
            # Process event
            self.process_event(event)
            
            # Print progress
            event_count += 1
            if event_count % 1000 == 0:
                print(f"Processed {event_count} events...")
        
        print(f"Simulation complete after {event_count} events")
        
        # Print statistics
        self._print_statistics()
        
        # Return patient histories
        return {pid: agent.history for pid, agent in self.agents.items()}
    
    def process_event(self, event):
        """
        Process a simulation event.
        
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
            
            # Process visit
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
            
            # Check if this is a monitoring visit for a discontinued patient
            is_monitoring = event.data.get("is_monitoring", False)
            
            if is_monitoring:
                self.stats["monitoring_visits"] += 1
                
                # Process monitoring visit
                # Convert Patient object to dictionary for discontinuation manager
                patient_state = {
                    "disease_activity": patient.disease_activity,
                    "treatment_status": patient.treatment_status,
                    "disease_characteristics": patient.disease_characteristics
                }
                
                # First get the protocol retreatment decision without clinician influence
                protocol_retreatment, _ = self.discontinuation_manager.process_monitoring_visit(
                    patient_state=patient_state,
                    actions=event.data["actions"]
                )
                
                # Then get the actual decision with clinician influence
                retreatment, updated_patient = self.discontinuation_manager.process_monitoring_visit(
                    patient_state=patient_state,
                    actions=event.data["actions"],
                    clinician=clinician
                )
                
                # Track clinician influence on decision
                if clinician and clinician.profile_name != "perfect":
                    self.discontinuation_manager.track_clinician_decision(
                        clinician=clinician,
                        decision_type="retreatment",
                        protocol_decision=protocol_retreatment,
                        actual_decision=retreatment
                    )
                    
                    # Update statistics
                    if protocol_retreatment != retreatment:
                        self.stats["clinician_decisions"]["protocol_overridden"] += 1
                    else:
                        self.stats["clinician_decisions"]["protocol_followed"] += 1
                
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
                    'clinician_id': clinician_id
                }
                patient.history.append(visit_record)
                
                # If retreatment is recommended, restart treatment
                if retreatment:
                    patient.treatment_status["active"] = True
                    patient.treatment_status["recurrence_detected"] = True
                    patient.current_phase = "loading"  # Restart with loading phase
                    patient.treatments_in_phase = 0
                    patient.next_visit_interval = 4  # Initial loading phase interval
                    patient.disease_activity["current_interval"] = 4
                    self.stats["retreatments"] += 1
                    
                    # Schedule next treatment visit
                    next_visit = self.schedule_next_visit(patient_id, event.time)
                    if next_visit:
                        self.clock.schedule_event(next_visit)
                
                return
            
            # Check if patient is in maintenance phase and at max interval
            if (patient.current_phase == "maintenance" and 
                patient.disease_activity["max_interval_reached"] and
                patient.disease_activity["consecutive_stable_visits"] >= 3):
                
                # Use discontinuation manager to evaluate discontinuation
                # Convert Patient object to dictionary for discontinuation manager
                patient_state = {
                    "disease_activity": patient.disease_activity,
                    "treatment_status": patient.treatment_status,
                    "disease_characteristics": patient.disease_characteristics
                }
                
                # First get the protocol decision without clinician influence
                protocol_decision, protocol_reason, protocol_probability, protocol_cessation_type = self.discontinuation_manager.evaluate_discontinuation(
                    patient_state=patient_state,
                    current_time=event.time,
                    treatment_start_time=patient.treatment_start
                )
                
                # Then get the actual decision with clinician influence
                should_discontinue, reason, probability, cessation_type = self.discontinuation_manager.evaluate_discontinuation(
                    patient_state=patient_state,
                    current_time=event.time,
                    clinician_id=clinician_id,
                    treatment_start_time=patient.treatment_start,
                    clinician=clinician
                )
                
                # Track clinician influence on decision
                if clinician and clinician.profile_name != "perfect":
                    self.discontinuation_manager.track_clinician_decision(
                        clinician=clinician,
                        decision_type="discontinuation",
                        protocol_decision=protocol_decision,
                        actual_decision=should_discontinue
                    )
                    
                    # Update statistics
                    if protocol_decision != should_discontinue:
                        self.stats["clinician_decisions"]["protocol_overridden"] += 1
                    else:
                        self.stats["clinician_decisions"]["protocol_followed"] += 1
                
                if should_discontinue:
                    patient.treatment_status["active"] = False
                    patient.treatment_status["discontinuation_date"] = event.time
                    patient.treatment_status["discontinuation_reason"] = reason
                    patient.treatment_status["cessation_type"] = cessation_type
                    self.stats["protocol_discontinuations"] += 1
                    
                    # Schedule monitoring visits
                    monitoring_events = self.discontinuation_manager.schedule_monitoring(
                        event.time, 
                        cessation_type=cessation_type,
                        clinician=clinician
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
                self.stats["protocol_discontinuations"] += 1
                return  # No more visits
            
            # Schedule next visit
            next_visit = self.schedule_next_visit(patient_id, event.time)
            if next_visit:
                self.clock.schedule_event(next_visit)
    
    def schedule_next_visit(self, patient_id, current_date):
        """
        Schedule the next visit for a patient.
        
        Parameters
        ----------
        patient_id : str
            ID of the patient to schedule
        current_date : datetime
            Current date in the simulation
            
        Returns
        -------
        Event
            Next visit event for the patient
        """
        patient = self.agents[patient_id]
        
        # Only schedule next visit if treatment is active
        if not patient.treatment_status["active"]:
            return None
        
        # Calculate next visit date based on interval
        next_visit_interval = patient.next_visit_interval
        next_visit_date = current_date + timedelta(weeks=next_visit_interval)
        
        # Only schedule if within simulation timeframe
        if next_visit_date > self.end_date:
            return None
        
        # Create visit event - always include injection in treat-and-extend protocol
        return Event(
            time=next_visit_date,
            event_type="visit",
            patient_id=patient_id,
            data={
                "visit_type": "injection_visit",
                "actions": ["vision_test", "oct_scan", "injection"],
                "decisions": ["nurse_vision_check", "doctor_treatment_decision"]
            },
            priority=1
        )
    
    def _print_statistics(self):
        """
        Print simulation statistics.
        """
        print("\nSimulation Statistics:")
        print("-" * 20)
        for stat, value in self.stats.items():
            print(f"{stat}: {value}")
        
        # Add discontinuation manager statistics
        discontinuation_stats = self.discontinuation_manager.get_statistics()
        if discontinuation_stats:
            print("\nDiscontinuation Statistics:")
            print("-" * 20)
            for stat, value in discontinuation_stats.items():
                print(f"{stat}: {value}")
        
        # Add clinician manager statistics
        if self.clinician_manager.enabled:
            clinician_metrics = self.clinician_manager.get_performance_metrics()
            print("\nClinician Statistics:")
            print("-" * 20)
            for metric_type, metrics in clinician_metrics.items():
                print(f"{metric_type}:")
                for profile, count in metrics.items():
                    print(f"  {profile}: {count}")
        
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
    Run an ABS simulation with the treat-and-extend protocol.
    
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
    # Create and run simulation
    config_name = config.config_name if config and hasattr(config, 'config_name') else "eylea_literature_based"
    
    if isinstance(config, str):
        config_name = config
    elif config and hasattr(config, 'config_name'):
        config_name = config.config_name
    
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
    df.to_csv('treat_and_extend_abs_data.csv', index=False)
    print(f"Saved data for {len(patient_histories)} patients to treat_and_extend_abs_data.csv")
    
    return patient_histories

if __name__ == "__main__":
    run_treat_and_extend_abs(verbose=True)
