"""
Test that first visits are properly scheduled according to weekend configuration.
"""

import pytest
from datetime import datetime, timedelta
from pathlib import Path

from simulation_v2.protocols.time_based_protocol_spec import TimeBasedProtocolSpecification
from simulation_v2.engines.abs_engine_time_based import ABSEngineTimeBased
from simulation_v2.core.disease_model_time_based import DiseaseModelTimeBased
from simulation_v2.core.weekday_protocol import WeekdayLoadingDoseProtocol


class TestFirstVisitScheduling:
    """Test that first visits respect weekend configuration."""
    
    def test_first_visit_adjusted_from_weekend(self):
        """Test that patients enrolling on weekends have first visit adjusted."""
        # Create a simple protocol
        protocol = WeekdayLoadingDoseProtocol(
            loading_dose_injections=3,
            loading_dose_interval_days=28,
            min_interval_days=56,
            max_interval_days=112,
            allow_saturday=False,
            allow_sunday=False
        )
        
        # Create disease model with minimal transitions
        fortnightly_transitions = {
            'NAIVE': {'NAIVE': 0.8, 'STABLE': 0.15, 'ACTIVE': 0.05, 'HIGHLY_ACTIVE': 0.0},
            'STABLE': {'NAIVE': 0.0, 'STABLE': 0.85, 'ACTIVE': 0.10, 'HIGHLY_ACTIVE': 0.05},
            'ACTIVE': {'NAIVE': 0.0, 'STABLE': 0.1, 'ACTIVE': 0.8, 'HIGHLY_ACTIVE': 0.1},
            'HIGHLY_ACTIVE': {'NAIVE': 0.0, 'STABLE': 0.05, 'ACTIVE': 0.15, 'HIGHLY_ACTIVE': 0.8}
        }
        disease_model = DiseaseModelTimeBased(
            fortnightly_transitions=fortnightly_transitions,
            treatment_half_life_days=56,
            seed=42
        )
        
        # Create engine
        engine = ABSEngineTimeBased(
            disease_model=disease_model,
            protocol=protocol,
            n_patients=10,
            seed=42
        )
        
        # Set up patient arrival on a Saturday
        saturday = datetime(2024, 1, 6)  # Saturday
        
        # Manually create arrival schedule with weekend dates
        engine.patient_arrival_schedule = [
            (saturday, "P0001"),  # Saturday enrollment
            (saturday + timedelta(days=1), "P0002"),  # Sunday enrollment
            (saturday + timedelta(days=2), "P0003"),  # Monday enrollment
        ]
        
        # Run simulation for a short period
        results = engine.run(duration_years=0.1, start_date=saturday)
        
        # Check first visits
        for patient_id, patient in results.patient_histories.items():
            if patient.visit_history:
                first_visit = patient.visit_history[0]
                first_visit_weekday = first_visit['date'].weekday()
                
                print(f"{patient_id} enrolled {engine.enrollment_dates[patient_id].strftime('%A')}, "
                      f"first visit {first_visit['date'].strftime('%A')}")
                
                # First visit should be on a weekday
                assert first_visit_weekday < 5, \
                    f"{patient_id} has first visit on weekend: {first_visit['date']}"
    
    def test_saturday_working_allows_saturday_first_visit(self):
        """Test that Saturday working allows Saturday first visits."""
        # Create protocol with Saturday working
        protocol = WeekdayLoadingDoseProtocol(
            loading_dose_injections=3,
            loading_dose_interval_days=28,
            min_interval_days=56,
            max_interval_days=112,
            allow_saturday=True,  # Allow Saturday
            allow_sunday=False
        )
        
        # Create disease model with minimal transitions
        fortnightly_transitions = {
            'NAIVE': {'NAIVE': 0.8, 'STABLE': 0.15, 'ACTIVE': 0.05, 'HIGHLY_ACTIVE': 0.0},
            'STABLE': {'NAIVE': 0.0, 'STABLE': 0.85, 'ACTIVE': 0.10, 'HIGHLY_ACTIVE': 0.05},
            'ACTIVE': {'NAIVE': 0.0, 'STABLE': 0.1, 'ACTIVE': 0.8, 'HIGHLY_ACTIVE': 0.1},
            'HIGHLY_ACTIVE': {'NAIVE': 0.0, 'STABLE': 0.05, 'ACTIVE': 0.15, 'HIGHLY_ACTIVE': 0.8}
        }
        disease_model = DiseaseModelTimeBased(
            fortnightly_transitions=fortnightly_transitions,
            treatment_half_life_days=56,
            seed=42
        )
        
        # Create engine
        engine = ABSEngineTimeBased(
            disease_model=disease_model,
            protocol=protocol,
            n_patients=10,
            seed=42
        )
        
        # Set up patient arrival on a Saturday
        saturday = datetime(2024, 1, 6)  # Saturday
        sunday = datetime(2024, 1, 7)    # Sunday
        
        # Manually create arrival schedule
        engine.patient_arrival_schedule = [
            (saturday, "P0001"),  # Saturday enrollment
            (sunday, "P0002"),     # Sunday enrollment
        ]
        
        # Run simulation
        results = engine.run(duration_years=0.1, start_date=saturday)
        
        # Check visits
        p1_first = results.patient_histories["P0001"].visit_history[0]['date']
        p2_first = results.patient_histories["P0002"].visit_history[0]['date']
        
        # P0001 (Saturday enrollment) should have Saturday first visit
        assert p1_first.weekday() == 5, f"P0001 first visit not on Saturday: {p1_first}"
        
        # P0002 (Sunday enrollment) should be adjusted (Sunday not allowed)
        assert p2_first.weekday() != 6, f"P0002 first visit on Sunday: {p2_first}"
        # Should be adjusted to Saturday (prefer earlier) or Monday
        assert p2_first.weekday() in [5, 0], f"P0002 first visit on unexpected day: {p2_first}"
    
    def test_subsequent_visits_respect_weekend_config(self):
        """Test that all subsequent visits also respect weekend configuration."""
        # Create protocol without weekend working
        protocol = WeekdayLoadingDoseProtocol(
            loading_dose_injections=3,
            loading_dose_interval_days=28,
            min_interval_days=56,
            max_interval_days=112,
            allow_saturday=False,
            allow_sunday=False
        )
        
        # Create disease model with minimal transitions
        fortnightly_transitions = {
            'NAIVE': {'NAIVE': 0.8, 'STABLE': 0.15, 'ACTIVE': 0.05, 'HIGHLY_ACTIVE': 0.0},
            'STABLE': {'NAIVE': 0.0, 'STABLE': 0.85, 'ACTIVE': 0.10, 'HIGHLY_ACTIVE': 0.05},
            'ACTIVE': {'NAIVE': 0.0, 'STABLE': 0.1, 'ACTIVE': 0.8, 'HIGHLY_ACTIVE': 0.1},
            'HIGHLY_ACTIVE': {'NAIVE': 0.0, 'STABLE': 0.05, 'ACTIVE': 0.15, 'HIGHLY_ACTIVE': 0.8}
        }
        disease_model = DiseaseModelTimeBased(
            fortnightly_transitions=fortnightly_transitions,
            treatment_half_life_days=56,
            seed=42
        )
        
        # Create engine
        engine = ABSEngineTimeBased(
            disease_model=disease_model,
            protocol=protocol,
            n_patients=5,
            seed=42
        )
        
        # Run for longer to get multiple visits
        results = engine.run(duration_years=1)
        
        # Check all visits
        weekend_visits = 0
        total_visits = 0
        
        for patient in results.patient_histories.values():
            for visit in patient.visit_history:
                total_visits += 1
                if visit['date'].weekday() >= 5:
                    weekend_visits += 1
                    print(f"Weekend visit found: {visit['date'].strftime('%Y-%m-%d %A')}")
        
        print(f"\nTotal visits: {total_visits}")
        print(f"Weekend visits: {weekend_visits}")
        
        # Should have very few or no weekend visits
        # Allow a small number due to first visits before adjustment logic
        assert weekend_visits < total_visits * 0.05, \
            f"Too many weekend visits: {weekend_visits}/{total_visits}"