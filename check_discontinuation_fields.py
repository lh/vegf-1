#!/usr/bin/env python3
"""
Check discontinuation fields in the simulation results.
"""

import json
import sys

def main():
    """Examine discontinuation fields in patient records."""
    try:
        with open('enhanced_streamgraph_test_data.json', 'r') as f:
            data = json.load(f)
        
        # Look at patient histories
        patient_histories = data.get("patient_histories", {})
        if not patient_histories:
            print("No patient histories found!")
            return
        
        # Keep track of discontinuation types
        discontinuation_types = set()
        cessation_types = set()
        
        # Check for patients with discontinuation visits
        disc_patient_count = 0
        
        # Examine a subset of patients (up to 5)
        sample_patients = list(patient_histories.items())[:10]
        
        for pid, visits in sample_patients:
            # Find discontinuation visits
            disc_visits = [v for v in visits if v.get('is_discontinuation_visit')]
            
            if disc_visits:
                disc_patient_count += 1
                print(f"\nPatient {pid} has {len(disc_visits)} discontinuation visits:")
                
                for i, visit in enumerate(disc_visits):
                    print(f"  Visit {i+1}:")
                    
                    # Check for discontinuation fields
                    for field in ['discontinuation_reason', 'discontinuation_type', 'cessation_type']:
                        value = visit.get(field)
                        print(f"    {field}: {value}")
                        
                        # Track types for overall stats
                        if field == 'discontinuation_type' and value:
                            discontinuation_types.add(value)
                        elif field == 'cessation_type' and value:
                            cessation_types.add(value)
        
        print("\nOverall Discontinuation Statistics:")
        print(f"Examined {len(sample_patients)} patients, {disc_patient_count} with discontinuations")
        print(f"Discontinuation types found: {discontinuation_types}")
        print(f"Cessation types found: {cessation_types}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()