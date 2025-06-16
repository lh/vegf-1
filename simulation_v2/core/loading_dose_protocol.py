"""
Loading dose protocol wrapper for AMD simulation.

Implements a loading dose phase followed by treat-and-extend.
"""

from datetime import datetime, timedelta
from typing import Optional
from .protocol import Protocol, StandardProtocol
from .patient import Patient


class LoadingDoseProtocol(Protocol):
    """
    Protocol with initial loading dose phase.
    
    - First N injections at fixed intervals regardless of disease state
    - Then switches to standard treat-and-extend protocol
    """
    
    def __init__(
        self,
        loading_dose_injections: int = 3,
        loading_dose_interval_days: int = 28,
        base_protocol: Optional[Protocol] = None,
        **kwargs
    ):
        """
        Initialize loading dose protocol.
        
        Args:
            loading_dose_injections: Number of initial injections
            loading_dose_interval_days: Days between loading doses
            base_protocol: Protocol to use after loading phase
            **kwargs: Arguments passed to StandardProtocol if base_protocol not provided
        """
        self.loading_dose_injections = loading_dose_injections
        self.loading_dose_interval_days = loading_dose_interval_days
        
        # Use provided protocol or create standard one
        if base_protocol is None:
            self.base_protocol = StandardProtocol(**kwargs)
        else:
            self.base_protocol = base_protocol
    
    def should_treat(self, patient: Patient, current_date: datetime) -> bool:
        """
        Determine if patient should receive treatment.
        
        During loading phase: Always treat
        After loading phase: Delegate to base protocol
        """
        if patient.is_discontinued:
            return False
        
        # Check if still in loading phase
        if patient.injection_count < self.loading_dose_injections:
            return True
        
        # After loading phase, use base protocol
        return self.base_protocol.should_treat(patient, current_date)
    
    def next_visit_date(self, patient: Patient, current_date: datetime, treated: bool) -> datetime:
        """
        Calculate next visit date.
        
        During loading phase: Fixed interval
        After loading phase: Delegate to base protocol
        """
        # Check if still in loading phase (subtract 1 because we just treated)
        if patient.injection_count < self.loading_dose_injections:
            # Use fixed loading dose interval
            return current_date + timedelta(days=self.loading_dose_interval_days)
        
        # After loading phase, use base protocol
        return self.base_protocol.next_visit_date(patient, current_date, treated)
    
    def is_in_loading_phase(self, patient: Patient) -> bool:
        """Check if patient is still in loading dose phase."""
        return patient.injection_count < self.loading_dose_injections