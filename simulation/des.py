from datetime import datetime, timedelta
from typing import Dict, List, Optional
import numpy as np
from .base import BaseSimulation, Event, SimulationEnvironment
from protocol_models import TreatmentProtocol
from .config import SimulationConfig

class DiscreteEventSimulation(BaseSimulation):
    """
    Pure DES implementation focusing on event flows and aggregate statistics
    rather than individual agent modeling.
    """
    def __init__(self, config: SimulationConfig,
                 environment: Optional[SimulationEnvironment] = None):
        """Initialize DES with configuration"""
        super().__init__(config.start_date, environment)
        self.config = config
        # Register protocol using its type from config
        protocol_type = "test_simulation"  # Use the type from YAML config
        self.register_protocol(protocol_type, config.protocol)
        self.patient_states: Dict[str, Dict] = {}
        
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
        
        # Track daily appointments
        self.daily_slots = {}  # date -> number of appointments
    
    def add_patient(self, patient_id: str, protocol_name: str):
        """Initialize a new patient in the simulation"""
        if protocol_name not in self.protocols:
            raise ValueError(f"Unknown protocol: {protocol_name}")
            
        vision_params = self.config.get_vision_params()
        initial_vision = vision_params["baseline_mean"]
        self.patient_states[patient_id] = {
            "protocol": protocol_name,
            "current_step": "injection_phase",
            "visits": 0,
            "injections": 0,
            "baseline_vision": initial_vision,
            "current_vision": initial_vision,
            "last_visit_date": self.clock.current_time,  # Set initial visit date
            "next_visit_interval": 4,
            "treatment_start": self.clock.current_time,
            "visit_history": [],
            # Add these new state variables
            "best_vision_achieved": 65,
            "last_treatment_response": None,
            "treatment_response_history": [],
            "weeks_since_last_injection": 0,
            "last_injection_date": None
        }
        
        # Schedule initial visit
        initial_visit = {
            "visit_type": "injection_visit",
            "actions": ["vision_test", "oct_scan", "injection"],
            "decisions": ["nurse_vision_check", "doctor_treatment_decision"]
        }
        
        self.clock.schedule_event(Event(
            time=self.clock.current_time,
            event_type="visit",
            patient_id=patient_id,
            data=initial_visit,
            priority=1
        ))
    
    def process_event(self, event: Event):
        """Process different event types in the simulation"""
        if event.event_type == "visit":
            self._handle_visit(event)
        elif event.event_type == "treatment_decision":
            self._handle_treatment_decision(event)
    
    def _handle_visit(self, event: Event):
        """Handle patient visit events using protocol objects"""
        patient_id = event.patient_id
        if patient_id not in self.patient_states:
            return
            
        state = self.patient_states[patient_id]
        protocol = self.get_protocol(state["protocol"])
        if not protocol:
            return
            
        # Only increment visits if resources are available
        if self._request_resources(event):
            self.global_stats["total_visits"] += 1
            state["visits"] += 1
            state["last_visit_date"] = event.time
            
            # Get current phase
            current_phase = protocol.phases.get(state.get("current_phase", "loading"))
            if not current_phase:
                return
                
            # Create protocol event
            event.phase = current_phase
            event.protocol = protocol
            
            # Process visit
            visit_data = self._process_visit(state, event)
            
            # Add visit to history with proper format
            visit_record = {
                'date': event.time.replace(second=0, microsecond=0),
                'actions': [action.value for action in event.get_required_actions()],
                'type': event.get_visit_type().name if event.get_visit_type() else "unknown",
                'vision': state['current_vision'],
                'phase': current_phase.phase_type.name
            }
            state['visit_history'].append(visit_record)
            
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
        else:
            # Reschedule visit for next available day if no capacity today
            self._reschedule_visit(event)

    def _process_visit(self, state: Dict, event: Event) -> Dict:
        """Process the actual visit activities"""
        # Update weeks since last injection
        if state.get("last_injection_date"):
            weeks_elapsed = (event.time - state["last_injection_date"]).days / 7.0
            state["weeks_since_last_injection"] = weeks_elapsed
        
        # Prepare state for vision calculation
        calc_state = {
            "current_vision": state["current_vision"],
            "best_vision_achieved": state.get("best_vision_achieved", state["current_vision"]),
            "baseline_vision": state["baseline_vision"],
            "last_treatment_response": state.get("last_treatment_response", 0),
            "treatment_response_history": state.get("treatment_response_history", []),
            "current_step": state["current_step"],
            "injections": state.get("injections", 0),
            "current_actions": event.data.get("actions", []),
            "weeks_since_last_injection": state.get("weeks_since_last_injection", 0)
        }
        
        # Calculate vision change using same method as ABS
        vision_change = self._simulate_vision_change(calc_state)
        
        # Update state with results
        state.update({
            "last_treatment_response": calc_state.get("last_treatment_response"),
            "treatment_response_history": calc_state.get("treatment_response_history", []),
            "best_vision_achieved": calc_state.get("best_vision_achieved")
        })
        
        visit_data = {
            "vision_change": vision_change,
            "oct_findings": self._simulate_oct_findings(state),
            "actions_performed": []
        }
        
        actions = event.data.get("actions", [])
        
        # Update state and stats based on actions performed
        if "vision_test" in actions:
            # Add measurement noise to vision test
            measurement_noise = np.random.normal(0, 2)  # SD of 2 letters
            new_vision = state["current_vision"] + vision_change + measurement_noise
            state["current_vision"] = min(max(new_vision, 0), 85)  # Clamp between 0-85
            if vision_change > 0:
                self.global_stats["vision_improvements"] += 1
            elif vision_change < 0:
                self.global_stats["vision_declines"] += 1
            visit_data["actions_performed"].append("vision_test")
        
        if "oct_scan" in actions:
            self.global_stats["total_oct_scans"] += 1
            visit_data["actions_performed"].append("oct_scan")
        
        if "injection" in actions:
            self.global_stats["total_injections"] += 1
            state["injections"] += 1
            state["last_injection_date"] = event.time
            state["weeks_since_last_injection"] = 0
            visit_data["actions_performed"].append("injection")
        
        return visit_data

    def _handle_treatment_decision(self, event: Event):
        """Handle treatment decision events using protocol objects"""
        patient_id = event.patient_id
        if patient_id not in self.patient_states:
            return
            
        state = self.patient_states[patient_id]
        protocol = self.get_protocol(state["protocol"])
        if not protocol:
            return
            
        # Get current phase
        current_phase = protocol.phases.get(state.get("current_phase", "loading"))
        if not current_phase:
            return
            
        # Process visit with current phase
        updated_state = current_phase.process_visit(state)
        state.update(updated_state)
        
        # Check for phase transition
        if state.get("phase_complete"):
            next_phase = protocol.process_phase_transition(current_phase, state)
            if next_phase:
                state["current_phase"] = next_phase.phase_type.name.lower()
                
        # Schedule next visit based on protocol with safety checks
        next_interval = state.get("next_visit_weeks", current_phase.visit_interval_weeks)
        if next_interval <= 0:
            next_interval = 4
        elif next_interval > 52:
            next_interval = 52
            
        # Only schedule next visit if we haven't reached the end date
        if event.time + timedelta(weeks=next_interval) <= self.config.start_date + timedelta(days=self.config.duration_days):
            self._schedule_next_visit(patient_id, next_interval)

    def _request_resources(self, event: Event) -> bool:
        """Check if there's capacity for this visit on this day"""
        visit_date = event.time.date()
        
        # Initialize slots for this date if not exists
        if visit_date not in self.daily_slots:
            self.daily_slots[visit_date] = 0
            
        # Check if this is a clinic day (Mon-Fri by default)
        if event.time.weekday() >= self.global_stats["scheduling"]["days_per_week"]:
            self._reschedule_visit(event, next_clinic_day=True)
            return False
            
        # Check daily capacity
        if self.daily_slots[visit_date] >= self.global_stats["scheduling"]["daily_capacity"]:
            self._reschedule_visit(event, next_clinic_day=False)
            return False
            
        # If we get here, we have capacity
        self.daily_slots[visit_date] += 1
        return True

    def _simulate_vision_change(self, state: Dict) -> float:
        """Calculate vision change with memory and ceiling effects"""
        import numpy as np
        
        # Get reference points
        current_vision = state["current_vision"]
        best_vision = state.get("best_vision_achieved", current_vision)
        baseline_vision = state.get("baseline_vision", current_vision)
        last_response = state.get("last_treatment_response", 0)
        response_history = state.get("treatment_response_history", [])
        
        # Calculate headroom (ceiling effect)
        absolute_max = 85  # ETDRS letter score maximum
        theoretical_max = min(absolute_max, best_vision + 5)
        headroom = max(0, theoretical_max - current_vision)
        headroom_factor = np.exp(-0.2 * headroom)
        
        # Check if this is an injection visit
        is_injection = state.get("injections", 0) > state.get("last_recorded_injection", -1)
        
        if is_injection:
            # Treatment effect
            memory_factor = 0.7
            base_effect = 0
            
            if response_history:
                base_effect = np.mean(response_history) * memory_factor
                if base_effect > 5:
                    base_effect *= 0.8
            
            # Different behavior for loading phase vs maintenance
            if state["current_step"] == "injection_phase" and state.get("injections", 0) < 3:
                random_effect = np.random.lognormal(mean=1.2, sigma=0.3)
            else:
                random_effect = np.random.lognormal(mean=0.5, sigma=0.4)
            
            improvement = (base_effect + random_effect) * (1 - headroom_factor)
            
            # Update treatment history
            state["last_treatment_response"] = improvement
            state["treatment_response_history"].append(improvement)
            if len(state["treatment_response_history"]) > 3:
                state["treatment_response_history"].pop(0)
            
            # Update best vision if applicable
            if current_vision + improvement > best_vision:
                state["best_vision_achieved"] = min(absolute_max, current_vision + improvement)
                
            return improvement
        else:
            # Natural disease progression
            weeks_since_injection = state.get("weeks_since_last_injection", 0)
            
            base_decline = -np.random.lognormal(mean=-2.0, sigma=0.5)
            
            time_factor = 1 + (weeks_since_injection/12)
            vision_factor = 1 + max(0, (current_vision - baseline_vision)/20)
            response_factor = 1.0
            
            if response_history:
                mean_response = np.mean(response_history)
                response_factor = 1 + max(0, mean_response/10)
                
            total_decline = base_decline * time_factor * vision_factor * response_factor
            
            return total_decline

    def _simulate_oct_findings(self, state: Dict) -> Dict:
        """Simulate OCT findings with realistic biological variation"""
        # Base risk increases with interval length
        interval = state["next_visit_interval"]
        base_risk = 0.2 + (interval - 4) * 0.05
        
        # Add random component from beta distribution
        risk_variation = np.random.beta(2, 5)
        fluid_risk = min(base_risk + risk_variation * 0.3, 1.0)
        
        # Thickness changes based on treatment phase
        if state["current_step"] == "injection_phase":
            if state["injections"] < 3:
                # Strong improvement during loading
                thickness_change = -np.random.lognormal(mean=1.5, sigma=0.3)
            else:
                # Moderate improvement after loading
                thickness_change = -np.random.lognormal(mean=1.0, sigma=0.4)
        else:
            # Maintenance phase - changes depend on interval
            if fluid_risk > 0.5:
                # Disease activity - thickness increases
                thickness_change = np.random.lognormal(mean=1.0, sigma=0.5)
            else:
                # Stable - small variations
                thickness_change = np.random.normal(0, 5)
        
        return {
            "fluid_present": np.random.random() < fluid_risk,
            "thickness_change": thickness_change
        }

    def _schedule_next_visit(self, patient_id: str, weeks: int):
        """Schedule the next visit for a patient"""
        state = self.patient_states[patient_id]
        last_visit = state["last_visit_date"]
        
        next_visit = {
            "visit_type": "injection_visit",
            "actions": ["vision_test", "oct_scan", "injection"],
            "decisions": ["nurse_vision_check", "doctor_treatment_decision"]
        }
        
        # Calculate next visit time based on last visit, not current time
        next_time = last_visit + timedelta(weeks=weeks)
        # Keep the same time of day as original appointment
        next_time = next_time.replace(hour=last_visit.hour, minute=last_visit.minute)
        
        self.clock.schedule_event(Event(
            time=next_time,
            event_type="visit",
            patient_id=patient_id,
            data=next_visit,
            priority=1
        ))

    def _reschedule_visit(self, event: Event, next_clinic_day: bool = False):
        """Reschedule a visit to the next available day"""
        # Calculate the intended end date of the simulation
        intended_end_date = self.config.start_date + timedelta(days=self.config.duration_days)
        
        # If the original event time is already past the intended duration, don't reschedule
        if event.time >= intended_end_date:
            return
            
        # Calculate next available day
        next_time = event.time
        if next_clinic_day:
            # Find next clinic day (e.g., if today is Friday, go to Monday)
            days_to_add = (self.global_stats["scheduling"]["days_per_week"] - 
                          next_time.weekday())
            if days_to_add <= 0:
                days_to_add += self.global_stats["scheduling"]["days_per_week"]
            next_time += timedelta(days=days_to_add)
        else:
            # Just go to next day
            next_time += timedelta(days=1)
            
        # Ensure we're on a clinic day
        while next_time.weekday() >= self.global_stats["scheduling"]["days_per_week"]:
            next_time += timedelta(days=1)
            
        # Check if the next day has available capacity
        next_date = next_time.date()
        if next_date not in self.daily_slots:
            self.daily_slots[next_date] = 0
            
        # If next day is full, try the following days
        while (self.daily_slots[next_date] >= self.global_stats["scheduling"]["daily_capacity"] and 
               next_time <= intended_end_date):
            next_time += timedelta(days=1)
            while next_time.weekday() >= self.global_stats["scheduling"]["days_per_week"]:
                next_time += timedelta(days=1)
            next_date = next_time.date()
            if next_date not in self.daily_slots:
                self.daily_slots[next_date] = 0
                
        # Only reschedule if we haven't reached the end date and found a day with capacity
        if next_time <= intended_end_date:
            self.global_stats["scheduling"]["rescheduled_visits"] += 1
            self.clock.schedule_event(Event(
                time=next_time,
                event_type="visit",
                patient_id=event.patient_id,
                data=event.data,
                priority=1
            ))
