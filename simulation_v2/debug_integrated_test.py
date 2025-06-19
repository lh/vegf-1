"""
Debug script to understand integration test issues
"""

import sys
import random
from datetime import datetime, timedelta
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from simulation_v2.clinical_improvements import ClinicalImprovements, ImprovedPatientWrapper
from simulation_v2.core.patient import Patient

# Set seed for reproducibility
random.seed(42)

# Create configuration
config = ClinicalImprovements()
config.enable_all()

# Create one patient and trace through the simulation
patient = Patient("debug_patient", baseline_vision=55)
patient.current_interval_days = 56  # 8-week protocol interval
wrapped = ImprovedPatientWrapper(patient, config)

start_date = datetime(2020, 1, 1)
current_date = start_date
wrapped.patient.first_visit_date = start_date

print(f"Starting simulation for patient: {wrapped.patient.id}")
print(f"Response type: {wrapped.response_type} (multiplier: {wrapped.response_multiplier})")
print(f"Baseline vision: {wrapped.patient.current_vision}")
print("\nVisit log:")
print("-" * 80)
print(f"{'Visit':>5} {'Date':>12} {'Days':>6} {'Interval':>8} {'Vision':>7} {'Change':>7} {'Loading':>8} {'Status':>15}")
print("-" * 80)

visit_num = 0
injections = 0
start_vision = wrapped.patient.current_vision

while (current_date - start_date).days < 365 and not wrapped.patient.is_discontinued:
    visit_num += 1
    days_elapsed = (current_date - start_date).days
    
    # Get injection interval
    interval = wrapped.get_next_injection_interval(current_date)
    
    # Apply vision change
    vision_change = wrapped.calculate_vision_change(current_date)
    old_vision = wrapped.patient.current_vision
    wrapped.update_vision(vision_change)
    
    # Record injection
    wrapped.record_injection(current_date)
    injections += 1
    
    # Check if in loading phase
    in_loading = injections <= config.loading_phase_injections
    
    print(f"{visit_num:>5} {current_date.strftime('%Y-%m-%d'):>12} {days_elapsed:>6} {interval:>8} "
          f"{wrapped.patient.current_vision:>7} {vision_change:>+7.1f} {'Yes' if in_loading else 'No':>8} "
          f"{'Active':>15}")
    
    # Next visit
    current_date += timedelta(days=interval)
    
    # Check discontinuation at visit
    if wrapped.check_time_based_discontinuation(current_date):
        print(f"{'':>5} {current_date.strftime('%Y-%m-%d'):>12} {(current_date - start_date).days:>6} "
              f"{'':>8} {'':>7} {'':>7} {'':>8} {'DISCONTINUED':>15}")
        break

print("-" * 80)
print(f"\nSummary:")
print(f"Total injections: {injections}")
print(f"Vision change: {wrapped.patient.current_vision - start_vision:+.0f} letters")
print(f"Discontinued: {'Yes' if wrapped.patient.is_discontinued else 'No'}")
if wrapped.patient.is_discontinued:
    print(f"Discontinuation reason: {wrapped.patient.discontinuation_reason}")

# Check why injections are so high
print(f"\nLoading phase injections: {wrapped.loading_phase_injection_count}")
print(f"Protocol interval: {wrapped.patient.current_interval_days} days")