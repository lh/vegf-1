"""
Test the new streamgraph visualization and save it.
"""

import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
from streamlit_app.streamgraph_patient_states import create_streamgraph
from datetime import datetime, timedelta
import numpy as np

# Create realistic patient histories
def create_test_data():
    np.random.seed(42)
    patient_histories = {}
    
    # Create 100 patients
    for i in range(100):
        patient_id = f"P{i:03d}"
        visits = []
        
        # Initial visit
        current_time = 0
        visits.append({
            "time": current_time,
            "is_discontinuation_visit": False,
            "vision": 60 + np.random.normal(0, 5)
        })
        
        # Simulate visits over 5 years
        while current_time < 1800:  # 5 years in days
            # Next visit interval
            interval = np.random.choice([30, 60, 90, 120], p=[0.3, 0.4, 0.2, 0.1])
            current_time += interval
            
            if current_time >= 1800:
                break
            
            # Decide if patient discontinues
            disc_chance = np.random.random()
            
            if disc_chance < 0.02:  # 2% chance per visit
                # Discontinue
                disc_type = np.random.choice(
                    ["stable_max_interval", "random_administrative", 
                     "course_complete_but_not_renewed", "premature"],
                    p=[0.3, 0.2, 0.2, 0.3]
                )
                
                visits.append({
                    "time": current_time,
                    "is_discontinuation_visit": True,
                    "discontinuation_reason": disc_type,
                    "vision": visits[-1]["vision"] + np.random.normal(0, 2)
                })
                
                # Chance of retreatment
                if np.random.random() < 0.4:  # 40% chance of retreatment
                    # Wait some time before retreatment
                    retreat_time = current_time + np.random.randint(90, 365)
                    if retreat_time < 1800:
                        visits.append({
                            "time": retreat_time,
                            "is_retreatment_visit": True,
                            "vision": visits[-1]["vision"] - 5
                        })
                        current_time = retreat_time
                else:
                    break  # Patient stays discontinued
            else:
                # Regular visit
                visits.append({
                    "time": current_time,
                    "is_discontinuation_visit": False,
                    "vision": visits[-1]["vision"] + np.random.normal(0.5, 2)
                })
        
        patient_histories[patient_id] = visits
    
    return {
        "patient_histories": patient_histories,
        "duration_years": 5
    }

# Create and save the streamgraph
if __name__ == "__main__":
    print("Creating test data...")
    results = create_test_data()
    
    # Print some stats about the data
    total_patients = len(results["patient_histories"])
    disc_counts = {"stable_max_interval": 0, "random_administrative": 0, 
                   "course_complete_but_not_renewed": 0, "premature": 0}
    retreatment_count = 0
    
    for patient_id, visits in results["patient_histories"].items():
        for visit in visits:
            if visit.get("is_discontinuation_visit"):
                reason = visit.get("discontinuation_reason")
                if reason in disc_counts:
                    disc_counts[reason] += 1
            if visit.get("is_retreatment_visit"):
                retreatment_count += 1
    
    print(f"\nData summary:")
    print(f"Total patients: {total_patients}")
    print(f"Discontinuations by type:")
    for disc_type, count in disc_counts.items():
        print(f"  {disc_type}: {count}")
    print(f"Retreatments: {retreatment_count}")
    
    print("\nGenerating streamgraph...")
    fig = create_streamgraph(results)
    
    # Save the figure
    fig.savefig("test_streamgraph.png", dpi=300, bbox_inches='tight')
    print("Saved to test_streamgraph.png")
    
    # Also save state counts at specific time points for debugging
    from streamlit_app.streamgraph_patient_states import extract_patient_states, aggregate_states_by_month
    
    patient_states_df = extract_patient_states(results["patient_histories"])
    monthly_counts = aggregate_states_by_month(patient_states_df, 60)  # 5 years
    
    # Print state counts at key time points
    for month in [0, 12, 24, 36, 48, 60]:
        month_data = monthly_counts[monthly_counts['time_months'] == month]
        print(f"\nMonth {month} state counts:")
        for _, row in month_data.iterrows():
            if row['count'] > 0:
                print(f"  {row['state']}: {row['count']}")