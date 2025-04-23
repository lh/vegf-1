"""Discrete Event Simulation (DES) core for AMD treatment modeling.

This module implements a pure Discrete Event Simulation approach for modeling
AMD treatment protocols, focusing on system-level performance and efficiency.

Classes
-------
DiscreteEventSimulation
    Core DES implementation with event processing and statistics

Key Components
--------------
- Event scheduling and processing
- Protocol-driven treatment decisions
- Clinic resource management
- Patient state tracking
- Statistical aggregation

Differences from ABS
-------------------
- Focuses on aggregate statistics rather than individual histories
- Uses simplified patient state representation
- More efficient for large-scale simulations
- Better for analyzing system-level performance

Examples
--------
>>> config = SimulationConfig(
...     protocol=load_protocol("treat_and_extend"),
...     start_date=datetime(2023,1,1),
...     duration_days=365,
...     random_seed=42
... )
>>> sim = DiscreteEventSimulation(config)
>>> sim.run()

Notes
-----
- Events are processed in chronological order
- Time values are in datetime objects
- Vision values are in ETDRS letters
- Visit intervals are in weeks
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
import numpy as np
from .base import BaseSimulation, Event, SimulationEnvironment
from protocol_models import TreatmentProtocol
from .config import SimulationConfig
from .patient_generator import PatientGenerator
from .patient_state import PatientState
from .clinical_model import ClinicalModel
from .scheduler import ClinicScheduler

class DiscreteEventSimulation(BaseSimulation):
    """Pure Discrete Event Simulation (DES) implementation for AMD treatment modeling.

    This implementation focuses on event flows and aggregate statistics rather than
    individual agent modeling. It provides a more efficient alternative to ABS when
    detailed patient-level tracking isn't required.

    Parameters
    ----------
    config : SimulationConfig
        Configuration object containing:
        - protocol: Treatment protocol definition
        - start_date: Simulation start date
        - duration_days: Simulation duration in days
        - random_seed: Optional random seed
    environment : Optional[SimulationEnvironment], optional
        Shared simulation environment, creates new one if None (default: None)

    Attributes
    ----------
    config : SimulationConfig
        Simulation configuration
    global_stats : Dict[str, Any]
        Aggregated statistics including:
        - total_visits: Count of all visits
        - total_injections: Count of injections
        - total_oct_scans: Count of OCT scans
        - vision_improvements: Count of vision improvements
        - vision_declines: Count of vision declines
        - scheduling: Clinic scheduling metrics
    scheduler : ClinicScheduler
        Manages clinic visit scheduling
    patient_generator : PatientGenerator
        Generates patient arrival times
    patients : Dict[str, PatientState]
        Dictionary of patient states keyed by ID

    Notes
    -----
    Key differences from ABS:
    - Tracks aggregate statistics rather than individual histories
    - Uses simplified patient state representation
    - More efficient for large-scale simulations
    - Better for analyzing system-level performance
    """
    def __init__(self, config: SimulationConfig,
                 environment: Optional[SimulationEnvironment] = None):
        """Initialize DES simulation with configuration.

        Parameters
        ----------
        config : SimulationConfig
            Simulation configuration parameters
        environment : Optional[SimulationEnvironment], optional
            Shared simulation environment (default: None)

        Notes
        -----
        Initializes:
        - Protocol registration
        - Random seed
        - Statistics tracking
        - Scheduler
        - Patient generator
        """
        super().__init__(config.start_date, environment)
        self.config = config
        
        # Register protocol using its type from config
        protocol_type = "test_simulation"  # Use the type from YAML config
        self.register_protocol(protocol_type, config.protocol)
        
        # Initialize random seed
        if config.random_seed is not None:
            np.random.seed(config.random_seed)
            
        # Initialize statistics
        des_params = config.get_des_params()
        self.global_stats = {
            "total_visits": 0,
            "total_injections": 0,
            "total_oct_scans": 0,
            "vision_improvements": 0,
            "vision_declines": 0,
            "protocol_completions": 0,
            "protocol_discontinuations": 0,
            "scheduling": {
                "daily_capacity": des_params["daily_capacity"],
                "days_per_week": des_params["days_per_week"],
                "rescheduled_visits": 0
            }
        }
        
        # Initialize components
        self.scheduler = ClinicScheduler(
            daily_capacity=des_params["daily_capacity"],
            days_per_week=des_params["days_per_week"]
        )
        
        patient_gen_params = des_params["patient_generation"]
        self.patient_generator = PatientGenerator(
            rate_per_week=patient_gen_params["rate_per_week"],
            start_date=config.start_date,
            end_date=config.start_date + timedelta(days=config.duration_days),
            random_seed=patient_gen_params["random_seed"] or config.random_seed
        )
        
        # Patient state management
        self.patients: Dict[str, PatientState] = {}
    
    def _schedule_patient_arrivals(self):
        """Schedule patient arrival events based on generator.

        Notes
        -----
        Uses Poisson process to generate realistic arrival times.
        Creates 'add_patient' events for each arrival.
        """
        arrival_times = self.patient_generator.generate_arrival_times()
        for arrival_time, patient_num in arrival_times:
            patient_id = f"TEST{patient_num:03d}"
            self.clock.schedule_event(Event(
                time=arrival_time,
                event_type="add_patient",
                patient_id=patient_id,
                data={"protocol_name": "test_simulation"},
                priority=1
            ))
    
    def process_event(self, event: Event):
        """Process different event types in the simulation.

        Parameters
        ----------
        event : Event
            Event to process, with types:
            - 'visit': Patient visit
            - 'treatment_decision': Treatment decision
            - 'add_patient': New patient arrival

        Notes
        -----
        Routes events to appropriate handler methods.
        """
        if event.event_type == "visit":
            self._handle_visit(event)
        elif event.event_type == "treatment_decision":
            self._handle_treatment_decision(event)
        elif event.event_type == "add_patient":
            self._handle_add_patient(event)
    
    def _handle_add_patient(self, event: Event):
        """Handle patient arrival events.

        Parameters
        ----------
        event : Event
            Event containing:
            - patient_id: Generated patient ID
            - data.protocol_name: Protocol to assign

        Notes
        -----
        Creates new patient state and schedules initial visit.
        """
        patient_id = event.patient_id
        protocol_name = event.data["protocol_name"]
        
        # Initialize patient state
        vision_params = self.config.get_vision_params()
        initial_vision = vision_params["baseline_mean"]
        
        patient = PatientState(
            patient_id=patient_id,
            protocol_name=protocol_name,
            initial_vision=initial_vision,
            start_time=event.time
        )
        self.patients[patient_id] = patient
        
        # Schedule initial visit
        initial_visit = {
            "visit_type": "injection_visit",
            "actions": ["vision_test", "oct_scan", "injection"],
            "decisions": ["nurse_vision_check", "doctor_treatment_decision"]
        }
        
        self.clock.schedule_event(Event(
            time=event.time,
            event_type="visit",
            patient_id=patient_id,
            data=initial_visit,
            priority=1
        ))
    
    def _handle_visit(self, event: Event):
        """Handle patient visit events using protocol objects.

        Parameters
        ----------
        event : Event
            Visit event containing:
            - patient_id: Patient identifier
            - data.actions: List of actions to perform
            - data.visit_type: Type of visit

        Notes
        -----
        Updates global statistics and schedules treatment decisions.
        Only processes visit if clinic resources are available.
        """
        patient_id = event.patient_id
        if patient_id not in self.patients:
            return
            
        patient = self.patients[patient_id]
        protocol = self.get_protocol(patient.state["protocol"])
        if not protocol:
            return
            
        # Only process visit if resources are available
        if self.scheduler.request_slot(event, self.clock.end_date):
            self.global_stats["total_visits"] += 1
            
            # Get current phase
            current_phase = protocol.phases.get(patient.state.get("current_phase", "loading"))
            if not current_phase:
                return
                
            # Create protocol event
            event.phase = current_phase
            event.protocol = protocol
            
            # Process visit
            actions = [action.value for action in event.get_required_actions()]
            clinical_model = ClinicalModel(self.config)
            visit_data = patient.process_visit(event.time, actions, clinical_model)
            
            # Update global stats
            if "injection" in actions:
                self.global_stats["total_injections"] += 1
            if "oct_scan" in actions:
                self.global_stats["total_oct_scans"] += 1
            if visit_data["vision_change"] > 0:
                self.global_stats["vision_improvements"] += 1
            elif visit_data["vision_change"] < 0:
                self.global_stats["vision_declines"] += 1
            
            # Schedule treatment decision for same day
            self.clock.schedule_event(Event(
                time=event.time,
                event_type="treatment_decision",
                patient_id=patient_id,
                data={"decision_type": "doctor_treatment_decision", "visit_data": visit_data},
                priority=2,
                phase=current_phase,
                protocol=protocol
            ))
    
    def _handle_treatment_decision(self, event: Event):
        """Handle treatment decision events using protocol objects.

        Parameters
        ----------
        event : Event
            Decision event containing:
            - patient_id: Patient identifier
            - data.decision_type: Type of decision
            - data.visit_data: Results from visit

        Notes
        -----
        Processes phase transitions and schedules next visit.
        Applies safety checks to visit intervals.
        """
        patient_id = event.patient_id
        if patient_id not in self.patients:
            return
            
        patient = self.patients[patient_id]
        protocol = self.get_protocol(patient.state["protocol"])
        if not protocol:
            return
            
        # Get current phase
        current_phase = protocol.phases.get(patient.state.get("current_phase", "loading"))
        if not current_phase:
            return
            
        # Process visit with current phase
        updated_state = current_phase.process_visit(patient.state)
        patient.state.update(updated_state)
        
        # Check for phase transition
        if patient.state.get("phase_complete"):
            next_phase = protocol.process_phase_transition(current_phase, patient.state)
            if next_phase:
                patient.update_phase(next_phase.phase_type.name.lower())
                
        # Schedule next visit based on protocol with safety checks
        next_interval = patient.state.get("next_visit_weeks", current_phase.visit_interval_weeks)
        if next_interval <= 0:
            next_interval = 4
        elif next_interval > 52:
            next_interval = 52
            
        # Only schedule next visit if we haven't reached the end date
        if event.time + timedelta(weeks=next_interval) <= self.clock.end_date:
            next_event = self.scheduler.schedule_next_visit(
                Event,  # Pass Event class as factory
                patient_id,
                patient.last_visit_date,
                next_interval
            )
            if next_event:
                self.clock.schedule_event(next_event)
    
    @property
    def patient_states(self) -> Dict[str, Dict]:
        """Get all patient states for analysis and reporting.

        Returns
        -------
        Dict[str, Dict]
            Dictionary mapping patient IDs to their state dictionaries

        Notes
        -----
        Provides compatibility with existing analysis code.
        State dictionaries contain:
        - current_vision: Visual acuity
        - disease_state: AMD stage
        - treatment_history: List of treatments
        - next_visit_weeks: Weeks until next visit
        """
        return {pid: patient.state for pid, patient in self.patients.items()}
