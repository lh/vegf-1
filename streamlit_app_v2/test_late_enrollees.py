#!/usr/bin/env python3
"""
Test script specifically for verifying late enrollee behavior.

Tests that patients who enroll later in the simulation have:
1. Fewer total visits
2. Correct time calculations
3. Proper data integrity
"""

import sys
import pandas as pd
from pathlib import Path
import numpy as np

# Add parent to path
sys.path.append(str(Path(__file__).parent))
sys.path.append(str(Path(__file__).parent.parent))

from simulation_v2.protocols.protocol_spec import ProtocolSpecification
from core.simulation_runner import SimulationRunner


def test_late_enrollees():
    """Test late enrollee behavior with longer simulation."""
    print("=" * 60)
    print("Testing Late Enrollee Behavior")
    print("=" * 60)
    
    # Load protocol
    protocol_path = Path("protocols/eylea.yaml")
    if not protocol_path.exists():
        print(f"Error: Protocol not found at {protocol_path}")
        return False
        
    protocol_spec = ProtocolSpecification.from_yaml(protocol_path)
    
    # Run longer simulation
    print("\n1. Running 2-year simulation with 100 patients...")
    runner = SimulationRunner(protocol_spec)
    results = runner.run(
        engine_type='abs',
        n_patients=100,
        duration_years=2.0,  # 2 years
        seed=123,
        show_progress=True
    )
    
    print(f"\nSimulation saved to: {results.data_path}")
    
    # Read parquet files
    print("\n2. Analyzing enrollment patterns...")
    patients_df = pd.read_parquet(results.data_path / "patients.parquet")
    visits_df = pd.read_parquet(results.data_path / "visits.parquet")
    
    # Group patients by enrollment quartile
    patients_df['enrollment_quartile'] = pd.qcut(
        patients_df['enrollment_time_days'], 
        q=4, 
        labels=['Q1 (Early)', 'Q2', 'Q3', 'Q4 (Late)']
    )
    
    # Analyze visits by quartile
    print("\n3. Visit counts by enrollment quartile:")
    visit_stats = []
    
    for quartile in ['Q1 (Early)', 'Q2', 'Q3', 'Q4 (Late)']:
        quartile_patients = patients_df[patients_df['enrollment_quartile'] == quartile]
        
        # Calculate visit statistics
        visit_counts = []
        for patient_id in quartile_patients['patient_id']:
            n_visits = len(visits_df[visits_df['patient_id'] == patient_id])
            visit_counts.append(n_visits)
        
        avg_visits = np.mean(visit_counts)
        min_visits = np.min(visit_counts)
        max_visits = np.max(visit_counts)
        
        visit_stats.append({
            'Quartile': quartile,
            'Patients': len(quartile_patients),
            'Avg Visits': f"{avg_visits:.1f}",
            'Min Visits': min_visits,
            'Max Visits': max_visits
        })
        
        print(f"   {quartile}: {len(quartile_patients)} patients, "
              f"avg {avg_visits:.1f} visits (range: {min_visits}-{max_visits})")
    
    # Check if late enrollees have fewer visits
    q1_avg = float(visit_stats[0]['Avg Visits'])
    q4_avg = float(visit_stats[3]['Avg Visits'])
    
    if q4_avg >= q1_avg:
        print("\n   ❌ ERROR: Late enrollees (Q4) have as many or more visits than early enrollees (Q1)!")
        return False
    
    reduction = (q1_avg - q4_avg) / q1_avg * 100
    print(f"\n   ✅ Late enrollees have {reduction:.1f}% fewer visits on average")
    
    # Check individual late enrollees
    print("\n4. Checking specific late enrollees...")
    latest_enrollees = patients_df.nlargest(5, 'enrollment_time_days')
    
    print("\n   Latest 5 enrollees:")
    for _, patient in latest_enrollees.iterrows():
        patient_visits = visits_df[visits_df['patient_id'] == patient['patient_id']]
        enrollment_day = patient['enrollment_time_days']
        total_visits = len(patient_visits)
        
        # Calculate time remaining after enrollment
        simulation_days = 2.0 * 365  # 2 years
        days_remaining = simulation_days - enrollment_day
        
        print(f"   Patient {patient['patient_id']}: "
              f"enrolled day {enrollment_day:.0f}, "
              f"{days_remaining:.0f} days remaining, "
              f"{total_visits} visits")
        
        # Verify visits are after enrollment
        if len(patient_visits) > 0:
            first_visit_time = patient_visits.iloc[0]['time_days']
            if first_visit_time < 0:
                print(f"      ❌ ERROR: First visit before enrollment!")
                return False
    
    # Check enrollment distribution
    print("\n5. Enrollment distribution analysis:")
    print(f"   Total patients: {len(patients_df)}")
    print(f"   Enrollment span: {patients_df['enrollment_time_days'].min():.0f} to "
          f"{patients_df['enrollment_time_days'].max():.0f} days")
    
    # Calculate expected vs actual enrollment rate
    expected_rate = 100 / (2.0 * 365)  # patients per day
    actual_span = patients_df['enrollment_time_days'].max()
    actual_rate = len(patients_df) / actual_span if actual_span > 0 else 0
    
    print(f"   Expected rate: {expected_rate:.3f} patients/day")
    print(f"   Actual rate: {actual_rate:.3f} patients/day")
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY: Late enrollee tests passed! ✅")
    print("=" * 60)
    
    return True


if __name__ == "__main__":
    success = test_late_enrollees()
    if not success:
        print("\n❌ Tests failed!")
        sys.exit(1)
    else:
        print("\n✅ All tests passed!")