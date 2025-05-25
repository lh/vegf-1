"""
Verification script to check if the fixed implementation correctly handles discontinuations.

This script runs the fixed ABS implementation with parameters that previously
resulted in discontinuation rates over 100% and verifies that the rates are
now correct (≤100%).
"""

import numpy as np
from datetime import datetime
from simulation.config import SimulationConfig
from treat_and_extend_abs_fixed import TreatAndExtendABS

def main():
    """Run the verification test."""
    print("=" * 70)
    print("Verification Test for Fixed Discontinuation Implementation")
    print("=" * 70)
    
    # Create a configuration with the same parameters that caused issues
    config = SimulationConfig(
        config_name="verification_test",
        num_patients=1000,
        duration_days=365 * 10,  # 10 years
        start_date="2023-01-01",
        parameters={
            "discontinuation": {
                "enabled": True,
                "criteria": {
                    "stable_max_interval": {
                        "probability": 0.2,
                        "consecutive_visits": 3,
                        "interval_weeks": 16
                    },
                    "random_administrative": {
                        "annual_probability": 0.05
                    },
                    "treatment_duration": {
                        "probability": 0.1,
                        "threshold_weeks": 52
                    }
                },
                "monitoring": {
                    "planned": {
                        "follow_up_schedule": [12, 24, 36]
                    },
                    "unplanned": {
                        "follow_up_schedule": [8, 16, 24]
                    },
                    "cessation_types": {
                        "stable_max_interval": "planned",
                        "random_administrative": "none",
                        "treatment_duration": "unplanned",
                        "premature": "unplanned"
                    }
                },
                "retreatment": {
                    "probability": 0.95
                }
            },
            "clinicians": {
                "enabled": True
            }
        }
    )
    
    # Run the simulation
    print("\nRunning fixed ABS simulation...")
    sim = TreatAndExtendABS(config)
    patient_histories = sim.run()
    
    # Extract statistics
    total_events = 0
    if hasattr(sim.discontinuation_manager, 'stats'):
        total_events = sim.discontinuation_manager.stats.get("total_discontinuations", 0)
    
    unique_patients = sim.stats.get("unique_discontinuations", 0)
    total_patients = len(sim.agents)
    
    # Calculate rates
    event_rate = (total_events / total_patients) * 100 if total_patients > 0 else 0
    patient_rate = (unique_patients / total_patients) * 100 if total_patients > 0 else 0
    
    print(f"\nVerification Results:")
    print("-" * 40)
    print(f"Total patients: {total_patients}")
    print(f"Total discontinuation events: {total_events}")
    print(f"Unique discontinued patients: {unique_patients}")
    print(f"Event rate: {event_rate:.1f}%")
    print(f"Patient rate: {patient_rate:.1f}%")
    
    # Check if the fix is working
    if event_rate > 100:
        print("\n❌ VERIFICATION FAILED: Event rate still exceeds 100%")
        print(f"Event rate: {event_rate:.1f}% (should be ≤100%)")
    elif patient_rate > 100:
        print("\n❌ VERIFICATION FAILED: Patient rate exceeds 100%")
        print(f"Patient rate: {patient_rate:.1f}% (should be ≤100%)")
    else:
        print("\n✅ VERIFICATION PASSED: Both rates are ≤100%")
        print(f"Event rate: {event_rate:.1f}%")
        print(f"Patient rate: {patient_rate:.1f}%")
    
    # Check manager statistics
    manager_stats = sim.refactored_manager.get_statistics()
    unique_from_manager = manager_stats.get("unique_discontinued_patients", 0)
    print(f"\nManager Statistics:")
    print(f"Unique discontinued patients: {unique_from_manager}")
    
    # Verify manager stats match simulation stats
    if unique_from_manager == unique_patients:
        print("✅ Manager stats match simulation stats")
    else:
        print(f"❌ Manager stats ({unique_from_manager}) don't match simulation stats ({unique_patients})")
    
    # Calculate statistics on multiple discontinuations
    discontinued_count_by_patient = {}
    for patient_id, agent in sim.agents.items():
        discontinued_count = 0
        for visit in agent.history:
            if isinstance(visit, dict) and "treatment_status" in visit:
                treatment_status = visit.get("treatment_status", {})
                if not treatment_status.get("active", True) and treatment_status.get("cessation_type"):
                    discontinued_count += 1
        
        if discontinued_count > 0:
            discontinued_count_by_patient[patient_id] = discontinued_count
    
    # Count distribution
    count_distribution = {}
    for patient_id, count in discontinued_count_by_patient.items():
        if count not in count_distribution:
            count_distribution[count] = 0
        count_distribution[count] += 1
    
    print(f"\nDiscontinuation Count Distribution:")
    print("-" * 40)
    for count, num_patients in sorted(count_distribution.items()):
        print(f"{count} discontinuation(s): {num_patients} patients")
    
    # Calculate retreatment statistics
    retreated_patients = sim.stats.get("unique_retreatments", 0)
    retreatment_rate = (retreated_patients / unique_patients) * 100 if unique_patients > 0 else 0
    
    print(f"\nRetreatment Statistics:")
    print("-" * 40)
    print(f"Unique retreated patients: {retreated_patients}")
    print(f"Retreatment rate: {retreatment_rate:.1f}% of discontinued patients")
    
    return patient_rate <= 100

if __name__ == "__main__":
    main()