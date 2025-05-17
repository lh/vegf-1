"""Create test data that matches the actual Streamlit data structure"""

import json
from datetime import datetime, timedelta
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import os
import sys

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from streamlit_app.simulation_runner import generate_va_over_time_plot

def create_streamlit_compatible_data():
    """Create data that matches the actual Streamlit data structure"""
    
    # Start date
    start_date = datetime(2023, 1, 1)
    
    # Create patient histories - this is what we see in the actual data
    patient_histories = {}
    
    # Create 3000 patients
    for patient_id in range(3000):
        visits = []
        current_date = start_date
        current_month = 0
        
        # Each patient has multiple visits
        # Simulate dropout: patients drop out over time
        max_months = np.random.geometric(0.05)  # Average 20 months
        
        while current_month < max_months and current_month < 110:
            # Create visit data structure matching what we see in the error message
            visit = {
                "date": current_date,  # This is a datetime object
                "vision": 67 - current_month * 0.1 + np.random.normal(0, 8),
                "time": int((current_date - start_date).days),  # Days since start
                "interval": 30 if current_month > 0 else 0
            }
            visits.append(visit)
            
            # Next visit
            interval_days = int(np.random.choice([28, 30, 35, 42, 56, 84]))
            current_date += timedelta(days=interval_days)
            current_month = (current_date - start_date).days / 30.44
        
        if visits:
            patient_histories[patient_id] = visits
    
    # Create mean_va_data that matches the expected structure
    mean_va_data = []
    
    for month in range(0, 110):
        # Count active patients at this time
        active_patients = 0
        va_values = []
        
        for patient_id, visits in patient_histories.items():
            for visit in visits:
                visit_month = (visit["date"] - start_date).days / 30.44
                if abs(visit_month - month) < 0.5:
                    active_patients += 1
                    va_values.append(visit["vision"])
        
        if va_values:
            mean_va = np.mean(va_values)
            std_va = np.std(va_values)
            sample_size = len(va_values)
            
            mean_va_data.append({
                "time": month,
                "visual_acuity": mean_va,
                "sample_size": sample_size,
                "std_error": std_va / np.sqrt(sample_size) if sample_size > 0 else 0
            })
    
    # Create the results structure
    results = {
        "mean_va_data": mean_va_data,
        "patient_histories": patient_histories,  # Using patient_histories, not patient_data
        "simulation_start_date": start_date,
        "failed": False
    }
    
    return results

def test_visualization_fix():
    """Test the visualization with the correct data structure"""
    
    print("Creating test data with correct structure...")
    results = create_streamlit_compatible_data()
    
    # Check data structure
    print(f"Results keys: {list(results.keys())}")
    print(f"Number of patients: {len(results['patient_histories'])}")
    
    # Check first patient structure
    first_patient_id = next(iter(results['patient_histories']))
    first_patient = results['patient_histories'][first_patient_id]
    print(f"\nFirst patient has {len(first_patient)} visits")
    print("First visit structure:")
    first_visit = first_patient[0]
    for key, value in first_visit.items():
        print(f"  {key}: {type(value).__name__}")
    
    # Generate the plot
    print("\nGenerating visualization...")
    fig = generate_va_over_time_plot(results)
    
    # Save the plot
    plot_filename = "test_data_structure_fix.png"
    fig.savefig(plot_filename, dpi=300, bbox_inches='tight')
    print(f"Plot saved as {plot_filename}")
    
    # Close the plot
    plt.close(fig)
    
    # Also save sample data
    sample_results = {
        "mean_va_data": results["mean_va_data"][:5],
        "patient_histories_sample": {
            str(k): v[:3] if isinstance(v, list) else v 
            for k, v in list(results["patient_histories"].items())[:3]
        },
        "simulation_start_date": str(results["simulation_start_date"])
    }
    
    with open("test_data_structure.json", "w") as f:
        json.dump(sample_results, f, default=str, indent=2)
    print("Sample data saved as test_data_structure.json")

if __name__ == "__main__":
    test_visualization_fix()