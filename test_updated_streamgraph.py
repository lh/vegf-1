#!/usr/bin/env python3
"""
Test the updated streamgraph visualization with our existing simulation data.
This version automatically closes the plot after a timeout to prevent script hanging.
"""

import json
import matplotlib.pyplot as plt
from streamlit_app.streamgraph_patient_states import create_streamgraph
import threading
import time

def close_plot_after_timeout(fig, timeout_seconds=10):
    """Close the plot after a specified timeout."""
    time.sleep(timeout_seconds)
    plt.close(fig)
    print(f"Plot automatically closed after {timeout_seconds} seconds")

def main():
    """Load existing data and create updated streamgraph."""
    try:
        # Load the simulation results
        with open('enhanced_streamgraph_test_data.json', 'r') as f:
            data = json.load(f)
        
        print("Data loaded successfully!")
        
        # Create streamgraph with updated code
        fig = create_streamgraph(data)
        
        # Save the figure
        output_file = "updated_streamgraph_test.png"
        fig.savefig(output_file, dpi=300, bbox_inches="tight")
        print(f"Updated streamgraph saved to {output_file}")
        
        # Start a timer to close the plot after 10 seconds
        timer = threading.Timer(10.0, lambda: plt.close(fig))
        timer.daemon = True  # This ensures the timer thread won't prevent the program from exiting
        timer.start()
        
        print("Displaying plot (will auto-close after 10 seconds)...")
        plt.show(block=False)  # Non-blocking show
        plt.pause(10)  # Pause for 10 seconds
        plt.close(fig)  # Make sure it's closed
    
    except Exception as e:
        import traceback
        print(f"Error: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()