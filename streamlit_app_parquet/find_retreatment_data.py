"""
Script to find where the retreatment data is stored in the results.
"""

import json

def find_retreatment_data(results):
    """Search through results to find retreatment information."""
    
    print("\n=== SEARCHING FOR RETREATMENT DATA ===")
    
    # Check all keys for retreatment-related information
    retreatment_keys = []
    for key in results.keys():
        if 'retreat' in key.lower() or 'recur' in key.lower():
            retreatment_keys.append(key)
            print(f"Found key: {key}")
    
    # Check the retreatments field
    if 'retreatments' in results:
        print(f"\n'retreatments' field: {results['retreatments']}")
    
    # Check the recurrences field
    if 'recurrences' in results:
        recurrences = results['recurrences']
        print(f"\n'recurrences' structure:")
        print(f"  Keys: {list(recurrences.keys())}")
        print(f"  Total: {recurrences.get('total', 'MISSING')}")
        print(f"  by_type: {recurrences.get('by_type', 'MISSING')}")
        print(f"  unique_count: {recurrences.get('unique_count', 'MISSING')}")
    
    # Check raw_discontinuation_stats
    if 'raw_discontinuation_stats' in results:
        raw_stats = results['raw_discontinuation_stats']
        print(f"\n'raw_discontinuation_stats' keys: {list(raw_stats.keys())}")
        
        # Look for retreatment data in raw stats
        for key, value in raw_stats.items():
            if 'retreat' in key.lower() or 'recur' in key.lower():
                print(f"  {key}: {value}")
    
    # Check patient_histories for actual retreatment events
    if 'patient_histories' in results:
        histories = results['patient_histories']
        
        # Count retreatments by looking at patient events
        retreatment_counts = {
            "Planned": 0,
            "Administrative": 0,
            "Not Renewed": 0,
            "Premature": 0
        }
        
        # Sample first few patients to understand structure
        patient_ids = list(histories.keys())[:5]
        print(f"\nSampling patient histories (first 5 patients):")
        
        for pid in patient_ids:
            patient = histories[pid]
            print(f"\nPatient {pid}:")
            print(f"  Keys: {list(patient.keys())}")
            
            if 'retreatment_count' in patient:
                print(f"  Retreatment count: {patient['retreatment_count']}")
            
            if 'retreatment_reasons' in patient:
                print(f"  Retreatment reasons: {patient['retreatment_reasons']}")
            
            if 'discontinuation_reasons' in patient:
                print(f"  Discontinuation reasons: {patient['discontinuation_reasons']}")
            
            # Look for visits with retreatment flags
            if 'visits' in patient:
                retreatment_visits = [v for v in patient['visits'] 
                                    if v.get('is_retreatment', False)]
                if retreatment_visits:
                    print(f"  Found {len(retreatment_visits)} retreatment visits")
    
    return retreatment_keys


# If run directly, load the results and search
if __name__ == "__main__":
    # Try to load from a saved results file
    try:
        with open('streamlit_debug_data.json', 'r') as f:
            debug_data = json.load(f)
            print("Loaded debug data")
            
            # Create a minimal results dict to search
            results = {
                'recurrences': debug_data.get('recurrences', {}),
                'raw_discontinuation_stats': {},
                'patient_histories': {}
            }
            
            find_retreatment_data(results)
    except Exception as e:
        print(f"Could not load debug data: {e}")