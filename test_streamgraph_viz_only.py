#!/usr/bin/env python3
"""
Test the streamgraph visualization with existing data.
This script doesn't run a simulation, it just loads existing data and visualizes it.
"""

import os
import sys
import json
import argparse
import glob
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# Add project root to path
root_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(root_dir)

# Import necessary modules
try:
    from streamgraph_fixed_phase_tracking import generate_phase_tracking_streamgraph
except ImportError as e:
    print(f"Failed to import required modules: {e}")
    sys.exit(1)

def find_most_recent_data_file():
    """Find the most recent streamgraph data file."""
    data_files = glob.glob(os.path.join(root_dir, "streamgraph_phase_data_*.json"))
    
    if not data_files:
        print("No streamgraph data files found.")
        sys.exit(1)
    
    # Sort by modification time, newest first
    data_files.sort(key=os.path.getmtime, reverse=True)
    return data_files[0]

def load_simulation_data(file_path):
    """Load simulation data from a JSON file."""
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading data from {file_path}: {e}")
        sys.exit(1)

def main():
    """Parse command line arguments and visualize data."""
    parser = argparse.ArgumentParser(description='Test streamgraph visualization with existing data')
    parser.add_argument('--input', '-i', type=str, default=None,
                        help='Input JSON file path (default: uses most recent streamgraph_phase_data_*.json)')
    parser.add_argument('--timeout', '-t', type=int, default=20,
                        help='Seconds to display the visualization before closing (default: 20)')
    args = parser.parse_args()
    
    # Find input file
    input_file = args.input
    if not input_file:
        input_file = find_most_recent_data_file()
        print(f"Using most recent data file: {input_file}")
    
    # Load data
    results = load_simulation_data(input_file)
    
    # Print basic stats about the data
    print(f"\nData summary:")
    print(f"Population size: {results.get('population_size', 'unknown')}")
    print(f"Duration years: {results.get('duration_years', 'unknown')}")
    print(f"Patient count: {results.get('patient_count', 'unknown')}")
    
    # Print discontinuation stats if available
    disc_counts = results.get("discontinuation_counts", {})
    if disc_counts:
        print("\nDiscontinuation counts:")
        patient_count = results.get('patient_count', 1)  # Avoid division by zero
        for type_name, count in disc_counts.items():
            percent = (count / patient_count) * 100
            print(f"  {type_name}: {count} ({percent:.1f}%)")
    
    # Generate visualization
    print("\nGenerating streamgraph visualization...")
    fig = generate_phase_tracking_streamgraph(results)
    
    # Save figure
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    plot_path = f"streamgraph_viz_test_{timestamp}.png"
    fig.savefig(plot_path, dpi=300, bbox_inches="tight")
    print(f"Streamgraph saved to {plot_path}")
    
    # Show figure with a better auto-close method
    print(f"Showing figure (will automatically close after {args.timeout} seconds)...")
    
    # Use a more reliable timer for auto-closing
    import matplotlib
    
    # Use this approach only if we're not in a non-interactive backend
    if matplotlib.get_backend() not in ['agg', 'png', 'pdf', 'ps', 'svg']:
        timer = fig.canvas.new_timer(interval=args.timeout * 1000)
        timer.add_callback(plt.close)
        timer.start()
        
    plt.show()

if __name__ == "__main__":
    main()