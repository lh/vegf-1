#!/usr/bin/env python3
"""
Script to examine the actual data structure in Streamlit visualization
to understand how discontinuation and retreatment states are tracked.
"""

import json
import pandas as pd
from pathlib import Path
import numpy as np

def load_simulation_data(filepath):
    """Load simulation results from JSON file"""
    with open(filepath, 'r') as f:
        data = json.load(f)
    return data

def examine_patient_structure(data):
    """Examine the structure of patient data"""
    # Get general statistics
    n_simulations = len(data['simulations'])
    print(f"Number of simulations: {n_simulations}")
    
    # Look at the first simulation
    sim0 = data['simulations'][0]
    n_patients = len(sim0['patient_histories'])
    print(f"Number of patients: {n_patients}")
    
    # Examine the structure of a single patient
    print("\n=== First Patient Structure ===")
    patient0 = sim0['patient_histories'][0]
    print(f"Patient ID: {patient0['patient_id']}")
    print(f"Keys in patient history: {list(patient0.keys())}")
    
    # Look at basic metrics
    if 'metrics' in patient0:
        print(f"\nMetrics: {patient0['metrics']}")
    
    # Look at visits structure
    print(f"\nNumber of visits: {len(patient0['visits'])}")
    
    if patient0['visits']:
        print("\n=== First Visit Structure ===")
        visit0 = patient0['visits'][0]
        print(f"Visit keys: {list(visit0.keys())}")
        print(f"Visit example: {visit0}")
        
        # Check last few visits
        print("\n=== Last 3 Visits ===")
        for i, visit in enumerate(patient0['visits'][-3:]):
            print(f"Visit {len(patient0['visits']) - 3 + i}: {visit}")
    
    # Look for discontinuation/retreatment indicators
    print("\n=== Looking for discontinuation markers ===")
    
    # Check visit statuses
    visit_statuses = set()
    for patient in sim0['patient_histories']:
        for visit in patient['visits']:
            if 'status' in visit:
                visit_statuses.add(visit['status'])
    
    print(f"All unique visit statuses: {visit_statuses}")
    
    # Check for discontinuation flags
    for patient in sim0['patient_histories'][:3]:  # First 3 patients
        print(f"\nPatient {patient['patient_id']}:")
        if 'metrics' in patient:
            metrics = patient['metrics']
            print(f"  Metrics: {metrics}")
        
        if 'discontinued' in patient:
            print(f"  Discontinued: {patient['discontinued']}")
        
        if 'retreated' in patient:
            print(f"  Retreated: {patient['retreated']}")
            
        # Check for discontinuation time
        discontinuation_time = None
        retreatment_time = None
        
        for visit in patient['visits']:
            if 'status' in visit and 'discontinu' in str(visit['status']).lower():
                discontinuation_time = visit.get('time', visit.get('visit_time'))
                break
                
        print(f"  Discontinuation time: {discontinuation_time}")
        
        # Check if retreated
        retreated = False
        for i, visit in enumerate(patient['visits']):
            if discontinuation_time and visit.get('time', visit.get('visit_time')) > discontinuation_time:
                retreated = True
                retreatment_time = visit.get('time', visit.get('visit_time'))
                break
                
        print(f"  Retreated: {retreated}, Retreatment time: {retreatment_time}")

def examine_state_tracking(data):
    """Examine how patient states are tracked over time"""
    print("\n=== State Tracking Analysis ===")
    
    sim0 = data['simulations'][0]
    
    # Check what fields exist for state tracking
    state_fields = set()
    for patient in sim0['patient_histories']:
        for visit in patient['visits']:
            state_fields.update(visit.keys())
    
    print(f"All visit fields: {state_fields}")
    
    # Look for patients with discontinuation
    discontinued_patients = []
    for patient in sim0['patient_histories']:
        for visit in patient['visits']:
            if 'discontin' in str(visit).lower():
                discontinued_patients.append(patient)
                break
    
    print(f"\nNumber of patients with 'discontin' in visits: {len(discontinued_patients)}")
    
    if discontinued_patients:
        print("\n=== Example Discontinued Patient ===")
        patient = discontinued_patients[0]
        print(f"Patient ID: {patient['patient_id']}")
        print(f"Patient keys: {list(patient.keys())}")
        
        # Show their visit progression
        print("\nVisit progression:")
        for i, visit in enumerate(patient['visits']):
            print(f"Visit {i}: Time={visit.get('time', visit.get('visit_time'))}, "
                  f"Status={visit.get('status', 'no status')}, "
                  f"Type={visit.get('visit_type', 'no type')}")

def analyze_time_points(data):
    """Analyze patient states at specific time points"""
    print("\n=== Time Point Analysis ===")
    
    sim0 = data['simulations'][0]
    time_points = [12, 24, 36, 48, 60]
    
    for time_point in time_points:
        counts = {
            'active': 0,
            'discontinued': 0,
            'retreated': 0,
            'unknown': 0
        }
        
        for patient in sim0['patient_histories']:
            # Determine state at time point
            state = 'active'  # Default assumption
            
            # Check visits up to this time point
            visits_before = [v for v in patient['visits'] 
                           if v.get('time', v.get('visit_time', 0)) <= time_point]
            
            # Check if patient has discontinued
            for visit in visits_before:
                if 'discontin' in str(visit).lower():
                    state = 'discontinued'
                    break
            
            # Check if patient retreated after discontinuation
            if state == 'discontinued':
                visits_after_disc = [v for v in patient['visits'] 
                                   if v.get('time', v.get('visit_time', 0)) > time_point]
                if visits_after_disc:
                    state = 'retreated'
            
            counts[state] += 1
        
        print(f"\nTime {time_point} months:")
        for state, count in counts.items():
            print(f"  {state}: {count}")

def main():
    # Find a recent simulation file
    sim_dir = Path("/Users/rose/Code/CC/output/simulation_results")
    
    # Get most recent file
    sim_files = list(sim_dir.glob("*.json"))
    if not sim_files:
        print("No simulation files found")
        return
    
    recent_file = max(sim_files, key=lambda p: p.stat().st_mtime)
    print(f"Analyzing: {recent_file}")
    
    # Load and examine data
    data = load_simulation_data(recent_file)
    
    examine_patient_structure(data)
    examine_state_tracking(data)
    analyze_time_points(data)

if __name__ == "__main__":
    main()