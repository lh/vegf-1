"""Unit tests for simulation_runner module"""
import unittest
from datetime import datetime, timedelta
import pandas as pd
from unittest.mock import Mock, patch

# Import with patched DEBUG_MODE
import streamlit_app.simulation_runner as sim_runner
sim_runner.DEBUG_MODE = False  # Disable debug for tests

from streamlit_app.simulation_runner import process_simulation_results
from streamlit_app.data_normalizer import DataNormalizer


class TestSimulationRunner(unittest.TestCase):
    """Test suite for simulation_runner functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.base_date = datetime(2023, 1, 1)
        
        # Create test patient data with datetime objects
        self.patient_histories = {
            "PATIENT001": [
                {
                    "date": self.base_date,
                    "vision": 75,
                    "actions": ["vision_test"]
                },
                {
                    "date": self.base_date + timedelta(days=30),
                    "vision": 76,
                    "actions": ["vision_test", "injection"]
                },
                {
                    "date": self.base_date + timedelta(days=60),
                    "vision": 77,
                    "actions": ["vision_test"]
                }
            ]
        }
        
        # Test parameters
        self.params = {
            "simulation_type": "abs",
            "population_size": 100,
            "duration_years": 5,
            "enable_clinician_variation": True,
            "planned_discontinue_prob": 0.1,
            "admin_discontinue_prob": 0.05
        }
        
        # Mock simulation object
        self.mock_sim = Mock()
        self.mock_sim.discontinuation_manager = Mock()
        self.mock_sim.discontinuation_manager.stats = {
            "discontinuations_by_reason": {},
            "total_discontinuations": 0
        }
        # Make sure the Mock doesn't throw errors for 'in' checks
        self.mock_sim.stats = {}
        
    def test_process_simulation_results_normalizes_data(self):
        """Test that process_simulation_results normalizes patient data"""
        with patch('streamlit_app.simulation_runner.DataNormalizer.normalize_patient_histories') as mock_normalize:
            # Set up the mock to return normalized data
            mock_normalize.return_value = self.patient_histories
            
            # Call the function
            process_simulation_results(self.mock_sim, self.patient_histories, self.params)
            
            # Verify normalization was called
            mock_normalize.assert_called_once_with(self.patient_histories)
            
    def test_date_calculations_with_normalized_data(self):
        """Test that date calculations work correctly with normalized datetime objects"""
        # Pre-normalize the data
        normalized_data = DataNormalizer.normalize_patient_histories(self.patient_histories)
        
        # Process the results
        results = process_simulation_results(self.mock_sim, normalized_data, self.params)
        
        # Check that visual acuity data was extracted correctly
        self.assertIn("visual_acuity_outcomes", results)
        va_outcomes = results["visual_acuity_outcomes"]
        
        # Verify correct time calculations
        expected_times = [0, 0.98, 1.97]  # Approximate months
        
        if "mean_va_by_time" in va_outcomes:
            times = va_outcomes["mean_va_by_time"]["time"]
            for i, expected_time in enumerate(expected_times):
                self.assertAlmostEqual(times[i], expected_time, places=1)
                
    def test_mixed_date_types_in_input(self):
        """Test handling of mixed date types (before normalization)"""
        # Create patient data with mixed date types
        mixed_data = {
            "PATIENT001": [
                {"date": "2023-01-01", "vision": 75},  # String
                {"date": self.base_date + timedelta(days=30), "vision": 76},  # datetime
                {"date": pd.Timestamp("2023-03-01"), "vision": 77}  # Timestamp
            ]
        }
        
        # Process should normalize automatically
        results = process_simulation_results(self.mock_sim, mixed_data, self.params)
        
        # Should complete without errors
        self.assertIsInstance(results, dict)
        self.assertIn("patient_count", results)
        
    def test_missing_date_field_raises_error(self):
        """Test that missing date fields raise appropriate errors"""
        # Create patient data with missing date
        invalid_data = {
            "PATIENT001": [
                {"vision": 75}  # Missing date field
            ]
        }
        
        # Should raise ValueError
        with self.assertRaises(ValueError) as context:
            process_simulation_results(self.mock_sim, invalid_data, self.params)
            
        self.assertIn("missing required 'date' field", str(context.exception))
        
    def test_visual_acuity_time_series_extraction(self):
        """Test extraction of visual acuity time series"""
        # Create more comprehensive test data
        patient_data = {
            "PATIENT001": [
                {"date": self.base_date, "vision": 70},
                {"date": self.base_date + timedelta(days=30), "vision": 72},
                {"date": self.base_date + timedelta(days=60), "vision": 74},
                {"date": self.base_date + timedelta(days=90), "vision": 73}
            ],
            "PATIENT002": [
                {"date": self.base_date, "vision": 65},
                {"date": self.base_date + timedelta(days=30), "vision": 68},
                {"date": self.base_date + timedelta(days=60), "vision": 69}
            ]
        }
        
        # Process the data
        results = process_simulation_results(self.mock_sim, patient_data, self.params)
        
        # Check visual acuity outcomes
        va_outcomes = results.get("visual_acuity_outcomes", {})
        
        # Verify that data was extracted for all patients
        if "mean_va_by_time" in va_outcomes:
            # Should have data points for each time across patients
            self.assertGreater(len(va_outcomes["mean_va_by_time"]["time"]), 0)
            self.assertGreater(len(va_outcomes["mean_va_by_time"]["visual_acuity"]), 0)
            
    def test_baseline_time_establishment(self):
        """Test that baseline time is correctly established from first visit"""
        # Create data where first visit establishes baseline
        patient_data = {
            "PATIENT001": [
                {"date": self.base_date + timedelta(days=10), "vision": 70},  # Baseline
                {"date": self.base_date + timedelta(days=40), "vision": 72},  # 30 days later
                {"date": self.base_date + timedelta(days=70), "vision": 74}   # 60 days later
            ]
        }
        
        # Process the data
        results = process_simulation_results(self.mock_sim, patient_data, self.params)
        
        # Visual acuity data should be relative to first visit, not absolute dates
        va_outcomes = results.get("visual_acuity_outcomes", {})
        
        if "mean_va_by_time" in va_outcomes:
            times = va_outcomes["mean_va_by_time"]["time"]
            # First visit should be at time 0
            self.assertEqual(times[0], 0)
            # Subsequent visits should be relative to baseline
            self.assertAlmostEqual(times[1], 1.0, places=1)  # ~30 days
            self.assertAlmostEqual(times[2], 2.0, places=1)  # ~60 days


if __name__ == '__main__':
    unittest.main()