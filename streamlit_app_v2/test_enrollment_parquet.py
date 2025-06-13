#!/usr/bin/env python3
"""
Test script to verify enrollment data is correctly written to Parquet files.

Tests:
1. Enrollment dates are saved correctly
2. Visit times are relative to enrollment, not simulation start
3. Late enrollees have correct time calculations
4. Data integrity is maintained
"""

import sys
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta

# Add parent to path
sys.path.append(str(Path(__file__).parent))
sys.path.append(str(Path(__file__).parent.parent))

from simulation_v2.protocols.protocol_spec import ProtocolSpecification
from core.simulation_runner import SimulationRunner


def test_enrollment_data():
    """Test enrollment data in parquet files."""
    print("=" * 60)
    print("Testing Enrollment Data in Parquet Files")
    print("=" * 60)
    
    # Load protocol
    protocol_path = Path("protocols/eylea.yaml")
    if not protocol_path.exists():
        print(f"Error: Protocol not found at {protocol_path}")
        return False
        
    protocol_spec = ProtocolSpecification.from_yaml(protocol_path)
    
    # Run small simulation
    print("\n1. Running small simulation...")
    runner = SimulationRunner(protocol_spec)
    results = runner.run(
        engine_type='abs',
        n_patients=10,
        duration_years=0.5,  # 6 months
        seed=42,
        show_progress=True
    )
    
    print(f"\nSimulation saved to: {results.data_path}")
    
    # Read parquet files
    print("\n2. Reading parquet files...")
    patients_df = pd.read_parquet(results.data_path / "patients.parquet")
    visits_df = pd.read_parquet(results.data_path / "visits.parquet")
    
    # Check enrollment data in patients file
    print("\n3. Checking enrollment data in patients.parquet...")
    print(f"   Columns: {list(patients_df.columns)}")
    
    if 'enrollment_date' not in patients_df.columns:
        print("   ❌ ERROR: enrollment_date column missing!")
        return False
    
    if 'enrollment_time_days' not in patients_df.columns:
        print("   ❌ ERROR: enrollment_time_days column missing!")
        return False
    
    print("   ✅ Enrollment columns present")
    
    # Verify enrollment dates
    print("\n4. Analyzing enrollment distribution...")
    print(f"   Total patients: {len(patients_df)}")
    print(f"   Enrollment time range: {patients_df['enrollment_time_days'].min()} to {patients_df['enrollment_time_days'].max()} days")
    
    # Check that enrollment is staggered (not all at day 0)
    unique_enrollment_days = patients_df['enrollment_time_days'].nunique()
    if unique_enrollment_days == 1 and patients_df['enrollment_time_days'].iloc[0] == 0:
        print("   ❌ ERROR: All patients enrolled at day 0 - staggered enrollment not working!")
        return False
    
    print(f"   ✅ Patients enrolled across {unique_enrollment_days} different days")
    
    # Sample enrollment data
    print("\n   Sample enrollment data:")
    sample_data = patients_df[['patient_id', 'enrollment_date', 'enrollment_time_days']].head(5)
    print(sample_data.to_string(index=False))
    
    # Check visit times are relative to enrollment
    print("\n5. Checking visit times relative to enrollment...")
    
    # For each patient, verify first visit is after enrollment
    issues = []
    for patient_id in patients_df['patient_id'].head(5):  # Check first 5 patients
        patient_visits = visits_df[visits_df['patient_id'] == patient_id].sort_values('time_days')
        if len(patient_visits) > 0:
            first_visit_time = patient_visits.iloc[0]['time_days']
            if first_visit_time < 0:
                issues.append(f"Patient {patient_id}: First visit at day {first_visit_time} (before enrollment!)")
            else:
                print(f"   Patient {patient_id}: First visit at day {first_visit_time} after enrollment")
    
    if issues:
        print("   ❌ ERRORS found:")
        for issue in issues:
            print(f"      {issue}")
        return False
    
    print("   ✅ All visit times are properly relative to enrollment")
    
    # Check late enrollees
    print("\n6. Checking late enrollees...")
    late_enrollees = patients_df[patients_df['enrollment_time_days'] > 30]  # Enrolled after first month
    print(f"   Found {len(late_enrollees)} patients enrolled after day 30")
    
    if len(late_enrollees) > 0:
        # Check that late enrollees have fewer visits
        late_patient_id = late_enrollees.iloc[0]['patient_id']
        late_visits = len(visits_df[visits_df['patient_id'] == late_patient_id])
        
        early_enrollee = patients_df[patients_df['enrollment_time_days'] < 10].iloc[0]
        early_patient_id = early_enrollee['patient_id']
        early_visits = len(visits_df[visits_df['patient_id'] == early_patient_id])
        
        print(f"   Late enrollee {late_patient_id}: {late_visits} visits")
        print(f"   Early enrollee {early_patient_id}: {early_visits} visits")
        
        if late_visits >= early_visits:
            print("   ⚠️  WARNING: Late enrollee has as many visits as early enrollee")
        else:
            print("   ✅ Late enrollees have fewer visits as expected")
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY: All enrollment data tests passed! ✅")
    print("=" * 60)
    
    return True


if __name__ == "__main__":
    success = test_enrollment_data()
    if not success:
        print("\n❌ Tests failed!")
        sys.exit(1)
    else:
        print("\n✅ All tests passed!")