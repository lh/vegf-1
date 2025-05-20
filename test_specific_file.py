#!/usr/bin/env python3
"""
Test the fixed streamgraph implementation with a specific data file.

This script loads a specific simulation results file and generates a visualization.
"""

import json
import sys
import os
import matplotlib.pyplot as plt
import logging
from datetime import datetime
import argparse

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import our fixed implementation
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from fixed_streamgraph import (
    extract_patient_states, 
    aggregate_states_by_month,
    create_streamgraph,
    PATIENT_STATES
)

def parse_time_format(time_value):
    """Parse different time formats into a standard format."""
    if isinstance(time_value, (int, float)):
        return time_value
    
    if isinstance(time_value, str):
        # Try different datetime formats
        formats = [
            "%Y-%m-%d",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%S.%f",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%dT%H:%M:%S.%fZ"
        ]
        
        for fmt in formats:
            try:
                dt = datetime.strptime(time_value, fmt)
                # Return timestamp in days
                return dt.timestamp() / (24 * 3600)
            except ValueError:
                continue
    
    return None

def analyze_time_formats(patient_histories):
    """Analyze the time formats used in the data."""
    time_formats = {}
    
    # Sample a few patients
    sample_size = min(5, len(patient_histories))
    sample_patients = list(patient_histories.keys())[:sample_size]
    
    for patient_id in sample_patients:
        visits = patient_histories[patient_id]
        if not visits:
            continue
        
        # Look at a few visits
        sample_visits = visits[:min(5, len(visits))]
        for visit in sample_visits:
            time_value = visit.get("time", visit.get("date"))
            if time_value is not None:
                time_type = type(time_value).__name__
                if time_type not in time_formats:
                    time_formats[time_type] = time_value
    
    logger.info(f"Time formats found: {list(time_formats.keys())}")
    for fmt, example in time_formats.items():
        logger.info(f"  {fmt} example: {example}")
    
    return time_formats

def fix_time_values(patient_histories):
    """Fix time values in the patient histories."""
    fixed_histories = {}
    
    for patient_id, visits in patient_histories.items():
        fixed_visits = []
        
        for visit in visits:
            # Create a copy of the visit
            fixed_visit = visit.copy()
            
            # Fix time value
            time_value = visit.get("time", visit.get("date"))
            if time_value is not None:
                parsed_time = parse_time_format(time_value)
                if parsed_time is not None:
                    fixed_visit["time"] = parsed_time
            
            fixed_visits.append(fixed_visit)
        
        fixed_histories[patient_id] = fixed_visits
    
    return fixed_histories

def analyze_patient_data(data):
    """Analyze patient data to understand its structure."""
    if not isinstance(data, dict):
        logger.error("Data is not a dictionary")
        return
    
    # Check if we have patient histories
    if "patient_histories" not in data:
        logger.error("No patient_histories in data")
        return
    
    patient_histories = data["patient_histories"]
    if not patient_histories:
        logger.error("Empty patient histories")
        return
    
    # Analyze patient counts
    patient_count = len(patient_histories)
    logger.info(f"Found {patient_count} patients")
    
    # Analyze time formats
    time_formats = analyze_time_formats(patient_histories)
    
    # Check for discontinuations and retreatments
    disc_count = 0
    disc_types = {}
    retreat_count = 0
    
    for patient_id, visits in patient_histories.items():
        for visit in visits:
            if visit.get("is_discontinuation_visit", False):
                disc_count += 1
                reason = visit.get("discontinuation_reason", "unknown")
                disc_types[reason] = disc_types.get(reason, 0) + 1
            
            if visit.get("is_retreatment_visit", False):
                retreat_count += 1
    
    logger.info(f"Found {disc_count} discontinuations by type: {disc_types}")
    logger.info(f"Found {retreat_count} retreatment events")
    
    return {
        "patient_count": patient_count,
        "discontinuations": disc_count,
        "retreatments": retreat_count,
        "time_formats": time_formats
    }

def main():
    """Main test function."""
    parser = argparse.ArgumentParser(description='Test streamgraph with specific file')
    parser.add_argument('--file', '-f', required=True, help='Path to simulation results file')
    parser.add_argument('--output', '-o', default='output_streamgraph.png', help='Output image path')
    args = parser.parse_args()
    
    file_path = args.file
    output_path = args.output
    
    logger.info(f"Loading data from {file_path}")
    
    try:
        # Load the data
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        # Analyze the data
        logger.info("Analyzing data structure...")
        analyze_patient_data(data)
        
        # Fix time values if needed
        logger.info("Fixing time values...")
        fixed_histories = fix_time_values(data["patient_histories"])
        data["patient_histories"] = fixed_histories
        
        # Extract patient states
        logger.info("Extracting patient states...")
        patient_states_df = extract_patient_states(data["patient_histories"])
        logger.info(f"Extracted {len(patient_states_df)} state records")
        
        # Aggregate by month
        logger.info("Aggregating by month...")
        duration_years = data.get("duration_years", 5)
        duration_months = int(duration_years * 12)
        monthly_counts = aggregate_states_by_month(patient_states_df, duration_months)
        
        # Check population conservation
        total_by_month = monthly_counts.groupby('time_months')['count'].sum()
        if len(total_by_month) > 0:
            first_total = total_by_month.iloc[0]
            is_conserved = (total_by_month == first_total).all()
            logger.info(f"Population conservation: {is_conserved} (total: {first_total})")
        
        # Create streamgraph
        logger.info("Creating streamgraph...")
        fig = create_streamgraph(data)
        
        # Save the visualization
        fig.savefig(output_path, dpi=100, bbox_inches="tight")
        logger.info(f"Saved streamgraph to {output_path}")
        
        # Show the visualization
        plt.show()
        
    except Exception as e:
        logger.error(f"Error processing file: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()