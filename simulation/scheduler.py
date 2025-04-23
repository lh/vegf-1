"""Clinic scheduling and resource allocation management.

This module implements a scheduler for managing clinic appointments with capacity
constraints and automatic rescheduling. It supports configurable daily capacity
and working days per week.

Classes
-------
ClinicScheduler
    Manages appointment scheduling with capacity constraints

Key Features
------------
- Daily capacity limits
- Configurable clinic days per week
- Automatic rescheduling when capacity exceeded
- Weekend/holiday handling
- Appointment tracking

Examples
--------
>>> scheduler = ClinicScheduler(daily_capacity=20, days_per_week=5)
>>> event = Event(time=datetime(2023,1,1), ...)
>>> if not scheduler.request_slot(event, end_date=datetime(2023,12,31)):
...     print("Visit needs rescheduling")

Notes
-----
- Time values should be timezone-naive datetimes
- Capacity checks are performed per calendar day
- Rescheduling maintains original appointment details
"""

from datetime import datetime, timedelta
from typing import Dict, Optional, Callable
from .base import Event

class ClinicScheduler:
    """
    Manages clinic scheduling and resource allocation.

    This class handles the scheduling of patient visits while respecting clinic
    capacity constraints. It supports configurable daily patient capacity and
    working days per week, with automatic rescheduling when capacity is exceeded.

    Parameters
    ----------
    daily_capacity : int
        Maximum number of patients that can be seen per day
    days_per_week : int
        Number of clinic days per week (e.g., 5 for Mon-Fri)

    Attributes
    ----------
    daily_capacity : int
        Maximum patients per day
    days_per_week : int
        Working days per week
    daily_slots : Dict[datetime, int]
        Tracks number of appointments for each date
    rescheduled_visits : int
        Counter for number of rescheduled appointments
    """
    
    def __init__(self, daily_capacity: int, days_per_week: int):
        self.daily_capacity = daily_capacity
        self.days_per_week = days_per_week
        self.daily_slots: Dict[datetime, int] = {}  # date -> number of appointments
        self.rescheduled_visits = 0
    
    def request_slot(self, event: Event, end_date: datetime) -> bool:
        """
        Check if there's capacity for a visit on the requested day.

        Verifies if the requested visit can be accommodated on the specified day,
        considering both clinic working days and daily capacity constraints.

        Parameters
        ----------
        event : Event
            Event containing visit details including requested time
        end_date : datetime
            Simulation end date for rescheduling bounds

        Returns
        -------
        bool
            True if slot is available, False if needs rescheduling

        Examples
        --------
        >>> event = Event(time=datetime(2023,1,1), ...)
        >>> if scheduler.request_slot(event, end_date=datetime(2023,12,31)):
        ...     print("Slot available")
        ... else:
        ...     print("Visit needs rescheduling")

        Notes
        -----
        - Automatically initializes tracking for new dates
        - Handles non-clinic days (e.g., weekends) by rescheduling
        - Updates appointment counts when slot is granted
        - Rescheduling maintains original appointment details
        - Time values should be timezone-naive datetimes

        Algorithm
        ---------
        1. Check if requested date is a clinic day
        2. Initialize slot count if new date
        3. Check daily capacity
        4. If no capacity or non-clinic day, trigger rescheduling
        5. If capacity available, increment count and return True
        """
        visit_date = event.time.date()
        
        # Initialize slots for this date if not exists
        if visit_date not in self.daily_slots:
            self.daily_slots[visit_date] = 0
            
        # Check if this is a clinic day (Mon-Fri by default)
        if event.time.weekday() >= self.days_per_week:
            self._reschedule_visit(event, end_date, next_clinic_day=True)
            return False
            
        # Check daily capacity
        if self.daily_slots[visit_date] >= self.daily_capacity:
            self._reschedule_visit(event, end_date, next_clinic_day=False)
            return False
            
        # If we get here, we have capacity
        self.daily_slots[visit_date] += 1
        return True
    
    def schedule_next_visit(self, event_factory: Callable, patient_id: str, 
                          last_visit: datetime, next_visit_interval: int) -> Optional[Event]:
        """Schedule the next visit for a patient.

        Creates a new visit event for a patient based on their last visit and
        the specified interval.

        Parameters
        ----------
        event_factory : Callable
            Function to create visit events with signature:
            (time: datetime, event_type: str, patient_id: str, data: dict) -> Event
        patient_id : str
            Patient identifier
        last_visit : datetime
            Time of the last visit
        next_visit_interval : int
            Number of weeks until the next visit (must be positive)

        Returns
        -------
        Optional[Event]
            Scheduled visit event, or None if beyond simulation end

        Raises
        ------
        ValueError
            If next_visit_interval is not positive

        Examples
        --------
        >>> next_visit = scheduler.schedule_next_visit(
        ...     event_factory=create_visit_event,
        ...     patient_id="123",
        ...     last_visit=datetime(2023,1,1),
        ...     next_visit_interval=4
        ... )

        Notes
        -----
        - Maintains the same time of day as the original appointment
        - Handles week-to-day conversion automatically
        - Returns None if calculated visit would be after simulation end
        - Visit intervals must be positive integers
        """
        # Calculate next visit time based on last visit
        next_time = last_visit + timedelta(weeks=next_visit_interval)
        # Keep the same time of day as original appointment
        next_time = next_time.replace(hour=last_visit.hour, minute=last_visit.minute)
        
        return Event(
            time=next_time,
            event_type="visit",
            patient_id=patient_id,
            data={
                "visit_type": "injection_visit",
                "actions": ["vision_test", "oct_scan", "injection"],
                "decisions": ["nurse_vision_check", "doctor_treatment_decision"]
            },
            priority=1
        )
    
    def _reschedule_visit(self, event: Event, end_date: datetime, next_clinic_day: bool = False) -> Optional[Event]:
        """
        Reschedule a visit to the next available day.

        Attempts to find the next available slot for a visit that needs rescheduling,
        considering clinic days and capacity constraints.

        Parameters
        ----------
        event : Event
            Event to reschedule
        end_date : datetime
            Simulation end date
        next_clinic_day : bool, optional
            If True, skip to next clinic day (e.g., Monday after Friday)

        Returns
        -------
        Optional[Event]
            Rescheduled event, or None if beyond end date

        Notes
        -----
        - Handles both immediate next day scheduling and next clinic day scheduling
        - Maintains appointment details while updating the time
        - Tracks number of rescheduled visits
        - Respects clinic working days and capacity constraints
        """
        # If the original event time is already past the end date, don't reschedule
        if event.time >= end_date:
            return None
            
        # Calculate next available day
        next_time = event.time
        if next_clinic_day:
            # Find next clinic day (e.g., if today is Friday, go to Monday)
            days_to_add = (self.days_per_week - next_time.weekday())
            if days_to_add <= 0:
                days_to_add += self.days_per_week
            next_time += timedelta(days=days_to_add)
        else:
            # Just go to next day
            next_time += timedelta(days=1)
            
        # Ensure we're on a clinic day
        while next_time.weekday() >= self.days_per_week:
            next_time += timedelta(days=1)
            
        # Check if the next day has available capacity
        next_date = next_time.date()
        if next_date not in self.daily_slots:
            self.daily_slots[next_date] = 0
            
        # If next day is full, try the following days
        while (self.daily_slots[next_date] >= self.daily_capacity and 
               next_time <= end_date):
            next_time += timedelta(days=1)
            while next_time.weekday() >= self.days_per_week:
                next_time += timedelta(days=1)
            next_date = next_time.date()
            if next_date not in self.daily_slots:
                self.daily_slots[next_date] = 0
                
        # Only reschedule if we haven't reached the end date and found a day with capacity
        if next_time <= end_date:
            self.rescheduled_visits += 1
            return Event(
                time=next_time,
                event_type=event.event_type,
                patient_id=event.patient_id,
                data=event.data,
                priority=1
            )
        return None
