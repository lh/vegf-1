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
        
        # Set initial protocol step if not set
        if agent.state["current_step"] is None:
            agent.state["current_step"] = "injection_phase"
            agent.state["injections_given"] = 0
        
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
            agent.state["injections_given"] = agent.state.get("injections_given", 0) + 1
        
        # Record visit
        agent.record_visit(visit_data)
        
        # Schedule decisions
        for decision in visit_type.get("decisions", []):
            if decision == "doctor_treatment_decision":
                # Add OCT review before treatment decision
                self.clock.schedule_event(Event(
                    time=event.time,
                    event_type="decision",
                    patient_id=agent.patient_id,
                    data={"decision_type": "doctor_oct_review", "visit_data": visit_data},
                    priority=2
                ))
            self.clock.schedule_event(Event(
                time=event.time,
                event_type="decision",
                patient_id=agent.patient_id,
                data={"decision_type": decision, "visit_data": visit_data},
                priority=3 if decision == "doctor_treatment_decision" else 2
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
        """Simulate a vision test result with realistic variation"""
        if agent.state["baseline_vision"] is None:
            # First visit - set baseline between 50-80 letters
            return 65  # Fixed value for reproducibility
            
        # Add small variations based on disease activity
        base_vision = agent.state["last_vision"]
        if agent.state.get("disease_activity") == "recurring":
            variation = -3  # Vision tends to decrease with active disease
        else:
            variation = 1  # Small improvement possible with stable disease
            
        new_vision = base_vision + variation
        return min(max(new_vision, 0), 100)  # Clamp between 0-100 letters
        
    def _simulate_oct_scan(self, agent: Patient) -> Dict:
        """Simulate OCT with more realistic disease progression"""
        current_interval = agent.state.get("current_interval", 8)
        last_visit = agent.history[-1]["date"] if agent.history else None
        weeks_since_injection = 0
        
        if last_visit:
            weeks_since_injection = (self.clock.current_time - last_visit).days / 7.0
        
        if current_interval is None:
            current_interval = 8
        current_interval = float(current_interval)
        
        # Base thickness varies with treatment effect
        base_thickness = 250
        treatment_effect = 50 * (1 - (weeks_since_injection / current_interval))
        
        # Disease progression factor - increases over time
        progression_factor = len(agent.history) / 20.0  # Slowly increases with visits
        
        # Calculate thickness with multiple factors
        thickness = (
            base_thickness 
            - treatment_effect  # Treatment reduces thickness
            + (progression_factor * 10)  # Disease slowly progresses
            + (weeks_since_injection * 2)  # Thickness increases between treatments
        )
        
        # Fluid risk calculation
        fluid_risk = (
            (weeks_since_injection / current_interval) * 0.4  # Time factor
            + (progression_factor * 0.2)  # Disease progression
            + (0.3 if thickness > 280 else 0)  # Thickness factor
        )
        
        # Determine fluid presence
        fluid_present = fluid_risk > 0.6
        
        return {
            "thickness": round(thickness, 1),
            "fluid_present": fluid_present
        }
        
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
        """Handle doctor OCT review decision with more sophisticated analysis"""
        oct_data = visit_data.get("oct", {})
        
        # Get previous OCT data
        prev_oct = None
        for visit in reversed(agent.history[:-1]):  # Skip current visit
            if "oct" in visit:
                prev_oct = visit["oct"]
                break
        
        # Determine disease activity based on multiple factors
        disease_recurring = False
        
        # Check for fluid
        if oct_data.get("fluid_present"):
            disease_recurring = True
        
        # Check thickness change
        if prev_oct:
            thickness_change = oct_data["thickness"] - prev_oct["thickness"]
            if thickness_change > 20:  # Significant increase in thickness
                disease_recurring = True
        
        # Update disease activity state
        if disease_recurring:
            agent.state["disease_activity"] = "recurring"
        else:
            agent.state["disease_activity"] = "stable"
            
    def _handle_doctor_treatment_decision(self, agent: Patient, visit_data: Dict):
        """Handle doctor treatment decision with logging"""
        current_step = agent.state["current_step"]
        old_interval = agent.state.get("current_interval")
        
        # Handle initial loading phase
        if current_step == "injection_phase":
            if agent.state["injections_given"] < 3:
                # Schedule next loading dose in 4 weeks
                next_visit = {
                    "visit_type": "injection_visit",
                    "actions": ["vision_test", "oct_scan", "injection"],
                    "decisions": ["nurse_vision_check", "doctor_treatment_decision"]
                }
                
                self.clock.schedule_event(Event(
                    time=self.clock.current_time + timedelta(weeks=4),
                    event_type="visit",
                    patient_id=agent.patient_id,
                    data={"visit_type": next_visit},
                    priority=1
                ))
            else:
                # Move to assessment phase after 3 injections
                agent.state["current_step"] = "dynamic_interval"
                agent.state["current_interval"] = 8  # Start with 8 week interval
                self._schedule_next_visit(agent)
        
        elif current_step == "dynamic_interval":
            self._adjust_treatment_interval(agent)
            
    def _adjust_treatment_interval(self, agent: Patient):
        """
        Adjust treatment interval based on treat-and-extend protocol rules
        """
        # Find the current step in the protocol steps list
        current_step = None
        for step in agent.protocol.steps:
            if step.get("step_type") == agent.state["current_step"]:
                current_step = step
                break
                
        if not current_step or current_step.get("step_type") != "dynamic_interval":
            return
                
        params = current_step.get("parameters", {})
        current_interval = agent.state.get("current_interval", params.get("initial_interval", 8))
        adjustment = params.get("adjustment_weeks", 2)
            
        if agent.state["disease_activity"] == "recurring":
            # Decrease interval if disease is recurring
            new_interval = max(current_interval - adjustment, params.get("min_interval", 4))
        elif agent.state["disease_activity"] == "stable":
            # Increase interval if disease is stable
            new_interval = min(current_interval + adjustment, params.get("max_interval", 12))
        else:
            # Keep same interval if disease activity status is unclear
            new_interval = current_interval
                
        agent.state["current_interval"] = new_interval
                
        # Store initial interval for logging
        initial_interval = agent.state.get("current_interval")
        
        # Update to new interval
        agent.state["current_interval"] = new_interval
        
        # Add logging for interval changes
        if initial_interval != new_interval:
            print(f"\nInterval adjusted: {initial_interval} -> {new_interval} weeks")
            print(f"Reason: Disease activity is {agent.state.get('disease_activity')}")
                
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
    def _schedule_next_visit(self, agent: Patient):
        """Schedule next visit based on current interval"""
        next_visit = {
            "visit_type": "injection_visit",
            "actions": ["vision_test", "oct_scan", "injection"],
            "decisions": ["nurse_vision_check", "doctor_treatment_decision"]
        }
        
        interval_weeks = agent.state.get("current_interval", 8)
        
        self.clock.schedule_event(Event(
            time=self.clock.current_time + timedelta(weeks=interval_weeks),
            event_type="visit",
            patient_id=agent.patient_id,
            data={"visit_type": next_visit},
            priority=1
        ))
