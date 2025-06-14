"""
Debug script to investigate why streamgraph shows empty in Streamlit.
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from typing import Dict

# Import the realistic streamgraph
from realistic_streamgraph import generate_realistic_streamgraph, extract_realistic_timeline


def debug_empty_streamgraph():
    """Debug why streamgraph appears empty in Streamlit."""
    
    # Create minimal test data with just the required fields
    test_results = {
        "duration_years": 5,
        "population_size": 250,
        "discontinuation_counts": {
            "Planned": 50,
            "Administrative": 30,
            "Not Renewed": 20,
            "Premature": 10
        },
        "recurrences": {
            "total": 40,
            "by_type": {
                "stable_max_interval": 20,
                "random_administrative": 10,
                "treatment_duration": 5,
                "premature": 5
            }
        }
    }
    
    print("Test results structure:")
    for key in test_results:
        print(f"  {key}: {type(test_results[key])}")
    
    # First check if timeline extraction works
    try:
        timeline_data = extract_realistic_timeline(test_results)
        print(f"\nExtracted timeline data shape: {timeline_data.shape}")
        print(f"Timeline columns: {timeline_data.columns.tolist()}")
        print(f"Unique states: {timeline_data['state'].unique()}")
        print(f"Time range: {timeline_data['time_months'].min()} to {timeline_data['time_months'].max()}")
        print(f"Count range: {timeline_data['count'].min()} to {timeline_data['count'].max()}")
        
        # Check if we have empty data
        if timeline_data.empty:
            print("\nERROR: Timeline data is empty!")
        elif timeline_data['count'].sum() == 0:
            print("\nERROR: All counts are zero!")
        else:
            print(f"\nTotal patients across all states/times: {timeline_data['count'].sum()}")
    except Exception as e:
        print(f"\nERROR extracting timeline: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Try to generate the streamgraph
    try:
        fig = generate_realistic_streamgraph(test_results)
        
        # Check if the figure is valid
        if fig is None:
            print("\nERROR: generate_realistic_streamgraph returned None!")
            return
            
        # Get the current axes
        ax = fig.get_axes()[0]
        
        # Check the data in the plot
        print(f"\nPlot information:")
        print(f"  X-axis limits: {ax.get_xlim()}")
        print(f"  Y-axis limits: {ax.get_ylim()}")
        print(f"  Number of artists: {len(ax.artists)}")
        print(f"  Number of lines: {len(ax.lines)}")
        print(f"  Number of patches: {len(ax.patches)}")
        print(f"  Number of collections: {len(ax.collections)}")
        
        # Check if there are any fill areas
        for i, coll in enumerate(ax.collections):
            paths = coll.get_paths()
            print(f"  Collection {i}: {len(paths)} paths")
            if paths:
                print(f"    First path vertices shape: {paths[0].vertices.shape}")
        
        # Save the figure
        fig.savefig('debug_streamgraph.png', dpi=150, bbox_inches='tight')
        print("\nSaved debug plot to debug_streamgraph.png")
        
        # Also create a simple diagnostic plot
        fig_diag, ax_diag = plt.subplots(figsize=(10, 6))
        
        # Plot the timeline data directly
        for state in timeline_data['state'].unique():
            state_data = timeline_data[timeline_data['state'] == state]
            ax_diag.plot(state_data['time_months'], state_data['count'], 
                        label=state, marker='o', markersize=3)
        
        ax_diag.set_xlabel('Time (Months)')
        ax_diag.set_ylabel('Count')
        ax_diag.set_title('Direct Timeline Data Plot')
        ax_diag.legend()
        ax_diag.grid(True, alpha=0.3)
        
        fig_diag.savefig('debug_timeline_direct.png', dpi=150, bbox_inches='tight')
        print("Saved direct timeline plot to debug_timeline_direct.png")
        
    except Exception as e:
        print(f"\nERROR generating streamgraph: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    debug_empty_streamgraph()