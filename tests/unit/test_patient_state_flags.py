"""
Tests for verifying that patient visit records include the required flags for visualization.

These tests will initially fail and will pass once the implementation is updated to
include the necessary flags (is_discontinuation_visit, is_retreatment, etc.) in the visit records.
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
from simulation.enhanced_discontinuation_manager import EnhancedDiscontinuationManager

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

class PatientStateFlagsTest(unittest.TestCase):
    """Test case for patient state visit records with visualization flags."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a mock clinical model
        self.clinical_model = MockClinicalModel()
        
        # Create a patient state
        self.start_date = datetime(2025, 1, 1)
        self.patient_state = PatientState("TEST001", "treat_and_extend", 70.0, self.start_date)
    
    def test_discontinuation_visit_flag(self):
        """Test that discontinuation visits include the required is_discontinuation_visit flag."""
        # Process a regular visit first
        visit_time = self.start_date + timedelta(days=7)
        actions = ["vision_test", "oct_scan", "injection"]
        self.patient_state.process_visit(visit_time, actions, self.clinical_model)
        
        # Now process a discontinuation visit
        discontinuation_time = self.start_date + timedelta(days=30)
        discontinuation_actions = ["vision_test", "oct_scan", "discontinue_treatment"]
        
        # Manually set up discontinuation
        self.patient_state.discontinue_treatment(discontinuation_time, reason="stable_max_interval")
        
        # Process the visit
        visit_data = self.patient_state.process_visit(discontinuation_time, discontinuation_actions, self.clinical_model)
        
        # Get the visit history
        visit_history = self.patient_state.visit_history
        
        # Get the latest visit - the discontinuation visit
        latest_visit = visit_history[-1]
        
        # Test that is_discontinuation_visit flag is present and True
        self.assertIn("is_discontinuation_visit", latest_visit)
        self.assertTrue(latest_visit["is_discontinuation_visit"])
        
        # Test that discontinuation_reason is present and matches the expected reason
        self.assertIn("discontinuation_reason", latest_visit)
        self.assertEqual(latest_visit["discontinuation_reason"], "stable_max_interval")
    
    def test_retreatment_visit_flag(self):
        """Test that retreatment visits include the required is_retreatment flag."""
        # First discontinue treatment
        discontinuation_time = self.start_date + timedelta(days=30)
        self.patient_state.discontinue_treatment(discontinuation_time, reason="stable_max_interval")
        
        # Process a discontinuation visit to record it
        discontinuation_actions = ["vision_test", "oct_scan", "discontinue_treatment"]
        self.patient_state.process_visit(discontinuation_time, discontinuation_actions, self.clinical_model)
        
        # Force a recurrence detection
        self.patient_state.state["treatment_status"]["recurrence_detected"] = True
        
        # Process a retreatment visit
        retreatment_time = discontinuation_time + timedelta(weeks=14)
        retreatment_actions = ["vision_test", "oct_scan", "injection"]
        self.patient_state.process_visit(retreatment_time, retreatment_actions, self.clinical_model)
        
        # Get the visit history
        visit_history = self.patient_state.visit_history
        
        # Get the latest visit - the retreatment visit
        latest_visit = visit_history[-1]
        
        # Test that is_retreatment flag is present and True
        self.assertIn("is_retreatment", latest_visit)
        self.assertTrue(latest_visit["is_retreatment"])
        
        # Test that retreatment_reason exists and contains the original cessation type
        self.assertIn("retreatment_reason", latest_visit)
        self.assertEqual(latest_visit["retreatment_reason"], "stable_max_interval")

class EnhancedDiscontinuationManagerFlagsTest(unittest.TestCase):
    """Test case for enhanced discontinuation manager flags."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create mock configuration
        self.config = MagicMock()
        self.config.get.return_value = {
            "enabled": True,
            "criteria": {
                "stable_max_interval": {
                    "consecutive_visits": 3,
                    "probability": 1.0,
                    "interval_weeks": 16
                },
                "random_administrative": {
                    "annual_probability": 0.0
                },
                "treatment_duration": {
                    "probability": 0.0
                },
                "premature": {
                    "probability_factor": 0.0
                }
            }
        }
        
        # Create a discontinuation manager
        self.discontinuation_manager = EnhancedDiscontinuationManager(self.config)
        
        # Create a patient state
        self.start_date = datetime(2025, 1, 1)
        self.patient_state = PatientState("TEST001", "treat_and_extend", 70.0, self.start_date)
    
    def test_discontinuation_type_tracking(self):
        """Test that discontinuation types are tracked correctly."""
        # Set up a patient ID and cessation type
        patient_id = "TEST001"
        cessation_type = "stable_max_interval"
        
        # Add to discontinuation types
        self.discontinuation_manager.discontinuation_types[patient_id] = cessation_type
        
        # Verify it's stored
        self.assertIn(patient_id, self.discontinuation_manager.discontinuation_types)
        self.assertEqual(self.discontinuation_manager.discontinuation_types[patient_id], cessation_type)
        
        # Ensure this data is accessible to the visualization process
        # This test will pass now, but it's included to document that the data exists
        # and should be used when adding the visualization flags

class ABSVisitFlagsTest(unittest.TestCase):
    """Test case for ABS visit flags in the process_event method."""
    
    def setUp(self):
        """Set up test fixtures."""
        # We'll need to patch several components to test the ABS implementation
        self.patcher1 = patch('simulation.abs.AgentBasedSimulation')
        self.patcher2 = patch('simulation.abs.Patient')
        self.patcher3 = patch('simulation.patient_state.PatientState')
        self.patcher4 = patch('simulation.enhanced_discontinuation_manager.EnhancedDiscontinuationManager')
        
        # Start the patchers
        self.MockABS = self.patcher1.start()
        self.MockPatient = self.patcher2.start()
        self.MockPatientState = self.patcher3.start()
        self.MockDiscontinuationManager = self.patcher4.start()
        
        # Create mock instances
        self.abs_instance = self.MockABS.return_value
        self.patient_instance = self.MockPatient.return_value
        self.patient_state_instance = self.MockPatientState.return_value
        self.discontinuation_manager_instance = self.MockDiscontinuationManager.return_value
        
        # Link the mocks
        self.abs_instance.agents = {"TEST001": self.patient_instance}
        self.abs_instance.clock = MagicMock()
        self.discontinuation_manager_instance.discontinuation_types = {"TEST001": "stable_max_interval"}
        
    def tearDown(self):
        """Tear down test fixtures."""
        # Stop the patchers
        self.patcher1.stop()
        self.patcher2.stop()
        self.patcher3.stop()
        self.patcher4.stop()
    
    def test_discontinuation_visit_event(self):
        """Test that discontinuation visit events have the required flags."""
        # Set up a discontinuation visit event for testing
        event_time = datetime(2025, 1, 30)
        patient_id = "TEST001"
        visit_data = {
            'visit_type': 'regular_visit',
            'baseline_vision': 70.0,
            'new_vision': 70.0,
            'disease_state': 'STABLE',
            'treatment_status': {
                'active': False,
                'recurrence_detected': False,
                'discontinuation_date': event_time,
                'reason_for_discontinuation': 'stable_max_interval'
            }
        }
        
        # Mock the process_visit method to return our test data
        self.patient_instance.state.process_visit.return_value = visit_data
        
        # Create a mock for patient history
        self.patient_instance.history = []
        
        # Create the event
        from simulation.base import Event
        event = Event(
            time=event_time,
            event_type="visit",
            patient_id=patient_id,
            data={
                "visit_type": "regular_visit",
                "actions": ["vision_test", "oct_scan", "discontinue_treatment"]
            },
            priority=1
        )
        
        # This is the method we're testing - we expect it to add is_discontinuation_visit
        # The actual implementation will be tested when we modify the code
        from simulation.abs import AgentBasedSimulation
        with patch.object(AgentBasedSimulation, 'process_event') as mock_process_event:
            # Create a real ABS instance but don't call the actual method
            abs_instance = AgentBasedSimulation(MagicMock(), datetime.now())
            
            # Create a test assertion to check the new flag that should be added
            def side_effect(event):
                # This asserts what should happen after our implementation change
                patient = abs_instance.agents[event.patient_id]
                visit_record = patient.history[-1]
                
                # These assertions will fail until we implement the changes
                self.assertIn('is_discontinuation_visit', visit_record)
                self.assertTrue(visit_record['is_discontinuation_visit'])
                self.assertIn('discontinuation_reason', visit_record)
                self.assertEqual(visit_record['discontinuation_reason'], 'stable_max_interval')
            
            mock_process_event.side_effect = side_effect
            
            # Add a visit record to history when process_event is called
            # This will be executed in the actual implementation
            self.patient_instance.history.append({
                'date': event_time,
                'type': 'regular_visit',
                'actions': event.data['actions'],
                'baseline_vision': 70.0,
                'vision': 70.0,
                'disease_state': 'STABLE',
                'treatment_status': {
                    'active': False,
                    'recurrence_detected': False,
                    'discontinuation_date': event_time,
                    'reason_for_discontinuation': 'stable_max_interval'
                }
            })
            
            # Call the method we're testing
            abs_instance.process_event(event)
    
    def test_retreatment_visit_event(self):
        """Test that retreatment visit events have the required flags."""
        # Set up a retreatment visit event for testing
        discontinuation_time = datetime(2025, 1, 30)
        retreatment_time = datetime(2025, 3, 15)
        patient_id = "TEST001"
        
        # Setup visit data for a retreatment
        visit_data = {
            'visit_type': 'regular_visit',
            'baseline_vision': 70.0,
            'new_vision': 70.0,
            'disease_state': 'ACTIVE',
            'treatment_status': {
                'active': True,  # Changed from False to True = retreatment
                'recurrence_detected': False,
                'discontinuation_date': None,
                'reason_for_discontinuation': None
            }
        }
        
        # Mock the process_visit method to return our test data
        self.patient_instance.state.process_visit.return_value = visit_data
        
        # Create a mock for patient history with a prior discontinuation
        self.patient_instance.history = [{
            'date': discontinuation_time,
            'type': 'regular_visit',
            'actions': ["vision_test", "oct_scan", "discontinue_treatment"],
            'baseline_vision': 70.0,
            'vision': 70.0,
            'disease_state': 'STABLE',
            'is_discontinuation_visit': True,
            'discontinuation_reason': 'stable_max_interval',
            'treatment_status': {
                'active': False,
                'recurrence_detected': False,
                'discontinuation_date': discontinuation_time,
                'reason_for_discontinuation': 'stable_max_interval'
            }
        }]
        
        # Create the event
        from simulation.base import Event
        event = Event(
            time=retreatment_time,
            event_type="visit",
            patient_id=patient_id,
            data={
                "visit_type": "regular_visit",
                "actions": ["vision_test", "oct_scan", "injection"]
            },
            priority=1
        )
        
        # This is the method we're testing - we expect it to add is_retreatment
        # The actual implementation will be tested when we modify the code
        from simulation.abs import AgentBasedSimulation
        with patch.object(AgentBasedSimulation, 'process_event') as mock_process_event:
            # Create a real ABS instance but don't call the actual method
            abs_instance = AgentBasedSimulation(MagicMock(), datetime.now())
            
            # Create a test assertion to check the new flag that should be added
            def side_effect(event):
                # This asserts what should happen after our implementation change
                patient = abs_instance.agents[event.patient_id]
                visit_record = patient.history[-1]
                
                # These assertions will fail until we implement the changes
                self.assertIn('is_retreatment', visit_record)
                self.assertTrue(visit_record['is_retreatment'])
                self.assertIn('retreatment_reason', visit_record)
                self.assertEqual(visit_record['retreatment_reason'], 'stable_max_interval')
            
            mock_process_event.side_effect = side_effect
            
            # Add a retreatment visit record to history
            # This will be executed in the actual implementation
            self.patient_instance.history.append({
                'date': retreatment_time,
                'type': 'regular_visit',
                'actions': event.data['actions'],
                'baseline_vision': 70.0,
                'vision': 70.0,
                'disease_state': 'ACTIVE',
                'treatment_status': {
                    'active': True,
                    'recurrence_detected': False,
                    'discontinuation_date': None,
                    'reason_for_discontinuation': None
                }
            })
            
            # Call the method we're testing
            abs_instance.process_event(event)

if __name__ == '__main__':
    unittest.main()