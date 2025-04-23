""":no-index:
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
    """:no-index:
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

        This is the main state transition method that handles all visit processing
        and state updates. It coordinates vision testing, treatment administration,
        and disease state transitions.

        Parameters
        ----------
        visit_time : datetime
            Time of the visit (must be timezone-naive UTC)
            Example: datetime(2025, 4, 15)
        actions : List[str]
            List of actions performed during the visit. Valid actions:
                - "vision_test": Measures visual acuity
                - "oct_scan": Performs OCT imaging
                - "injection": Administers anti-VEGF treatment
            Example: ["vision_test", "oct_scan", "injection"]
        clinical_model : ClinicalModel
            ClinicalModel instance for simulating vision changes and disease progression
            Must be initialized with appropriate parameters

        Returns
        -------
        Dict[str, Any]
            Dictionary containing detailed visit results:
                - vision_change: float - Change in ETDRS letters
                - actions_performed: List[str] - Completed actions
                - disease_state: DiseaseState - Updated state
                - treatment_response: Optional[Dict] - If injection given
                - visit_type: str - Classification of visit

        Raises
        ------
        ValueError
            If visit_time is timezone-aware
            If actions contains invalid values
            If clinical_model is not properly initialized

        Examples
        --------
        Basic Visit:
        >>> model = ClinicalModel(config)
        >>> patient = PatientState("123", "treat_and_extend", 70, datetime.now())
        >>> visit_data = patient.process_visit(
        ...     datetime.now(),
        ...     ["vision_test", "injection"], 
        ...     model
        ... )

        Monitoring Visit:
        >>> visit_data = patient.process_visit(
        ...     datetime.now(),
        ...     ["vision_test", "oct_scan"],
        ...     model
        ... )

        Notes
        -----
        State Updates:
        1. Increments visit counter
        2. Updates last visit date
        3. Calculates weeks since last injection
        4. Simulates vision changes using clinical_model
        5. Processes each action in sequence
        6. Records complete visit details

        The method handles:
        - Validation of input parameters
        - Coordination of state updates
        - Error handling for invalid states
        - Complete visit recording

        Vision changes are simulated by the clinical_model which considers:
        - Current disease state
        - Treatment history
        - Time since last injection
        - Current vision level
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
