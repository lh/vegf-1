"""
Unit tests for streamgraph date handling in the streamgraph_patient_states module.
"""

import sys
import os
import unittest
import pandas as pd
import numpy as np
from datetime import datetime
import json

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import the module to test
from streamlit_app.streamgraph_patient_states import (
    extract_patient_states,
    aggregate_states_by_month,
    convert_timestamp_to_months
)

class TestStreamgraphDateHandling(unittest.TestCase):
    """Test date handling in the streamgraph_patient_states module."""
    
    def test_convert_timestamp_to_months(self):
        """Test conversion of different timestamp formats to months."""
        # Test start date
        start_date = pd.to_datetime("2023-01-01")
        
        # Test cases with different formats
        test_cases = [
            # Nanosecond timestamp (Jan 2024 = 12 months from start)
            {"timestamp": 1704067200000000000, "expected_months": 12},
            # String datetime
            {"timestamp": "2023-07-01", "expected_months": 6},
            # Datetime object
            {"timestamp": pd.to_datetime("2023-04-01"), "expected_months": 3}
        ]
        
        for tc in test_cases:
            months = convert_timestamp_to_months(tc["timestamp"], start_date)
            self.assertEqual(months, tc["expected_months"])
    
    def test_extract_patient_states(self):
        """Test extraction of patient states from visit data."""
        # Create test data
        test_data = {
            "P001": [
                {"date": "2023-01-01", "is_discontinuation_visit": False},
                {"date": "2023-07-01", "is_discontinuation_visit": True, 
                 "discontinuation_reason": "stable_max_interval"}
            ],
            "P002": [
                {"date": "2023-01-15", "is_discontinuation_visit": False},
                {"date": "2023-04-15", "is_discontinuation_visit": True,
                 "discontinuation_reason": "premature"}
            ]
        }
        
        # Extract states
        states_df = extract_patient_states(test_data)
        
        # Verify states
        self.assertEqual(len(states_df), 4)  # 2 patients x 2 visits each
        
        # Verify state transitions
        p001_states = states_df[states_df["patient_id"] == "P001"]["state"].tolist()
        p002_states = states_df[states_df["patient_id"] == "P002"]["state"].tolist()
        
        self.assertEqual(p001_states, ["active", "discontinued_stable_max_interval"])
        self.assertEqual(p002_states, ["active", "discontinued_premature"])
    
    def test_aggregate_states_with_string_dates(self):
        """Test aggregation with string dates."""
        # Create test dataframe with string dates
        test_df = pd.DataFrame([
            {"patient_id": "P001", "state": "active", "visit_time": "2023-01-01"},
            {"patient_id": "P001", "state": "discontinued_stable_max_interval", "visit_time": "2023-07-01"},
            {"patient_id": "P002", "state": "active", "visit_time": "2023-01-15"},
            {"patient_id": "P002", "state": "discontinued_premature", "visit_time": "2023-04-15"}
        ])
        
        # Aggregate by month
        monthly_df = aggregate_states_by_month(test_df, 12)
        
        # Verify monthly data
        self.assertGreater(len(monthly_df), 0)
        
        # Pivot for easier verification
        pivot_df = monthly_df.pivot(index="time_months", columns="state", values="count").fillna(0)
        
        # Check state counts at key months
        month_0 = pivot_df.loc[0].to_dict()
        self.assertEqual(month_0.get("active", 0), 2)
        
        month_6 = pivot_df.loc[6].to_dict() if 6 in pivot_df.index else {}
        self.assertEqual(month_6.get("discontinued_stable_max_interval", 0), 1)
        self.assertEqual(month_6.get("discontinued_premature", 0), 1)
        self.assertEqual(month_6.get("active", 0), 0)
    
    def test_aggregate_states_with_timestamp_dates(self):
        """Test aggregation with timestamp dates."""
        # Create test dataframe with nanosecond timestamp dates
        jan_1 = int(pd.to_datetime("2023-01-01").timestamp() * 1e9)
        jul_1 = int(pd.to_datetime("2023-07-01").timestamp() * 1e9)
        jan_15 = int(pd.to_datetime("2023-01-15").timestamp() * 1e9)
        apr_15 = int(pd.to_datetime("2023-04-15").timestamp() * 1e9)
        
        test_df = pd.DataFrame([
            {"patient_id": "P001", "state": "active", "visit_time": jan_1},
            {"patient_id": "P001", "state": "discontinued_stable_max_interval", "visit_time": jul_1},
            {"patient_id": "P002", "state": "active", "visit_time": jan_15},
            {"patient_id": "P002", "state": "discontinued_premature", "visit_time": apr_15}
        ])
        
        # Aggregate by month
        monthly_df = aggregate_states_by_month(test_df, 12)
        
        # Verify monthly data
        self.assertGreater(len(monthly_df), 0)

if __name__ == "__main__":
    unittest.main()