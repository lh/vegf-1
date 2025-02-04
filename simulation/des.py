from datetime import datetime, timedelta
from typing import Dict, List, Optional
from .base import BaseSimulation, Event, SimulationEnvironment
from protocol_models import TreatmentProtocol

class DiscreteEventSimulation(BaseSimulation):
    """
    Pure DES implementation focusing on event flows and aggregate statistics
    rather than individual agent modeling.
    """
    def __init__(self, start_date: datetime, protocols: Dict[str, TreatmentProtocol],
                 environment: Optional[SimulationEnvironment] = None,
                 random_seed: Optional[int] = None):
        super().__init__(start_date, environment)
        self.protocols = protocols
        self.patient_states: Dict[str, Dict] = {}
        
        # Initialize random seed
        import numpy as np
        if random_seed is not None:
            np.random.seed(random_seed)
        self.global_stats = {
            "total_visits": 0,
            "total_injections": 0,
            "total_oct_scans": 0,
            "vision_improvements": 0,
            "vision_declines": 0,
            "protocol_completions": 0,
            "protocol_discontinuations": 0,
            "resource_utilization": {
                "doctors": 0,
                "nurses": 0,
                "oct_machines": 0
            }
        }
        self.resource_capacity = {
            "doctors": 2,
            "nurses": 4,
            "oct_machines": 2
        }
        self.resource_queue = {
            "doctors": [],
            "nurses": [],
            "oct_machines": []
        }
    
    def add_patient(self, patient_id: str, protocol_name: str):
        """Initialize a new patient in the simulation"""
        if protocol_name not in self.protocols:
            raise ValueError(f"Unknown protocol: {protocol_name}")
            
        self.patient_states[patient_id] = {
            "protocol": protocol_name,
            "current_step": "injection_phase",
            "visits": 0,
            "injections": 0,
            "baseline_vision": 65,
            "current_vision": 65,
            "last_visit_date": None,
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
    
    def process_event(self, event: Event):
        """Process different event types in the simulation"""
        if event.event_type == "visit":
            self._handle_visit(event)
        elif event.event_type == "resource_release":
            self._handle_resource_release(event)
        elif event.event_type == "treatment_decision":
            self._handle_treatment_decision(event)
    
    def _handle_visit(self, event: Event):
        """Handle patient visit events"""
        patient_id = event.patient_id
        if patient_id not in self.patient_states:
            return
            
        state = self.patient_states[patient_id]
        
        # Only increment visits if resources are available
        if self._request_resources(event):
            self.global_stats["total_visits"] += 1
            state["visits"] += 1
            state["last_visit_date"] = event.time
            
            # Process visit
            visit_data = self._process_visit(state, event)
            
            # Schedule resource release
            for resource in ["nurses", "oct_machines", "doctors"]:
                if self.global_stats["resource_utilization"][resource] > 0:
                    self.clock.schedule_event(Event(
                        time=event.time + timedelta(minutes=30),
                        event_type="resource_release",
                        patient_id=None,
                        data={"resource_type": resource},
                        priority=1
                    ))
            
            # Add visit to history with proper format including vision data
            visit_record = {
                'date': event.time.replace(second=0, microsecond=0),  # Clean up time
                'actions': event.data.get('actions', []),
                'type': event.data.get('visit_type', 'unknown'),
                'vision': state['current_vision']  # Add current vision to record
            }
            state['visit_history'].append(visit_record)
            
            # Schedule treatment decision
            self.clock.schedule_event(Event(
                time=event.time + timedelta(minutes=30),
                event_type="treatment_decision",
                patient_id=patient_id,
                data=visit_data,
                priority=2
            ))
        else:
            # Reschedule visit for next hour if resources unavailable
            self._reschedule_visit(event)

    def _process_visit(self, state: Dict, event: Event) -> Dict:
        """Process the actual visit activities"""
        # Update weeks since last injection
        if state.get("last_injection_date"):
            weeks_elapsed = (event.time - state["last_injection_date"]).days / 7.0
            state["weeks_since_last_injection"] = weeks_elapsed
        
        visit_data = {
            "vision_change": self._simulate_vision_change(state),
            "oct_findings": self._simulate_oct_findings(state),
            "resources_used": []
        }
        
        actions = event.data.get("actions", [])
        
        # Update state and stats based on actions performed
        if "vision_test" in actions:
            new_vision = state["current_vision"] + visit_data["vision_change"]
            state["current_vision"] = min(max(new_vision, 0), 85)  # Clamp between 0-85
            if visit_data["vision_change"] > 0:
                self.global_stats["vision_improvements"] += 1
            elif visit_data["vision_change"] < 0:
                self.global_stats["vision_declines"] += 1
                
        if "oct_scan" in actions:
            self.global_stats["total_oct_scans"] += 1
            visit_data["resources_used"].append("oct_machines")
                
        if "injection" in actions:
            self.global_stats["total_injections"] += 1
            state["injections"] += 1
            state["last_injection_date"] = event.time
            state["weeks_since_last_injection"] = 0
            visit_data["resources_used"].append("doctors")
        
        visit_data["resources_used"].append("nurses")
        
        return visit_data

    def _handle_resource_release(self, event: Event):
        """Handle resource release events"""
        resource_type = event.data["resource_type"]
        if self.global_stats["resource_utilization"][resource_type] > 0:
            self.global_stats["resource_utilization"][resource_type] -= 1
        
        # Process queued events if any
        if self.resource_queue[resource_type]:
            queued_event = self.resource_queue[resource_type].pop(0)
            self._handle_visit(queued_event)

    def _handle_treatment_decision(self, event: Event):
        """Handle treatment decision events with proper loading phase"""
        patient_id = event.patient_id
        if patient_id not in self.patient_states:
            return
            
        state = self.patient_states[patient_id]
        
        # Determine next visit interval
        if state["current_step"] == "injection_phase":
            if state["injections"] < 3:  # Loading phase
                next_interval = 4  # 4 weeks between loading doses
            else:
                # Move to maintenance phase after 3 injections
                state["current_step"] = "maintenance"
                state["next_visit_interval"] = 8  # Start with 8 weeks
                next_interval = 8
        else:
            # Maintenance phase - adjust interval based on OCT findings
            current_interval = state["next_visit_interval"]
            if event.data["oct_findings"]["fluid_present"]:
                next_interval = max(4, current_interval - 2)
            else:
                next_interval = min(12, current_interval + 2)
                
            state["next_visit_interval"] = next_interval
            
        # Schedule next visit
        self._schedule_next_visit(patient_id, next_interval)

    def _request_resources(self, event: Event) -> bool:
        """Attempt to reserve needed resources for visit"""
        needed_resources = {
            "nurses": 1,
            "oct_machines": 1 if "oct_scan" in event.data.get("actions", []) else 0,
            "doctors": 1 if "injection" in event.data.get("actions", []) else 0
        }
        
        # Check resource availability
        for resource, needed in needed_resources.items():
            if (self.global_stats["resource_utilization"][resource] + 
                needed > self.resource_capacity[resource]):
                # Add to resource queue
                self.resource_queue[resource].append(event)
                return False
        
        # Reserve resources
        for resource, needed in needed_resources.items():
            self.global_stats["resource_utilization"][resource] += needed
            
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
        import numpy as np
        
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

    def _schedule_resource_release(self, visit_time: datetime, visit_data: Dict):
        """Schedule resource release events"""
        for resource in visit_data["resources_used"]:
            self.clock.schedule_event(Event(
                time=visit_time + timedelta(minutes=30),
                event_type="resource_release",
                patient_id=None,
                data={"resource_type": resource},
                priority=1
            ))

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

    def _reschedule_visit(self, event: Event):
        """Reschedule a visit due to resource constraints"""
        self.clock.schedule_event(Event(
            time=event.time + timedelta(hours=1),
            event_type="visit",
            patient_id=event.patient_id,
            data=event.data,
            priority=1
        ))
    def _calculate_loading_phase_change(self, state: Dict) -> float:
        """Calculate vision change during loading phase (first 3 injections)
        
        Real-world outcomes during loading:
        - ~25% improve (>5 letters)
        - ~70% stable (within 5 letters)
        - ~5% decline (>5 letters)
        """
        import numpy as np
        
        # Determine outcome category using realistic probabilities
        outcome = np.random.choice(['improve', 'stable', 'decline'], p=[0.25, 0.70, 0.05])
        
        if outcome == 'improve':
            # Improvement: log-normal distribution for positive changes
            # Mean around 7-8 letters, mostly between 5-15 letters
            change = np.random.lognormal(mean=1.8, sigma=0.3)  # Reduced from 2.0
        elif outcome == 'decline':
            # Decline: negative log-normal for rare but potentially significant losses
            change = -np.random.lognormal(mean=1.8, sigma=0.4)  # Increased from 1.5
        else:
            # Stable: small normal distribution changes with slight negative bias
            change = np.random.normal(-1, 2)  # Changed from (0, 2)
        
        # Apply minimal ceiling effect during loading
        current_vision = state["current_vision"]
        headroom = max(0, 85 - current_vision)
        if change > 0:
            change = min(change, headroom * 0.7)  # Reduced from 0.8
            
        return change

    def _calculate_vision_change(self, state: Dict) -> float:
        """Calculate vision change with memory and ceiling effects"""
        import numpy as np
        
        # Check if we're in loading phase
        if (state.get("current_step") == "injection_phase" and 
            state.get("injections", 0) < 3 and 
            "injection" in state.get("current_actions", [])):
            
            return self._calculate_loading_phase_change(state)
        
        # Get reference points
        current_vision = state["current_vision"]
        best_vision = state.get("best_vision_achieved", current_vision)
        baseline_vision = state.get("baseline_vision", current_vision)
        last_response = state.get("last_treatment_response", 0)
        response_history = state.get("treatment_response_history", [])
        
        # Calculate headroom (ceiling effect)
        absolute_max = 85
        theoretical_max = min(absolute_max, best_vision + 3)  # Reduced from +5
        headroom = max(0, theoretical_max - current_vision)
        headroom_factor = np.exp(-0.3 * headroom)  # Increased from -0.2
        
        if "injection" in state.get("current_actions", []):
            # Treatment effect with stronger regression to mean
            memory_factor = 0.6  # Reduced from 0.7
            base_effect = 0
            
            if response_history:
                base_effect = np.mean(response_history) * memory_factor
                if base_effect > 3:  # Reduced from 5
                    base_effect *= 0.7  # Reduced from 0.8
            
            # More modest improvements in maintenance phase
            random_effect = np.random.lognormal(mean=0.3, sigma=0.4)  # Reduced from 0.5
            
            improvement = (base_effect + random_effect) * (1 - headroom_factor)
            
            # Add small random chance of decline even with treatment
            if np.random.random() < 0.15:  # 15% chance of decline
                improvement = -np.random.lognormal(mean=-1.5, sigma=0.3)
            
            # Update treatment history
            state["last_treatment_response"] = improvement
            state["treatment_response_history"].append(improvement)
            if len(state["treatment_response_history"]) > 3:
                state["treatment_response_history"].pop(0)
            
            return improvement
        else:
            # Stronger natural disease progression
            weeks_since_injection = state.get("weeks_since_last_injection", 0)
            
            # Stronger base decline
            base_decline = -np.random.lognormal(mean=-1.5, sigma=0.5)  # Increased from -2.0
            
            # More aggressive time factor
            time_factor = 1 + (weeks_since_injection/8)  # Changed from /12
            
            # Stronger vision factor
            vision_factor = 1 + max(0, (current_vision - baseline_vision)/15)  # Changed from /20
            
            # Calculate total decline
            total_decline = base_decline * time_factor * vision_factor
            
            return total_decline
