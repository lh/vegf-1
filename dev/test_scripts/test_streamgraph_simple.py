#!/usr/bin/env python3
"""
Simple test for the fixed streamgraph implementation.

This script creates a simple test dataset and generates a streamgraph visualization
to verify that the implementation correctly tracks patient states.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import sys
import json
import os

# Import our fixed implementation
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from fixed_streamgraph import (
    extract_patient_states, 
    aggregate_states_by_month,
    create_streamgraph,
    PATIENT_STATES
)

def generate_test_data():
    """Generate a simple test dataset with known patient transitions."""
    # We'll create a dataset with different patient patterns:
    # - Never discontinued patients
    # - Planned discontinuation with no retreatment
    # - Planned discontinuation with retreatment
    # - Administrative discontinuation (lost to follow-up)
    # - Premature discontinuation with retreatment
    
    test_data = {
        "patient_histories": {},
        "duration_years": 5
    }
    
    # Create 20 test patients with different patterns
    patient_patterns = [
        {
            "name": "Never discontinued",
            "count": 4,
            "pattern": lambda i: [
                {"time": j*30, "is_discontinuation_visit": False} 
                for j in range(60)
            ]
        },
        {
            "name": "Planned discontinuation - no retreatment",
            "count": 4,
            "pattern": lambda i: [
                {"time": j*30, "is_discontinuation_visit": False} 
                for j in range(20)
            ] + [
                {"time": 600, 
                "is_discontinuation_visit": True,
                "discontinuation_reason": "stable_max_interval"}
            ] + [
                {"time": 600 + j*30, "is_discontinuation_visit": False} 
                for j in range(1, 40)
            ]
        },
        {
            "name": "Planned discontinuation - with retreatment",
            "count": 4,
            "pattern": lambda i: [
                {"time": j*30, "is_discontinuation_visit": False} 
                for j in range(15)
            ] + [
                {"time": 450,
                "is_discontinuation_visit": True,
                "discontinuation_reason": "stable_max_interval"}
            ] + [
                {"time": 450 + j*30, "is_discontinuation_visit": False} 
                for j in range(1, 10)
            ] + [
                {"time": 750, "is_retreatment_visit": True}
            ] + [
                {"time": 750 + j*30, "is_discontinuation_visit": False} 
                for j in range(1, 30)
            ]
        },
        {
            "name": "Administrative discontinuation",
            "count": 4,
            "pattern": lambda i: [
                {"time": j*30, "is_discontinuation_visit": False} 
                for j in range(10)
            ] + [
                {"time": 300,
                "is_discontinuation_visit": True,
                "discontinuation_reason": "random_administrative"}
            ]
            # No visits after administrative discontinuation (lost to follow-up)
        },
        {
            "name": "Premature discontinuation - with retreatment",
            "count": 4,
            "pattern": lambda i: [
                {"time": j*30, "is_discontinuation_visit": False} 
                for j in range(5)
            ] + [
                {"time": 150,
                "is_discontinuation_visit": True,
                "discontinuation_reason": "premature"}
            ] + [
                {"time": 150 + j*30, "is_discontinuation_visit": False} 
                for j in range(1, 5)
            ] + [
                {"time": 300, "is_retreatment_visit": True}
            ] + [
                {"time": 300 + j*30, "is_discontinuation_visit": False} 
                for j in range(1, 50)
            ]
        }
    ]
    
    # Generate patients for each pattern
    patient_id = 1
    for pattern in patient_patterns:
        for i in range(pattern["count"]):
            test_data["patient_histories"][f"P{patient_id:03d}"] = pattern["pattern"](i)
            patient_id += 1
    
    return test_data

def print_data_summary(data):
    """Print a summary of the test data."""
    print(f"Generated {len(data['patient_histories'])} test patients")
    
    # Count visit types
    disc_count = 0
    disc_types = {}
    retreat_count = 0
    
    for patient_id, visits in data["patient_histories"].items():
        for visit in visits:
            if visit.get("is_discontinuation_visit", False):
                disc_count += 1
                disc_type = visit.get("discontinuation_reason", "unknown")
                disc_types[disc_type] = disc_types.get(disc_type, 0) + 1
            if visit.get("is_retreatment_visit", False):
                retreat_count += 1
    
    print(f"Created {disc_count} discontinuation events by type: {disc_types}")
    print(f"Created {retreat_count} retreatment events")

def validate_patient_counts(monthly_counts):
    """Verify population conservation."""
    # Group by month and sum counts
    total_by_month = monthly_counts.groupby('time_months')['count'].sum()
    
    # Check if all months have the same count
    total_patients = total_by_month.iloc[0]
    is_conserved = (total_by_month == total_patients).all()
    
    print(f"Total patient count: {total_patients}")
    print(f"Population conservation verified: {is_conserved}")
    
    # Print counts at specific months
    print("\nPatient counts by state at key timepoints:")
    
    pivot_data = monthly_counts.pivot(
        index='time_months',
        columns='state',
        values='count'
    ).fillna(0)
    
    for month in [0, 12, 24, 36, 48, 60]:
        if month in pivot_data.index:
            row = pivot_data.loc[month]
            print(f"\nMonth {month}:")
            for state in PATIENT_STATES:
                if state in row and row[state] > 0:
                    print(f"  {state}: {int(row[state])}")
    
    return is_conserved

def main():
    """Main test function."""
    # Generate test data
    print("Generating test data...")
    test_data = generate_test_data()
    print_data_summary(test_data)
    
    # Process the data through our pipeline
    print("\nExtracting patient states...")
    patient_states_df = extract_patient_states(test_data["patient_histories"])
    print(f"Extracted {len(patient_states_df)} state records")
    
    print("\nAggregating states by month...")
    duration_months = int(test_data["duration_years"] * 12)
    monthly_counts = aggregate_states_by_month(patient_states_df, duration_months)
    print(f"Aggregated into {len(monthly_counts)} monthly state counts")
    
    # Validate patient counts
    print("\nValidating patient counts...")
    validate_patient_counts(monthly_counts)
    
    # Create streamgraph visualization
    print("\nCreating streamgraph visualization...")
    fig = create_streamgraph(test_data)
    
    # Save the visualization
    output_path = "test_streamgraph.png"
    fig.savefig(output_path, dpi=100, bbox_inches="tight")
    print(f"Saved streamgraph to {output_path}")
    
    # Output data for debugging
    with open("test_patient_data.json", "w") as f:
        json.dump(test_data, f, indent=2)
    print("Saved test data to test_patient_data.json")
    
    # Show the visualization
    plt.show()

if __name__ == "__main__":
    main()