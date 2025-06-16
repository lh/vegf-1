"""
Patient class for AMD simulation V2.

Tracks individual patient state, treatment history, and outcomes.
Part of the FOV (Four Option Version) internal model.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Callable
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
    
    def __init__(self, patient_id: str, baseline_vision: int = 70,
                 visit_metadata_enhancer: Optional[Callable] = None,
                 enrollment_date: Optional[datetime] = None):
        """
        Initialize a new patient.
        
        Args:
            patient_id: Unique identifier for the patient
            baseline_vision: Starting visual acuity in ETDRS letters (0-100, default: 70)
            visit_metadata_enhancer: Optional function to enhance visit metadata
            enrollment_date: Date when patient enters the simulation
        """
        if not 0 <= baseline_vision <= 100:
            raise ValueError(f"Baseline vision must be between 0 and 100 ETDRS letters, got {baseline_vision}")
            
        self.id = patient_id
        self.baseline_vision = baseline_vision
        self.current_vision = baseline_vision
        self.current_state = DiseaseState.NAIVE
        self.enrollment_date = enrollment_date
        
        # Visit and treatment tracking
        self.visit_history: List[Dict[str, Any]] = []
        self.injection_count = 0
        self._last_injection_date: Optional[datetime] = None
        
        # Discontinuation tracking
        self.is_discontinued = False
        self.discontinuation_date: Optional[datetime] = None
        self.discontinuation_type: Optional[str] = None  # e.g., "poor_response"
        self.discontinuation_reason: Optional[str] = None  # Detailed reason
        
        # Additional discontinuation tracking for V2
        self.consecutive_stable_visits = 0
        self.consecutive_poor_vision_visits = 0
        self.monitoring_schedule: List[datetime] = []
        self.pre_discontinuation_vision: Optional[float] = None
        self.first_visit_date: Optional[datetime] = None
        self.current_interval_days: int = 28  # Default 4 weeks
        
        # Extended discontinuation tracking for all reasons
        self.visits_without_improvement = 0
        self.visits_with_significant_loss = 0
        self.age_years: Optional[int] = None  # Patient age for mortality calculations
        self.birth_date: Optional[datetime] = None  # Alternative to age tracking
        self.sex: Optional[str] = None  # Patient sex ('male' or 'female')
        
        # Retreatment tracking
        self.retreatment_count = 0
        self.retreatment_dates: List[datetime] = []
        
        # Visit metadata enhancement for cost tracking
        self.visit_metadata_enhancer = visit_metadata_enhancer
        
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
        
        # Apply metadata enhancement if configured
        if self.visit_metadata_enhancer:
            visit = self.visit_metadata_enhancer(visit, self)
        
        self.visit_history.append(visit)
        
        # Update current state
        self.current_state = disease_state
        self.current_vision = vision
        
        # Update first visit date if needed
        if self.first_visit_date is None:
            self.first_visit_date = date
        
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
        
    def discontinue(self, date: datetime, discontinuation_type: str, reason: Optional[str] = None) -> None:
        """
        Mark patient as discontinued from treatment.
        
        Args:
            date: Discontinuation date
            discontinuation_type: Type of discontinuation (e.g., "poor_response", "premature")
            reason: Optional detailed reason for discontinuation
        """
        self.is_discontinued = True
        self.discontinuation_date = date
        self.discontinuation_type = discontinuation_type
        self.discontinuation_reason = reason
        self.pre_discontinuation_vision = self.current_vision
        
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
        
    def calculate_recent_injection_rate(self, reference_date: datetime, lookback_months: int = 12) -> Optional[float]:
        """
        Calculate the recent injection rate (injections per year) based on treatment history.
        
        Args:
            reference_date: Date to calculate from
            lookback_months: Number of months to look back (default: 12)
            
        Returns:
            Injections per year rate, or None if insufficient data
        """
        if not self.visit_history:
            return None
            
        # Calculate lookback start date
        lookback_days = lookback_months * 30.44  # Average days per month
        lookback_start = reference_date - timedelta(days=lookback_days)
        
        # Count injections in the lookback period
        injection_count = 0
        earliest_visit_in_period = None
        latest_visit_in_period = None
        
        for visit in self.visit_history:
            visit_date = visit['date']
            if lookback_start <= visit_date <= reference_date:
                if visit['treatment_given']:
                    injection_count += 1
                    
                # Track date range
                if earliest_visit_in_period is None or visit_date < earliest_visit_in_period:
                    earliest_visit_in_period = visit_date
                if latest_visit_in_period is None or visit_date > latest_visit_in_period:
                    latest_visit_in_period = visit_date
        
        # Need at least one visit in the period
        if earliest_visit_in_period is None:
            return None
            
        # Calculate actual time span
        if earliest_visit_in_period == latest_visit_in_period:
            # Only one visit in period, can't calculate rate
            return None
            
        time_span_days = (latest_visit_in_period - earliest_visit_in_period).days
        if time_span_days <= 0:
            return None
            
        # Convert to years and calculate rate
        time_span_years = time_span_days / 365.25
        if time_span_years > 0:
            return injection_count / time_span_years
        
        return None