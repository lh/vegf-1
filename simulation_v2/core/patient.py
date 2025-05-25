"""
Patient class for AMD simulation V2.

Tracks individual patient state, treatment history, and outcomes.
Part of the FOV (Four Option Version) internal model.
"""

from datetime import datetime
from typing import List, Dict, Optional, Any
from .disease_model import DiseaseState


class Patient:
    """
    Represents an individual patient in the simulation.
    
    Tracks:
    - Disease state progression (FOV model)
    - Treatment history
    - Vision measurements
    - Discontinuation and retreatment
    """
    
    def __init__(self, patient_id: str, baseline_vision: int = 70):
        """
        Initialize a new patient.
        
        Args:
            patient_id: Unique identifier for the patient
            baseline_vision: Starting visual acuity in ETDRS letters (0-100, default: 70)
        """
        if not 0 <= baseline_vision <= 100:
            raise ValueError(f"Baseline vision must be between 0 and 100 ETDRS letters, got {baseline_vision}")
            
        self.id = patient_id
        self.baseline_vision = baseline_vision
        self.current_vision = baseline_vision
        self.current_state = DiseaseState.NAIVE
        
        # Visit and treatment tracking
        self.visit_history: List[Dict[str, Any]] = []
        self.injection_count = 0
        self._last_injection_date: Optional[datetime] = None
        
        # Discontinuation tracking
        self.is_discontinued = False
        self.discontinuation_date: Optional[datetime] = None
        self.discontinuation_type: Optional[str] = None
        
        # Retreatment tracking
        self.retreatment_count = 0
        self.retreatment_dates: List[datetime] = []
        
    def record_visit(
        self, 
        date: datetime, 
        disease_state: DiseaseState,
        treatment_given: bool,
        vision: int
    ) -> None:
        """
        Record a patient visit.
        
        Args:
            date: Visit date
            disease_state: Current disease state
            treatment_given: Whether injection was administered
            vision: Current visual acuity in ETDRS letters (0-100)
            
        Raises:
            ValueError: If trying to give treatment to discontinued patient
        """
        # Validate vision
        if not 0 <= vision <= 100:
            raise ValueError(f"Vision must be between 0 and 100 ETDRS letters, got {vision}")
            
        # Check if trying to treat discontinued patient
        if self.is_discontinued and treatment_given:
            raise ValueError("Cannot give treatment to discontinued patient")
            
        # Record the visit
        visit = {
            'date': date,
            'disease_state': disease_state,
            'treatment_given': treatment_given,
            'vision': vision
        }
        self.visit_history.append(visit)
        
        # Update current state
        self.current_state = disease_state
        self.current_vision = vision
        
        # Update injection tracking
        if treatment_given:
            self.injection_count += 1
            self._last_injection_date = date
            
    @property
    def days_since_last_injection(self) -> Optional[int]:
        """
        Calculate days since last injection.
        
        Returns:
            Number of days, or None if no injections yet
        """
        if self._last_injection_date is None:
            return None
        return self.days_since_last_injection_at(datetime.now())
        
    def days_since_last_injection_at(self, reference_date: datetime) -> Optional[int]:
        """
        Calculate days since last injection at a specific date.
        
        Args:
            reference_date: Date to calculate from
            
        Returns:
            Number of days, or None if no injections yet
        """
        if self._last_injection_date is None:
            return None
            
        delta = reference_date - self._last_injection_date
        return delta.days
        
    # Convenience methods for other units
    def weeks_since_last_injection_at(self, reference_date: datetime) -> Optional[float]:
        """
        Calculate weeks since last injection at a specific date.
        
        Args:
            reference_date: Date to calculate from
            
        Returns:
            Number of weeks (as float), or None if no injections yet
        """
        days = self.days_since_last_injection_at(reference_date)
        return days / 7.0 if days is not None else None
        
    def discontinue(self, date: datetime, discontinuation_type: str) -> None:
        """
        Mark patient as discontinued from treatment.
        
        Args:
            date: Discontinuation date
            discontinuation_type: Type of discontinuation (e.g., "planned", "adverse")
        """
        self.is_discontinued = True
        self.discontinuation_date = date
        self.discontinuation_type = discontinuation_type
        
    def restart_treatment(self, date: datetime) -> None:
        """
        Restart treatment after discontinuation (retreatment).
        
        Args:
            date: Date of retreatment start
        """
        if not self.is_discontinued:
            return  # Already active
            
        self.is_discontinued = False
        self.retreatment_count += 1
        self.retreatment_dates.append(date)