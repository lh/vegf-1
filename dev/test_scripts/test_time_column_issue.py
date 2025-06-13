#!/usr/bin/env python3
"""
Test the time column handling issue.
"""

import pandas as pd
import numpy as np

# Test different data structures that might come from the simulation
test_cases = [
    # Case 1: Data with 'time' column
    {
        'name': 'With time column',
        'data': [
            {'time': 0, 'visual_acuity': 70, 'std_error': 1.0, 'sample_size': 100},
            {'time': 1, 'visual_acuity': 69.5, 'std_error': 1.1, 'sample_size': 99},
            {'time': 2, 'visual_acuity': 69, 'std_error': 1.2, 'sample_size': 98},
        ]
    },
    # Case 2: Data with 'time_months' column  
    {
        'name': 'With time_months column',
        'data': [
            {'time_months': 0, 'visual_acuity': 70, 'std_error': 1.0, 'sample_size': 100},
            {'time_months': 1, 'visual_acuity': 69.5, 'std_error': 1.1, 'sample_size': 99},
            {'time_months': 2, 'visual_acuity': 69, 'std_error': 1.2, 'sample_size': 98},
        ]
    },
    # Case 3: Data with only 'month' column
    {
        'name': 'With month column',
        'data': [
            {'month': 0, 'visual_acuity': 70, 'std_error': 1.0, 'sample_size': 100},
            {'month': 1, 'visual_acuity': 69.5, 'std_error': 1.1, 'sample_size': 99},
            {'month': 2, 'visual_acuity': 69, 'std_error': 1.2, 'sample_size': 98},
        ]
    },
    # Case 4: Data with no obvious time column
    {
        'name': 'With no time column',
        'data': [
            {'index': 0, 'visual_acuity': 70, 'std_error': 1.0, 'sample_size': 100},
            {'index': 1, 'visual_acuity': 69.5, 'std_error': 1.1, 'sample_size': 99},
            {'index': 2, 'visual_acuity': 69, 'std_error': 1.2, 'sample_size': 98},
        ]
    }
]

# Test the time column detection logic
for test_case in test_cases:
    print(f"\nTesting: {test_case['name']}")
    df = pd.DataFrame(test_case['data'])
    print(f"Columns: {list(df.columns)}")
    
    # Simulate the logic from the thumbnail function
    if "time_months" in df.columns:
        time_col = "time_months"
        print(f"Found time_months column")
    elif "time" in df.columns:
        time_col = "time"
        df["time_months"] = df["time"]
        print(f"Found time column, created time_months")
    else:
        # Look for any column that might be time
        time_candidates = [col for col in df.columns if 'time' in col.lower() or col == 'month' or col == 'months']
        if time_candidates:
            time_col = time_candidates[0]
            df["time_months"] = df[time_col]
            print(f"Found candidate time column: {time_col}, created time_months")
        else:
            print("ERROR: No time column found!")
            
    if "time_months" in df.columns:
        print(f"time_months values: {df['time_months'].tolist()}")

# Now test with actual simulation results structure
print("\n\nTesting actual simulation results structure:")
results = {
    'mean_va_data': [
        {'time': 0, 'visual_acuity': 70, 'std_error': 1.0, 'sample_size': 100},
        {'time': 1, 'visual_acuity': 69.5, 'std_error': 1.1, 'sample_size': 99},
        {'time': 2, 'visual_acuity': 69, 'std_error': 1.2, 'sample_size': 98},
    ],
    'duration_years': 5
}

try:
    from streamlit_app.simulation_runner import generate_va_over_time_thumbnail
    fig = generate_va_over_time_thumbnail(results)
    print("✓ Thumbnail generation successful")
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()