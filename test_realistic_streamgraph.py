"""
Test the realistic streamgraph implementation.
"""

import matplotlib.pyplot as plt
from streamlit_app.realistic_streamgraph import generate_realistic_streamgraph

# Test with interpolated data (no patient histories)
test_results = {
    "simulation_type": "ABS",
    "population_size": 1000,
    "duration_years": 5,
    "discontinuation_counts": {
        "Planned": 200,      # These happen later
        "Administrative": 50,  # Random timing
        "Not Renewed": 50,     # Clustered timing  
        "Premature": 100      # Early timing
    },
    "recurrences": {
        "total": 180,
        "unique_count": 150,
        "by_type": {
            "stable_max_interval": 120,
            "random_administrative": 20,
            "treatment_duration": 20,
            "premature": 20
        }
    }
}

# Generate the streamgraph
try:
    fig = generate_realistic_streamgraph(test_results)
    plt.savefig('test_realistic_streamgraph.png', dpi=150, bbox_inches='tight')
    print("Realistic streamgraph saved to test_realistic_streamgraph.png")
    
    # Close the figure
    plt.close(fig)
except Exception as e:
    print(f"Error generating streamgraph: {e}")
    import traceback
    traceback.print_exc()

# Now test with mock patient histories for more realistic data
import numpy as np
from datetime import datetime, timedelta

# Create mock patient histories
patient_histories = {}
start_date = datetime(2020, 1, 1)

for patient_id in range(100):  # Smaller sample for testing
    history = []
    current_time = start_date
    discontinued = False
    retreated = False
    disc_reason = None
    
    # Generate visits over 5 years
    for week in range(0, 260, 4):  # Monthly visits
        visit = {
            'time_weeks': week,
            'time': current_time,
            'treatment_status': {'active': True}
        }
        
        # Simulate discontinuation probability
        if not discontinued and week > 12:
            # Different discontinuation patterns
            if patient_id < 20 and week > 156:  # 20% planned after 3 years
                if np.random.random() < 0.05:  # 5% chance per visit
                    discontinued = True
                    disc_reason = 'stable_max_interval'
            elif patient_id < 30 and week < 52:  # 10% premature in first year
                if np.random.random() < 0.02:
                    discontinued = True
                    disc_reason = 'premature'
            elif patient_id < 35:  # 5% administrative (random timing)
                if np.random.random() < 0.001:
                    discontinued = True
                    disc_reason = 'administrative'
            elif patient_id < 40 and week % 52 == 0:  # 5% not renewed (yearly)
                if np.random.random() < 0.05:
                    discontinued = True
                    disc_reason = 'not_renewed'
        
        # Update visit status
        if discontinued:
            visit['treatment_status'] = {
                'active': False,
                'discontinuation_reason': disc_reason,
                'retreated': retreated
            }
            
            # Simulate retreatment
            if not retreated and week > 26:  # After 6 months
                retreat_prob = 0.6 if disc_reason == 'stable_max_interval' else 0.2
                if np.random.random() < retreat_prob / 10:  # Small chance per visit
                    retreated = True
                    visit['treatment_status']['retreated'] = True
        
        history.append(visit)
        current_time += timedelta(weeks=4)
    
    patient_histories[f'patient_{patient_id}'] = history

# Test with patient histories
test_results_with_histories = test_results.copy()
test_results_with_histories['patient_histories'] = patient_histories

try:
    fig = generate_realistic_streamgraph(test_results_with_histories)
    plt.savefig('test_realistic_streamgraph_with_histories.png', dpi=150, bbox_inches='tight')
    print("Realistic streamgraph with histories saved to test_realistic_streamgraph_with_histories.png")
    
    # Close the figure
    plt.close(fig)
except Exception as e:
    print(f"Error generating streamgraph with histories: {e}")
    import traceback
    traceback.print_exc()