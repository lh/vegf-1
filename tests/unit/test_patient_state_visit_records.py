"""
Tests for patient visit records in the ABS simulation.

This module tests the structure and content of patient visit records to ensure
key fields required for visualization are correctly present and populated.
"""

import unittest
import sys
import os
from datetime import datetime, timedelta
import numpy as np
from unittest.mock import patch, MagicMock

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from simulation.patient_state import PatientState
from simulation.clinical_model import ClinicalModel

class MockClinicalModel:
    """Mock clinical model for testing."""
    
    def __init__(self):
        """Initialize with default parameters."""
        self.config = MagicMock()
        self.config.get_treatment_discontinuation_params.return_value = {
            "recurrence_probabilities": {
                "base_risk_per_year": 0.2
            },
            "symptom_detection": {
                "probability": 0.8,
                "detection_sensitivity": 0.9
            },
            "recurrence_impact": {
                "vision_loss_letters": 5.0
            }
        }
    
    def simulate_vision_change(self, patient_state):
        """Return a constant vision change and disease state."""
        if "disease_state" in patient_state:
            return 0.0, patient_state["disease_state"]
        return 0.0, "STABLE"
    
    def get_initial_vision(self):
        """Return a constant initial vision."""
        return 70.0

class PatientStateVisitRecordsTest(unittest.TestCase):
    """Test case for patient visit records structure."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a mock clinical model
        self.clinical_model = MockClinicalModel()
        
        # Create a patient state
        self.start_date = datetime(2025, 1, 1)
        self.patient_state = PatientState("TEST001", "treat_and_extend", 70.0, self.start_date)
    
    def test_initial_treatment_status(self):
        """Test the initial treatment status structure."""
        # Verify the structure of initial treatment status
        self.assertIn("treatment_status", self.patient_state.state)
        treatment_status = self.patient_state.state["treatment_status"]
        
        # Check all expected keys exist
        self.assertIn("active", treatment_status)
        self.assertIn("weeks_since_discontinuation", treatment_status)
        self.assertIn("monitoring_schedule", treatment_status)
        self.assertIn("recurrence_detected", treatment_status)
        self.assertIn("discontinuation_date", treatment_status)
        self.assertIn("reason_for_discontinuation", treatment_status)
        
        # Check initial values
        self.assertTrue(treatment_status["active"])
        self.assertEqual(treatment_status["weeks_since_discontinuation"], 0)
        self.assertEqual(treatment_status["monitoring_schedule"], 12)
        self.assertFalse(treatment_status["recurrence_detected"])
        self.assertIsNone(treatment_status["discontinuation_date"])
        self.assertIsNone(treatment_status["reason_for_discontinuation"])
    
    def test_visit_record_structure(self):
        """Test the structure of visit records."""
        # Process a visit
        visit_time = self.start_date + timedelta(days=7)
        actions = ["vision_test", "oct_scan", "injection"]
        self.patient_state.process_visit(visit_time, actions, self.clinical_model)
        
        # Verify the visit history contains at least one record
        visit_history = self.patient_state.visit_history
        self.assertGreaterEqual(len(visit_history), 1)
        
        # Get the latest visit record
        latest_visit = visit_history[-1]
        
        # Check all expected keys exist
        self.assertIn("date", latest_visit)
        self.assertIn("actions", latest_visit)
        self.assertIn("vision", latest_visit)
        self.assertIn("baseline_vision", latest_visit)
        self.assertIn("phase", latest_visit)
        self.assertIn("type", latest_visit)
        self.assertIn("disease_state", latest_visit)
        self.assertIn("treatment_status", latest_visit)
        
        # Check treatment_status structure in visit record
        treatment_status = latest_visit["treatment_status"]
        self.assertIn("active", treatment_status)
        self.assertIn("recurrence_detected", treatment_status)
        self.assertIn("weeks_since_discontinuation", treatment_status)
    
    def test_discontinuation_visit_recording(self):
        """Test recording of discontinuation visits."""
        # Process a regular visit first
        visit_time = self.start_date + timedelta(days=7)
        actions = ["vision_test", "oct_scan", "injection"]
        self.patient_state.process_visit(visit_time, actions, self.clinical_model)
        
        # Now process a discontinuation visit
        discontinuation_time = self.start_date + timedelta(days=30)
        discontinuation_actions = ["vision_test", "oct_scan", "discontinue_treatment"]
        self.patient_state.process_visit(discontinuation_time, discontinuation_actions, self.clinical_model)
        
        # Verify the visit history
        visit_history = self.patient_state.visit_history
        self.assertEqual(len(visit_history), 2)
        
        # Check the discontinuation visit record
        discontinuation_visit = visit_history[-1]
        
        # Verify discontinuation action was recorded
        self.assertIn("discontinue_treatment", discontinuation_visit["actions"])
        
        # Verify treatment status was updated
        treatment_status = discontinuation_visit["treatment_status"]
        self.assertFalse(treatment_status["active"])
        
        # Check patient state reflects discontinuation
        self.assertFalse(self.patient_state.state["treatment_status"]["active"])
        self.assertEqual(self.patient_state.state["treatment_status"]["discontinuation_date"], discontinuation_time)
        self.assertEqual(self.patient_state.state["treatment_status"]["reason_for_discontinuation"], "protocol_decision")
    
    def test_monitoring_visit_recording(self):
        """Test recording of monitoring visits after discontinuation."""
        # First discontinue treatment
        discontinuation_time = self.start_date + timedelta(days=30)
        self.patient_state.discontinue_treatment(discontinuation_time, reason="stable_max_interval")
        
        # Process a monitoring visit
        monitoring_time = discontinuation_time + timedelta(weeks=12)
        monitoring_actions = ["vision_test", "oct_scan"]
        
        # Force the visit to be a monitoring visit
        with patch.object(self.patient_state, "_record_visit") as mock_record_visit:
            self.patient_state.process_visit(monitoring_time, monitoring_actions, self.clinical_model)
            
            # Check that _record_visit was called with the right visit_type
            call_args = mock_record_visit.call_args[0]
            visit_data = call_args[2]
            self.assertEqual(visit_data["visit_type"], "monitoring_visit")
    
    def test_retreatment_visit_recording(self):
        """Test recording of retreatment visits after discontinuation and recurrence."""
        # First discontinue treatment
        discontinuation_time = self.start_date + timedelta(days=30)
        self.patient_state.discontinue_treatment(discontinuation_time, reason="stable_max_interval")
        
        # Force a recurrence detection
        self.patient_state.state["treatment_status"]["recurrence_detected"] = True
        
        # Process a retreatment visit
        retreatment_time = discontinuation_time + timedelta(weeks=14)
        retreatment_actions = ["vision_test", "oct_scan", "injection"]
        self.patient_state.process_visit(retreatment_time, retreatment_actions, self.clinical_model)
        
        # Verify the treatment status changed back to active
        self.assertTrue(self.patient_state.state["treatment_status"]["active"])
        self.assertFalse(self.patient_state.state["treatment_status"]["recurrence_detected"])
        self.assertIsNone(self.patient_state.state["treatment_status"]["discontinuation_date"])
        
        # Check the visit record
        visit_history = self.patient_state.visit_history
        retreatment_visit = visit_history[-1]
        
        # Verify retreatment is indicated by active status and injection action
        self.assertTrue(retreatment_visit["treatment_status"]["active"])
        self.assertIn("injection", retreatment_visit["actions"])
    
    def test_cessation_type_missing(self):
        """Test that cessation_type is not present in the current implementation."""
        # Discontinue treatment
        discontinuation_time = self.start_date + timedelta(days=30)
        self.patient_state.discontinue_treatment(discontinuation_time, reason="stable_max_interval")
        
        # Process a visit to capture the discontinuation
        actions = ["vision_test", "oct_scan"]
        self.patient_state.process_visit(discontinuation_time, actions, self.clinical_model)
        
        # Get the latest visit record
        visit_history = self.patient_state.visit_history
        latest_visit = visit_history[-1]
        
        # Check if cessation_type (which is needed by the streamgraph visualization) exists
        treatment_status = latest_visit["treatment_status"]
        self.assertNotIn("cessation_type", treatment_status)  # This should fail in current implementation
        
        # Check if reason_for_discontinuation exists instead
        self.assertEqual(self.patient_state.state["treatment_status"]["reason_for_discontinuation"], "stable_max_interval")
    
    def test_is_discontinuation_visit_present(self):
        """Test that is_discontinuation_visit flag is present in the updated implementation."""
        # Discontinue treatment
        discontinuation_time = self.start_date + timedelta(days=30)
        self.patient_state.discontinue_treatment(discontinuation_time, reason="stable_max_interval")
        
        # Process a visit to record the discontinuation
        actions = ["vision_test", "oct_scan", "discontinue_treatment"]
        self.patient_state.process_visit(discontinuation_time, actions, self.clinical_model)
        
        # Get the latest visit record
        visit_history = self.patient_state.visit_history
        latest_visit = visit_history[-1]
        
        # Check if is_discontinuation_visit exists
        self.assertIn("is_discontinuation_visit", latest_visit)
        self.assertTrue(latest_visit["is_discontinuation_visit"])
        self.assertIn("discontinuation_reason", latest_visit)
        self.assertEqual(latest_visit["discontinuation_reason"], "stable_max_interval")
    
    def test_is_retreatment_present(self):
        """Test that is_retreatment flag is present in the updated implementation."""
        # First discontinue treatment
        discontinuation_time = self.start_date + timedelta(days=30)
        self.patient_state.discontinue_treatment(discontinuation_time, reason="stable_max_interval")
        
        # Process discontinuation visit to record it
        discontinuation_actions = ["vision_test", "oct_scan", "discontinue_treatment"]
        self.patient_state.process_visit(discontinuation_time, discontinuation_actions, self.clinical_model)
        
        # Force a recurrence detection
        self.patient_state.state["treatment_status"]["recurrence_detected"] = True
        
        # Process a retreatment visit
        retreatment_time = discontinuation_time + timedelta(weeks=14)
        retreatment_actions = ["vision_test", "oct_scan", "injection"]
        self.patient_state.process_visit(retreatment_time, retreatment_actions, self.clinical_model)
        
        # Get the latest visit record
        visit_history = self.patient_state.visit_history
        latest_visit = visit_history[-1]
        
        # Check if is_retreatment exists
        self.assertIn("is_retreatment", latest_visit)
        self.assertTrue(latest_visit["is_retreatment"])
        self.assertIn("retreatment_reason", latest_visit)
        self.assertEqual(latest_visit["retreatment_reason"], "stable_max_interval")

if __name__ == '__main__':
    unittest.main()