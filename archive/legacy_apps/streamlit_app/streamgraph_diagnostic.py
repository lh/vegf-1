"""
Diagnostic wrapper for streamgraph to log what data it receives.
"""

import json
import pandas as pd
import matplotlib.pyplot as plt
from streamgraph_fix import generate_fixed_streamgraph

def diagnostic_streamgraph(results):
    """Debug wrapper that logs data before generating streamgraph."""
    
    # Log the data structure
    print("\n=== STREAMGRAPH DIAGNOSTIC ===")
    print(f"Results keys: {list(results.keys())}")
    
    # Check discontinuation counts
    disc_counts = results.get("discontinuation_counts", {})
    print(f"\nDiscontinuation counts: {disc_counts}")
    print(f"Total discontinuations: {sum(disc_counts.values())}")
    
    # Check recurrence data  
    recurrences = results.get("recurrences", {})
    print(f"\nRecurrences structure: {list(recurrences.keys())}")
    print(f"Total recurrences: {recurrences.get('total', 0)}")
    if "by_type" in recurrences:
        print(f"Recurrences by type: {recurrences['by_type']}")
    
    # Save full data to file
    debug_data = {
        "discontinuation_counts": disc_counts,
        "recurrences": recurrences,
        "population_size": results.get("population_size", 0),
        "duration_years": results.get("duration_years", 0)
    }
    
    with open("streamgraph_debug_data.json", "w") as f:
        json.dump(debug_data, f, indent=2)
    
    print("\nSaved debug data to streamgraph_debug_data.json")
    print("=== END DIAGNOSTIC ===\n")
    
    # Generate the actual streamgraph
    try:
        return generate_fixed_streamgraph(results)
    except Exception as e:
        print(f"ERROR in streamgraph generation: {e}")
        # Create error plot showing what data we have
        fig, ax = plt.subplots(figsize=(10, 6))
        error_msg = f"Error: {str(e)}\n\nData received:\n"
        error_msg += f"Discontinuations: {disc_counts}\n"
        error_msg += f"Recurrences: {recurrences.get('total', 0)}"
        ax.text(0.5, 0.5, error_msg, ha='center', va='center', 
                fontsize=10, wrap=True)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        return fig