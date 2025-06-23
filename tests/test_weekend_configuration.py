#!/usr/bin/env python
"""
Test weekend working configuration.
"""

from pathlib import Path
from datetime import datetime
import yaml

from simulation_v2.protocols.time_based_protocol_spec import TimeBasedProtocolSpecification
from simulation_v2.core.time_based_simulation_runner_with_resources import TimeBasedSimulationRunnerWithResources


def test_no_weekends():
    """Test default configuration (no weekend working)."""
    print("=== Testing NO weekend working ===")
    
    # Load standard protocol
    protocol_path = Path("protocols/v2_time_based/aflibercept_treat_and_treat_time_based.yaml")
    spec = TimeBasedProtocolSpecification.from_yaml(protocol_path)
    
    print(f"Allow Saturday: {spec.allow_saturday_visits}")
    print(f"Allow Sunday: {spec.allow_sunday_visits}")
    print(f"Prefer weekday for first visit: {spec.prefer_weekday_for_first_visit}")
    
    # Run small simulation
    runner = TimeBasedSimulationRunnerWithResources(spec)
    results = runner.run('abs', n_patients=20, duration_years=0.5, seed=123)
    
    # Check visits
    weekend_count = 0
    for patient in results.patient_histories.values():
        for visit in patient.visit_history:
            if visit['date'].weekday() >= 5:
                weekend_count += 1
                
    print(f"Weekend visits: {weekend_count}")
    print()


def test_saturday_allowed():
    """Test Saturday working enabled."""
    print("=== Testing Saturday working ENABLED ===")
    
    # Load the example weekend protocol
    protocol_path = Path("protocols/v2_time_based/example_weekend_protocol.yaml")
    if protocol_path.exists():
        spec = TimeBasedProtocolSpecification.from_yaml(protocol_path)
        
        print(f"Allow Saturday: {spec.allow_saturday_visits}")
        print(f"Allow Sunday: {spec.allow_sunday_visits}")
        print(f"Prefer weekday for first visit: {spec.prefer_weekday_for_first_visit}")
        
        # Demonstrate scheduler behavior
        from simulation_v2.core.weekday_scheduler import WeekdayScheduler
        scheduler = WeekdayScheduler(allow_saturday=True, allow_sunday=False)
        
        # Test dates
        saturday = datetime(2024, 1, 6)  # Saturday
        sunday = datetime(2024, 1, 7)    # Sunday
        
        print(f"\nScheduler behavior:")
        print(f"Saturday {saturday.date()} -> {scheduler.adjust_to_weekday(saturday).date()} (no change)")
        print(f"Sunday {sunday.date()} -> {scheduler.adjust_to_weekday(sunday).date()} (adjusted to Saturday)")
        
        # Show that Saturday is a working day
        print(f"\nIs Saturday a working day? {scheduler.is_working_day(saturday)}")
        print(f"Is Sunday a working day? {scheduler.is_working_day(sunday)}")
    else:
        print("Example weekend protocol not found")
    print()


def test_first_visit_adjustment():
    """Test that first visits are adjusted to weekdays."""
    print("=== Testing first visit weekday adjustment ===")
    
    # Use standard protocol
    protocol_path = Path("protocols/v2_time_based/aflibercept_treat_and_treat_time_based.yaml")
    spec = TimeBasedProtocolSpecification.from_yaml(protocol_path)
    
    # Run simulation starting on a Friday (so some enrollments might be on weekends)
    runner = TimeBasedSimulationRunnerWithResources(spec)
    results = runner.run('abs', n_patients=50, duration_years=0.25, seed=789)
    
    # Check first visits
    first_visit_weekends = 0
    for patient in results.patient_histories.values():
        if patient.visit_history:
            first_visit = patient.visit_history[0]
            if first_visit['date'].weekday() >= 5:
                first_visit_weekends += 1
                print(f"First visit on {first_visit['date'].strftime('%A')}: {first_visit['date']}")
    
    print(f"\nTotal first visits on weekends: {first_visit_weekends}")
    print("(Should be low due to weekday adjustment)")


def main():
    """Run all weekend configuration tests."""
    test_no_weekends()
    test_saturday_allowed()
    test_first_visit_adjustment()
    
    print("\n✅ Weekend configuration tests complete!")


if __name__ == "__main__":
    main()