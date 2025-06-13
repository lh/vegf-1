"""Test script for streamgraph discontinuation visualization."""

import matplotlib.pyplot as plt
from streamlit_app.streamgraph_discontinuation import generate_enhanced_discontinuation_streamgraph

# Sample results data WITHOUT patient histories - should fail fast
sample_results_no_history = {
    "population_size": 100,
    "duration_years": 5,
    "discontinuation_counts": {
        "Planned": 15,
        "Administrative": 8,
        "Not Renewed": 12,
        "Premature": 10
    },
    "recurrences": {
        "total": 20,
        "by_type": {
            "stable_max_interval": 9,
            "random_administrative": 2,
            "treatment_duration": 2,
            "premature": 7
        }
    }
}

print("Testing with missing patient history data (should show error)...")
fig = generate_enhanced_discontinuation_streamgraph(sample_results_no_history)
fig.savefig("test_streamgraph_error.png", dpi=150, bbox_inches='tight')
plt.close()
print("Error figure saved to test_streamgraph_error.png")

# Sample results WITH patient histories - should work
sample_results_with_history = {
    "population_size": 2,
    "duration_years": 1,
    "discontinuation_counts": {
        "Planned": 1
    },
    "patients": [
        {
            "id": "patient_1",
            "visit_history": [
                {
                    "time_weeks": 0,
                    "treatment_status": {"active": True},
                    "disease_state": "ACTIVE"
                },
                {
                    "time_weeks": 12,
                    "treatment_status": {"active": True},
                    "disease_state": "STABLE"
                },
                {
                    "time_weeks": 24,
                    "treatment_status": {
                        "active": False,
                        "discontinuation_reason": "Planned"
                    },
                    "disease_state": "STABLE"
                }
            ]
        },
        {
            "id": "patient_2",
            "visit_history": [
                {
                    "time_weeks": 0,
                    "treatment_status": {"active": True},
                    "disease_state": "ACTIVE"
                },
                {
                    "time_weeks": 12,
                    "treatment_status": {"active": True},
                    "disease_state": "ACTIVE"
                }
            ]
        }
    ]
}

print("\nTesting with patient history data (should work)...")
fig = generate_enhanced_discontinuation_streamgraph(sample_results_with_history)
fig.savefig("test_streamgraph_success.png", dpi=150, bbox_inches='tight')
plt.close()
print("Success figure saved to test_streamgraph_success.png")