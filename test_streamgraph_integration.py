"""
Test the fixed streamgraph implementation with real simulation data.

This script loads simulation results and displays the patient state streamgraph 
using the fixed implementation. It can be used to test the visualization with 
real data and verify that population conservation and state transitions are 
working correctly.
"""

import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import sys
import argparse
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import the fixed streamgraph implementation
try:
    from fixed_streamgraph import (
        extract_patient_states, 
        aggregate_states_by_month,
        create_streamgraph,
        PATIENT_STATES
    )
    logger.info("Successfully imported fixed_streamgraph module")
except ImportError as e:
    logger.error(f"Failed to import fixed_streamgraph: {e}")
    sys.exit(1)

def load_simulation_results(file_path=None):
    """Load simulation results from file or find a suitable file."""
    if file_path and os.path.exists(file_path):
        logger.info(f"Loading simulation results from {file_path}")
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            return data
        except Exception as e:
            logger.error(f"Error loading file: {e}")
    
    # Try to find simulation results in common locations
    common_paths = [
        "output/simulation_results/latest_results.json",
        "simulation_results.json",
        "output/staggered_comparison/latest_comparison.json",
        "streamgraph_debug_data.json"
    ]
    
    for path in common_paths:
        if os.path.exists(path):
            logger.info(f"Found simulation results at {path}")
            try:
                with open(path, 'r') as f:
                    data = json.load(f)
                return data
            except Exception as e:
                logger.warning(f"Error loading {path}: {e}")
    
    logger.warning("No simulation results found. Using test data.")
    return generate_test_data()

def generate_test_data():
    """Generate minimal test data for debugging."""
    logger.info("Generating test data...")
    
    test_data = {
        "patient_histories": {},
        "duration_years": 5
    }
    
    # Create 10 test patients with different pathways
    for i in range(10):
        patient_id = f"P{i+1:03d}"
        
        # Create different patient pathways
        if i % 5 == 0:
            # No discontinuation
            visits = [
                {"time": j*30, "is_discontinuation_visit": False} 
                for j in range(60)
            ]
        elif i % 5 == 1:
            # Planned discontinuation, no retreatment
            visits = [
                {"time": j*30, "is_discontinuation_visit": False} 
                for j in range(20)
            ]
            visits.append({
                "time": 600, 
                "is_discontinuation_visit": True,
                "discontinuation_reason": "stable_max_interval"
            })
            visits.extend([
                {"time": 600 + j*30, "is_discontinuation_visit": False} 
                for j in range(1, 40)
            ])
        elif i % 5 == 2:
            # Planned discontinuation with retreatment
            visits = [
                {"time": j*30, "is_discontinuation_visit": False} 
                for j in range(15)
            ]
            visits.append({
                "time": 450, 
                "is_discontinuation_visit": True,
                "discontinuation_reason": "stable_max_interval"
            })
            visits.extend([
                {"time": 450 + j*30, "is_discontinuation_visit": False} 
                for j in range(1, 10)
            ])
            visits.append({
                "time": 750,
                "is_retreatment_visit": True
            })
            visits.extend([
                {"time": 750 + j*30, "is_discontinuation_visit": False} 
                for j in range(1, 30)
            ])
        elif i % 5 == 3:
            # Random administrative discontinuation
            visits = [
                {"time": j*30, "is_discontinuation_visit": False} 
                for j in range(10)
            ]
            visits.append({
                "time": 300, 
                "is_discontinuation_visit": True,
                "discontinuation_reason": "random_administrative"
            })
        else:
            # Premature discontinuation with retreatment
            visits = [
                {"time": j*30, "is_discontinuation_visit": False} 
                for j in range(5)
            ]
            visits.append({
                "time": 150, 
                "is_discontinuation_visit": True,
                "discontinuation_reason": "premature"
            })
            visits.extend([
                {"time": 150 + j*30, "is_discontinuation_visit": False} 
                for j in range(1, 5)
            ])
            visits.append({
                "time": 300,
                "is_retreatment_visit": True
            })
            visits.extend([
                {"time": 300 + j*30, "is_discontinuation_visit": False} 
                for j in range(1, 50)
            ])
        
        test_data["patient_histories"][patient_id] = visits
    
    return test_data

def validate_patient_data(results):
    """Validate the patient data structure."""
    logger.info("Validating patient data structure")
    
    # Check for essential fields
    if "patient_histories" not in results:
        logger.error("Missing 'patient_histories' in results")
        return False
    
    patient_histories = results["patient_histories"]
    if not patient_histories:
        logger.error("Empty patient histories")
        return False
    
    # Check a sample patient
    sample_patient_id = next(iter(patient_histories))
    sample_visits = patient_histories[sample_patient_id]
    
    logger.info(f"Sample patient {sample_patient_id} has {len(sample_visits)} visits")
    
    # Verify visit structure
    if sample_visits:
        sample_visit = sample_visits[0]
        logger.info(f"Sample visit structure: {list(sample_visit.keys())}")
        
        # Check for time field
        if "time" not in sample_visit and "date" not in sample_visit:
            logger.warning("Missing time field in visits - check data structure")
    
    # Check discontinuation events
    disc_count = 0
    disc_types = set()
    retreat_count = 0
    
    for patient_id, visits in patient_histories.items():
        for visit in visits:
            if visit.get("is_discontinuation_visit", False):
                disc_count += 1
                disc_type = visit.get("discontinuation_reason")
                if disc_type:
                    disc_types.add(disc_type)
            if visit.get("is_retreatment_visit", False):
                retreat_count += 1
    
    logger.info(f"Found {disc_count} discontinuation events with types: {disc_types}")
    logger.info(f"Found {retreat_count} retreatment events")
    
    return True

def verify_population_conservation(monthly_data):
    """Verify total population is conserved across all months."""
    logger.info("Verifying population conservation")
    
    months = monthly_data["time_months"].unique()
    
    previous_total = None
    conservation_issues = []
    
    for month in sorted(months):
        month_data = monthly_data[monthly_data["time_months"] == month]
        total = month_data["count"].sum()
        
        if previous_total is not None and total != previous_total:
            issue = f"Month {month}: Previous: {previous_total}, Current: {total}, Diff: {total - previous_total}"
            conservation_issues.append(issue)
            logger.warning(f"WARNING: Population not conserved at month {month}. {issue}")
        
        previous_total = total
    
    logger.info(f"Final population count: {previous_total}")
    if not conservation_issues:
        logger.info("Population is conserved across all time points")
        return True
    else:
        logger.warning(f"Found {len(conservation_issues)} conservation issues")
        return False

def process_results(results):
    """Process simulation results and create visualizations."""
    logger.info("Processing simulation results")
    
    # Validate data structure
    if not validate_patient_data(results):
        logger.error("Invalid data structure - cannot create visualization")
        return None, None
    
    # Create streamgraph using fixed implementation
    try:
        logger.info("Creating streamgraph visualization")
        fig = create_streamgraph(results)
        
        # Extract data for validation
        patient_histories = results.get("patient_histories", {})
        duration_years = results.get("duration_years", 5)
        duration_months = int(duration_years * 12)
        
        # Extract patient states
        logger.info("Extracting patient states")
        states_df = extract_patient_states(patient_histories)
        
        # Aggregate by month
        logger.info("Aggregating states by month")
        monthly_counts = aggregate_states_by_month(states_df, duration_months)
        
        # Verify population conservation
        verify_population_conservation(monthly_counts)
        
        return fig, monthly_counts
        
    except Exception as e:
        logger.error(f"Error creating streamgraph: {e}")
        import traceback
        traceback.print_exc()
        return None, None

def main():
    """Main function to process results and display visualization."""
    parser = argparse.ArgumentParser(description='Test streamgraph visualization')
    parser.add_argument('--input', help='Input JSON file with simulation results')
    parser.add_argument('--output', help='Output file for visualization (.png)')
    parser.add_argument('--streamlit', action='store_true', help='Run in Streamlit mode')
    args = parser.parse_args()
    
    # Load simulation results
    results = load_simulation_results(args.input)
    
    # Process results and create visualizations
    fig, monthly_counts = process_results(results)
    
    if fig:
        if args.streamlit:
            # For Streamlit integration, return the figure directly
            import streamlit as st
            st.title("Patient State Streamgraph")
            st.pyplot(fig)
            
            # Show data table
            if monthly_counts is not None:
                with st.expander("View Data"):
                    pivot = monthly_counts.pivot(
                        index='time_months',
                        columns='state',
                        values='count'
                    ).fillna(0)
                    
                    # Add total column
                    pivot['Total'] = pivot.sum(axis=1)
                    st.dataframe(pivot)
        else:
            # Save or show the figure
            if args.output:
                fig.savefig(args.output, dpi=100, bbox_inches="tight")
                logger.info(f"Saved visualization to {args.output}")
            else:
                plt.show()
    else:
        logger.error("Failed to create visualization")

if __name__ == "__main__":
    main()