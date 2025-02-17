from datetime import datetime, timedelta
from typing import Dict, Optional
from .base import Event

class ClinicScheduler:
    """Manages clinic scheduling and resource allocation"""
    
    def __init__(self, daily_capacity: int, days_per_week: int):
        """
        Args:
            daily_capacity: Maximum number of patients that can be seen per day
            days_per_week: Number of clinic days per week (e.g., 5 for Mon-Fri)
        """
        self.daily_capacity = daily_capacity
        self.days_per_week = days_per_week
        self.daily_slots: Dict[datetime, int] = {}  # date -> number of appointments
        self.rescheduled_visits = 0
    
    def request_slot(self, event: Event, end_date: datetime) -> bool:
        """Check if there's capacity for this visit on this day
        
        Args:
            event: Event containing visit details
            end_date: Simulation end date for rescheduling bounds
            
        Returns:
            bool: True if slot is available, False if needs rescheduling
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
    
    def schedule_next_visit(self, event_factory, patient_id: str, 
                          last_visit: datetime, weeks: int) -> Optional[Event]:
        """Schedule the next visit for a patient
        
        Args:
            event_factory: Function to create visit events
            patient_id: Patient identifier
            last_visit: Time of the last visit
            weeks: Number of weeks until next visit
            
        Returns:
            Event: Scheduled visit event, or None if beyond simulation end
        """
        # Calculate next visit time based on last visit
        next_time = last_visit + timedelta(weeks=weeks)
        # Keep the same time of day as original appointment
        next_time = next_time.replace(hour=last_visit.hour, minute=last_visit.minute)
        
        return event_factory(
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
        """Reschedule a visit to the next available day
        
        Args:
            event: Event to reschedule
            end_date: Simulation end date
            next_clinic_day: If True, skip to next clinic day (e.g., Monday after Friday)
            
        Returns:
            Event: Rescheduled event, or None if beyond end date
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
