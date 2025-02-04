from datetime import datetime, timedelta
from typing import Dict, List, Optional
import numpy as np
from .base import BaseSimulation, Event, SimulationEnvironment
from protocol_models import TreatmentProtocol

class Patient:
    def __init__(self, patient_id: str, protocol: TreatmentProtocol):
        self.patient_id = patient_id
        self.protocol = protocol
        initial_vision = 65  # Starting vision
        self.state: Dict = {
            "current_step": "injection_phase",  # Start in injection phase
            "baseline_vision": initial_vision,
            "last_vision": initial_vision,
            "last_oct": None,
            "disease_activity": None,
            "current_interval": 8.0,  # Initialize with default interval
            "injections": 0,  # Use injections instead of injections_given
            "best_vision_achieved": initial_vision,  # Initialize best vision
            "last_treatment_response": None,
            "treatment_response_history": [],
            "weeks_since_last_injection": 0,
            "last_injection_date": None,
            "current_actions": []
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
                 environment: Optional[SimulationEnvironment] = None,
                 verbose: bool = False):
        super().__init__(start_date, environment)
        self.protocols = protocols
        self.agents: Dict[str, Patient] = {}
        self.verbose = verbose
    
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
            agent.state["last_injection_date"] = event.time
            agent.state["weeks_since_last_injection"] = 0
            agent.state["current_actions"].append("injection")  # Add to current actions

        # Update weeks since last injection
        if agent.state.get("last_injection_date"):
            weeks_elapsed = (event.time - agent.state["last_injection_date"]).days / 7.0
            agent.state["weeks_since_last_injection"] = weeks_elapsed
        
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
        """Simulate vision test with proper injection effects and measurement noise"""
        # Baseline vision is now always initialized
            
        # Prepare state for vision calculation
        calc_state = {
            "current_vision": agent.state["last_vision"],
            "best_vision_achieved": agent.state.get("best_vision_achieved", agent.state["last_vision"]),
            "baseline_vision": agent.state["baseline_vision"],
            "last_treatment_response": agent.state.get("last_treatment_response", 0),
            "treatment_response_history": agent.state.get("treatment_response_history", []),
            "current_step": agent.state["current_step"],
            "injections_given": agent.state.get("injections_given", 0),
            "current_actions": ["injection"] if "injection" in agent.state.get("current_actions", []) else [],
            "weeks_since_last_injection": agent.state.get("weeks_since_last_injection", 0)
        }
        
        # Add injection to current actions if this is an injection visit
        if "injection" in agent.state.get("current_actions", []):
            calc_state["current_actions"].append("injection")
        
        change = self._calculate_vision_change(calc_state)
        
        # Update agent state
        agent.state.update({
            "last_treatment_response": calc_state.get("last_treatment_response"),
            "treatment_response_history": calc_state.get("treatment_response_history", []),
            "best_vision_achieved": calc_state.get("best_vision_achieved"),
            "current_actions": []  # Reset current actions after processing
        })
        
        # Add measurement noise
        measurement_noise = np.random.normal(0, 2)  # SD of 2 letters
        
        new_vision = agent.state["last_vision"] + change + measurement_noise
        return int(min(max(new_vision, 0), 85))  # Clamp between 0-85 letters
        
    def _simulate_oct_scan(self, agent: Patient) -> Dict:
        """Simulate OCT with realistic biological variation"""
        current_interval = agent.state.get("current_interval", 8.0)
        last_visit = agent.history[-1]["date"] if agent.history else None
        weeks_since_injection = 0
        
        if last_visit:
            weeks_since_injection = (self.clock.current_time - last_visit).days / 7.0
        
        # Base thickness with log-normal variation
        base_thickness = 250 + np.random.lognormal(mean=0, sigma=0.3)
        
        # Treatment effect varies by phase
        if agent.state["current_step"] == "injection_phase" and agent.state.get("injections_given", 0) < 3:
            # Stronger, more consistent effect during loading
            treatment_effect = 50 * (1 - (weeks_since_injection / current_interval))
            effect_variation = np.random.lognormal(mean=-1.5, sigma=0.3)  # Small variation
        else:
            # More variable effect during maintenance
            treatment_effect = 40 * (1 - (weeks_since_injection / current_interval))
            effect_variation = np.random.lognormal(mean=-1.0, sigma=0.5)  # Larger variation
        
        treatment_effect *= (1 + effect_variation)
        
        # Disease progression increases over time with log-normal variation
        time_factor = len(agent.history) / 20.0
        progression = time_factor * np.random.lognormal(mean=0, sigma=0.4) * 10
        
        thickness = (
            base_thickness 
            - treatment_effect
            + progression
            + (weeks_since_injection * np.random.lognormal(mean=0, sigma=0.3))
        )
        
        # Fluid risk calculation with asymmetric distribution
        base_risk = (weeks_since_injection / current_interval) * 0.4
        risk_variation = np.random.beta(2, 5)  # Beta distribution for [0,1] bounded variation
        fluid_risk = min(base_risk + risk_variation * 0.3, 1.0)
        
        return {
            "thickness": round(thickness, 1),
            "fluid_present": fluid_risk > 0.6
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
        """Handle doctor OCT review with more sophisticated analysis"""
        oct_data = visit_data.get("oct", {})
        
        # Get current interval - use the value from state or default to 8.0
        current_interval = agent.state["current_interval"]  # This will now always have a value
        
        # Get previous OCT data
        prev_oct = None
        for visit in reversed(agent.history[:-1]):
            if "oct" in visit:
                prev_oct = visit["oct"]
                break
        
        # Calculate risk score for disease recurrence
        risk_score = 0
        
        # Fluid presence is highest risk factor
        if oct_data.get("fluid_present"):
            risk_score += 3
            
        # Thickness changes
        if prev_oct:
            thickness_change = oct_data["thickness"] - prev_oct["thickness"]
            if thickness_change > 20:
                risk_score += 2
            elif thickness_change > 10:
                risk_score += 1
                
        # Absolute thickness threshold
        if oct_data["thickness"] > 280:
            risk_score += 2
        elif oct_data["thickness"] > 260:
            risk_score += 1
            
        # Consider interval length in risk assessment
        if current_interval >= 10:  # Now current_interval is guaranteed to be a float
            risk_score += 1  # Higher risk with longer intervals
            
        # Determine disease activity based on risk score
        if risk_score >= 3:
            agent.state["disease_activity"] = "recurring"
        else:
            agent.state["disease_activity"] = "stable"
            
        # Log the assessment only if verbose mode is enabled
        if self.verbose:
            print(f"\nOCT Review at {visit_data['date']}")
            print(f"Risk Score: {risk_score}")
            print(f"Disease Activity: {agent.state['disease_activity']}")
            
    def _handle_doctor_treatment_decision(self, agent: Patient, visit_data: Dict):
        """Handle doctor treatment decision with logging"""
        current_step = agent.state["current_step"]
        old_interval = agent.state.get("current_interval")
        
        # Handle initial loading phase
        if current_step == "injection_phase":
            if agent.state["injections_given"] < 3:  # Still in loading phase
                if self.verbose:
                    print(f"\nLoading Phase - Injection {agent.state['injections_given']} of 3")
                # Schedule next loading dose in 4 weeks
                next_visit = {
                    "visit_type": "injection_visit",
                    "actions": ["vision_test", "oct_scan", "injection"],
                    "decisions": ["nurse_vision_check", "doctor_treatment_decision"]
                }
                
                self.clock.schedule_event(Event(
                    time=self.clock.current_time + timedelta(weeks=4),  # Fixed 4-week interval during loading
                    event_type="visit",
                    patient_id=agent.patient_id,
                    data={"visit_type": next_visit},
                    priority=1
                ))
                if self.verbose:
                    print(f"Next loading dose scheduled for {self.clock.current_time + timedelta(weeks=4)}")
            else:
                # Move to dynamic interval phase after completing loading
                if self.verbose:
                    print("\nCompleted loading phase - moving to dynamic interval phase")
                agent.state["current_step"] = "dynamic_interval"
                agent.state["current_interval"] = 8.0  # Start with 8 week interval
                self._schedule_next_visit(agent)
                if self.verbose:
                    print(f"First maintenance visit scheduled at 8-week interval")
        
        elif current_step == "dynamic_interval":
            self._adjust_treatment_interval(agent)
            
    def _adjust_treatment_interval(self, agent: Patient):
        """Adjust treatment interval based on treat-and-extend protocol rules"""
        # Store initial values for logging
        initial_interval = agent.state.get("current_interval")
        initial_activity = agent.state.get("disease_activity")
        
        # Find the current step in the protocol steps list
        current_step = None
        for step in agent.protocol.steps:
            if step.get("step_type") == agent.state["current_step"]:
                current_step = step
                break
                
        if not current_step or current_step.get("step_type") != "dynamic_interval":
            return
                
        params = current_step.get("parameters", {})
        current_interval = agent.state.get("current_interval", params.get("initial_interval", 8.0))
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
        
        # Enhanced logging of changes only if verbose mode is enabled
        if initial_interval != agent.state["current_interval"] and self.verbose:
            print(f"\nVisit Date: {self.clock.current_time}")
            print(f"Disease Activity: {initial_activity}")
            print(f"OCT Thickness: {agent.state['last_oct']['thickness']}")
            print(f"Fluid Present: {agent.state['last_oct']['fluid_present']}")
            print(f"Interval Change: {initial_interval} -> {agent.state['current_interval']} weeks")
            if agent.state["current_interval"] > initial_interval:
                print("Action: Extending interval due to stable disease")
            else:
                print("Action: Shortening interval due to disease activity")
                
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
        
        interval_weeks = agent.state.get("current_interval", 8.0)
        
        self.clock.schedule_event(Event(
            time=self.clock.current_time + timedelta(weeks=interval_weeks),
            event_type="visit",
            patient_id=agent.patient_id,
            data={"visit_type": next_visit},
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
            change = np.random.lognormal(mean=2.0, sigma=0.3)
        elif outcome == 'decline':
            # Decline: negative log-normal for rare but potentially significant losses
            change = -np.random.lognormal(mean=1.5, sigma=0.4)
        else:
            # Stable: small normal distribution changes
            change = np.random.normal(0, 2)
        
        # Apply minimal ceiling effect during loading
        current_vision = state["current_vision"]
        headroom = max(0, 85 - current_vision)
        if change > 0:
            change = min(change, headroom * 0.8)  # Allow most of headroom during loading
            
        return change

    def _calculate_vision_change(self, state: Dict) -> float:
        """Calculate vision change with memory and ceiling effects"""
        import numpy as np
        
        # Check if we're in loading phase
        if (state.get("current_step") == "injection_phase" and 
            state.get("injections_given", 0) < 3 and 
            "injection" in state.get("current_actions", [])):
            
            return self._calculate_loading_phase_change(state)
        
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
        
        if "injection" in state.get("current_actions", []):
            # Treatment effect
            # Treatment effect
            # Treatment effect
            memory_factor = 0.7
            base_effect = 0
            
            if response_history:
                base_effect = np.mean(response_history) * memory_factor
                if base_effect > 5:
                    base_effect *= 0.8

            if state.get("current_step") == "injection_phase" and state.get("injections_given", 0) < 3:
                # Loading phase - strong positive response expected
                random_effect = np.random.lognormal(mean=1.2, sigma=0.3)
            else:
                # Maintenance phase - more variable response
                random_effect = np.random.lognormal(mean=0.5, sigma=0.4)
            
            improvement = (base_effect + random_effect) * (1 - headroom_factor)
            
            # Store response
            state["last_treatment_response"] = improvement
            state["treatment_response_history"].append(improvement)
            if len(state["treatment_response_history"]) > 3:
                state["treatment_response_history"].pop(0)
            
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
