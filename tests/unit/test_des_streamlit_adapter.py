"""
Unit tests for the DES to Streamlit adapter.

These tests verify that the DES simulation results with enhanced discontinuation
are correctly transformed into the format expected by the Streamlit dashboard.
"""

import unittest
import sys
import os
from datetime import datetime
from typing import Dict, Any

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from simulation.des_streamlit_adapter import (
    adapt_des_for_streamlit,
    enhance_patient_histories,
    format_discontinuation_counts
)

class DESStreamlitAdapterTest(unittest.TestCase):
    """Test cases for the DES to Streamlit adapter."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create sample DES results for testing
        self.sample_des_results = {
            "simulation_type": "DES",
            "population_size": 100,
            "duration_years": 5,
            "statistics": {
                "discontinuation_stats": {
                    "stable_max_interval_discontinuations": 30,
                    "random_administrative_discontinuations": 10,
                    "treatment_duration_discontinuations": 15,
                    "premature_discontinuations": 5,
                    "total_discontinuations": 60
                },
                "retreatment_stats": {
                    "total_retreatments": 25,
                    "retreatments_by_type": {
                        "stable_max_interval": 15,
                        "random_administrative": 2,
                        "treatment_duration": 5,
                        "premature": 3
                    }
                }
            },
            "patient_histories": {
                "PATIENT001": [
                    # First regular visit
                    {
                        "date": datetime(2025, 1, 1),
                        "actions": ["vision_test", "oct_scan", "injection"],
                        "type": "regular_visit",
                        "treatment_status": {
                            "active": True
                        }
                    },
                    # Discontinuation visit
                    {
                        "date": datetime(2025, 2, 1),
                        "actions": ["vision_test", "oct_scan", "injection"],
                        "type": "regular_visit",
                        "treatment_status": {
                            "active": False,
                            "cessation_type": "stable_max_interval"
                        }
                    },
                    # Monitoring visit
                    {
                        "date": datetime(2025, 5, 1),
                        "actions": ["vision_test", "oct_scan"],
                        "type": "monitoring_visit",
                        "is_monitoring": True,
                        "treatment_status": {
                            "active": False,
                            "cessation_type": "stable_max_interval"
                        }
                    },
                    # Retreatment visit
                    {
                        "date": datetime(2025, 8, 1),
                        "actions": ["vision_test", "oct_scan", "injection"],
                        "type": "regular_visit",
                        "treatment_status": {
                            "active": True
                        }
                    }
                ]
            }
        }
    
    def test_adapt_des_for_streamlit(self):
        """Test that DES results are correctly adapted for Streamlit."""
        # Adapt DES results
        adapted_results = adapt_des_for_streamlit(self.sample_des_results)
        
        # Check core properties
        self.assertEqual(adapted_results["simulation_type"], "DES")
        self.assertEqual(adapted_results["population_size"], 100)
        self.assertEqual(adapted_results["duration_years"], 5)
        
        # Check discontinuation counts
        self.assertIn("discontinuation_counts", adapted_results)
        self.assertEqual(adapted_results["discontinuation_counts"]["Planned"], 30)
        self.assertEqual(adapted_results["discontinuation_counts"]["Administrative"], 10)
        self.assertEqual(adapted_results["discontinuation_counts"]["Not Renewed"], 15)
        self.assertEqual(adapted_results["discontinuation_counts"]["Premature"], 5)
        
        # Check recurrence data
        self.assertIn("recurrences", adapted_results)
        self.assertEqual(adapted_results["recurrences"]["total"], 25)
        self.assertEqual(len(adapted_results["recurrences"]["by_type"]), 4)
    
    def test_enhance_patient_histories(self):
        """Test patient history enhancement."""
        # Get patient histories from sample data
        patient_histories = self.sample_des_results["patient_histories"]
        
        # Need to modify third visit for test to be consistent
        patient_histories["PATIENT001"][2]["treatment_status"] = {
            "active": False,
            "cessation_type": "stable_max_interval"
        }
        
        # Enhance patient histories
        enhanced = enhance_patient_histories(patient_histories)
        
        # Check enhanced histories
        self.assertIn("PATIENT001", enhanced)
        visits = enhanced["PATIENT001"]
        
        # Check first visit (regular)
        self.assertFalse(visits[0]["is_discontinuation_visit"])
        self.assertFalse(visits[0]["is_retreatment"])
        
        # Check second visit (discontinuation)
        self.assertTrue(visits[1]["is_discontinuation_visit"])
        self.assertEqual(visits[1]["discontinuation_reason"], "stable_max_interval")
        
        # Check third visit (monitoring) - should have is_discontinuation_visit=False
        self.assertEqual(visits[2]["type"], "monitoring_visit")  # Verify it's a monitoring visit
        self.assertFalse(visits[2]["is_retreatment"])
        
        # Check fourth visit (retreatment)
        self.assertFalse(visits[3]["is_discontinuation_visit"])
        self.assertTrue(visits[3]["is_retreatment"])
        self.assertEqual(visits[3]["retreatment_reason"], "stable_max_interval")
    
    def test_format_discontinuation_counts(self):
        """Test discontinuation count formatting."""
        # Format counts from sample data
        raw_stats = self.sample_des_results["statistics"]["discontinuation_stats"]
        formatted = format_discontinuation_counts(raw_stats)
        
        # Check formatted counts
        self.assertEqual(formatted["Planned"], 30)
        self.assertEqual(formatted["Administrative"], 10)
        self.assertEqual(formatted["Not Renewed"], 15)
        self.assertEqual(formatted["Premature"], 5)
        
        # Test with alternative key format
        alternative_stats = {
            "stable_max_interval": 25,
            "random_administrative": 15,
            "treatment_duration": 10,
            "premature": 8
        }
        alt_formatted = format_discontinuation_counts(alternative_stats)
        
        # Check formatted counts with alternative keys
        self.assertEqual(alt_formatted["Planned"], 25)
        self.assertEqual(alt_formatted["Administrative"], 15)
        self.assertEqual(alt_formatted["Not Renewed"], 10)
        self.assertEqual(alt_formatted["Premature"], 8)

if __name__ == "__main__":
    unittest.main()