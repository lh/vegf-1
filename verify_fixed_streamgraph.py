#!/usr/bin/env python3
"""
Verification script for the fixed streamgraph implementation.

This script loads simulation data, runs the fixed implementation, and validates
that it properly preserves patient counts and correctly tracks state transitions.
"""

import json
import argparse
import sys
import logging
import os
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from collections import defaultdict

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import fixed implementation
try:
    from fixed_streamgraph import (
        extract_patient_states, 
        aggregate_states_by_month,
        create_streamgraph,
        PATIENT_STATES
    )
    logger.info("Successfully imported fixed_streamgraph module")
except ImportError:
    logger.error("Failed to import fixed_streamgraph. Make sure the file exists.")
    sys.exit(1)

def find_simulation_data():
    """Find a suitable simulation data file for testing."""
    possible_paths = [
        "streamgraph_debug_data.json",
        "deep_debug_output.json",
        "output/simulation_results/latest_results.json",
        "streamlit_debug_data.json"
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            logger.info(f"Found simulation data at {path}")
            return path
    
    logger.warning("No simulation data found")
    return None

def load_data(data_path=None):
    """Load simulation data for testing."""
    # Find data if path not provided
    if not data_path:
        data_path = find_simulation_data()
        if not data_path:
            logger.error("No data file found or provided")
            sys.exit(1)
    
    # Load the data
    try:
        with open(data_path, 'r') as f:
            data = json.load(f)
        logger.info(f"Loaded data from {data_path}")
        return data
    except Exception as e:
        logger.error(f"Error loading data file: {e}")
        sys.exit(1)

def validate_data_structure(data):
    """Validate the simulation data structure."""
    # Check basic structure
    if "patient_histories" not in data:
        logger.error("Missing 'patient_histories' in data")
        return False
    
    patient_histories = data.get("patient_histories", {})
    patient_count = len(patient_histories)
    
    if patient_count == 0:
        logger.error("No patients in data")
        return False
    
    logger.info(f"Found {patient_count} patients in data")
    
    # Check sample patient
    first_patient_id = next(iter(patient_histories))
    visits = patient_histories[first_patient_id]
    
    if not visits:
        logger.warning(f"Patient {first_patient_id} has no visits")
    else:
        # Check visit structure
        visit = visits[0]
        logger.info(f"Sample visit structure: {list(visit.keys())}")
        
        # Check for time field
        if "time" not in visit and "date" not in visit:
            logger.warning("Missing time field in visits")
    
    # Check discontinuation and retreatment
    disc_count = 0
    disc_reasons = defaultdict(int)
    retreat_count = 0
    
    for patient_id, visits in patient_histories.items():
        for visit in visits:
            if visit.get("is_discontinuation_visit", False):
                disc_count += 1
                reason = visit.get("discontinuation_reason", "unknown")
                disc_reasons[reason] += 1
            
            if visit.get("is_retreatment_visit", False):
                retreat_count += 1
    
    logger.info(f"Found {disc_count} discontinuation events with reasons: {dict(disc_reasons)}")
    logger.info(f"Found {retreat_count} retreatment events")
    
    return True

def verify_conservation(monthly_counts):
    """Verify population conservation in aggregated state data."""
    # Check if patient counts remain constant over time
    months = monthly_counts["time_months"].unique()
    
    first_month = months[0] if len(months) > 0 else None
    last_month = months[-1] if len(months) > 0 else None
    
    if first_month is not None and last_month is not None:
        first_count = monthly_counts[monthly_counts["time_months"] == first_month]["count"].sum()
        last_count = monthly_counts[monthly_counts["time_months"] == last_month]["count"].sum()
        
        if first_count != last_count:
            logger.error(f"Population not conserved! First month: {first_count}, Last month: {last_count}")
            return False
        else:
            logger.info(f"Population conservation verified! Consistent count: {first_count}")
            return True
    
    return False

def validate_state_logic(patient_states):
    """Validate state transition logic."""
    # Check for inconsistent states
    potential_issues = []
    
    # Group by patient ID
    grouped = patient_states.groupby("patient_id")
    
    for patient_id, states in grouped:
        # Sort by time
        sorted_states = states.sort_values("time_months")
        
        # Check state transitions
        prev_state = None
        for _, row in sorted_states.iterrows():
            current_state = row["state"]
            
            # Check invalid transitions
            if prev_state == "active" and current_state.startswith("active_retreated"):
                potential_issues.append(f"Patient {patient_id}: Invalid transition from {prev_state} to {current_state}")
            
            prev_state = current_state
    
    if potential_issues:
        logger.warning("Found potential state transition issues:")
        for issue in potential_issues[:5]:  # Show first 5 issues
            logger.warning(f"  {issue}")
        
        if len(potential_issues) > 5:
            logger.warning(f"  ... and {len(potential_issues) - 5} more issues")
        
        return False
    else:
        logger.info("No state transition issues found")
        return True

def main():
    """Main verification function."""
    parser = argparse.ArgumentParser(description='Verify fixed streamgraph implementation')
    parser.add_argument('--input', help='Input data file path')
    parser.add_argument('--output', help='Output image file path')
    args = parser.parse_args()
    
    # Load data
    data = load_data(args.input)
    
    # Validate data structure
    if not validate_data_structure(data):
        logger.warning("Data validation issues detected")
    
    try:
        # Extract patient states
        logger.info("Extracting patient states...")
        patient_states = extract_patient_states(data["patient_histories"])
        logger.info(f"Extracted {len(patient_states)} state records")
        
        # Validate state logic
        validate_state_logic(patient_states)
        
        # Aggregate by month
        logger.info("Aggregating states by month...")
        duration_years = data.get("duration_years", 5)
        duration_months = int(duration_years * 12)
        monthly_counts = aggregate_states_by_month(patient_states, duration_months)
        logger.info(f"Aggregated {len(monthly_counts)} state counts across {duration_months} months")
        
        # Verify population conservation
        verify_conservation(monthly_counts)
        
        # Create streamgraph
        logger.info("Creating streamgraph visualization...")
        fig = create_streamgraph(data)
        
        # Show data points at key timepoints
        pivot_data = monthly_counts.pivot(
            index='time_months',
            columns='state',
            values='count'
        ).fillna(0)
        
        print("\nState counts at key timepoints:")
        for month in [0, 12, 24, 36, 60]:
            if month in pivot_data.index:
                row = pivot_data.loc[month]
                total = row.sum()
                print(f"\nMonth {month} (Total: {total}):")
                for state in PATIENT_STATES:
                    if state in row and row[state] > 0:
                        print(f"  {state}: {row[state]}")
        
        # Save or show visualization
        if args.output:
            fig.savefig(args.output, dpi=100, bbox_inches="tight")
            logger.info(f"Saved visualization to {args.output}")
        else:
            output_path = "verified_streamgraph.png"
            fig.savefig(output_path, dpi=100, bbox_inches="tight")
            logger.info(f"Saved visualization to {output_path}")
            plt.show()
        
        logger.info("Verification complete!")
        
    except Exception as e:
        logger.error(f"Error during verification: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()