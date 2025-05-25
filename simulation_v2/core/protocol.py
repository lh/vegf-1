"""
Treatment protocols for AMD simulation V2.

Protocols define when patients should receive treatment based on
their disease state and treatment history.
"""

from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Optional
from .disease_model import DiseaseState
from .patient import Patient


class Protocol(ABC):
    """Base class for treatment protocols."""
    
    @abstractmethod
    def should_treat(self, patient: Patient, current_date: datetime) -> bool:
        """
        Determine if patient should receive treatment.
        
        Args:
            patient: Patient to evaluate
            current_date: Current simulation date
            
        Returns:
            True if patient should receive injection
        """
        pass
        
    @abstractmethod
    def next_visit_date(self, patient: Patient, current_date: datetime, treated: bool) -> datetime:
        """
        Calculate next visit date based on protocol.
        
        Args:
            patient: Patient to schedule
            current_date: Current date
            treated: Whether patient was treated at current visit
            
        Returns:
            Date of next scheduled visit
        """
        pass


class StandardProtocol(Protocol):
    """
    Standard treat-and-extend protocol.
    
    - Treat active disease states (NAIVE, ACTIVE, HIGHLY_ACTIVE)
    - Don't treat stable disease
    - Extend intervals when stable
    - Shorten intervals when active
    """
    
    def __init__(
        self,
        min_interval_days: int = 28,  # 4 weeks
        max_interval_days: int = 112,  # 16 weeks
        extension_days: int = 14,  # 2 weeks
        shortening_days: int = 14  # 2 weeks
    ):
        """
        Initialize protocol parameters.
        
        Args:
            min_interval_days: Minimum interval between visits (default: 28 days / 4 weeks)
            max_interval_days: Maximum interval between visits (default: 112 days / 16 weeks)
            extension_days: Days to extend when stable (default: 14 days / 2 weeks)
            shortening_days: Days to shorten when active (default: 14 days / 2 weeks)
        """
        self.min_interval_days = min_interval_days
        self.max_interval_days = max_interval_days
        self.extension_days = extension_days
        self.shortening_days = shortening_days
        
    @classmethod
    def from_weeks(
        cls,
        min_interval_weeks: int = 4,
        max_interval_weeks: int = 16,
        extension_weeks: int = 2,
        shortening_weeks: int = 2
    ):
        """
        Create protocol using week-based parameters.
        
        Args:
            min_interval_weeks: Minimum interval in weeks
            max_interval_weeks: Maximum interval in weeks
            extension_weeks: Weeks to extend when stable
            shortening_weeks: Weeks to shorten when active
            
        Returns:
            StandardProtocol instance
        """
        return cls(
            min_interval_days=min_interval_weeks * 7,
            max_interval_days=max_interval_weeks * 7,
            extension_days=extension_weeks * 7,
            shortening_days=shortening_weeks * 7
        )
        
    def should_treat(self, patient: Patient, current_date: datetime) -> bool:
        """
        Treat if disease is active.
        
        FOV states that require treatment:
        - NAIVE: First presentation
        - ACTIVE: Active disease
        - HIGHLY_ACTIVE: Severe active disease
        
        FOV states that don't require treatment:
        - STABLE: No active disease
        """
        if patient.is_discontinued:
            return False
            
        # Treatment decision based on disease state
        active_states = {DiseaseState.NAIVE, DiseaseState.ACTIVE, DiseaseState.HIGHLY_ACTIVE}
        return patient.current_state in active_states
        
    def next_visit_date(self, patient: Patient, current_date: datetime, treated: bool) -> datetime:
        """
        Calculate next visit using treat-and-extend logic.
        
        - If treated (active disease): maintain or shorten interval
        - If not treated (stable): extend interval
        - Respect min/max bounds
        """
        # Get current interval in days
        days_since_last = patient.days_since_last_injection_at(current_date)
        if days_since_last is None:
            # First visit, use minimum interval
            current_interval = self.min_interval_days
        else:
            # Use actual interval, bounded by protocol limits
            current_interval = max(self.min_interval_days, 
                                  min(days_since_last, self.max_interval_days))
        
        # Adjust interval based on treatment
        if treated:
            if patient.current_state == DiseaseState.HIGHLY_ACTIVE:
                # Shorten for highly active disease
                new_interval = max(self.min_interval_days, 
                                 current_interval - self.shortening_days)
            else:
                # Maintain for regular active disease
                new_interval = current_interval
        else:
            # Extend for stable disease
            new_interval = min(self.max_interval_days,
                             current_interval + self.extension_days)
            
        # Calculate next date
        return current_date + timedelta(days=new_interval)