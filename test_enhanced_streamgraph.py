"""
Test the enhanced streamgraph with real-looking simulation data.
"""

import matplotlib.pyplot as plt
from streamlit_app.enhanced_streamgraph import generate_cohort_flow_streamgraph

# Create test data with more balanced proportions to see all colors
test_results = {
    "simulation_type": "ABS",
    "population_size": 1000,
    "duration_years": 5,
    "discontinuation_counts": {
        "Planned": 200,      # Amber - stable disease discontinuations
        "Administrative": 50,  # Red - administrative errors
        "Not Renewed": 50,     # Dark red - renewal errors  
        "Premature": 100      # Darker red - premature discontinuations
    },
    "recurrences": {
        "total": 180,
        "unique_count": 150,
        "by_type": {
            "stable_max_interval": 120,   # Planned retreatments (pale green)
            "random_administrative": 20,  # Administrative retreatments (light pink)
            "treatment_duration": 20,     # Not Renewed retreatments (medium pink)
            "premature": 20              # Premature retreatments (stronger pink)
        }
    }
}

# Generate the streamgraph
try:
    fig = generate_cohort_flow_streamgraph(test_results)
    plt.savefig('test_enhanced_streamgraph.png', dpi=150, bbox_inches='tight')
    print("Enhanced streamgraph saved to test_enhanced_streamgraph.png")
    
    # Print what the streamgraph shows
    print("\nStreamgraph should show:")
    print(f"- Total patients: {test_results['population_size']}")
    print(f"- Total discontinuations: {sum(test_results['discontinuation_counts'].values())}")
    print(f"- Total retreatments: {test_results['recurrences']['total']}")
    
    # Close the figure to free memory
    plt.close(fig)
except Exception as e:
    print(f"Error generating streamgraph: {e}")
    import traceback
    traceback.print_exc()