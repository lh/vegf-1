"""
Unit tests for the enhanced discontinuation manager.

This module contains tests for the EnhancedDiscontinuationManager class, verifying that
it correctly implements the enhanced discontinuation model with multiple discontinuation types,
time-dependent recurrence probabilities, and clinician variation.
"""

import unittest
import sys
import os
from datetime import datetime, timedelta
import numpy as np
from unittest.mock import patch, MagicMock

# Add the parent directory to the path so we can import the simulation modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from simulation.enhanced_discontinuation_manager import EnhancedDiscontinuationManager
from simulation.clinician import Clinician

class TestEnhancedDiscontinuationManager(unittest.TestCase):
    """Test cases for the EnhancedDiscontinuationManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a sample configuration for testing
        self.config = {
            "discontinuation": {
                "enabled": True,
                "criteria": {
                    "stable_max_interval": {
                        "consecutive_visits": 3,
                        "probability": 0.2,
                        "interval_weeks": 16
                    },
                    "random_administrative": {
                        "annual_probability": 0.05
                    },
                    "treatment_duration": {
                        "threshold_weeks": 52,
                        "probability": 0.1
                    },
                    "premature": {
                        "min_interval_weeks": 8,
                        "probability_factor": 2.0
                    }
                },
                "monitoring": {
                    "planned": {
                        "follow_up_schedule": [12, 24, 36]
                    },
                    "unplanned": {
                        "follow_up_schedule": [8, 16, 24]
                    },
                    "recurrence_detection_probability": 0.87
                },
                "recurrence": {
                    "planned": {
                        "base_annual_rate": 0.13,
                        "cumulative_rates": {
                            "year_1": 0.13,
                            "year_3": 0.40,
                            "year_5": 0.65
                        }
                    },
                    "premature": {
                        "base_annual_rate": 0.53,
                        "cumulative_rates": {
                            "year_1": 0.53,
                            "year_3": 0.85,
                            "year_5": 0.95
                        }
                    },
                    "risk_modifiers": {
                        "with_PED": 1.54,
                        "without_PED": 1.0
                    }
                },
                "retreatment": {
                    "eligibility_criteria": {
                        "detected_fluid": True,
                        "vision_loss_letters": 5
                    },
                    "probability": 0.95
                }
            }
        }
        
        # Create a discontinuation manager
        self.manager = EnhancedDiscontinuationManager(self.config)
        
        # Create a sample patient state
        self.patient_state = {
            "disease_activity": {
                "fluid_detected": False,
                "consecutive_stable_visits": 3,
                "max_interval_reached": True,
                "current_interval": 16
            },
            "treatment_status": {
                "active": True,
                "recurrence_detected": False,
                "discontinuation_date": None,
                "cessation_type": None
            },
            "disease_characteristics": {
                "has_PED": False
            }
        }
        
        # Create a sample clinician
        self.clinician = Clinician("adherent", {
            "protocol_adherence_rate": 0.95,
            "characteristics": {
                "risk_tolerance": "low",
                "conservative_retreatment": True
            }
        })
        
        # Set the current time
        self.current_time = datetime(2025, 1, 1)
        self.treatment_start_time = self.current_time - timedelta(weeks=52)
    
    def test_initialization(self):
        """Test that the manager initializes correctly."""
        self.assertTrue(self.manager.enabled)
        self.assertEqual(self.manager.stats["premature_discontinuations"], 0)
        self.assertEqual(len(self.manager.stats["retreatments_by_type"]), 4)
    
    def test_evaluate_discontinuation_stable_max_interval(self):
        """Test discontinuation evaluation for stable max interval."""
        # Force discontinuation for this test
        with patch.object(np.random, 'random', return_value=0.1):  # Return a value less than probability (0.2)
            # Call the method
            should_discontinue, reason, probability, cessation_type = self.manager.evaluate_discontinuation(
                patient_state=self.patient_state,
                current_time=self.current_time,
                treatment_start_time=self.treatment_start_time
            )
            
            # Check the result
            self.assertTrue(should_discontinue)
            self.assertEqual(reason, "stable_max_interval")
            self.assertEqual(cessation_type, "stable_max_interval")
            self.assertAlmostEqual(probability, 0.2)
    
    def test_evaluate_discontinuation_with_clinician(self):
        """Test discontinuation evaluation with clinician influence."""
        # Create a mock clinician that always follows protocol
        mock_clinician = MagicMock()
        mock_clinician.profile_name = "adherent"
        mock_clinician.follows_protocol.return_value = True
        mock_clinician.evaluate_discontinuation.return_value = (True, 0.2)
        
        # Force discontinuation for this test
        with patch.object(np.random, 'random', return_value=0.1):
            # Call the method with the mock clinician
            should_discontinue, reason, probability, cessation_type = self.manager.evaluate_discontinuation(
                patient_state=self.patient_state,
                current_time=self.current_time,
                treatment_start_time=self.treatment_start_time,
                clinician=mock_clinician
            )
            
            # Check the result - the adherent clinician should follow protocol
            self.assertTrue(should_discontinue)
            self.assertEqual(reason, "stable_max_interval")
            self.assertEqual(cessation_type, "stable_max_interval")
            self.assertAlmostEqual(probability, 0.2)
        
        # Create a non-adherent clinician
        non_adherent_clinician = Clinician("non_adherent", {
            "protocol_adherence_rate": 0.5,
            "characteristics": {
                "risk_tolerance": "high",
                "conservative_retreatment": False
            }
        })
        
        # Set a different seed to get a different result
        np.random.seed(12345)
        
        # Call the method with the non-adherent clinician
        should_discontinue, reason, probability, cessation_type = self.manager.evaluate_discontinuation(
            patient_state=self.patient_state,
            current_time=self.current_time,
            treatment_start_time=self.treatment_start_time,
            clinician=non_adherent_clinician
        )
        
        # Check the result - with this seed, the non-adherent clinician might override
        # The exact result depends on the random seed, so we'll just check that it's valid
        self.assertIn(cessation_type, ["stable_max_interval", "premature", ""])
    
    def test_schedule_monitoring(self):
        """Test scheduling monitoring visits."""
        # Schedule monitoring for stable_max_interval
        monitoring_events = self.manager.schedule_monitoring(
            discontinuation_time=self.current_time,
            cessation_type="stable_max_interval"
        )
        
        # Check the result
        self.assertEqual(len(monitoring_events), 3)
        self.assertEqual(monitoring_events[0]["time"], self.current_time + timedelta(weeks=12))
        self.assertEqual(monitoring_events[1]["time"], self.current_time + timedelta(weeks=24))
        self.assertEqual(monitoring_events[2]["time"], self.current_time + timedelta(weeks=36))
        
        # Schedule monitoring for premature
        monitoring_events = self.manager.schedule_monitoring(
            discontinuation_time=self.current_time,
            cessation_type="premature"
        )
        
        # Check the result - should use unplanned schedule
        self.assertEqual(len(monitoring_events), 3)
        self.assertEqual(monitoring_events[0]["time"], self.current_time + timedelta(weeks=8))
        self.assertEqual(monitoring_events[1]["time"], self.current_time + timedelta(weeks=16))
        self.assertEqual(monitoring_events[2]["time"], self.current_time + timedelta(weeks=24))
    
    def test_calculate_recurrence_probability(self):
        """Test calculating recurrence probability."""
        # Calculate for stable_max_interval at 6 months
        probability = self.manager.calculate_recurrence_probability(
            weeks_since_discontinuation=26,
            cessation_type="stable_max_interval",
            has_PED=False
        )
        
        # Check the result - should be about half of the year 1 rate
        self.assertAlmostEqual(probability, 0.13 * 0.5, delta=0.01)
        
        # Calculate for premature at 6 months
        probability = self.manager.calculate_recurrence_probability(
            weeks_since_discontinuation=26,
            cessation_type="premature",
            has_PED=False
        )
        
        # Check the result - should be about half of the year 1 rate
        self.assertAlmostEqual(probability, 0.53 * 0.5, delta=0.01)
        
        # Calculate for stable_max_interval at 6 months with PED
        probability = self.manager.calculate_recurrence_probability(
            weeks_since_discontinuation=26,
            cessation_type="stable_max_interval",
            has_PED=True
        )
        
        # Check the result - should be about half of the year 1 rate times the PED modifier
        self.assertAlmostEqual(probability, 0.13 * 0.5 * 1.54, delta=0.01)
    
    def test_process_monitoring_visit(self):
        """Test processing a monitoring visit."""
        # Reset the stats before the test
        self.manager.stats["retreatments"] = 0
        self.manager.stats["retreatments_by_type"]["stable_max_interval"] = 0
        
        # Set up a patient state with a discontinuation date
        patient_state = self.patient_state.copy()
        patient_state["treatment_status"] = {
            "active": False,
            "recurrence_detected": False,
            "discontinuation_date": self.current_time - timedelta(weeks=26),
            "cessation_type": "stable_max_interval"
        }
        
        # Force recurrence and retreatment for this test
        with patch.object(self.manager, 'calculate_recurrence_probability', return_value=1.0), \
             patch.object(np.random, 'random', return_value=0.1), \
             patch.object(self.manager, 'evaluate_retreatment', return_value=(True, 0.95)):
            # Process a monitoring visit
            retreatment, updated_state = self.manager.process_monitoring_visit(
                patient_state=patient_state,
                actions=["vision_test", "oct_scan"]
            )
            
            # Check the result - recurrence should be detected and retreatment recommended
            self.assertTrue(retreatment)
            self.assertTrue(updated_state["treatment_status"]["active"])
            self.assertTrue(updated_state["treatment_status"]["recurrence_detected"])
            
            # Check that the statistics were updated
            self.assertEqual(self.manager.stats["retreatments"], 1)
            self.assertEqual(self.manager.stats["retreatments_by_type"]["stable_max_interval"], 1)
    
    def test_get_statistics(self):
        """Test getting statistics."""
        # Add some discontinuations and retreatments
        self.manager.stats["stable_max_interval_discontinuations"] = 10
        self.manager.stats["premature_discontinuations"] = 5
        self.manager.stats["total_discontinuations"] = 15
        self.manager.stats["retreatments"] = 6
        self.manager.stats["retreatments_by_type"]["stable_max_interval"] = 4
        self.manager.stats["retreatments_by_type"]["premature"] = 2
        
        # Get statistics
        stats = self.manager.get_statistics()
        
        # Check the result
        self.assertEqual(stats["stable_max_interval_discontinuations"], 10)
        self.assertEqual(stats["premature_discontinuations"], 5)
        self.assertEqual(stats["total_discontinuations"], 15)
        self.assertEqual(stats["retreatments"], 6)
        self.assertEqual(stats["retreatment_rate"], 6/15)
        self.assertEqual(stats["retreatment_rates_by_type"]["stable_max_interval"], 4/10)
        self.assertEqual(stats["retreatment_rates_by_type"]["premature"], 2/5)

if __name__ == '__main__':
    unittest.main()
