from datetime import datetime
from typing import Dict, List, Any, Optional
import numpy as np
from .clinical_model import ClinicalModel

class PatientState:
    """Manages patient state and history throughout the simulation"""
    
    def __init__(self, patient_id: str, protocol_name: str, initial_vision: float, 
                 start_time: datetime):
        """Initialize a new patient state
        
        Args:
            patient_id: Unique identifier for the patient
            protocol_name: Name of the treatment protocol
            initial_vision: Baseline visual acuity (ETDRS letters)
            start_time: Time when patient enters the simulation
        """
        self.patient_id = patient_id
        self.state = {
            "protocol": protocol_name,
            "current_step": "injection_phase",
            "visits": 0,
            "injections": 0,
            "baseline_vision": initial_vision,
            "current_vision": initial_vision,
            "last_visit_date": start_time,
            "next_visit_interval": 4,
            "treatment_start": start_time,
            "visit_history": [],
            "best_vision_achieved": initial_vision,
            "last_treatment_response": None,
            "treatment_response_history": [],
            "weeks_since_last_injection": 0,
            "last_injection_date": None
        }
    
    def process_visit(self, visit_time: datetime, actions: List[str]) -> Dict[str, Any]:
        """Process a clinic visit and update patient state
        
        Args:
            visit_time: Time of the visit
            actions: List of actions performed (e.g., ["vision_test", "oct_scan", "injection"])
            
        Returns:
            Dict containing visit data including vision changes and OCT findings
        """
        self.state["visits"] += 1
        self.state["last_visit_date"] = visit_time
        
        # Update weeks since last injection
        if self.state.get("last_injection_date"):
            weeks_elapsed = (visit_time - self.state["last_injection_date"]).days / 7.0
            self.state["weeks_since_last_injection"] = weeks_elapsed
        
        # Calculate vision changes
        vision_change = ClinicalModel.simulate_vision_change(self.state)
        
        # Process actions
        visit_data = {
            "vision_change": vision_change,
            "oct_findings": ClinicalModel.simulate_oct_findings(self.state),
            "actions_performed": []
        }
        
        for action in actions:
            if action == "vision_test":
                self._process_vision_test(vision_change)
                visit_data["actions_performed"].append("vision_test")
            elif action == "oct_scan":
                visit_data["actions_performed"].append("oct_scan")
            elif action == "injection":
                self._process_injection(visit_time)
                visit_data["actions_performed"].append("injection")
        
        # Record visit in history
        self._record_visit(visit_time, actions, visit_data)
        
        return visit_data
    
    def _process_vision_test(self, vision_change: float):
        """Process vision test results"""
        # Add measurement noise
        measurement_noise = np.random.normal(0, 2)  # SD of 2 letters
        new_vision = self.state["current_vision"] + vision_change + measurement_noise
        self.state["current_vision"] = min(max(new_vision, 0), 85)  # Clamp between 0-85
        
        # Update best vision if applicable
        if self.state["current_vision"] > self.state["best_vision_achieved"]:
            self.state["best_vision_achieved"] = min(self.state["current_vision"], 85)
    
    def _process_injection(self, visit_time: datetime):
        """Process injection treatment"""
        self.state["injections"] += 1
        self.state["last_injection_date"] = visit_time
        self.state["weeks_since_last_injection"] = 0
    
    def _record_visit(self, visit_time: datetime, actions: List[str], 
                     visit_data: Dict[str, Any]):
        """Record visit details in patient history"""
        visit_record = {
            'date': visit_time.replace(second=0, microsecond=0),
            'actions': actions,
            'vision': self.state['current_vision'],
            'phase': self.state.get('current_phase', 'loading')
        }
        self.state['visit_history'].append(visit_record)
    
    def update_phase(self, new_phase: str):
        """Update treatment phase"""
        self.state["current_phase"] = new_phase
    
    def set_next_visit_interval(self, weeks: int):
        """Set interval until next scheduled visit"""
        self.state["next_visit_interval"] = max(min(weeks, 52), 4)  # Clamp between 4-52 weeks
    
    @property
    def visit_history(self) -> List[Dict]:
        """Get patient's visit history"""
        return self.state["visit_history"]
    
    @property
    def current_vision(self) -> float:
        """Get patient's current visual acuity"""
        return self.state["current_vision"]
    
    @property
    def last_visit_date(self) -> datetime:
        """Get date of patient's last visit"""
        return self.state["last_visit_date"]
    
    @property
    def next_visit_interval(self) -> int:
        """Get weeks until next scheduled visit"""
        return self.state["next_visit_interval"]
