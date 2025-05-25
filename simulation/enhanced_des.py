"""Enhanced Discrete Event Simulation (DES) core with extension support.

This module provides an enhanced version of the Discrete Event Simulation core
that supports extension through event handler registration. It maintains all
functionality of the original DES implementation while adding:

1. Support for external event handlers
2. Standardized event structure
3. Improved extension points for protocol-specific behavior

Classes
-------
EnhancedDES
    Enhanced Discrete Event Simulation core with extension support

Examples
--------
>>> from simulation.enhanced_des import EnhancedDES
>>> config = SimulationConfig.from_yaml("test_simulation")
>>> sim = EnhancedDES(config)
>>> sim.register_event_handler("visit", my_visit_handler)
>>> sim.run()
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Union
import logging
import numpy as np
from .base import BaseSimulation, Event, SimulationEnvironment, SimulationClock
from .config import SimulationConfig
from .patient_generator import PatientGenerator
from .patient_state import PatientState
from .clinical_model import ClinicalModel
from .scheduler import ClinicScheduler

# Configure logging
logger = logging.getLogger(__name__)

# Define event handler type
EventHandler = Callable[[Event], None]

class EnhancedDES(BaseSimulation):
    """Enhanced Discrete Event Simulation core with extension support.
    
    This class extends the original DiscreteEventSimulation with support for
    external event handlers and improved extension points. It maintains all
    functionality of the original implementation while providing a more
    modular and composable architecture.
    
    Parameters
    ----------
    config : SimulationConfig
        Configuration object containing simulation parameters
    environment : Optional[SimulationEnvironment], optional
        Shared simulation environment, by default None
        
    Attributes
    ----------
    config : SimulationConfig
        Simulation configuration
    global_stats : Dict[str, Any]
        Aggregated statistics
    scheduler : ClinicScheduler
        Manages clinic visit scheduling
    patient_generator : PatientGenerator
        Generates patient arrival times
    patients : Dict[str, PatientState]
        Dictionary of patient states keyed by ID
    event_handlers : Dict[str, EventHandler]
        Dictionary of event handlers keyed by event type
    """
    
    def __init__(self, config: SimulationConfig,
                 environment: Optional[SimulationEnvironment] = None):
        """Initialize enhanced DES simulation with configuration.
        
        Parameters
        ----------
        config : SimulationConfig
            Simulation configuration parameters
        environment : Optional[SimulationEnvironment], optional
            Shared simulation environment, by default None
        """
        # Initialize with start date from config
        start_date = datetime.strptime(config.start_date, "%Y-%m-%d") if isinstance(config.start_date, str) else config.start_date
        super().__init__(start_date, environment)
        
        self.config = config
        
        # Register protocol using its type from config
        protocol_type = config.parameters.get("protocol_type", "treat_and_extend")
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
            "unique_discontinuations": 0,
            "monitoring_visits": 0,
            "retreatments": 0,
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
        
        # Event handler registry
        self.event_handlers: Dict[str, EventHandler] = {}
        
        # Register default event handlers
        self.register_default_event_handlers()
    
    def register_default_event_handlers(self):
        """Register default event handlers.
        
        This method sets up the default event handlers for the simulation.
        These handlers can be overridden by external handlers if needed.
        """
        self.event_handlers = {
            "visit": self._handle_visit,
            "treatment_decision": self._handle_treatment_decision,
            "add_patient": self._handle_add_patient
        }
    
    def register_event_handler(self, event_type: str, handler: EventHandler):
        """Register an external event handler.
        
        Parameters
        ----------
        event_type : str
            Type of event to handle
        handler : EventHandler
            Function to handle the event
            
        Notes
        -----
        If a handler already exists for the event type, it will be replaced.
        """
        self.event_handlers[event_type] = handler
        logger.info(f"Registered external handler for event type: {event_type}")
    
    def register_event_handlers(self, handlers: Dict[str, EventHandler]):
        """Register multiple event handlers at once.
        
        Parameters
        ----------
        handlers : Dict[str, EventHandler]
            Dictionary mapping event types to handler functions
        """
        self.event_handlers.update(handlers)
        logger.info(f"Registered {len(handlers)} external event handlers")
    
    def run(self, until: Optional[datetime] = None) -> Dict[str, Any]:
        """Run the simulation until the specified end date.
        
        Parameters
        ----------
        until : Optional[datetime], optional
            End date for the simulation, by default None (uses config end date)
            
        Returns
        -------
        Dict[str, Any]
            Simulation results including patient histories and statistics
        """
        # Set end date
        if until is None:
            until = self.config.start_date + timedelta(days=self.config.duration_days)
        self.clock.end_date = until
        
        # Schedule patient arrivals
        self._schedule_patient_arrivals()
        
        # Run simulation
        logger.info(f"Starting simulation from {self.clock.current_time} to {until}")
        super().run(until)
        
        # Collect results
        results = {
            "patient_histories": self._get_patient_histories(),
            "statistics": self.global_stats
        }
        
        return results
    
    def _schedule_patient_arrivals(self):
        """Schedule patient arrival events based on generator.
        
        Uses Poisson process to generate realistic arrival times.
        Creates 'add_patient' events for each arrival.
        """
        arrival_times = self.patient_generator.generate_arrival_times()
        for arrival_time, patient_num in arrival_times:
            patient_id = f"PATIENT{patient_num:03d}"
            # Get protocol type from config 
            protocol_type = self.config.parameters.get("protocol_type", "treat_and_extend")
            
            self.clock.schedule_event(Event(
                time=arrival_time,
                event_type="add_patient",
                patient_id=patient_id,
                data={"protocol_name": protocol_type},
                priority=1
            ))
    
    def _get_patient_histories(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get patient visit histories for analysis.
        
        Returns
        -------
        Dict[str, List[Dict[str, Any]]]
            Dictionary mapping patient IDs to lists of visit records
        """
        histories = {}
        for patient_id, patient in self.patients.items():
            # Extract visit history if available
            if "visit_history" in patient.state:
                histories[patient_id] = patient.state["visit_history"]
            else:
                # Create minimal history from visits field
                histories[patient_id] = [
                    {
                        "date": visit.get("time"),
                        "actions": visit.get("actions", []),
                        "vision": visit.get("vision", 0),
                        "phase": visit.get("phase", "unknown")
                    }
                    for visit in patient.state.get("visits", [])
                ]
        
        return histories
    
    def process_event(self, event: Event):
        """Process different event types in the simulation.
        
        Parameters
        ----------
        event : Event
            Event to process
            
        Notes
        -----
        Dispatches event to registered handler based on event type.
        If no handler is registered, logs a warning.
        """
        event_type = event.event_type
        
        if event_type in self.event_handlers:
            self.event_handlers[event_type](event)
        else:
            logger.warning(f"No handler registered for event type: {event_type}")
    
    def _handle_add_patient(self, event: Event):
        """Handle patient arrival events.
        
        Parameters
        ----------
        event : Event
            Event containing:
            - patient_id: Generated patient ID
            - data.protocol_name: Protocol to assign
        """
        patient_id = event.patient_id
        protocol_name = event.data["protocol_name"]
        
        # Initialize patient state
        vision_params = self.config.get_vision_params()
        initial_vision = vision_params["baseline_mean"]
        
        # Add randomness to initial vision if standard deviation is specified
        if "baseline_std" in vision_params and vision_params["baseline_std"] > 0:
            initial_vision = np.random.normal(
                initial_vision, 
                vision_params["baseline_std"]
            )
            # Clamp vision between 0-85 ETDRS letters
            initial_vision = min(max(initial_vision, 0), 85)
        
        patient = PatientState(
            patient_id=patient_id,
            protocol_name=protocol_name,
            initial_vision=initial_vision,
            start_time=event.time
        )
        
        # Get protocol parameters from config
        protocol_name = event.data.get("protocol_name", "treat_and_extend")
        protocol_config = self.config.parameters.get("protocols", {}).get(protocol_name, {})
        protocol_phases = protocol_config.get("treatment_phases", {})
        
        # Get loading phase parameters
        loading_phase = protocol_phases.get("initial_loading", {})
        loading_rules = loading_phase.get("rules", {})
        
        # Get interval settings with fallbacks
        loading_interval_weeks = loading_rules.get("interval_weeks", 4)  # Use 4 weeks as fallback
        
        # Initialize patient with necessary tracking fields
        patient.state.update({
            "current_phase": "loading",
            "treatments_in_phase": 0,
            "next_visit_interval": loading_interval_weeks,
            "disease_activity": {
                "fluid_detected": True,
                "consecutive_stable_visits": 0,
                "max_interval_reached": False,
                "current_interval": loading_interval_weeks
            },
            "treatment_status": {
                "active": True,
                "recurrence_detected": False,
                "weeks_since_discontinuation": 0,
                "cessation_type": None,
                "discontinuation_date": None,
            },
            "disease_characteristics": {
                "has_PED": np.random.random() < 0.3,  # 30% of patients have PED
            },
            "visit_history": [],
            "treatment_start": event.time
        })
        
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
        """
        patient_id = event.patient_id
        if patient_id not in self.patients:
            logger.warning(f"Visit event for unknown patient: {patient_id}")
            return
            
        patient = self.patients[patient_id]
        protocol = self.get_protocol(patient.state["protocol"])
        if not protocol:
            logger.warning(f"Unknown protocol for patient: {patient_id}")
            return
            
        # Only process visit if resources are available
        if self.scheduler.request_slot(event, self.clock.end_date):
            self.global_stats["total_visits"] += 1
            
            # Check if this is a monitoring visit
            is_monitoring = event.data.get("is_monitoring", False)
            if is_monitoring:
                self.global_stats["monitoring_visits"] += 1
            
            # Get current phase
            current_phase = protocol.phases.get(patient.state.get("current_phase", "loading"))
            if not current_phase:
                logger.warning(f"Unknown phase for patient: {patient_id}")
                return
                
            # Create protocol event context
            event.phase = current_phase
            event.protocol = protocol
            
            # Extract actions
            actions = event.data.get("actions", [])
            
            # Update global stats for actions
            if "injection" in actions:
                self.global_stats["total_injections"] += 1
            if "oct_scan" in actions:
                self.global_stats["total_oct_scans"] += 1
            
            # Process visit
            clinical_model = ClinicalModel(self.config)
            visit_data = patient.process_visit(event.time, actions, clinical_model)
            
            # Store current vision for vision change calculation
            current_vision = visit_data.get("new_vision", 0)
            baseline_vision = visit_data.get("baseline_vision", 0)
            
            # Calculate vision change from baseline
            vision_change = current_vision - baseline_vision
            if vision_change > 0:
                self.global_stats["vision_improvements"] += 1
            elif vision_change < 0:
                self.global_stats["vision_declines"] += 1
            
            # Add visit to patient history
            if "visit_history" not in patient.state:
                patient.state["visit_history"] = []
            
            # Create visit record
            visit_record = {
                'date': event.time,
                'type': 'monitoring_visit' if is_monitoring else 'regular_visit',
                'actions': actions,
                'vision': current_vision,
                'baseline_vision': baseline_vision,
                'phase': patient.state.get("current_phase", "unknown"),
                'disease_state': 'active' if patient.state.get("disease_activity", {}).get("fluid_detected", True) else 'stable',
                'treatment_status': patient.state.get("treatment_status", {}).copy()
            }
            
            patient.state["visit_history"].append(visit_record)
            
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
        """
        patient_id = event.patient_id
        if patient_id not in self.patients:
            logger.warning(f"Treatment decision for unknown patient: {patient_id}")
            return
            
        patient = self.patients[patient_id]
        protocol = self.get_protocol(patient.state["protocol"])
        if not protocol:
            logger.warning(f"Unknown protocol for patient: {patient_id}")
            return
            
        # Get current phase
        current_phase = protocol.phases.get(patient.state.get("current_phase", "loading"))
        if not current_phase:
            logger.warning(f"Unknown phase for patient: {patient_id}")
            return
            
        # Process visit with current phase
        updated_state = current_phase.process_visit(patient.state)
        patient.state.update(updated_state)
        
        # Check for phase transition
        if patient.state.get("phase_complete"):
            next_phase = protocol.process_phase_transition(current_phase, patient.state)
            if next_phase:
                patient.update_phase(next_phase.phase_type.name.lower())
                self.global_stats["protocol_completions"] += 1
        
        # Handle treat-and-extend protocol specifics
        self._handle_treat_and_extend_updates(patient, event)
        
        # Schedule next visit if treatment is active
        if patient.state.get("treatment_status", {}).get("active", True):
            self._schedule_next_visit(patient_id, event.time)
    
    def _handle_treat_and_extend_updates(self, patient: PatientState, event: Event):
        """Handle treat-and-extend protocol specific updates.
        
        Parameters
        ----------
        patient : PatientState
            Patient state to update
        event : Event
            Current event being processed
        """
        # Get protocol parameters from config
        protocol_name = patient.state.get("protocol", "treat_and_extend")
        protocol_config = self.config.parameters.get("protocols", {}).get(protocol_name, {})
        protocol_phases = protocol_config.get("treatment_phases", {})
        
        # Get loading phase parameters
        loading_phase = protocol_phases.get("initial_loading", {})
        loading_rules = loading_phase.get("rules", {})
        loading_interval_weeks = loading_rules.get("interval_weeks", 4)  # Use 4 weeks as fallback
        injections_required = loading_rules.get("injections_required", 3)  # Use 3 as fallback
        
        # Get maintenance phase parameters
        maintenance_phase = protocol_phases.get("maintenance", {})
        maintenance_rules = maintenance_phase.get("rules", {})
        initial_interval_weeks = maintenance_rules.get("initial_interval_weeks", 8)  # Use 8 weeks as fallback
        max_interval_weeks = maintenance_rules.get("max_interval_weeks", 16)  # Use 16 weeks as fallback
        extension_step = maintenance_rules.get("extension_step", 2)  # Use 2 weeks as fallback
        reduction_step = maintenance_rules.get("reduction_step", 2)  # Use 2 weeks as fallback
        
        # Update treatment phase counts
        phase = patient.state.get("current_phase", "loading")
        treatments_in_phase = patient.state.get("treatments_in_phase", 0) + 1
        patient.state["treatments_in_phase"] = treatments_in_phase
        
        # Update treatment intervals based on phase
        disease_activity = patient.state.get("disease_activity", {})
        fluid_detected = disease_activity.get("fluid_detected", True)
        
        if phase == "loading":
            # Fixed intervals during loading, from configuration
            patient.state["next_visit_interval"] = loading_interval_weeks
            disease_activity["current_interval"] = loading_interval_weeks
            
            # Check for phase completion (default 3 loading injections or from config)
            if treatments_in_phase >= injections_required:
                # Will transition to maintenance in next visit
                patient.state["next_visit_interval"] = initial_interval_weeks
                disease_activity["current_interval"] = initial_interval_weeks
        
        elif phase == "maintenance":
            current_interval = disease_activity.get("current_interval", initial_interval_weeks)
            
            if fluid_detected:
                # Decrease interval by reduction_step, but not below initial interval
                new_interval = max(initial_interval_weeks, current_interval - reduction_step)
                disease_activity["consecutive_stable_visits"] = 0
                disease_activity["max_interval_reached"] = False
            else:
                # Increase interval by extension_step, up to max interval
                new_interval = min(max_interval_weeks, current_interval + extension_step)
                disease_activity["consecutive_stable_visits"] = disease_activity.get("consecutive_stable_visits", 0) + 1
                
                # Check if max interval reached
                if new_interval >= max_interval_weeks:
                    disease_activity["max_interval_reached"] = True
            
            # Update interval
            patient.state["next_visit_interval"] = new_interval
            disease_activity["current_interval"] = new_interval
        
        # Update disease activity
        patient.state["disease_activity"] = disease_activity
    
    def _schedule_next_visit(self, patient_id: str, current_time: datetime):
        """Schedule the next visit for a patient.
        
        Parameters
        ----------
        patient_id : str
            Patient ID to schedule for
        current_time : datetime
            Current simulation time
        """
        if patient_id not in self.patients:
            logger.warning(f"Cannot schedule next visit for unknown patient: {patient_id}")
            return
            
        patient = self.patients[patient_id]
        
        # Get next visit interval
        next_interval = patient.state.get("next_visit_interval", 4)
        if next_interval <= 0:
            next_interval = 4  # Safety check
        elif next_interval > 52:
            next_interval = 52  # Cap at 1 year
        
        # Calculate next visit date
        next_visit_time = current_time + timedelta(weeks=next_interval)
        
        # Only schedule if within simulation timeframe
        if next_visit_time <= self.clock.end_date:
            # Create visit event - always include injection in treat-and-extend
            visit_event = Event(
                time=next_visit_time,
                event_type="visit",
                patient_id=patient_id,
                data={
                    "visit_type": "injection_visit",
                    "actions": ["vision_test", "oct_scan", "injection"]
                },
                priority=1
            )
            
            # Schedule next visit
            self.clock.schedule_event(visit_event)