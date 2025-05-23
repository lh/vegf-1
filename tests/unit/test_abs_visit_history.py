"""
Tests for verifying the completeness of visit history records in the ABS simulation.

This module focuses on verifying that the agent-based simulation correctly records
patient visit history, including treatment events, discontinuations, and retreatments,
but currently lacks fields needed by the streamgraph visualization.
"""

import unittest
import sys
import os
from datetime import datetime, timedelta
import numpy as np
from unittest.mock import patch, MagicMock

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from simulation.abs import AgentBasedSimulation, Patient
from simulation.patient_state import PatientState
from simulation.clinical_model import ClinicalModel
from simulation.base import Event, SimulationClock
from simulation.enhanced_discontinuation_manager import EnhancedDiscontinuationManager

class MockConfig:
    """Mock configuration for testing."""
    
    def __init__(self):
        """Initialize with default parameters."""
        self.start_date = "2025-01-01"
        self.duration_days = 365
        self.num_patients = 10
        
        # Mock treatment discontinuation parameters
        self.discontinuation_params = {
            "enabled": True,
            "criteria": {
                "stable_max_interval": {
                    "consecutive_visits": 3,
                    "probability": 0.5,
                    "interval_weeks": 16
                },
                "random_administrative": {
                    "annual_probability": 0.1
                },
                "treatment_duration": {
                    "threshold_weeks": 52,
                    "probability": 0.2
                },
                "premature": {
                    "min_interval_weeks": 8,
                    "probability_factor": 1.5
                }
            },
            "monitoring": {
                "cessation_types": {
                    "stable_max_interval": "planned",
                    "premature": "unplanned",
                    "treatment_duration": "unplanned",
                    "random_administrative": "none"
                },
                "planned": {
                    "follow_up_schedule": [12, 24, 36]
                },
                "unplanned": {
                    "follow_up_schedule": [8, 16, 24]
                },
                "recurrence_detection_probability": 0.8
            },
            "recurrence": {
                "planned": {
                    "base_annual_rate": 0.2,
                    "cumulative_rates": {
                        "year_1": 0.2,
                        "year_3": 0.5,
                        "year_5": 0.7
                    }
                },
                "premature": {
                    "base_annual_rate": 0.4,
                    "cumulative_rates": {
                        "year_1": 0.4,
                        "year_3": 0.7,
                        "year_5": 0.9
                    }
                }
            }
        }
    
    def get_vision_params(self):
        """Get vision parameters."""
        return {
            "baseline_mean": 65.0,
            "baseline_std": 10.0
        }
    
    def get_clinical_model_params(self):
        """Get clinical model parameters."""
        return {
            "disease_states": ["NAIVE", "STABLE", "ACTIVE", "HIGHLY_ACTIVE"],
            "transition_probabilities": {
                "NAIVE": {"STABLE": 1.0},
                "STABLE": {"STABLE": 0.8, "ACTIVE": 0.2},
                "ACTIVE": {"STABLE": 0.3, "ACTIVE": 0.7},
                "HIGHLY_ACTIVE": {"ACTIVE": 0.2, "HIGHLY_ACTIVE": 0.8}
            },
            "vision_change": {
                "base_change": {
                    "NAIVE": {
                        "injection": [8.0, 1.0],
                        "no_injection": [-2.0, 1.0]
                    },
                    "STABLE": {
                        "injection": [1.0, 0.5],
                        "no_injection": [-1.0, 0.5]
                    },
                    "ACTIVE": {
                        "injection": [0.5, 0.5],
                        "no_injection": [-2.0, 1.0]
                    },
                    "HIGHLY_ACTIVE": {
                        "injection": [0.0, 1.0],
                        "no_injection": [-4.0, 1.5]
                    }
                }
            }
        }
    
    def get_treatment_discontinuation_params(self):
        """Get treatment discontinuation parameters."""
        return self.discontinuation_params
    
    def get_simulation_params(self):
        """Get simulation parameters."""
        return {
            "start_date": self.start_date,
            "duration_days": self.duration_days,
            "num_patients": self.num_patients
        }
        
    def get(self, key, default=None):
        """Mock get method to support dictionary-like access."""
        if key == "discontinuation":
            return self.discontinuation_params
        return default

class ABSVisitHistoryTest(unittest.TestCase):
    """Test case for ABS visit history completeness."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create mock configuration
        self.config = MockConfig()
        
        # Create start date
        self.start_date = datetime(2025, 1, 1)
        
        # Create a simulation with the mock config
        with patch('simulation.clinical_model.ClinicalModel.get_initial_vision', return_value=70.0), \
             patch.object(SimulationClock, 'schedule_event', return_value=None):
            self.simulation = AgentBasedSimulation(self.config, self.start_date)
            self.simulation.clock.end_date = self.start_date + timedelta(days=365)
    
    def test_visit_record_structure(self):
        """Test the structure of visit records in ABS."""
        # Add a patient
        self.simulation.add_patient("TEST001", "treat_and_extend")
        
        # Get the patient
        patient = self.simulation.agents["TEST001"]
        
        # Mock patient state to process_visit method
        with patch.object(PatientState, 'process_visit') as mock_process_visit:
            # Set up the mock to return visit data
            mock_process_visit.return_value = {
                'visit_type': 'regular_visit',
                'baseline_vision': 70.0,
                'new_vision': 71.0,
                'disease_state': 'STABLE',
                'actions_performed': ['vision_test', 'oct_scan', 'injection']
            }
            
            # Create a visit event
            visit_event = Event(
                time=self.start_date + timedelta(days=7),
                event_type="visit",
                patient_id="TEST001",
                data={
                    "visit_type": "injection_visit",
                    "actions": ["vision_test", "oct_scan", "injection"],
                    "decisions": ["nurse_vision_check", "doctor_treatment_decision"]
                },
                priority=1
            )
            
            # Process the event
            self.simulation.process_event(visit_event)
            
            # Check that a visit record was added to patient history
            self.assertEqual(len(patient.history), 1)
            
            # Check the visit record structure
            visit_record = patient.history[0]
            self.assertIn('date', visit_record)
            self.assertIn('type', visit_record)
            self.assertIn('actions', visit_record)
            self.assertIn('baseline_vision', visit_record)
            self.assertIn('vision', visit_record)
            self.assertIn('disease_state', visit_record)
            
            # Check the content matches the expected values
            self.assertEqual(visit_record['date'], self.start_date + timedelta(days=7))
            self.assertEqual(visit_record['type'], 'regular_visit')
            self.assertIn('injection', visit_record['actions'])
            self.assertEqual(visit_record['vision'], 71.0)
            self.assertEqual(visit_record['disease_state'], 'STABLE')
    
    def test_discontinuation_info_missing(self):
        """Test that ABS records don't include is_discontinuation_visit flag."""
        # Add a patient
        self.simulation.add_patient("TEST001", "treat_and_extend")
        
        # Get the patient
        patient = self.simulation.agents["TEST001"]
        
        # Mock the PatientState.process_visit method
        with patch.object(PatientState, 'process_visit') as mock_process_visit:
            # Set up mock to simulate a discontinuation visit
            mock_process_visit.return_value = {
                'visit_type': 'regular_visit',
                'baseline_vision': 70.0,
                'new_vision': 70.0,
                'disease_state': 'STABLE',
                'actions_performed': ['vision_test', 'oct_scan', 'discontinue_treatment'],
                'treatment_status': {
                    'active': False,
                    'recurrence_detected': False,
                    'weeks_since_discontinuation': 0,
                    'discontinuation_date': self.start_date + timedelta(days=30),
                    'reason_for_discontinuation': 'stable_max_interval'
                }
            }
            
            # Create a visit event with discontinue_treatment action
            visit_event = Event(
                time=self.start_date + timedelta(days=30),
                event_type="visit",
                patient_id="TEST001",
                data={
                    "visit_type": "regular_visit",
                    "actions": ["vision_test", "oct_scan", "discontinue_treatment"],
                    "decisions": ["nurse_vision_check", "doctor_treatment_decision"]
                },
                priority=1
            )
            
            # Process the event
            self.simulation.process_event(visit_event)
            
            # Check that a visit record was added
            self.assertEqual(len(patient.history), 1)
            
            # Check that the visit record doesn't have is_discontinuation_visit flag
            visit_record = patient.history[0]
            self.assertNotIn('is_discontinuation_visit', visit_record)
            
            # Check that the treatment_status is not included (in ABS implementation)
            self.assertNotIn('treatment_status', visit_record)
    
    def test_retreatment_info_missing(self):
        """Test that ABS records don't include is_retreatment flag."""
        # Add a patient
        self.simulation.add_patient("TEST001", "treat_and_extend")
        
        # Get the patient
        patient = self.simulation.agents["TEST001"]
        
        # Mock the PatientState.process_visit method to simulate a retreatment
        with patch.object(PatientState, 'process_visit') as mock_process_visit:
            # First, add a discontinuation visit
            mock_process_visit.return_value = {
                'visit_type': 'regular_visit',
                'baseline_vision': 70.0,
                'new_vision': 70.0,
                'disease_state': 'STABLE',
                'actions_performed': ['vision_test', 'oct_scan', 'discontinue_treatment'],
                'treatment_status': {
                    'active': False,
                    'recurrence_detected': False,
                    'weeks_since_discontinuation': 0,
                    'discontinuation_date': self.start_date + timedelta(days=30),
                    'reason_for_discontinuation': 'stable_max_interval'
                }
            }
            
            # Create and process a discontinuation visit
            discontinuation_event = Event(
                time=self.start_date + timedelta(days=30),
                event_type="visit",
                patient_id="TEST001",
                data={
                    "visit_type": "regular_visit",
                    "actions": ["vision_test", "oct_scan", "discontinue_treatment"],
                    "decisions": ["nurse_vision_check", "doctor_treatment_decision"]
                },
                priority=1
            )
            self.simulation.process_event(discontinuation_event)
            
            # Reset the mock for retreatment visit
            mock_process_visit.return_value = {
                'visit_type': 'regular_visit',
                'baseline_vision': 68.0,
                'new_vision': 69.0,
                'disease_state': 'ACTIVE',
                'actions_performed': ['vision_test', 'oct_scan', 'injection'],
                'treatment_status': {
                    'active': True,
                    'recurrence_detected': False,
                    'weeks_since_discontinuation': 0,
                    'discontinuation_date': None,
                    'reason_for_discontinuation': None
                }
            }
            
            # Create and process a retreatment visit
            retreatment_event = Event(
                time=self.start_date + timedelta(days=90),
                event_type="visit",
                patient_id="TEST001",
                data={
                    "visit_type": "injection_visit",
                    "actions": ["vision_test", "oct_scan", "injection"],
                    "decisions": ["nurse_vision_check", "doctor_treatment_decision"]
                },
                priority=1
            )
            self.simulation.process_event(retreatment_event)
            
            # Check that two visit records were added
            self.assertEqual(len(patient.history), 2)
            
            # Check that the retreatment visit record doesn't have is_retreatment flag
            retreatment_record = patient.history[1]
            self.assertNotIn('is_retreatment', retreatment_record)
    
    def test_enhanced_discontinuation_manager_structure(self):
        """Test structure of discontinuation data in EnhancedDiscontinuationManager."""
        # Create an EnhancedDiscontinuationManager instance
        discontinuation_manager = EnhancedDiscontinuationManager(self.config)
        
        # Check that discontinuation_types dict exists or is initialized in constructor
        self.assertTrue(hasattr(discontinuation_manager, 'discontinuation_types'))
        
        # Initialize the discontinuation_types dict if not already present
        if not hasattr(discontinuation_manager, 'discontinuation_types'):
            discontinuation_manager.discontinuation_types = {}
            
        # Set a discontinuation type for a test patient
        discontinuation_manager.discontinuation_types["TEST001"] = "stable_max_interval"
        
        # Verify the structure
        self.assertIsInstance(discontinuation_manager.discontinuation_types, dict)
        
        # Check structure of discontinuation_types
        for patient_id, cessation_type in discontinuation_manager.discontinuation_types.items():
            self.assertIsInstance(patient_id, str)
            self.assertIsInstance(cessation_type, str)

if __name__ == '__main__':
    unittest.main()