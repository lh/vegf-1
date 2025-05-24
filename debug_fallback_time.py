#!/usr/bin/env python3
"""Debug script to investigate visit times exceeding expected simulation duration."""

import json
import os
from datetime import datetime
from pathlib import Path
import glob

def find_latest_simulation_result():
    """Find the most recent simulation result file."""
    result_files = glob.glob(os.path.join('output', 'simulation_results', 'ape_simulation_*.json'))
    if not result_files:
        print("No simulation result files found")
        return None
    return max(result_files, key=os.path.getctime)

def analyze_visit_times(simulation_data):
    """Analyze visit times across all patients."""
    max_time_days = 0
    max_time_patient = None
    max_time_visit = None
    
    # Track cumulative times for each patient
    patient_time_issues = []
    
    # Analyze each patient
    for patient_id, patient_data in simulation_data['simulation_results']['patient_histories'].items():
        visits = patient_data.get('visits', [])
        
        if not visits:
            continue
            
        # Track cumulative time
        cumulative_time = 0
        prev_time = 0
        
        for i, visit in enumerate(visits):
            visit_time_days = visit.get('time', 0)
            visit_time_months = visit_time_days / 30.44  # Average days per month
            
            # Check if time is increasing properly
            if visit_time_days < prev_time:
                patient_time_issues.append({
                    'patient_id': patient_id,
                    'visit_index': i,
                    'issue': 'Time going backwards',
                    'current_time': visit_time_days,
                    'previous_time': prev_time
                })
            
            # Check for maximum time
            if visit_time_days > max_time_days:
                max_time_days = visit_time_days
                max_time_patient = patient_id
                max_time_visit = visit
            
            prev_time = visit_time_days
            
            # Check if any visit occurs after 60 months
            if visit_time_months > 60:
                patient_time_issues.append({
                    'patient_id': patient_id,
                    'visit_index': i,
                    'issue': 'Visit after 60 months',
                    'time_days': visit_time_days,
                    'time_months': visit_time_months,
                    'visit_type': visit.get('visit_type', 'Unknown')
                })
    
    # Print findings
    print(f"\n=== Visit Time Analysis ===")
    print(f"Maximum visit time: {max_time_days:.1f} days ({max_time_days/30.44:.1f} months)")
    print(f"Patient with max time: {max_time_patient}")
    if max_time_visit:
        print(f"Visit type: {max_time_visit.get('visit_type', 'Unknown')}")
        print(f"Visit date: {max_time_visit.get('date', 'Unknown')}")
    
    print(f"\n=== Time Issues Found ===")
    print(f"Total issues: {len(patient_time_issues)}")
    
    # Group issues by type
    issues_by_type = {}
    for issue in patient_time_issues:
        issue_type = issue['issue']
        if issue_type not in issues_by_type:
            issues_by_type[issue_type] = []
        issues_by_type[issue_type].append(issue)
    
    for issue_type, issues in issues_by_type.items():
        print(f"\n{issue_type}: {len(issues)} occurrences")
        # Show first few examples
        for issue in issues[:5]:
            print(f"  Patient {issue['patient_id']}, Visit {issue['visit_index']}: {issue}")
            
    # Analyze visit distribution by time
    print(f"\n=== Visit Distribution by Time ===")
    time_buckets = {
        '0-12 months': 0,
        '12-24 months': 0,
        '24-36 months': 0,
        '36-48 months': 0,
        '48-60 months': 0,
        '>60 months': 0
    }
    
    for patient_id, patient_data in simulation_data['simulation_results']['patient_histories'].items():
        for visit in patient_data.get('visits', []):
            time_months = visit.get('time', 0) / 30.44
            if time_months <= 12:
                time_buckets['0-12 months'] += 1
            elif time_months <= 24:
                time_buckets['12-24 months'] += 1
            elif time_months <= 36:
                time_buckets['24-36 months'] += 1
            elif time_months <= 48:
                time_buckets['36-48 months'] += 1
            elif time_months <= 60:
                time_buckets['48-60 months'] += 1
            else:
                time_buckets['>60 months'] += 1
    
    for bucket, count in time_buckets.items():
        print(f"{bucket}: {count} visits")
    
    # Check simulation parameters
    print(f"\n=== Simulation Parameters ===")
    sim_duration = simulation_data.get('parameters', {}).get('simulation_duration', 'Unknown')
    print(f"Simulation duration: {sim_duration}")
    
    # Check if simulation end date is respected
    if isinstance(sim_duration, (int, float)):
        print(f"Expected max time: {sim_duration * 365.25:.1f} days ({sim_duration * 12:.1f} months)")
        if max_time_days > sim_duration * 365.25:
            print(f"WARNING: Visits exceed simulation duration by {max_time_days - sim_duration * 365.25:.1f} days")

def main():
    # Find latest simulation result
    result_file = find_latest_simulation_result()
    if not result_file:
        return
    
    print(f"Analyzing: {result_file}")
    
    # Load simulation data
    with open(result_file, 'r') as f:
        simulation_data = json.load(f)
    
    # Analyze visit times
    analyze_visit_times(simulation_data)

if __name__ == "__main__":
    main()