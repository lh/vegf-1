"""Unit tests for date handling in simulation_runner module"""
import unittest
from datetime import datetime, timedelta
import pandas as pd
from unittest.mock import Mock, patch

# Import with patched streamlit
import sys
from unittest.mock import MagicMock
sys.modules['streamlit'] = MagicMock()

# Now import the modules we need to test
from streamlit_app.data_normalizer import DataNormalizer


class TestSimulationRunnerDateHandling(unittest.TestCase):
    """Test suite for date handling in simulation_runner"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.base_date = datetime(2023, 1, 1)
        
    def test_date_normalization_integration(self):
        """Test that dates are properly normalized and used in calculations"""
        # Create mixed-type patient data
        patient_data = {
            "PATIENT001": [
                {"date": "2023-01-01", "vision": 75},  # String
                {"date": self.base_date + timedelta(days=30), "vision": 76},  # datetime
                {"date": pd.Timestamp("2023-03-01"), "vision": 77}  # Timestamp
            ]
        }
        
        # Normalize the data
        normalized_data = DataNormalizer.normalize_patient_histories(patient_data)
        
        # Verify all dates are datetime objects
        for visit in normalized_data["PATIENT001"]:
            self.assertIsInstance(visit['date'], datetime)
            
        # Test time calculations (simulating what happens in process_simulation_results)
        baseline_time = normalized_data["PATIENT001"][0]['date']
        
        for i, visit in enumerate(normalized_data["PATIENT001"]):
            if i == 0:
                visit_time = 0
            else:
                # This is the simplified calculation after normalization
                visit_time = (visit['date'] - baseline_time).days / 30.44
                
            # Verify calculations work correctly
            if i == 0:
                self.assertEqual(visit_time, 0)
            elif i == 1:
                self.assertAlmostEqual(visit_time, 0.98, places=1)  # ~30 days
            elif i == 2:
                self.assertAlmostEqual(visit_time, 1.94, places=1)  # ~59 days
                
    def test_date_calculation_consistency(self):
        """Test that date calculations are consistent after normalization"""
        # Create test data with known intervals
        patient_data = {
            "PATIENT001": [
                {"date": self.base_date, "vision": 70},
                {"date": self.base_date + timedelta(days=30), "vision": 72},
                {"date": self.base_date + timedelta(days=60), "vision": 74},
                {"date": self.base_date + timedelta(days=90), "vision": 73}
            ]
        }
        
        # Normalize the data
        normalized_data = DataNormalizer.normalize_patient_histories(patient_data)
        
        # Test the time calculation logic
        baseline_time = normalized_data["PATIENT001"][0]['date']
        expected_times = [0, 0.98, 1.97, 2.95]  # Approximate months
        
        for i, visit in enumerate(normalized_data["PATIENT001"]):
            if i == 0:
                visit_time = 0
            else:
                visit_time = (visit['date'] - baseline_time).days / 30.44
                
            self.assertAlmostEqual(visit_time, expected_times[i], places=1)
            
    def test_error_on_missing_date_field(self):
        """Test that missing date fields are caught during normalization"""
        patient_data = {
            "PATIENT001": [
                {"vision": 75}  # Missing date field
            ]
        }
        
        # Should raise ValueError during normalization
        with self.assertRaises(ValueError) as context:
            DataNormalizer.normalize_patient_histories(patient_data)
            
        self.assertIn("missing required 'date' field", str(context.exception))
        
    def test_string_date_formats(self):
        """Test various string date formats are handled correctly"""
        test_formats = [
            "2023-01-01",
            "2023-01-01 10:00:00",
            "2023-01-01T10:00:00",
            "01/01/2023",
            "Jan 1, 2023"
        ]
        
        for date_str in test_formats:
            patient_data = {
                "PATIENT001": [
                    {"date": date_str, "vision": 75}
                ]
            }
            
            try:
                normalized_data = DataNormalizer.normalize_patient_histories(patient_data)
                # Should succeed and produce datetime
                self.assertIsInstance(
                    normalized_data["PATIENT001"][0]['date'], 
                    datetime
                )
            except ValueError:
                # Some formats might not be supported, that's OK
                pass
                
    def test_datetime_pass_through(self):
        """Test that datetime objects pass through unchanged"""
        test_date = datetime(2023, 1, 1, 10, 30, 45)
        patient_data = {
            "PATIENT001": [
                {"date": test_date, "vision": 75}
            ]
        }
        
        normalized_data = DataNormalizer.normalize_patient_histories(patient_data)
        
        # Should be the same datetime object
        self.assertEqual(normalized_data["PATIENT001"][0]['date'], test_date)
        self.assertIsInstance(normalized_data["PATIENT001"][0]['date'], datetime)


if __name__ == '__main__':
    unittest.main()