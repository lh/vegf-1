"""Patient state management for AMD treatment simulation.

This module handles the state tracking and updates for individual patients throughout
the simulation, including vision changes, treatment history, and visit scheduling.

Classes
-------
PatientState
    Tracks all aspects of a patient's state during treatment

Key Features
------------
- Maintains complete treatment history
- Tracks visual acuity changes
- Manages disease state transitions
- Records all visits and treatments
- Handles treatment phase transitions

Examples
--------
>>> model = ClinicalModel()
>>> patient = PatientState("123", "treat_and_extend", 70, datetime.now())
>>> visit_data = patient.process_visit(datetime.now(), ["vision_test", "injection"], model)
>>> print(f"Vision change: {visit_data['vision_change']} letters")

Notes
-----
- Visual acuity is measured in ETDRS letters (0-85 range)
- Disease states include: NAIVE, ACTIVE, INACTIVE, ATROPHIC
- Visit intervals are clamped between 4-52 weeks
"""

from datetime import datetime
from typing import Dict, List, Any, Optional
import numpy as np
from .clinical_model import ClinicalModel

class PatientState:
    """
    Manages patient state and history throughout the simulation.

    This class maintains the complete state of a patient including their treatment history,
    vision measurements, disease state, and scheduled visits. It provides methods for
    processing clinic visits and updating patient state based on treatments and disease
    progression.

    Parameters
    ----------
    patient_id : str
        Unique identifier for the patient
    protocol_name : str
        Name of the treatment protocol
    initial_vision : float
        Baseline visual acuity (ETDRS letters)
    start_time : datetime
        Time when patient enters the simulation

    Attributes
    ----------
    MAX_TREATMENTS_IN_PHASE : int
        Maximum allowed treatments in a phase
    patient_id : str
        Unique identifier for the patient
    state : Dict
        Dictionary containing all patient state information including:
        - protocol: Treatment protocol name
        - current_step: Current treatment phase
        - visits: Total number of visits
        - injections: Total number of injections
        - baseline_vision: Initial visual acuity
        - current_vision: Current visual acuity
        - disease_state: Current disease state
        And various other tracking variables
    """
    
    def __init__(self, patient_id: str, protocol_name: str, initial_vision: float, 
                 start_time: datetime):
        self.MAX_TREATMENTS_IN_PHASE = 1000  # Maximum allowed treatments in a phase
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
            "last_injection_date": None,
            "disease_state": "NAIVE"  # Set initial disease state to NAIVE
        }
    
    def process_visit(self, visit_time: datetime, actions: List[str], clinical_model: ClinicalModel) -> Dict[str, Any]:
        """
        Process a clinic visit and update patient state.

        Parameters
        ----------
        visit_time : datetime
            Time of the visit
        actions : List[str]
            List of actions performed (e.g., ["vision_test", "oct_scan", "injection"])
        clinical_model : ClinicalModel
            ClinicalModel instance for simulating vision changes

        Returns
        -------
        Dict[str, Any]
            Dictionary containing visit data including:
            - vision_change: Change in visual acuity
            - actions_performed: List of completed actions
            - disease_state: Updated disease state

        Notes
        -----
        Updates multiple aspects of patient state including:
        - Visit count and timing
        - Vision measurements
        - Disease state
        - Treatment history
        """
        self.state["visits"] += 1
        self.state["last_visit_date"] = visit_time
        
        # Update weeks since last injection
        if self.state.get("last_injection_date"):
            weeks_elapsed = (visit_time - self.state["last_injection_date"]).days / 7.0
            self.state["weeks_since_last_injection"] = weeks_elapsed
        
        # Calculate vision changes and update disease state
        vision_change, new_disease_state = clinical_model.simulate_vision_change(self.state)
        self.state["disease_state"] = new_disease_state
        
        # Process actions
        visit_data = {
            "vision_change": vision_change,
            "actions_performed": [],
            "disease_state": new_disease_state
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
                self._increment_treatments_in_phase()
        
        # Record visit in history
        self._record_visit(visit_time, actions, visit_data)
        
        return visit_data

    def _increment_treatments_in_phase(self):
        """
        Safely increment the treatments_in_phase counter.

        Notes
        -----
        Uses modulo operation to prevent counter overflow beyond MAX_TREATMENTS_IN_PHASE.
        """
        if "treatments_in_phase" not in self.state:
            self.state["treatments_in_phase"] = 0
        self.state["treatments_in_phase"] = (self.state["treatments_in_phase"] + 1) % self.MAX_TREATMENTS_IN_PHASE
    
    def _process_vision_test(self, vision_change: float):
        """
        Process vision test results.

        Parameters
        ----------
        vision_change : float
            Change in visual acuity since last measurement

        Notes
        -----
        Includes measurement noise and updates best vision achieved if applicable.
        Vision scores are clamped between 0 and 85 ETDRS letters.
        """
        # Add measurement noise
        measurement_noise = np.random.normal(0, 2)  # SD of 2 letters
        new_vision = self.state["baseline_vision"] + vision_change + measurement_noise
        self.state["current_vision"] = min(max(new_vision, 0), 85)  # Clamp between 0-85
        
        # Update best vision if applicable
        if self.state["current_vision"] > self.state["best_vision_achieved"]:
            self.state["best_vision_achieved"] = min(self.state["current_vision"], 85)
    
    def _process_injection(self, visit_time: datetime):
        """
        Process injection treatment.

        Parameters
        ----------
        visit_time : datetime
            Time of the injection

        Notes
        -----
        Updates injection count and resets the weeks since last injection counter.
        """
        self.state["injections"] += 1
        self.state["last_injection_date"] = visit_time
        self.state["weeks_since_last_injection"] = 0
    
    def _record_visit(self, visit_time: datetime, actions: List[str], 
                     visit_data: Dict[str, Any]):
        """
        Record visit details in patient history.

        Parameters
        ----------
        visit_time : datetime
            Time of the visit
        actions : List[str]
            List of actions performed during the visit
        visit_data : Dict[str, Any]
            Data collected during the visit

        Notes
        -----
        Stores a standardized record of each visit including timing, actions,
        vision measurements, and disease state.
        """
        visit_record = {
            'date': visit_time.replace(second=0, microsecond=0),
            'actions': actions,
            'vision': self.state['current_vision'],
            'phase': self.state.get('current_phase', 'loading'),
            'type': visit_data.get('visit_type', 'regular_visit'),
            'disease_state': str(self.state.get('disease_state', 'NAIVE'))
        }
        self.state['visit_history'].append(visit_record)
    
    def update_phase(self, new_phase: str):
        """
        Update treatment phase.

        Parameters
        ----------
        new_phase : str
            Name of the new treatment phase
        """
        self.state["current_phase"] = new_phase
    
    def set_next_visit_interval(self, weeks: int):
        """
        Set interval until next scheduled visit.

        Parameters
        ----------
        weeks : int
            Number of weeks until next visit

        Notes
        -----
        Interval is clamped between 4 and 52 weeks.
        """
        self.state["next_visit_interval"] = max(min(weeks, 52), 4)  # Clamp between 4-52 weeks
    
    @property
    def visit_history(self) -> List[Dict]:
        """
        Get patient's visit history.

        Returns
        -------
        List[Dict]
            List of visit records in chronological order
        """
        return self.state["visit_history"]
    
    @property
    def current_vision(self) -> float:
        """
        Get patient's current visual acuity.

        Returns
        -------
        float
            Current vision in ETDRS letters
        """
        return self.state["current_vision"]
    
    @property
    def last_visit_date(self) -> datetime:
        """
        Get date of patient's last visit.

        Returns
        -------
        datetime
            Date and time of the most recent visit
        """
        return self.state["last_visit_date"]
    
    @property
    def next_visit_interval(self) -> int:
        """
        Get weeks until next scheduled visit.

        Returns
        -------
        int
            Number of weeks until next scheduled visit
        """
        return self.state["next_visit_interval"]
