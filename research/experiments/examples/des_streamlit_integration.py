"""
Example usage of the DES to Streamlit adapter.

This script demonstrates how to run a DES simulation with the enhanced discontinuation model
and use the adapter to transform the results for the Streamlit dashboard.
"""

import os
import sys
import json
from datetime import datetime
import matplotlib.pyplot as plt

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from simulation.config import SimulationConfig
from treat_and_extend_des import TreatAndExtendDES, run_treat_and_extend_des
from simulation.des_streamlit_adapter import adapt_des_for_streamlit
from streamlit_app.streamgraph_actual_data import generate_actual_data_streamgraph

def main():
    """Run a DES simulation and generate Streamlit visualizations."""
    print("Running DES simulation with enhanced discontinuation model...")
    
    # Configure for a smaller test simulation
    config_name = "eylea_literature_based"
    
    # Run the simulation with Streamlit-compatible output
    results = run_treat_and_extend_des(verbose=False, streamlit_compatible=True)
    
    # Print the keys in the results 
    print("\nSimulation completed. Result keys:")
    print(", ".join(results.keys()))
    
    # Print summary statistics
    print("\nSummary Statistics:")
    print(f"Population Size: {results['population_size']}")
    print(f"Duration (years): {results['duration_years']}")
    
    # Print discontinuation counts
    print("\nDiscontinuation Counts:")
    for reason, count in results["discontinuation_counts"].items():
        print(f"  {reason}: {count}")
    
    # Print recurrence data
    print("\nRecurrence Data:")
    recurrences = results.get("recurrences", {})
    print(f"  Total Recurrences: {recurrences.get('total', 0)}")
    
    # Check that the format is compatible with Streamlit visualization
    print("\nTesting Streamlit visualization compatibility...")
    
    # Generate a streamgraph using the Streamlit visualization code
    try:
        fig = generate_actual_data_streamgraph(results)
        
        # Save the figure to a file
        output_file = "des_streamlit_integration_streamgraph.png"
        fig.savefig(output_file, dpi=150, bbox_inches='tight')
        print(f"Streamgraph successfully created and saved to {output_file}")
        
        # Also save the adapted results for future testing
        output_json = "des_streamlit_integration_results.json"
        
        # Convert datetime objects to strings for JSON serialization
        serializable_results = results.copy()
        
        # Make patient histories serializable
        if "patient_histories" in serializable_results:
            serializable_histories = {}
            for patient_id, visits in serializable_results["patient_histories"].items():
                serializable_visits = []
                for visit in visits:
                    serializable_visit = visit.copy()
                    # Convert datetime objects to ISO format strings
                    if "date" in serializable_visit:
                        if isinstance(serializable_visit["date"], datetime):
                            serializable_visit["date"] = serializable_visit["date"].isoformat()
                    if "time" in serializable_visit:
                        if isinstance(serializable_visit["time"], datetime):
                            serializable_visit["time"] = serializable_visit["time"].isoformat()
                    serializable_visits.append(serializable_visit)
                serializable_histories[patient_id] = serializable_visits
            serializable_results["patient_histories"] = serializable_histories
        
        # Save the serializable results
        with open(output_json, 'w') as f:
            json.dump(serializable_results, f, indent=2, default=str)
        print(f"Adapted results saved to {output_json}")
        
    except Exception as e:
        print(f"Error generating Streamlit visualization: {e}")
        import traceback
        traceback.print_exc()
    
    print("\nDES to Streamlit adapter test complete!")

if __name__ == "__main__":
    main()