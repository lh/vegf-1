"""
Tests for weekday-aware scheduling.

Ensures visits are properly scheduled on weekdays with appropriate flexibility.
"""

import pytest
from datetime import datetime, timedelta

from simulation_v2.core.weekday_scheduler import WeekdayScheduler
from simulation_v2.core.weekday_protocol import WeekdayStandardProtocol, WeekdayLoadingDoseProtocol
from simulation_v2.core.patient import Patient
from simulation_v2.core.disease_model import DiseaseState


class TestWeekdayScheduler:
    """Test the WeekdayScheduler utility class."""
    
    def test_adjust_to_weekday_already_weekday(self):
        """Test that weekdays are not adjusted."""
        # Monday
        monday = datetime(2024, 1, 1)
        assert WeekdayScheduler.adjust_to_weekday(monday) == monday
        
        # Friday
        friday = datetime(2024, 1, 5)
        assert WeekdayScheduler.adjust_to_weekday(friday) == friday
    
    def test_adjust_saturday_prefer_earlier(self):
        """Test Saturday adjustment preferring Friday."""
        saturday = datetime(2024, 1, 6)  # Saturday
        adjusted = WeekdayScheduler.adjust_to_weekday(saturday, prefer_earlier=True)
        assert adjusted.weekday() == 4  # Friday
        assert adjusted == datetime(2024, 1, 5)
    
    def test_adjust_saturday_prefer_later(self):
        """Test Saturday adjustment preferring Monday."""
        saturday = datetime(2024, 1, 6)  # Saturday
        adjusted = WeekdayScheduler.adjust_to_weekday(saturday, prefer_earlier=False)
        assert adjusted.weekday() == 0  # Monday
        assert adjusted == datetime(2024, 1, 8)
    
    def test_adjust_sunday_prefer_earlier(self):
        """Test Sunday adjustment preferring Friday."""
        sunday = datetime(2024, 1, 7)  # Sunday
        adjusted = WeekdayScheduler.adjust_to_weekday(sunday, prefer_earlier=True)
        assert adjusted.weekday() == 4  # Friday
        assert adjusted == datetime(2024, 1, 5)
    
    def test_adjust_sunday_prefer_later(self):
        """Test Sunday adjustment preferring Monday."""
        sunday = datetime(2024, 1, 7)  # Sunday
        adjusted = WeekdayScheduler.adjust_to_weekday(sunday, prefer_earlier=False)
        assert adjusted.weekday() == 0  # Monday
        assert adjusted == datetime(2024, 1, 8)
    
    def test_interval_flexibility_loading_phase(self):
        """Test flexibility for loading phase visits."""
        # First 3 visits should have 4-5 week flexibility
        min_days, max_days = WeekdayScheduler.get_interval_flexibility(1, 4)
        assert min_days == 28  # 4 weeks
        assert max_days == 35  # 5 weeks
        
        min_days, max_days = WeekdayScheduler.get_interval_flexibility(3, 4)
        assert min_days == 28
        assert max_days == 35
    
    def test_interval_flexibility_8_week(self):
        """Test flexibility for 8-week visits."""
        min_days, max_days = WeekdayScheduler.get_interval_flexibility(5, 8)
        assert min_days == 56  # 8 weeks
        assert max_days == 63  # 9 weeks
    
    def test_interval_flexibility_12_week(self):
        """Test flexibility for 12-week visits."""
        min_days, max_days = WeekdayScheduler.get_interval_flexibility(10, 12)
        assert min_days == 77  # 11 weeks
        assert max_days == 91  # 13 weeks
    
    def test_interval_flexibility_16_week(self):
        """Test flexibility for 16-week visits."""
        min_days, max_days = WeekdayScheduler.get_interval_flexibility(15, 16)
        assert min_days == 105  # 15 weeks
        assert max_days == 119  # 17 weeks
    
    def test_schedule_next_visit_simple(self):
        """Test basic next visit scheduling."""
        # Start on Monday
        current = datetime(2024, 1, 1)  # Monday
        
        # 4 weeks later would be Monday
        next_visit = WeekdayScheduler.schedule_next_visit(current, 28, 1)
        assert next_visit.weekday() < 5
        assert next_visit == datetime(2024, 1, 29)  # Monday
    
    def test_schedule_next_visit_weekend_adjustment(self):
        """Test visit scheduling when target falls on weekend."""
        # Start on Friday
        current = datetime(2024, 1, 5)  # Friday
        
        # 4 weeks later would be Saturday
        next_visit = WeekdayScheduler.schedule_next_visit(current, 28, 1, prefer_earlier=True)
        assert next_visit.weekday() == 4  # Friday
        assert next_visit == datetime(2024, 2, 2)  # Friday (one day earlier)
    
    def test_schedule_respects_flexibility(self):
        """Test that scheduling respects interval flexibility."""
        # Start on Monday
        current = datetime(2024, 1, 1)  # Monday
        
        # Try to schedule 8 weeks + 3 days (would be Thursday to Sunday)
        # Should end up on Friday (within 8-9 week range)
        next_visit = WeekdayScheduler.schedule_next_visit(current, 59, 5)
        assert next_visit.weekday() < 5
        
        # Check it's within allowed range
        interval = (next_visit - current).days
        assert 56 <= interval <= 63  # 8-9 weeks


class TestWeekdayProtocol:
    """Test weekday-aware protocol implementations."""
    
    @pytest.fixture
    def patient(self):
        """Create a test patient."""
        return Patient("P001", baseline_vision=70)
    
    def test_weekday_standard_protocol(self, patient):
        """Test WeekdayStandardProtocol scheduling."""
        protocol = WeekdayStandardProtocol(
            min_interval_days=28,
            max_interval_days=112,
            extension_days=14,
            shortening_days=14
        )
        
        # First visit on a Friday
        current_date = datetime(2024, 1, 5)  # Friday
        patient.current_state = DiseaseState.ACTIVE
        
        # Should treat active disease
        assert protocol.should_treat(patient, current_date)
        
        # Schedule next visit
        next_date = protocol.next_visit_date(patient, current_date, treated=True)
        
        # Should be on a weekday
        assert next_date.weekday() < 5
        
        # Should be approximately 4 weeks later
        interval = (next_date - current_date).days
        assert 28 <= interval <= 35  # 4-5 week flexibility
    
    def test_loading_dose_weekday_scheduling(self, patient):
        """Test loading dose protocol with weekday scheduling."""
        protocol = WeekdayLoadingDoseProtocol(
            loading_dose_injections=3,
            loading_dose_interval_days=28,
            min_interval_days=56,  # 8 weeks after loading
            max_interval_days=112
        )
        
        # Simulate loading phase
        current_date = datetime(2024, 1, 1)  # Monday
        
        # First loading dose
        patient.injection_count = 0
        next_date = protocol.next_visit_date(patient, current_date, treated=True)
        assert next_date.weekday() < 5
        assert 28 <= (next_date - current_date).days <= 35
        
        # Second loading dose
        current_date = next_date
        patient.injection_count = 1
        next_date = protocol.next_visit_date(patient, current_date, treated=True)
        assert next_date.weekday() < 5
        assert 28 <= (next_date - current_date).days <= 35
        
        # Third loading dose
        current_date = next_date
        patient.injection_count = 2
        next_date = protocol.next_visit_date(patient, current_date, treated=True)
        assert next_date.weekday() < 5
        assert 28 <= (next_date - current_date).days <= 35
        
        # After loading - should switch to 8-week intervals
        current_date = next_date
        patient.injection_count = 3
        next_date = protocol.next_visit_date(patient, current_date, treated=True)
        assert next_date.weekday() < 5
        assert 56 <= (next_date - current_date).days <= 63  # 8-9 weeks
    
    def test_no_consecutive_weekend_visits(self, patient):
        """Test that no visits are scheduled on weekends over extended period."""
        protocol = WeekdayStandardProtocol()
        
        # Run for multiple visits
        current_date = datetime(2024, 1, 1)  # Start on Monday
        patient.current_state = DiseaseState.ACTIVE
        
        for i in range(20):
            # All visits should be on weekdays
            assert current_date.weekday() < 5, f"Visit {i+1} on {current_date} is on weekend!"
            
            # Schedule next visit
            treated = protocol.should_treat(patient, current_date)
            next_date = protocol.next_visit_date(patient, current_date, treated)
            
            # Simulate visit
            if treated:
                patient.record_visit(current_date, patient.current_state, True, 70)
            
            current_date = next_date
    
    def test_visit_counter_reset(self, patient):
        """Test that visit counter can be reset."""
        protocol = WeekdayStandardProtocol()
        
        # Schedule some visits
        current_date = datetime(2024, 1, 1)
        for _ in range(3):
            next_date = protocol.next_visit_date(patient, current_date, True)
            current_date = next_date
        
        # Reset counter
        protocol._visit_counter = {patient.id: 0}
        
        # Next visit should use loading phase flexibility again
        next_date = protocol.next_visit_date(patient, current_date, True)
        interval = (next_date - current_date).days
        assert 28 <= interval <= 35  # Back to 4-5 week flexibility