#!/usr/bin/env python3
"""Test data normalization functionality"""
from datetime import datetime
import pandas as pd
from streamlit_app.data_normalizer import DataNormalizer

# Test data with mixed date types
test_data = {
    "PATIENT001": [
        {"date": "2023-01-01 02:00:00", "vision": 75},
        {"date": datetime(2023, 2, 1, 2, 0), "vision": 76},
        {"date": pd.Timestamp("2023-03-01 02:00:00"), "vision": 77}
    ],
    "PATIENT002": {
        "visit_history": [
            {"date": "2023-01-15", "vision": 70},
            {"date": datetime.now(), "vision": 71}
        ]
    }
}

print("Original data types:")
for pid, data in test_data.items():
    print(f"\n{pid}:")
    if isinstance(data, list):
        for i, visit in enumerate(data):
            print(f"  Visit {i}: date type = {type(visit['date'])}")
    elif isinstance(data, dict) and 'visit_history' in data:
        for i, visit in enumerate(data['visit_history']):
            print(f"  Visit {i}: date type = {type(visit['date'])}")

# Normalize the data
normalized_data = DataNormalizer.normalize_patient_histories(test_data)

print("\n\nNormalized data types:")
for pid, data in normalized_data.items():
    print(f"\n{pid}:")
    if isinstance(data, list):
        for i, visit in enumerate(data):
            print(f"  Visit {i}: date type = {type(visit['date'])}, value = {visit['date']}")
    elif isinstance(data, dict) and 'visit_history' in data:
        for i, visit in enumerate(data['visit_history']):
            print(f"  Visit {i}: date type = {type(visit['date'])}, value = {visit['date']}")

# Validate the normalization
try:
    DataNormalizer.validate_normalized_data(normalized_data)
    print("\n✓ Data validation passed!")
except ValueError as e:
    print(f"\n✗ Data validation failed: {e}")

# Test time calculation with normalized data
print("\n\nTime calculations:")
for pid, data in normalized_data.items():
    print(f"\n{pid}:")
    visits = data if isinstance(data, list) else data.get('visit_history', [])
    
    if visits:
        baseline = visits[0]['date']
        for i, visit in enumerate(visits):
            time_months = (visit['date'] - baseline).days / 30.44
            print(f"  Visit {i}: {time_months:.2f} months from baseline")