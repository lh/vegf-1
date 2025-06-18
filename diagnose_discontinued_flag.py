#!/usr/bin/env python3
"""
Examine how the discontinued flag is set in patient data.
"""

from pathlib import Path
from ape.core.results.factory import ResultsFactory

def examine_discontinued_patients(sim_path):
    """Examine a few discontinued patients to understand the data structure."""
    print(f"\nExamining discontinued patients in: {sim_path.name}")
    print("=" * 80)
    
    results = ResultsFactory.load_results(sim_path)
    
    # Find some discontinued patients
    discontinued_examples = []
    active_examples = []
    
    count = 0
    for batch in results.iterate_patients(batch_size=100):
        for patient in batch:
            if patient.get('discontinued', False) and len(discontinued_examples) < 3:
                discontinued_examples.append(patient)
            elif not patient.get('discontinued', False) and len(active_examples) < 3:
                active_examples.append(patient)
            
            count += 1
            if len(discontinued_examples) >= 3 and len(active_examples) >= 3:
                break
        if len(discontinued_examples) >= 3 and len(active_examples) >= 3:
            break
    
    print(f"\nTotal patients examined: {count}")
    
    # Show discontinued patient examples
    print("\nDISCONTINUED PATIENT EXAMPLES:")
    print("-" * 40)
    for i, patient in enumerate(discontinued_examples):
        print(f"\nPatient {i+1} (ID: {patient['patient_id']})")
        print(f"  Discontinued: {patient.get('discontinued', 'N/A')}")
        print(f"  Discontinuation time: {patient.get('discontinuation_time', 'N/A')}")
        print(f"  Total visits: {len(patient.get('visits', []))}")
        
        visits = patient.get('visits', [])
        if visits:
            last_visit = visits[-1]
            print(f"  Last visit:")
            print(f"    - Visit keys: {list(last_visit.keys())}")
            print(f"    - Time: {last_visit.get('time', 'N/A')}")
            print(f"    - Treatment state: {last_visit.get('treatment_state', 'N/A')}")
            print(f"    - Is discontinuation: {last_visit.get('is_discontinuation_visit', 'N/A')}")
            
            # Check different possible time fields
            for key in ['time', 'month', 'time_days', 'visit_time']:
                if key in last_visit:
                    print(f"    - {key}: {last_visit[key]}")
    
    # Show active patient examples  
    print("\n\nACTIVE PATIENT EXAMPLES:")
    print("-" * 40)
    for i, patient in enumerate(active_examples):
        print(f"\nPatient {i+1} (ID: {patient['patient_id']})")
        print(f"  Discontinued: {patient.get('discontinued', 'N/A')}")
        print(f"  Total visits: {len(patient.get('visits', []))}")
        
        visits = patient.get('visits', [])
        if visits:
            last_visit = visits[-1]
            print(f"  Last visit:")
            print(f"    - Visit keys: {list(last_visit.keys())}")
            
            # Check different possible time fields
            for key in ['time', 'month', 'time_days', 'visit_time']:
                if key in last_visit:
                    print(f"    - {key}: {last_visit[key]}")

if __name__ == "__main__":
    results_dir = Path("simulation_results")
    
    # Find super-pine
    for sim_dir in results_dir.iterdir():
        if sim_dir.is_dir() and 'super-pine' in sim_dir.name:
            examine_discontinued_patients(sim_dir)
            break