#!/usr/bin/env python3
"""
Headless test for the streamgraph visualization - no display, just saves the image.
"""

import json
import matplotlib
# Force matplotlib to not use any Xwindow backend
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from streamlit_app.streamgraph_patient_states import create_streamgraph

def main():
    """Load existing data and create updated streamgraph without displaying it."""
    try:
        # Load the simulation results
        with open('enhanced_streamgraph_test_data.json', 'r') as f:
            data = json.load(f)
        
        print("Data loaded successfully!")
        
        # Create streamgraph with updated code
        print("Creating streamgraph visualization...")
        fig = create_streamgraph(data)
        
        # Save the figure
        output_file = "updated_streamgraph_headless.png"
        fig.savefig(output_file, dpi=300, bbox_inches="tight")
        print(f"Updated streamgraph saved to {output_file}")
        
        # Close the figure
        plt.close(fig)
        print("Success! Visualization complete.")
    
    except Exception as e:
        import traceback
        print(f"Error: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()