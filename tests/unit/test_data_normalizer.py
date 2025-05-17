"""Unit tests for DataNormalizer class"""
import unittest
from datetime import datetime
import pandas as pd
from streamlit_app.data_normalizer import DataNormalizer


class TestDataNormalizer(unittest.TestCase):
    """Test suite for DataNormalizer functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_date_str = "2023-01-01 02:00:00"
        self.test_date_datetime = datetime(2023, 1, 1, 2, 0)
        self.test_date_timestamp = pd.Timestamp("2023-01-01 02:00:00")
        
    def test_to_datetime_string_input(self):
        """Test conversion of string dates to datetime"""
        result = DataNormalizer._to_datetime(self.test_date_str)
        self.assertIsInstance(result, datetime)
        self.assertEqual(result, self.test_date_datetime)
        
    def test_to_datetime_datetime_input(self):
        """Test that datetime objects pass through unchanged"""
        result = DataNormalizer._to_datetime(self.test_date_datetime)
        self.assertIsInstance(result, datetime)
        self.assertEqual(result, self.test_date_datetime)
        
    def test_to_datetime_timestamp_input(self):
        """Test conversion of pandas Timestamp to datetime"""
        result = DataNormalizer._to_datetime(self.test_date_timestamp)
        self.assertIsInstance(result, datetime)
        self.assertEqual(result, self.test_date_datetime)
        
    def test_to_datetime_invalid_type(self):
        """Test that invalid types raise ValueError"""
        with self.assertRaises(ValueError) as context:
            DataNormalizer._to_datetime(["not", "a", "date"])
        self.assertIn("Unsupported date type", str(context.exception))
        
    def test_normalize_visit_list(self):
        """Test normalization of a list of visits"""
        visits = [
            {"date": self.test_date_str, "vision": 75},
            {"date": self.test_date_datetime, "vision": 76},
            {"date": self.test_date_timestamp, "vision": 77}
        ]
        
        normalized = DataNormalizer._normalize_visit_list(visits, "TEST_PATIENT")
        
        # All dates should be datetime objects
        for visit in normalized:
            self.assertIsInstance(visit['date'], datetime)
            
    def test_normalize_visit_list_missing_date(self):
        """Test that visits without dates raise ValueError"""
        visits = [
            {"vision": 75}  # Missing date field
        ]
        
        with self.assertRaises(ValueError) as context:
            DataNormalizer._normalize_visit_list(visits, "TEST_PATIENT")
        self.assertIn("missing required 'date' field", str(context.exception))
        
    def test_normalize_patient_histories_list_structure(self):
        """Test normalization of patient data with list structure"""
        patient_data = {
            "PATIENT001": [
                {"date": self.test_date_str, "vision": 75},
                {"date": self.test_date_datetime, "vision": 76}
            ]
        }
        
        normalized = DataNormalizer.normalize_patient_histories(patient_data)
        
        self.assertIn("PATIENT001", normalized)
        for visit in normalized["PATIENT001"]:
            self.assertIsInstance(visit['date'], datetime)
            
    def test_normalize_patient_histories_dict_structure(self):
        """Test normalization of patient data with dict structure"""
        patient_data = {
            "PATIENT002": {
                "visit_history": [
                    {"date": self.test_date_str, "vision": 70},
                    {"date": self.test_date_datetime, "vision": 71}
                ]
            }
        }
        
        normalized = DataNormalizer.normalize_patient_histories(patient_data)
        
        self.assertIn("PATIENT002", normalized)
        self.assertIn("visit_history", normalized["PATIENT002"])
        for visit in normalized["PATIENT002"]["visit_history"]:
            self.assertIsInstance(visit['date'], datetime)
            
    def test_normalize_patient_histories_mixed_structures(self):
        """Test normalization with mixed patient data structures"""
        patient_data = {
            "PATIENT001": [
                {"date": self.test_date_str, "vision": 75}
            ],
            "PATIENT002": {
                "visit_history": [
                    {"date": self.test_date_datetime, "vision": 70}
                ]
            },
            "PATIENT003": "unknown_structure"  # Should pass through
        }
        
        normalized = DataNormalizer.normalize_patient_histories(patient_data)
        
        # Check list structure
        self.assertIsInstance(normalized["PATIENT001"][0]['date'], datetime)
        
        # Check dict structure
        self.assertIsInstance(
            normalized["PATIENT002"]["visit_history"][0]['date'], 
            datetime
        )
        
        # Check passthrough
        self.assertEqual(normalized["PATIENT003"], "unknown_structure")
        
    def test_validate_normalized_data_valid(self):
        """Test validation of properly normalized data"""
        normalized_data = {
            "PATIENT001": [
                {"date": datetime.now(), "vision": 75}
            ]
        }
        
        # Should not raise an exception
        result = DataNormalizer.validate_normalized_data(normalized_data)
        self.assertTrue(result)
        
    def test_validate_normalized_data_invalid(self):
        """Test validation catches non-datetime dates"""
        invalid_data = {
            "PATIENT001": [
                {"date": "2023-01-01", "vision": 75}  # String, not datetime
            ]
        }
        
        with self.assertRaises(ValueError) as context:
            DataNormalizer.validate_normalized_data(invalid_data)
        self.assertIn("has non-datetime date", str(context.exception))
        
    def test_date_format_edge_cases(self):
        """Test handling of various date format edge cases"""
        test_cases = [
            "2023-01-01",  # Date only
            "2023-01-01T00:00:00",  # ISO format
            "01/01/2023",  # US format
            "2023-01-01 15:30:45.123456",  # With microseconds
        ]
        
        for date_str in test_cases:
            result = DataNormalizer._to_datetime(date_str, f"test case {date_str}")
            self.assertIsInstance(result, datetime)
            
    def test_numeric_date_conversion(self):
        """Test conversion of numeric timestamps"""
        timestamp = 1672531200  # 2023-01-01 00:00:00 UTC
        result = DataNormalizer._to_datetime(timestamp)
        self.assertIsInstance(result, datetime)
        self.assertEqual(result.year, 2023)
        self.assertEqual(result.month, 1)
        self.assertEqual(result.day, 1)


if __name__ == '__main__':
    unittest.main()