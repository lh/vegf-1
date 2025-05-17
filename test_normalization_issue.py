"""
Test if the DataNormalizer is breaking patient histories.
"""

from datetime import datetime, timedelta
from streamlit_app.data_normalizer import DataNormalizer

# Create mock patient history similar to what simulation produces
mock_histories = {
    "patient_0": [
        {
            "time": datetime(2020, 1, 1),
            "time_weeks": 0,
            "treatment_status": {"active": True}
        },
        {
            "time": datetime(2020, 1, 29),
            "time_weeks": 4,
            "treatment_status": {"active": True}
        }
    ]
}

print("Original patient history:")
print(mock_histories["patient_0"][0])

try:
    normalized = DataNormalizer.normalize_patient_histories(mock_histories)
    print("\nNormalization succeeded")
    print("Normalized first visit:")
    print(normalized["patient_0"][0])
except Exception as e:
    print(f"\nNormalization failed: {e}")
    print("This explains why patient histories might be missing or corrupted")

# Test with the expected 'date' field
mock_histories_with_date = {
    "patient_0": [
        {
            "date": datetime(2020, 1, 1),
            "time_weeks": 0,
            "treatment_status": {"active": True}
        }
    ]
}

try:
    normalized = DataNormalizer.normalize_patient_histories(mock_histories_with_date)
    print("\nNormalization with 'date' field succeeded")
except Exception as e:
    print(f"\nNormalization with 'date' field failed: {e}")