from datetime import datetime, timedelta
from typing import Dict, List, Optional
from .base import BaseSimulation, Event, SimulationEnvironment
from protocol_models import TreatmentProtocol

class Patient:
    def __init__(self, patient_id: str, protocol: TreatmentProtocol):
        self.patient_id = patient_id
        self.protocol = protocol
        self.state: Dict = {
            "current_step": None,
            "baseline_vision": None,
            "last_vision": None,
            "last_oct": None,
            "disease_activity": None,
            "current_interval": None
        }
        self.history: List[Dict] = []
        
    def record_visit(self, visit_data: Dict):
        """Record visit data and update patient state"""
        # Ensure required fields exist
        if "date" not in visit_data:
            raise ValueError("Visit data must include date")
        if "type" not in visit_data:
            raise ValueError("Visit data must include type")
            
        self.history.append(visit_data)
        
        # Update state based on visit data
        if "vision" in visit_data:
            if self.state["baseline_vision"] is None:
                self.state["baseline_vision"] = visit_data["vision"]
            self.state["last_vision"] = visit_data["vision"]
            
        if "oct" in visit_data:
            self.state["last_oct"] = visit_data["oct"]

class AgentBasedSimulation(BaseSimulation):
    def __init__(self, start_date: datetime, protocols: Dict[str, TreatmentProtocol],
                 environment: Optional[SimulationEnvironment] = None):
        super().__init__(start_date, environment)
        self.protocols = protocols
        self.agents: Dict[str, Patient] = {}
    
    def add_patient(self, patient_id: str, protocol_name: str):
        if protocol_name in self.protocols:
            self.agents[patient_id] = Patient(patient_id, self.protocols[protocol_name])
    
    def process_event(self, event: Event):
        if event.patient_id in self.agents:
            agent = self.agents[event.patient_id]
            if event.event_type == "visit":
                self._handle_agent_visit(agent, event)
            elif event.event_type == "decision":
                self._handle_agent_decision(agent, event)
    
    def _handle_agent_visit(self, agent: Patient, event: Event):
        """Handle a patient visit event"""
        visit_type = event.data.get("visit_type")
        if not visit_type:
            return
            
        # Create visit data with proper date field
        visit_data = {
            "date": event.time,
            "type": visit_type.get("visit_type", "unknown"),
            "actions": []  # Initialize empty actions list
        }
        
        # Perform visit actions
        if "vision_test" in visit_type.get("actions", []):
            visit_data["actions"].append("vision_test")
            visit_data["vision"] = self._simulate_vision_test(agent)
            
        if "oct_scan" in visit_type.get("actions", []):
            visit_data["actions"].append("oct_scan")
            visit_data["oct"] = self._simulate_oct_scan(agent)
            
        if "injection" in visit_type.get("actions", []):
            visit_data["actions"].append("injection")
            visit_data["injection"] = {
                "agent": agent.protocol.agent,
                "dose": "0.5mg"
            }
            
        # Record visit
        agent.record_visit(visit_data)
        
        # Schedule decisions
        for decision in visit_type.get("decisions", []):
            self.clock.schedule_event(Event(
                time=event.time,
                event_type="decision",
                patient_id=agent.patient_id,
                data={"decision_type": decision, "visit_data": visit_data},
                priority=2  # Decisions happen after visits
            ))

    def _handle_agent_decision(self, agent: Patient, event: Event):
        """Handle a patient decision event"""
        decision_type = event.data.get("decision_type")
        visit_data = event.data.get("visit_data", {})
        
        if decision_type == "nurse_vision_check":
            self._handle_nurse_vision_check(agent, visit_data)
        elif decision_type == "doctor_oct_review":
            self._handle_doctor_oct_review(agent, visit_data)
        elif decision_type == "doctor_treatment_decision":
            self._handle_doctor_treatment_decision(agent, visit_data)
            
    def _simulate_vision_test(self, agent: Patient) -> int:
        """Simulate a vision test result"""
        if agent.state["baseline_vision"] is None:
            # First visit - set baseline between 50-80 letters
            return 65  # Fixed value for reproducibility, could be random
        return agent.state["last_vision"]  # Return last recorded vision
        
    def _simulate_oct_scan(self, agent: Patient) -> Dict:
        """Simulate an OCT scan result"""
        # Placeholder - implement actual OCT simulation logic
        return {"thickness": 300, "fluid_present": True}
        
    def _handle_nurse_vision_check(self, agent: Patient, visit_data: Dict):
        """Handle nurse vision check decision"""
        if agent.state["baseline_vision"] is not None:
            vision_drop = agent.state["baseline_vision"] - visit_data.get("vision", 0)
            if vision_drop >= 15:
                # Schedule doctor review
                self.clock.schedule_event(Event(
                    time=visit_data["date"],
                    event_type="decision",
                    patient_id=agent.patient_id,
                    data={"decision_type": "doctor_treatment_decision", "visit_data": visit_data},
                    priority=3
                ))
                
    def _handle_doctor_oct_review(self, agent: Patient, visit_data: Dict):
        """Handle doctor OCT review decision"""
        oct_data = visit_data.get("oct", {})
        if oct_data.get("fluid_present"):
            agent.state["disease_activity"] = "active"
        else:
            agent.state["disease_activity"] = "stable"
            
    def _handle_doctor_treatment_decision(self, agent: Patient, visit_data: Dict):
        """Handle doctor treatment decision"""
        current_step = agent.state["current_step"]
        if current_step and "dynamic_interval" in current_step:
            self._adjust_treatment_interval(agent)
            
    def _adjust_treatment_interval(self, agent: Patient):
        """
        Adjust treatment interval based on treat-and-extend protocol rules
        """
        current_step = agent.protocol.steps.get(agent.state["current_step"])
        if not current_step or current_step.step_type != "dynamic_interval":
            return
            
        params = current_step.parameters
        current_interval = agent.state.get("current_interval", params["initial_interval"])
        adjustment = params["adjustment_weeks"]
        
        if agent.state["disease_activity"] == "recurring":
            # Decrease interval if disease is recurring
            new_interval = max(current_interval - adjustment, params["min_interval"])
        elif agent.state["disease_activity"] == "stable":
            # Increase interval if disease is stable
            new_interval = min(current_interval + adjustment, params["max_interval"])
        else:
            # Keep same interval if disease activity status is unclear
            new_interval = current_interval
            
        agent.state["current_interval"] = new_interval
        
        # Schedule next visit based on new interval
        next_visit = {
            "visit_type": "injection_visit",
            "actions": ["vision_test", "oct_scan", "injection"],
            "decisions": ["nurse_vision_check", "doctor_treatment_decision"]
        }
        
        self.clock.schedule_event(Event(
            time=self.clock.current_time + timedelta(weeks=new_interval),
            event_type="visit",
            patient_id=agent.patient_id,
            data={"visit_type": next_visit},
            priority=1
        ))
