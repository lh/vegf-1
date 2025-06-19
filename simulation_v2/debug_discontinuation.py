"""
Debug discontinuation behavior
"""

import sys
import random
from datetime import datetime, timedelta
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from simulation_v2.clinical_improvements import ClinicalImprovements
from simulation_v2.clinical_improvements.discontinuation import TimeBasedDiscontinuationManager

# Set seed for reproducibility
random.seed(42)

# Test discontinuation manager directly
manager = TimeBasedDiscontinuationManager()

# Simulate 1000 patients
n_patients = 1000
discontinued_patients = []
discontinuation_dates = []

print("Testing discontinuation logic...")
print("-" * 60)

for i in range(n_patients):
    patient_id = f"patient_{i}"
    first_visit = datetime(2020, 1, 1)
    is_discontinued = False
    
    # Check at monthly intervals throughout the year
    for month in range(1, 13):
        current_date = first_visit + timedelta(days=month * 30)
        
        should_disc, reason = manager.should_discontinue(
            patient_id,
            current_date,
            first_visit,
            is_discontinued
        )
        
        if should_disc:
            is_discontinued = True
            discontinued_patients.append(patient_id)
            discontinuation_dates.append(current_date)
            
            # Debug first few discontinuations
            if len(discontinued_patients) <= 5:
                days_elapsed = (current_date - first_visit).days
                print(f"Patient {i}: Discontinued on day {days_elapsed} ({current_date.strftime('%Y-%m-%d')})")
                print(f"  Reason: {reason}")
            break

print("-" * 60)
print(f"\nTotal discontinued in Year 1: {len(discontinued_patients)} / {n_patients}")
print(f"Rate: {len(discontinued_patients)/n_patients:.1%} (target: 12.5%)")

# Check distribution of discontinuation dates
if discontinuation_dates:
    days_to_disc = [(d - datetime(2020, 1, 1)).days for d in discontinuation_dates]
    print(f"\nDiscontinuation timing:")
    print(f"  Earliest: Day {min(days_to_disc)}")
    print(f"  Latest: Day {max(days_to_disc)}")
    print(f"  Average: Day {sum(days_to_disc)/len(days_to_disc):.0f}")

# Test what happens with the wrapper's check logic
print("\n" + "="*60)
print("Testing wrapper discontinuation check behavior")
print("="*60)

from simulation_v2.clinical_improvements import ImprovedPatientWrapper
from simulation_v2.core.patient import Patient

# Create test patient
config = ClinicalImprovements()
config.use_time_based_discontinuation = True
patient = Patient("test_patient", baseline_vision=55)
wrapped = ImprovedPatientWrapper(patient, config)

first_visit = datetime(2020, 1, 1)
wrapped.patient.first_visit_date = first_visit

# Check discontinuation at different points in year 1
check_dates = [
    first_visit + timedelta(days=30),   # Month 1
    first_visit + timedelta(days=90),   # Month 3
    first_visit + timedelta(days=180),  # Month 6
    first_visit + timedelta(days=270),  # Month 9
    first_visit + timedelta(days=365),  # Year boundary
    first_visit + timedelta(days=395),  # Into year 2
]

print("\nChecking discontinuation at various dates:")
for date in check_dates:
    if not wrapped.patient.is_discontinued:
        result = wrapped.check_time_based_discontinuation(date)
        days = (date - first_visit).days
        year = int(days / 365.25) + 1
        print(f"  Day {days:3} (Year {year}): {'DISCONTINUED' if result else 'Continue'}")
        if result:
            print(f"    Reason: {wrapped.patient.discontinuation_reason}")
            break