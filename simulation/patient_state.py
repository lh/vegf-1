"""
Patient state management for AMD treatment simulation.

This module implements a state machine for tracking individual patient progression
through AMD treatment protocols. It maintains all clinical and treatment-related
state information and handles state transitions during clinic visits.

Key Concepts
------------
1. **State Machine**:
   - Tracks disease state (NAIVE, ACTIVE, INACTIVE, ATROPHIC)
   - Manages treatment phases (loading, maintenance, etc.)
   - Handles transitions between states based on clinical outcomes

2. **Clinical Tracking**:
   - Visual acuity measurements (ETDRS letters 0-85)
   - Treatment history (injections, visits, responses)
   - Disease progression over time

3. **Visit Processing**:
   - Handles different visit types and actions
   - Updates state based on clinical model outputs
   - Maintains complete visit history

Classes
-------
PatientState
    Core state machine class tracking all patient attributes and history

Key Methods
-----------
process_visit()
    Main entry point for processing clinic visits and updating state

Examples
--------
Basic Usage:
>>> model = ClinicalModel()
>>> patient = PatientState("123", "treat_and_extend", 70, datetime.now())
>>> visit_data = patient.process_visit(
...     datetime.now(), 
...     ["vision_test", "injection"], 
...     model
... )
>>> print(f"Vision change: {visit_data['vision_change']} letters")

Advanced Usage:
>>> # Custom treatment protocol with phase transitions
>>> patient = PatientState("456", "custom_protocol", 65, datetime.now())
>>> while patient.visits < 24:
...     visit_data = patient.process_visit(
...         datetime.now(),
...         ["vision_test", "oct_scan", "injection"],
...         model
...     )
...     if visit_data["vision_change"] < -5:
...         patient.update_phase("intensified_treatment")

Notes
-----
- Visual acuity measurements use ETDRS letters (0-85 range)
- Disease states follow ClinicalModel definitions
- Visit intervals are clamped between 4-52 weeks
- All state changes are recorded in visit_history
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
        Maximum allowed treatments in a phase (default: 1000)
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
            - last_visit_date: Date of last visit
            - next_visit_interval: Weeks until next visit
            - treatment_start: Date treatment began
            - visit_history: List of all visits
            - best_vision_achieved: Highest vision recorded
            - last_treatment_response: Most recent treatment response
            - treatment_response_history: List of all responses
            - weeks_since_last_injection: Weeks since last injection
            - last_injection_date: Date of last injection

    Notes
    -----
    The state dictionary maintains a complete record of the patient's:
    - Treatment history and responses
    - Vision measurements over time
    - Disease progression
    - Visit schedule and history
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
            "disease_state": "NAIVE",  # Set initial disease state to NAIVE
            # Treatment discontinuation tracking
            "treatment_status": {
                "active": True,
                "weeks_since_discontinuation": 0,
                "monitoring_schedule": 12,  # Default weeks between monitoring visits
                "recurrence_detected": False,
                "discontinuation_date": None,
                "reason_for_discontinuation": None
            }
        }
    
    def process_visit(self, visit_time: datetime, actions: List[str], clinical_model: ClinicalModel) -> Dict[str, Any]:
        """
        Process a clinic visit and update patient state.

        This is the main state transition method that handles all visit processing
        and state updates. It coordinates vision testing, treatment administration,
        and disease state transitions.

        Parameters
        ----------
        visit_time : datetime
            Time of the visit (must be timezone-naive UTC)
        actions : List[str]
            List of actions performed during the visit
        clinical_model : ClinicalModel
            ClinicalModel instance for simulating vision changes and disease progression

        Returns
        -------
        Dict[str, Any]
            Dictionary containing detailed visit results:
                - baseline_vision: float - Vision before treatment
                - new_vision: float - Vision after treatment
                - actions_performed: List[str] - Completed actions
                - disease_state: str - Updated disease state
                - visit_type: str - Classification of visit
                - treatment_status: Dict - Current treatment status
        """
        self.state["visits"] += 1
        self.state["last_visit_date"] = visit_time
        
        # Capture baseline vision before any changes
        baseline_vision = self.state["current_vision"]
        
        # Update weeks since last injection
        if self.state.get("last_injection_date"):
            weeks_elapsed = (visit_time - self.state["last_injection_date"]).days / 7.0
            self.state["weeks_since_last_injection"] = weeks_elapsed
        
        # Update weeks since discontinuation if treatment is inactive
        if not self.state["treatment_status"]["active"] and self.state["treatment_status"]["discontinuation_date"]:
            weeks_since_discontinuation = (visit_time - self.state["treatment_status"]["discontinuation_date"]).days / 7.0
            self.state["treatment_status"]["weeks_since_discontinuation"] = weeks_since_discontinuation
        
        # Determine visit type
        visit_type = "regular_visit"
        if not self.state["treatment_status"]["active"]:
            visit_type = "monitoring_visit"
            # Check if this is a recurrence detection visit
            if "check_recurrence" in actions:
                visit_type = "recurrence_check"
        
        # Calculate vision changes and update disease state
        vision_change, new_disease_state = clinical_model.simulate_vision_change(self.state)
        self.state["disease_state"] = new_disease_state
        
        # Process actions
        visit_data = {
            "baseline_vision": baseline_vision,
            "new_vision": baseline_vision + vision_change,
            "actions_performed": [],
            "disease_state": new_disease_state,
            "visit_type": visit_type,
            "treatment_status": self.state["treatment_status"].copy()
        }
        
        for action in actions:
            if action == "vision_test":
                self._process_vision_test(vision_change)
                visit_data["actions_performed"].append("vision_test")
            elif action == "oct_scan":
                visit_data["actions_performed"].append("oct_scan")
            elif action == "injection":
                # If treatment was discontinued but recurrence detected, resume treatment
                if not self.state["treatment_status"]["active"] and self.state["treatment_status"]["recurrence_detected"]:
                    self.resume_treatment()
                    visit_data["treatment_status"] = self.state["treatment_status"].copy()
                
                self._process_injection(visit_time)
                visit_data["actions_performed"].append("injection")
                self._increment_treatments_in_phase()
            elif action == "check_recurrence":
                recurrence_detected = self._check_for_recurrence(clinical_model)
                visit_data["actions_performed"].append("check_recurrence")
                visit_data["recurrence_detected"] = recurrence_detected
                visit_data["treatment_status"] = self.state["treatment_status"].copy()
            elif action == "discontinue_treatment":
                self.discontinue_treatment(visit_time, reason="protocol_decision")
                visit_data["actions_performed"].append("discontinue_treatment")
                visit_data["treatment_status"] = self.state["treatment_status"].copy()
        
        # Update current vision after all actions
        self.state["current_vision"] = visit_data["new_vision"]
        
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
        Process vision test results with measurement noise and bounds checking.

        Parameters
        ----------
        vision_change : float
            Change in visual acuity since last measurement (ETDRS letters)

        Notes
        -----
        Key steps:
        1. Adds Gaussian measurement noise (SD=2 letters)
        2. Updates current vision score
        3. Clamps vision between 0-85 ETDRS letters
        4. Updates best vision achieved if improved

        Measurement noise represents typical test-retest variability in
        clinical vision testing. The 0-85 letter range reflects the
        standard ETDRS chart limits.
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
    
    def _check_for_recurrence(self, clinical_model: ClinicalModel) -> bool:
        """
        Check for disease recurrence after treatment discontinuation.

        Parameters
        ----------
        clinical_model : ClinicalModel
            Clinical model with recurrence parameters

        Returns
        -------
        bool
            True if recurrence is detected, False otherwise

        Notes
        -----
        Uses the recurrence probabilities from the clinical model to determine
        if a recurrence has occurred. Also considers symptom detection probability.
        """
        # If treatment is active or recurrence already detected, no need to check
        if self.state["treatment_status"]["active"] or self.state["treatment_status"]["recurrence_detected"]:
            return False
        
        # Get discontinuation parameters from clinical model
        discontinuation_params = clinical_model.config.get_treatment_discontinuation_params()
        if not discontinuation_params:
            return False
        
        # Calculate recurrence probability based on time since discontinuation
        recurrence_probs = discontinuation_params.get("recurrence_probabilities", {})
        base_risk_per_year = recurrence_probs.get("base_risk_per_year", 0.2)
        
        # Convert annual risk to weekly risk (approximation)
        weekly_risk = base_risk_per_year / 52.0
        
        # Calculate cumulative risk based on weeks since discontinuation
        weeks_since_discontinuation = self.state["treatment_status"]["weeks_since_discontinuation"]
        cumulative_risk = min(weekly_risk * weeks_since_discontinuation, 0.95)  # Cap at 95%
        
        # Determine if recurrence occurs
        recurrence_occurs = np.random.random() < cumulative_risk
        
        if recurrence_occurs:
            # Check if symptoms are detected
            symptom_detection = discontinuation_params.get("symptom_detection", {})
            symptom_probability = symptom_detection.get("probability", 0.6)
            detection_sensitivity = symptom_detection.get("detection_sensitivity", 1.0)
            
            # Determine if symptoms occur and are detected
            symptoms_occur = np.random.random() < symptom_probability
            symptoms_detected = symptoms_occur and (np.random.random() < detection_sensitivity)
            
            # Apply vision loss due to recurrence
            if recurrence_occurs:
                recurrence_impact = discontinuation_params.get("recurrence_impact", {})
                vision_loss_letters = recurrence_impact.get("vision_loss_letters", 3.6)
                self.state["current_vision"] -= vision_loss_letters
                
                # Mark recurrence as detected
                self.state["treatment_status"]["recurrence_detected"] = True
                
                return True
        
        return False

    def discontinue_treatment(self, visit_time: datetime, reason: str = "protocol_decision") -> None:
        """
        Discontinue active treatment and set up monitoring schedule.

        Parameters
        ----------
        visit_time : datetime
            Time when treatment is discontinued
        reason : str, optional
            Reason for discontinuation (default: "protocol_decision")

        Notes
        -----
        Updates treatment status to inactive and sets up monitoring schedule.
        """
        if not self.state["treatment_status"]["active"]:
            return  # Already discontinued
        
        self.state["treatment_status"]["active"] = False
        self.state["treatment_status"]["discontinuation_date"] = visit_time
        self.state["treatment_status"]["weeks_since_discontinuation"] = 0
        self.state["treatment_status"]["reason_for_discontinuation"] = reason
        
        # Default monitoring schedule if not specified
        if "monitoring_schedule" not in self.state["treatment_status"]:
            self.state["treatment_status"]["monitoring_schedule"] = 12  # Every 12 weeks
    
    def resume_treatment(self) -> None:
        """
        Resume treatment after discontinuation.

        Notes
        -----
        Called when recurrence is detected and treatment needs to be resumed.
        """
        self.state["treatment_status"]["active"] = True
        self.state["treatment_status"]["weeks_since_discontinuation"] = 0
        self.state["treatment_status"]["recurrence_detected"] = False
        self.state["treatment_status"]["discontinuation_date"] = None
    
    def set_monitoring_schedule(self, weeks: int) -> None:
        """
        Set the monitoring schedule for a patient after treatment discontinuation.

        Parameters
        ----------
        weeks : int
            Number of weeks between monitoring visits
        """
        self.state["treatment_status"]["monitoring_schedule"] = max(4, min(weeks, 52))  # Clamp between 4-52 weeks

    def _record_visit(self, visit_time: datetime, actions: List[str],
                     visit_data: Dict[str, Any]):
        """
        Record visit details in patient history.

        Parameters
        ----------
        visit_time : datetime
            Time of visit (will be stripped to minute precision)
        actions : List[str]
            Actions performed, validated against allowed actions
        visit_data : Dict[str, Any]
            Must contain at minimum:
                - vision: float - Current ETDRS letters
                - disease_state: str/DiseaseState - Current state

        Returns
        -------
        None
            Modifies state['visit_history'] in place

        Notes
        -----
        Visit records contain these standardized fields:
            - date: datetime - Visit time
            - actions: List[str] - Performed actions
            - vision: float - ETDRS letters
            - phase: str - Current treatment phase
            - type: str - Visit classification
            - disease_state: str - Current disease state
            - treatment_status: Dict - Treatment status information

        The visit history provides a complete audit trail of all patient
        interactions and is used for:
            - Treatment decision making
            - Outcome analysis
            - Protocol adherence monitoring
            - Simulation validation
        """
        visit_record = {
            'date': visit_time.replace(second=0, microsecond=0),
            'actions': actions,
            'vision': self.state['current_vision'],
            'baseline_vision': visit_data.get('baseline_vision'),
            'phase': self.state.get('current_phase', 'loading'),
            'type': visit_data.get('visit_type', 'regular_visit'),
            'disease_state': str(self.state.get('disease_state', 'NAIVE')),
            'treatment_status': {
                'active': self.state['treatment_status']['active'],
                'recurrence_detected': self.state['treatment_status']['recurrence_detected'],
                'weeks_since_discontinuation': self.state['treatment_status']['weeks_since_discontinuation']
            }
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
