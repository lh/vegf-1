#!/usr/bin/env python
"""
Test that weekday scheduling is working correctly.
"""

from pathlib import Path
from datetime import datetime

from simulation_v2.protocols.time_based_protocol_spec import TimeBasedProtocolSpecification
from simulation_v2.core.time_based_simulation_runner_with_resources import TimeBasedSimulationRunnerWithResources


def main():
    """Test weekday scheduling."""
    # Load protocol
    protocol_path = Path("protocols/v2_time_based/aflibercept_treat_and_treat_time_based.yaml")
    spec = TimeBasedProtocolSpecification.from_yaml(protocol_path)
    
    # Create runner
    runner = TimeBasedSimulationRunnerWithResources(spec)
    
    # Run small simulation
    print("Running simulation with weekday scheduling...")
    results = runner.run(
        engine_type='abs',
        n_patients=50,
        duration_years=1,
        seed=42
    )
    
    print(f"\nTotal patients: {results.patient_count}")
    print(f"Total visits tracked: {len(results.visit_records) if hasattr(results, 'visit_records') else 'N/A'}")
    
    # Check visit dates
    weekend_visits = 0
    weekday_visits = 0
    
    if hasattr(results, 'visit_records'):
        for visit in results.visit_records:
            date = visit['date']
            if isinstance(date, str):
                date = datetime.fromisoformat(date)
            
            if date.weekday() >= 5:  # Saturday or Sunday
                weekend_visits += 1
                print(f"Weekend visit found: {date.strftime('%Y-%m-%d %A')}")
            else:
                weekday_visits += 1
    
    print(f"\nWeekday visits: {weekday_visits}")
    print(f"Weekend visits: {weekend_visits}")
    
    # Also check from patient histories
    print("\n--- Checking patient histories ---")
    patient_weekend_visits = 0
    patient_weekday_visits = 0
    
    for patient_id, patient in results.patient_histories.items():
        for visit in patient.visit_history:
            date = visit['date']
            if date.weekday() >= 5:
                patient_weekend_visits += 1
                if patient_weekend_visits <= 5:  # Show first few
                    print(f"Patient {patient_id}: Weekend visit on {date.strftime('%Y-%m-%d %A')}")
            else:
                patient_weekday_visits += 1
    
    print(f"\nFrom patient histories:")
    print(f"Weekday visits: {patient_weekday_visits}")
    print(f"Weekend visits: {patient_weekend_visits}")
    
    if patient_weekend_visits == 0:
        print("\n✅ SUCCESS: No visits scheduled on weekends!")
    else:
        print(f"\n⚠️  WARNING: {patient_weekend_visits} visits still on weekends")


if __name__ == "__main__":
    main()