#!/usr/bin/env python3
"""Debug the exact error in streamlit"""
import pandas as pd

# Create a visit structure like the one from the error
visit = {'date': '2025-02-25 02:00:00', 'vision': 75}
i = 10
baseline_time = None

try:
    if isinstance(visit['date'], str):
        print(f"Date is string: {visit['date']}")
        visit_date = pd.to_datetime(visit['date'])
        print(f"Parsed date: {visit_date}")
        
        if baseline_time is None and i == 0:
            baseline_time = visit_date
            print("Set baseline time (i==0)")
        elif baseline_time is None:
            print(f"ERROR: No baseline time established for patient, i={i}")
            raise ValueError(f"No baseline time established for patient")
        else:
            print(f"Calculating time difference")
            visit_time = (visit_date - baseline_time).days / 30.44
            print(f"Visit time: {visit_time}")
    else:
        print(f"Invalid date format: {visit['date']}")
        raise ValueError(f"Invalid date format: {visit['date']}")
except Exception as e:
    print(f"Exception occurred: {e}")
    import traceback
    traceback.print_exc()