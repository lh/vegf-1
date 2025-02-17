from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
from .patient_state import PatientState
from .clinical_model import ClinicalModel

class AgentState(PatientState):
    """Manages agent state and behavior for agent-based simulation.
    
    Extends PatientState with additional functionality for:
    - Risk factor tracking
    - Treatment adherence
    - Decision making
    - Outcome tracking
    """
    
    def __init__(self, patient_id: str, protocol_name: str, initial_vision: float,
                 start_time: datetime, risk_factors: Optional[Dict[str, float]] = None):
        """Initialize a new agent state
        
        Args:
            patient_id: Unique identifier for the patient
            protocol_name: Name of the treatment protocol
            initial_vision: Baseline visual acuity (ETDRS letters)
            start_time: Time when patient enters the simulation
            risk_factors: Dictionary of risk factors and their values
        """
        # Initialize base state
        super().__init__(patient_id, protocol_name, initial_vision, start_time)
        
        # Initialize risk factors first
        self.state["risk_factors"] = risk_factors or {}
        
        # Calculate progression rate based on risk factors
        progression_rate = self._calculate_progression_rate()
        
        # Add remaining agent-specific state
        self.state.update({
            "treatment_adherence": 1.0,  # Base adherence rate
            "missed_appointments": 0,
            "treatment_decisions": [],
            "disease_progression_rate": progression_rate,
            "quality_of_life": self._calculate_qol(),
            "last_decision_time": start_time,
            "treatment_outcomes": {
                "vision_stability": True,
                "disease_control": True,
                "treatment_burden": 0.0
            }
        })
    
    def _calculate_progression_rate(self) -> float:
        """Calculate disease progression rate based on risk factors"""
        base_rate = 0.1  # letters per week
        risk_multiplier = 1.0
        
        for factor, value in self.state["risk_factors"].items():
            if factor == "age":
                risk_multiplier *= 1.0 + max(0, (value - 65) / 100)
            elif factor == "smoking":
                risk_multiplier *= 1.0 + (value * 0.2)
            elif factor == "genetic_risk":
                risk_multiplier *= 1.0 + (value * 0.3)
        
        return base_rate * risk_multiplier
    
    def _calculate_qol(self) -> float:
        """Calculate quality of life score based on vision and treatment burden"""
        vision_score = self.state["current_vision"] / 85.0  # Normalize to 0-1
        treatment_burden = min(1.0, self.state["injections"] / 12.0)  # Normalize to 0-1
        
        qol = (0.7 * vision_score) + (0.3 * (1.0 - treatment_burden))
        return max(0.0, min(1.0, qol))
    
    def make_treatment_decision(self, current_time: datetime) -> Tuple[bool, List[str]]:
        """Make a decision about attending appointment and following treatment
        
        Returns:
            Tuple of (attend_appointment: bool, actions_to_take: List[str])
        """
        # Calculate probability of attending appointment
        attendance_prob = self.state["treatment_adherence"]
        
        # Adjust for various factors
        vision_change = self.state["current_vision"] - self.state["baseline_vision"]
        if vision_change > 5:
            attendance_prob *= 0.9  # Slightly less likely if vision improved significantly
        elif vision_change < -5:
            attendance_prob *= 1.1  # More likely if vision declined
        
        # Consider treatment burden
        if self.state["injections"] > 6:
            attendance_prob *= 0.95  # Slightly less likely with high treatment burden
        
        # Make attendance decision
        will_attend = np.random.random() < min(1.0, attendance_prob)
        
        if not will_attend:
            self.state["missed_appointments"] += 1
            self.state["treatment_adherence"] *= 0.95  # Reduce future adherence
            return (False, [])
        
        # Determine actions to take
        actions = ["vision_test", "oct_scan"]
        if self._needs_injection(current_time):
            actions.append("injection")
        
        # Record decision
        self.state["treatment_decisions"].append({
            "time": current_time,
            "attended": True,
            "actions": actions
        })
        
        return (True, actions)
    
    def _needs_injection(self, current_time: datetime) -> bool:
        """Determine if patient needs injection based on clinical factors"""
        if not self.state["last_injection_date"]:
            return True
        
        weeks_since_injection = (current_time - self.state["last_injection_date"]).days / 7.0
        
        # Consider disease activity and vision changes
        vision_declining = (self.state["current_vision"] < 
                          self.state["best_vision_achieved"] - 5)
        high_disease_activity = self.state["disease_progression_rate"] > 0.15
        
        return (weeks_since_injection >= 12 or 
                vision_declining or 
                high_disease_activity)
    
    def update_outcomes(self, current_time: datetime):
        """Update treatment outcomes and metrics"""
        # Update vision stability
        vision_change = self.state["current_vision"] - self.state["baseline_vision"]
        self.state["treatment_outcomes"]["vision_stability"] = abs(vision_change) <= 5
        
        # Update disease control
        weeks_since_last_visit = ((current_time - self.state["last_visit_date"])
                                 .days / 7.0)
        self.state["treatment_outcomes"]["disease_control"] = (
            weeks_since_last_visit <= 12 and 
            self.state["disease_progression_rate"] <= 0.15
        )
        
        # Update treatment burden
        annual_visits = (self.state["visits"] * 52 / 
                        max(1, (current_time - self.state["treatment_start"])
                            .days / 7.0))
        self.state["treatment_outcomes"]["treatment_burden"] = annual_visits
        
        # Update quality of life
        self.state["quality_of_life"] = self._calculate_qol()
    
    def get_outcome_metrics(self) -> Dict[str, Any]:
        """Get comprehensive outcome metrics for the agent
        
        Returns:
            Dictionary containing various outcome metrics
        """
        return {
            "vision_change": self.state["current_vision"] - self.state["baseline_vision"],
            "best_vision": self.state["best_vision_achieved"],
            "total_visits": self.state["visits"],
            "total_injections": self.state["injections"],
            "missed_appointments": self.state["missed_appointments"],
            "treatment_adherence": self.state["treatment_adherence"],
            "quality_of_life": self.state["quality_of_life"],
            "disease_progression_rate": self.state["disease_progression_rate"],
            "treatment_outcomes": self.state["treatment_outcomes"].copy()
        }
