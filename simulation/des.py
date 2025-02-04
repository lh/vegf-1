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
            "visit_history": []  # Add visit history tracking
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
        visit_data = {
            "vision_change": self._simulate_vision_change(state),
            "oct_findings": self._simulate_oct_findings(state),
            "resources_used": []
        }
        
        actions = event.data.get("actions", [])
        
        # Update state and stats based on actions performed
        if "vision_test" in actions:
            state["current_vision"] += visit_data["vision_change"]
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
            visit_data["resources_used"].append("doctors")
        
        visit_data["resources_used"].append("nurses")  # Always need a nurse
        
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

    def _simulate_vision_change(self, state: Dict) -> int:
        """Simulate vision change with realistic biological variation"""
        import numpy as np
        
        if state["current_step"] == "injection_phase":
            if state["injections"] < 3:
                # Loading phase: improvement likely
                # Shift and reflect log-normal for improvements
                change = 5 - np.random.lognormal(mean=0.5, sigma=0.5)
            else:
                # Just finished loading: smaller improvements
                change = 2 - np.random.lognormal(mean=0.8, sigma=0.3)
        else:
            # Maintenance phase
            interval = state["next_visit_interval"]
            if interval > 8:
                # Higher chance of decline with longer intervals
                change = -np.random.lognormal(mean=-0.5, sigma=0.7)
            else:
                # More stable with shorter intervals
                change = -np.random.lognormal(mean=-2.0, sigma=0.5)
        
        return int(change)

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
