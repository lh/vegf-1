"""
Debug script to check what data is passed to streamgraph in Streamlit.
"""

import json
import matplotlib.pyplot as plt

# Create a debug wrapper for the streamgraph function
def debug_streamgraph_wrapper(results):
    """Wrapper to debug what data is passed to streamgraph."""
    
    # Save the results to a file for inspection
    with open('debug_streamlit_results.json', 'w') as f:
        # Convert complex types to strings for JSON serialization
        debug_results = {}
        for key, value in results.items():
            if isinstance(value, (dict, list, str, int, float, bool, type(None))):
                debug_results[key] = value
            else:
                debug_results[key] = str(type(value))
        
        json.dump(debug_results, f, indent=2)
    
    # Check the structure
    print("DEBUG: Streamgraph called with results keys:", list(results.keys()))
    print("DEBUG: Population size:", results.get("population_size", "MISSING"))
    print("DEBUG: Duration years:", results.get("duration_years", "MISSING"))
    print("DEBUG: Discontinuation counts:", results.get("discontinuation_counts", "MISSING"))
    print("DEBUG: Recurrences:", results.get("recurrences", "MISSING"))
    
    # Check if we have the required fields
    has_required = all([
        "population_size" in results,
        "duration_years" in results,
        "discontinuation_counts" in results
    ])
    
    if not has_required:
        print("ERROR: Missing required fields for streamgraph!")
        # Create a simple error plot
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.text(0.5, 0.5, "Missing data for streamgraph", 
                ha='center', va='center', fontsize=16)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        return fig
    
    # Import and call the real function
    try:
        from streamlit_app.realistic_streamgraph import generate_realistic_streamgraph
        return generate_realistic_streamgraph(results)
    except Exception as e:
        print(f"ERROR in streamgraph generation: {e}")
        import traceback
        traceback.print_exc()
        
        # Create error plot
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.text(0.5, 0.5, f"Error: {str(e)}", 
                ha='center', va='center', fontsize=12)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        return fig