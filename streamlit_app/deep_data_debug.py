"""
Deep debug to find retreatment data in the results.
"""

import json
import matplotlib.pyplot as plt
from streamgraph_traffic_light import generate_traffic_light_streamgraph

def deep_debug_streamgraph(results):
    """Deep dive into the results to find retreatment data."""
    
    print("\n=== DEEP DATA DEBUG ===")
    
    # Search for retreatment data in different locations
    retreatment_data = {}
    
    # 1. Check recurrences field
    recurrences = results.get("recurrences", {})
    print(f"\nRecurrences field:")
    print(f"  Total: {recurrences.get('total', 0)}")
    print(f"  by_type: {recurrences.get('by_type', {})}")
    
    # 2. Check raw_discontinuation_stats
    raw_stats = results.get("raw_discontinuation_stats", {})
    print(f"\nRaw discontinuation stats keys: {list(raw_stats.keys())[:10]}...")
    
    # Look for retreatment-related fields
    for key in raw_stats:
        if 'retreat' in key.lower() or 'recur' in key.lower():
            print(f"  Found: {key} = {raw_stats[key]}")
            retreatment_data[key] = raw_stats[key]
    
    # 3. Check patient_histories to count retreatments manually
    if "patient_histories" in results:
        histories = results["patient_histories"]
        
        # Initialize counters
        retreatment_by_disc_type = {
            "Planned": 0,
            "Administrative": 0,
            "Not Renewed": 0,
            "Premature": 0
        }
        
        # Count retreatments from patient data
        print(f"\nScanning {len(histories)} patient histories...")
        
        for patient_id, patient in histories.items():
            if 'retreatment_count' in patient:
                retreat_count = patient['retreatment_count']
                disc_reasons = patient.get('discontinuation_reasons', [])
                
                # Map discontinuation reasons to retreatments
                if retreat_count > 0 and disc_reasons:
                    # Use the first discontinuation reason for categorization
                    first_disc = disc_reasons[0] if disc_reasons else None
                    
                    if first_disc == 'stable_max_interval':
                        retreatment_by_disc_type["Planned"] += retreat_count
                    elif first_disc == 'random_administrative':
                        retreatment_by_disc_type["Administrative"] += retreat_count
                    elif first_disc == 'treatment_duration':
                        retreatment_by_disc_type["Not Renewed"] += retreat_count
                    elif first_disc == 'premature':
                        retreatment_by_disc_type["Premature"] += retreat_count
        
        print(f"\nManually counted retreatments by type:")
        for disc_type, count in retreatment_by_disc_type.items():
            print(f"  {disc_type}: {count}")
        
        # Update the results with the manual counts
        if recurrences.get("by_type", {}) == {}:
            print("\nUpdating empty by_type with manual counts...")
            recurrences["by_type"] = {
                "stable_max_interval": retreatment_by_disc_type["Planned"],
                "random_administrative": retreatment_by_disc_type["Administrative"],
                "treatment_duration": retreatment_by_disc_type["Not Renewed"],
                "premature": retreatment_by_disc_type["Premature"]
            }
            results["recurrences"] = recurrences
    
    # Save debug info
    debug_output = {
        "original_recurrences": results.get("recurrences", {}),
        "retreatment_data_found": retreatment_data,
        "manual_counts": retreatment_by_disc_type if 'retreatment_by_disc_type' in locals() else {}
    }
    
    with open("deep_debug_output.json", "w") as f:
        json.dump(debug_output, f, indent=2)
    
    print("\nSaved deep debug output to deep_debug_output.json")
    print("=== END DEEP DEBUG ===\n")
    
    # Generate the streamgraph with potentially updated data
    try:
        return generate_traffic_light_streamgraph(results)
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        
        # Error plot
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.text(0.5, 0.5, f"Error: {str(e)}", ha='center', va='center')
        ax.axis('off')
        return fig