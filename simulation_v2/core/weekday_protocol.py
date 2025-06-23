"""
Weekday-aware treatment protocols.

Extends standard protocols to ensure visits are scheduled on weekdays
with appropriate flexibility for different visit types.
"""

from datetime import datetime
from typing import Optional

from .protocol import StandardProtocol, Protocol
from .loading_dose_protocol import LoadingDoseProtocol
from .patient import Patient
from .weekday_scheduler import WeekdayScheduler


class WeekdayAwareProtocol(Protocol):
    """Wrapper that makes any protocol weekday-aware."""
    
    def __init__(self, base_protocol: Protocol, prefer_earlier: bool = True):
        """
        Initialize weekday-aware protocol.
        
        Args:
            base_protocol: The underlying protocol to wrap
            prefer_earlier: Whether to prefer Friday over Monday for weekend adjustments
        """
        self.base_protocol = base_protocol
        self.prefer_earlier = prefer_earlier
        self.scheduler = WeekdayScheduler()
        self._visit_counter = {}  # Track visit numbers per patient
    
    def should_treat(self, patient: Patient, current_date: datetime) -> bool:
        """Delegate treatment decision to base protocol."""
        return self.base_protocol.should_treat(patient, current_date)
    
    def next_visit_date(self, patient: Patient, current_date: datetime, treated: bool) -> datetime:
        """
        Calculate next visit date ensuring it falls on a weekday.
        
        Applies appropriate flexibility based on visit number and interval.
        """
        # Track visit number
        if patient.id not in self._visit_counter:
            self._visit_counter[patient.id] = 0
        self._visit_counter[patient.id] += 1
        visit_number = self._visit_counter[patient.id]
        
        # Get base protocol's next date
        base_next_date = self.base_protocol.next_visit_date(patient, current_date, treated)
        target_interval_days = (base_next_date - current_date).days
        
        # Schedule on weekday with appropriate flexibility
        return self.scheduler.schedule_next_visit(
            current_date,
            target_interval_days,
            visit_number,
            self.prefer_earlier
        )
    
    def reset_patient_counter(self, patient_id: str):
        """Reset visit counter for a patient (e.g., after discontinuation)."""
        if patient_id in self._visit_counter:
            del self._visit_counter[patient_id]


class WeekdayStandardProtocol(StandardProtocol):
    """Standard protocol with built-in weekday scheduling."""
    
    def __init__(self, *args, prefer_earlier: bool = True, 
                 allow_saturday: bool = False, allow_sunday: bool = False, **kwargs):
        """
        Initialize with weekday scheduling.
        
        Args:
            *args, **kwargs: Arguments for StandardProtocol
            prefer_earlier: Whether to prefer Friday over Monday
            allow_saturday: Whether Saturday visits are allowed
            allow_sunday: Whether Sunday visits are allowed
        """
        super().__init__(*args, **kwargs)
        self.scheduler = WeekdayScheduler(allow_saturday=allow_saturday, 
                                         allow_sunday=allow_sunday)
        self.prefer_earlier = prefer_earlier
        self._visit_counter = {}
    
    def next_visit_date(self, patient: Patient, current_date: datetime, treated: bool) -> datetime:
        """Override to ensure weekday scheduling."""
        # Track visit number
        if patient.id not in self._visit_counter:
            self._visit_counter[patient.id] = 0
        self._visit_counter[patient.id] += 1
        visit_number = self._visit_counter[patient.id]
        
        # Get base interval calculation
        base_next_date = super().next_visit_date(patient, current_date, treated)
        target_interval_days = (base_next_date - current_date).days
        
        # Schedule on weekday
        return self.scheduler.schedule_next_visit(
            current_date,
            target_interval_days,
            visit_number,
            self.prefer_earlier
        )


class WeekdayLoadingDoseProtocol(LoadingDoseProtocol):
    """Loading dose protocol with built-in weekday scheduling."""
    
    def __init__(self, *args, prefer_earlier: bool = True,
                 allow_saturday: bool = False, allow_sunday: bool = False, **kwargs):
        """
        Initialize with weekday scheduling.
        
        Args:
            *args, **kwargs: Arguments for LoadingDoseProtocol
            prefer_earlier: Whether to prefer Friday over Monday
            allow_saturday: Whether Saturday visits are allowed
            allow_sunday: Whether Sunday visits are allowed
        """
        super().__init__(*args, **kwargs)
        self.scheduler = WeekdayScheduler(allow_saturday=allow_saturday,
                                         allow_sunday=allow_sunday)
        self.prefer_earlier = prefer_earlier
        self._visit_counter = {}
    
    def next_visit_date(self, patient: Patient, current_date: datetime, treated: bool) -> datetime:
        """Override to ensure weekday scheduling."""
        # Track visit number
        if patient.id not in self._visit_counter:
            self._visit_counter[patient.id] = 0
        self._visit_counter[patient.id] += 1
        visit_number = self._visit_counter[patient.id]
        
        # Get base interval calculation
        base_next_date = super().next_visit_date(patient, current_date, treated)
        target_interval_days = (base_next_date - current_date).days
        
        # Schedule on weekday
        return self.scheduler.schedule_next_visit(
            current_date,
            target_interval_days,
            visit_number,
            self.prefer_earlier
        )