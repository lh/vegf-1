"""
Debug wrapper to see exactly what data is passed to streamgraph in Streamlit.
"""

import json
import matplotlib.pyplot as plt
from streamgraph_traffic_light import generate_traffic_light_streamgraph

def debug_streamgraph_data(results):
    """Debug wrapper that logs and visualizes the exact data structure."""
    
    print("\n=== STREAMGRAPH DATA DEBUG ===")
    print(f"Results type: {type(results)}")
    print(f"Results keys: {list(results.keys())[:20]}...")  # Show first 20 keys
    
    # Check for expected data fields
    print("\nChecking for expected fields:")
    print(f"  discontinuation_counts: {'discontinuation_counts' in results}")
    print(f"  recurrences: {'recurrences' in results}")
    print(f"  population_size: {'population_size' in results}")
    print(f"  duration_years: {'duration_years' in results}")
    
    # Log discontinuation data
    disc_counts = results.get("discontinuation_counts", {})
    print(f"\nDiscontinuation counts:")
    for k, v in disc_counts.items():
        print(f"  {k}: {v}")
    print(f"Total discontinuations: {sum(disc_counts.values())}")
    
    # Log recurrence data
    recurrences = results.get("recurrences", {})
    print(f"\nRecurrences:")
    print(f"  Total: {recurrences.get('total', 'MISSING')}")
    print(f"  Structure: {list(recurrences.keys())}")
    
    if "by_type" in recurrences:
        print(f"\nRecurrences by_type:")
        for k, v in recurrences["by_type"].items():
            print(f"  {k}: {v}")
    
    # Save data for inspection
    debug_data = {
        "discontinuation_counts": disc_counts,
        "recurrences": recurrences,
        "population_size": results.get("population_size", "MISSING"),
        "duration_years": results.get("duration_years", "MISSING"),
        "has_patient_histories": "patient_histories" in results,
        "has_patients": "patients" in results,
        "result_keys": list(results.keys())[:50]  # First 50 keys
    }
    
    with open("streamlit_debug_data.json", "w") as f:
        json.dump(debug_data, f, indent=2, default=str)
    
    print("\nSaved debug data to streamlit_debug_data.json")
    print("=== END DEBUG ===\n")
    
    # Try to generate the streamgraph
    try:
        return generate_traffic_light_streamgraph(results)
    except Exception as e:
        print(f"ERROR in streamgraph: {e}")
        import traceback
        traceback.print_exc()
        
        # Create error plot
        fig, ax = plt.subplots(figsize=(10, 6))
        error_text = f"Error: {str(e)}\n\n"
        error_text += f"Discontinuation counts: {disc_counts}\n"
        error_text += f"Recurrences total: {recurrences.get('total', 'MISSING')}\n"
        error_text += f"Recurrences by_type: {recurrences.get('by_type', 'MISSING')}"
        
        ax.text(0.5, 0.5, error_text, ha='center', va='center', 
                fontsize=10, wrap=True, horizontalalignment='center')
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        return fig