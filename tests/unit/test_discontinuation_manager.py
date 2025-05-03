"""
Unit tests for the DiscontinuationManager class.

This module contains tests for the discontinuation manager functionality,
including discontinuation criteria evaluation, monitoring scheduling,
and retreatment evaluation.
"""

import unittest
from datetime import datetime, timedelta
from simulation.discontinuation_manager import DiscontinuationManager

class TestDiscontinuationManager(unittest.TestCase):
    """Test cases for the DiscontinuationManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a test configuration
        self.config = {
            "discontinuation": {
                "enabled": True,
                "criteria": {
                    "stable_max_interval": {
                        "consecutive_visits": 3,
                        "probability": 1.0  # Always discontinue for testing
                    },
                    "random_administrative": {
                        "annual_probability": 0.0  # Disable for testing
                    },
                    "treatment_duration": {
                        "threshold_weeks": 52,
                        "probability": 1.0  # Always discontinue for testing
                    }
                },
                "monitoring": {
                    "follow_up_schedule": [12, 24, 36],
                    "recurrence_detection_probability": 1.0  # Always detect for testing
                },
                "retreatment": {
                    "eligibility_criteria": {
                        "detected_fluid": True
                    },
                    "probability": 1.0  # Always retreat for testing
                }
            }
        }
        
        # Create a discontinuation manager
        self.manager = DiscontinuationManager(self.config)
        
        # Create a test patient state
        self.patient_state = {
            "disease_activity": {
                "fluid_detected": False,
                "consecutive_stable_visits": 0,
                "max_interval_reached": False,
                "current_interval": 8
            },
            "treatment_status": {
                "active": True,
                "recurrence_detected": False,
                "weeks_since_discontinuation": 0
            }
        }
        
        # Set current time and treatment start time
        self.current_time = datetime(2023, 1, 1)
        self.treatment_start_time = datetime(2022, 1, 1)  # 1 year before current time
    
    def test_initialization(self):
        """Test initialization of the discontinuation manager."""
        self.assertTrue(self.manager.enabled)
        self.assertEqual(self.manager.stats["total_discontinuations"], 0)
    
    def test_evaluate_discontinuation_not_eligible(self):
        """Test that patients not meeting criteria are not discontinued."""
        # Disable treatment duration criterion for this test
        self.config["discontinuation"]["criteria"]["treatment_duration"]["probability"] = 0.0
        
        # Patient with 0 consecutive stable visits should not be discontinued
        should_discontinue, reason, probability = self.manager.evaluate_discontinuation(
            patient_state=self.patient_state,
            current_time=self.current_time,
            treatment_start_time=self.treatment_start_time
        )
        
        self.assertFalse(should_discontinue)
        self.assertEqual(reason, "")
        self.assertEqual(probability, 0.0)
    
    def test_evaluate_discontinuation_stable_max_interval(self):
        """Test discontinuation for patients with stable visits at max interval."""
        # Update patient state to meet stable_max_interval criteria
        self.patient_state["disease_activity"]["consecutive_stable_visits"] = 3
        self.patient_state["disease_activity"]["max_interval_reached"] = True
        
        should_discontinue, reason, probability = self.manager.evaluate_discontinuation(
            patient_state=self.patient_state,
            current_time=self.current_time,
            treatment_start_time=self.treatment_start_time
        )
        
        self.assertTrue(should_discontinue)
        self.assertEqual(reason, "stable_max_interval")
        self.assertEqual(probability, 1.0)
        self.assertEqual(self.manager.stats["stable_max_interval_discontinuations"], 1)
        self.assertEqual(self.manager.stats["total_discontinuations"], 1)
    
    def test_evaluate_discontinuation_treatment_duration(self):
        """Test discontinuation based on treatment duration."""
        # Reset patient state
        self.patient_state["disease_activity"]["consecutive_stable_visits"] = 0
        self.patient_state["disease_activity"]["max_interval_reached"] = False
        
        # Set treatment start time to meet duration criteria
        treatment_start_time = self.current_time - timedelta(weeks=53)  # Just over threshold
        
        should_discontinue, reason, probability = self.manager.evaluate_discontinuation(
            patient_state=self.patient_state,
            current_time=self.current_time,
            treatment_start_time=treatment_start_time
        )
        
        self.assertTrue(should_discontinue)
        self.assertEqual(reason, "treatment_duration")
        self.assertEqual(probability, 1.0)
        self.assertEqual(self.manager.stats["treatment_duration_discontinuations"], 1)
        self.assertEqual(self.manager.stats["total_discontinuations"], 1)
    
    def test_schedule_monitoring(self):
        """Test scheduling of monitoring visits."""
        monitoring_events = self.manager.schedule_monitoring(self.current_time)
        
        self.assertEqual(len(monitoring_events), 3)  # 3 follow-up visits
        
        # Check that visits are scheduled at the correct times
        expected_times = [
            self.current_time + timedelta(weeks=12),
            self.current_time + timedelta(weeks=24),
            self.current_time + timedelta(weeks=36)
        ]
        
        for i, event in enumerate(monitoring_events):
            self.assertEqual(event["time"], expected_times[i])
            self.assertEqual(event["type"], "monitoring_visit")
            self.assertIn("vision_test", event["actions"])
            self.assertIn("oct_scan", event["actions"])
            self.assertTrue(event["is_monitoring"])
    
    def test_process_monitoring_visit_no_fluid(self):
        """Test processing a monitoring visit with no fluid detected."""
        # Set patient as discontinued
        self.patient_state["treatment_status"]["active"] = False
        
        # No fluid detected
        self.patient_state["disease_activity"]["fluid_detected"] = False
        
        retreatment, updated_patient = self.manager.process_monitoring_visit(
            patient_state=self.patient_state,
            actions=["vision_test", "oct_scan"]
        )
        
        self.assertFalse(retreatment)
        self.assertFalse(updated_patient["treatment_status"]["active"])
    
    def test_process_monitoring_visit_with_fluid(self):
        """Test processing a monitoring visit with fluid detected."""
        # Set patient as discontinued
        self.patient_state["treatment_status"]["active"] = False
        
        # Fluid detected
        self.patient_state["disease_activity"]["fluid_detected"] = True
        
        retreatment, updated_patient = self.manager.process_monitoring_visit(
            patient_state=self.patient_state,
            actions=["vision_test", "oct_scan"]
        )
        
        self.assertTrue(retreatment)
        self.assertTrue(updated_patient["treatment_status"]["active"])
        self.assertTrue(updated_patient["treatment_status"]["recurrence_detected"])
        self.assertEqual(self.manager.stats["retreatments"], 1)
    
    def test_disabled_manager(self):
        """Test that a disabled manager does not discontinue patients."""
        # Create a disabled manager
        disabled_config = self.config.copy()
        disabled_config["discontinuation"]["enabled"] = False
        disabled_manager = DiscontinuationManager(disabled_config)
        
        # Update patient state to meet criteria
        self.patient_state["disease_activity"]["consecutive_stable_visits"] = 3
        self.patient_state["disease_activity"]["max_interval_reached"] = True
        
        should_discontinue, reason, probability = disabled_manager.evaluate_discontinuation(
            patient_state=self.patient_state,
            current_time=self.current_time,
            treatment_start_time=self.treatment_start_time
        )
        
        self.assertFalse(should_discontinue)
        self.assertEqual(reason, "")
        self.assertEqual(probability, 0.0)
        
        # Check that monitoring visits are not scheduled
        monitoring_events = disabled_manager.schedule_monitoring(self.current_time)
        self.assertEqual(len(monitoring_events), 0)

if __name__ == '__main__':
    unittest.main()
