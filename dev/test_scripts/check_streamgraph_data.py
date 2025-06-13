#!/usr/bin/env python3
"""
Check the streamgraph data to understand why discontinuation states aren't shown.
"""

import json
import pandas as pd
import numpy as np
from streamlit_app.streamgraph_patient_states import extract_patient_states, aggregate_states_by_month

def main():
    """Load simulation data and analyze patient states."""
    try:
        # Load simulation results
        with open('full_streamgraph_test_data.json', 'r') as f:
            data = json.load(f)
        
        # Check visit records
        print("Checking visit records...")
        disc_found = False
        is_disc_visit_found = False
        
        # Sample first 10 patients
        sample_patients = list(data['patient_histories'].items())[:10]
        
        for pid, visits in sample_patients:
            # Find discontinuation visits
            disc_visits = [v for v in visits if v.get('is_discontinuation_visit')]
            
            if disc_visits:
                print(f"Patient {pid} has {len(disc_visits)} discontinuation visits")
                for v in disc_visits:
                    is_disc_visit_found = True
                    if 'discontinuation_type' in v:
                        disc_found = True
                        print(f"  Found discontinuation_type: {v.get('discontinuation_type')}")
                    
                    # Debug all fields
                    print("  Visit fields:")
                    for k, val in v.items():
                        print(f"    {k}: {val}")
        
        print(f"Any discontinuation visits found: {is_disc_visit_found}")
        print(f"Discontinuation_type field found: {disc_found}")
        
        # Test state extraction and aggregation
        print("\nTesting state extraction:")
        patient_states_df = extract_patient_states(data['patient_histories'])
        print(f"- Extracted {len(patient_states_df)} patient state records")
        
        # What states were found?
        unique_states = patient_states_df['state'].unique()
        print(f"- Unique states: {unique_states}")
        
        # Counts by state
        state_counts = patient_states_df['state'].value_counts()
        print("\nState counts in extraction:")
        for state, count in state_counts.items():
            print(f"  {state}: {count}")
        
        # Test aggregation
        print("\nTesting state aggregation:")
        duration_months = int(data.get('duration_years', 5) * 12)
        monthly_counts = aggregate_states_by_month(patient_states_df, duration_months)
        
        # Check if we got data for all months
        month_count = monthly_counts['time_months'].nunique()
        print(f"- Generated data for {month_count} months")
        
        # Check for all 9 states being represented across all months
        columns_in_pivot = monthly_counts.pivot(
            index='time_months',
            columns='state',
            values='count'
        ).columns
        
        print(f"- States in pivot: {list(columns_in_pivot)}")
        
        # Check for any discontinuation states at specific months
        for month in [12, 24, 36, 48, 60]:
            month_data = monthly_counts[monthly_counts['time_months'] == month]
            print(f"\nMonth {month} state counts:")
            for _, row in month_data.iterrows():
                if row['state'] != 'active' and row['count'] > 0:
                    print(f"  {row['state']}: {row['count']}")
        
    except Exception as e:
        import traceback
        print(f"Error: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()