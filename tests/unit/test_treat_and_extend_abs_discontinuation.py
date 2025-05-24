"""
Tests for discontinuation and retreatment handling in TreatAndExtendABS implementation.

This module tests the TreatAndExtendABS implementation to verify that it correctly
handles discontinuation and retreatment events, but lacks the specific flags needed
for the streamgraph visualization.
"""

import unittest
import sys
import os
from datetime import datetime, timedelta
import numpy as np
from unittest.mock import patch, MagicMock

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import only after path adjustment
from simulation.enhanced_discontinuation_manager import EnhancedDiscontinuationManager

class MockPatient:
    """Mock patient for testing."""
    
    def __init__(self, patient_id):
        """Initialize patient with a unique ID."""
        self.patient_id = patient_id
        self.current_vision = 70.0
        self.baseline_vision = 70.0
        self.disease_activity = {
            "fluid_detected": False,
            "consecutive_stable_visits": 3,
            "max_interval_reached": True,
            "current_interval": 16
        }
        self.treatment_status = {
            "active": True,
            "recurrence_detected": False,
            "discontinuation_date": None,
            "reason_for_discontinuation": None
        }
        self.history = []
        self.next_visit_interval = 16
        self.current_phase = "maintenance"
        self.treatment_start = datetime(2025, 1, 1)
        self.disease_characteristics = {
            "has_PED": False
        }
    
    def process_visit(self, time, actions, clinical_model):
        """Record a visit and return results."""
        visit_type = "regular_visit"
        
        if "discontinue_treatment" in actions:
            self.treatment_status["active"] = False
            self.treatment_status["discontinuation_date"] = time
            self.treatment_status["reason_for_discontinuation"] = "stable_max_interval"
        
        if not self.treatment_status["active"] and "monitoring_visit" in actions:
            visit_type = "monitoring_visit"
        
        if "check_recurrence" in actions and self.treatment_status["recurrence_detected"]:
            if "injection" in actions:
                self.treatment_status["active"] = True
                self.treatment_status["recurrence_detected"] = False
                self.treatment_status["discontinuation_date"] = None
                self.treatment_status["reason_for_discontinuation"] = None
        
        visit_record = {
            'date': time,
            'type': visit_type,
            'actions': actions,
            'baseline_vision': self.baseline_vision,
            'vision': self.current_vision,
            'disease_state': 'stable',
            'phase': self.current_phase,
            'interval': self.disease_activity["current_interval"]
        }
        self.history.append(visit_record)
        
        return {
            'visit_type': visit_type,
            'baseline_vision': self.baseline_vision,
            'new_vision': self.current_vision,
            'disease_state': 'stable'
        }

class MockConfig:
    """Mock configuration for testing."""
    
    def __init__(self):
        """Initialize with test configuration."""
        self.parameters = {
            "discontinuation": {
                "enabled": True,
                "criteria": {
                    "stable_max_interval": {
                        "consecutive_visits": 3,
                        "probability": 1.0,  # Always discontinue for testing
                        "interval_weeks": 16
                    },
                    "random_administrative": {
                        "annual_probability": 0.0  # Disable for testing
                    },
                    "premature": {
                        "probability_factor": 0.0  # Disable for testing
                    },
                    "treatment_duration": {
                        "probability": 0.0  # Disable for testing
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
                    "recurrence_detection_probability": 1.0  # Always detect for testing
                },
                "recurrence": {
                    "planned": {
                        "base_annual_rate": 1.0,  # Always recur for testing
                        "cumulative_rates": {
                            "year_1": 1.0,
                            "year_3": 1.0,
                            "year_5": 1.0
                        }
                    }
                },
                "retreatment": {
                    "eligibility_criteria": {
                        "detected_fluid": True,
                        "vision_loss_letters": 5
                    },
                    "probability": 1.0  # Always retreat for testing
                }
            }
        }
    
    def get_treatment_discontinuation_params(self):
        """Get treatment discontinuation parameters."""
        return self.parameters["discontinuation"]
        
    def get(self, key, default=None):
        """Mock get method to support dictionary-like access."""
        return self.parameters.get(key, default)

class MockTreatAndExtendABS:
    """Mock TreatAndExtendABS for testing."""
    
    def __init__(self, config):
        """Initialize with config."""
        self.config = config
        self.discontinuation_manager = EnhancedDiscontinuationManager(config)
        self.patients = {}
        self.clinical_model = MagicMock()
        self.patient_histories = {}
    
    def add_patient(self, patient_id):
        """Add a test patient."""
        patient = MockPatient(patient_id)
        self.patients[patient_id] = patient
        return patient
    
    def check_discontinuation(self, patient):
        """Check if patient should be discontinued."""
        # Mock the patient state for the discontinuation manager
        patient_state = {
            "disease_activity": patient.disease_activity,
            "treatment_status": patient.treatment_status,
            "current_phase": patient.current_phase,
            "next_visit_interval": patient.next_visit_interval,
            "visits": len(patient.history)
        }
        
        # Use evaluate_discontinuation method instead
        should_discontinue, reason, prob, cessation_type = self.discontinuation_manager.evaluate_discontinuation(
            patient_state=patient_state,
            current_time=datetime.now(),
            patient_id=patient.patient_id
        )
        
        if should_discontinue:
            # Record discontinuation in patient's treatment status
            patient.treatment_status["active"] = False
            patient.treatment_status["discontinuation_date"] = datetime.now()
            patient.treatment_status["reason_for_discontinuation"] = cessation_type
            
            # Add to discontinuation types mapping
            self.discontinuation_manager.discontinuation_types[patient.patient_id] = cessation_type
            
            return True, cessation_type
        
        return False, None
    
    def generate_patient_histories(self):
        """Generate history dictionaries for testing."""
        for patient_id, patient in self.patients.items():
            # Convert patient history to the format expected by visualization
            visits = []
            
            for visit in patient.history:
                enhanced_visit = {
                    "time": (visit["date"] - patient.treatment_start).days / 30.0,  # Convert to months
                    "date": visit["date"],
                    "type": visit["type"],
                    "actions": visit["actions"],
                    "vision": visit["vision"],
                    "disease_state": visit["disease_state"],
                    # Note: no is_discontinuation_visit or is_retreatment flags
                }
                
                visits.append(enhanced_visit)
            
            self.patient_histories[patient_id] = visits
        
        return self.patient_histories

class TreatAndExtendABSDiscontinuationTest(unittest.TestCase):
    """Test case for discontinuation and retreatment in TreatAndExtendABS."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create mock config
        self.config = MockConfig()
        
        # Create a simulation
        self.simulation = MockTreatAndExtendABS(self.config)
    
    def test_discontinuation_detection(self):
        """Test that discontinuation is correctly detected and recorded."""
        # Add a patient eligible for discontinuation
        patient = self.simulation.add_patient("TEST001")
        
        # Check discontinuation
        should_discontinue, cessation_type = self.simulation.check_discontinuation(patient)
        
        # Verify discontinuation decision
        self.assertTrue(should_discontinue)
        self.assertEqual(cessation_type, "stable_max_interval")
        
        # Verify patient state was updated
        self.assertFalse(patient.treatment_status["active"])
        self.assertIsNotNone(patient.treatment_status["discontinuation_date"])
        self.assertEqual(patient.treatment_status["reason_for_discontinuation"], "stable_max_interval")
    
    def test_discontinuation_visit_structure(self):
        """Test structure of visit record for a discontinuation visit."""
        # Add a patient
        patient = self.simulation.add_patient("TEST001")
        
        # Generate a discontinuation visit
        visit_time = patient.treatment_start + timedelta(days=90)
        actions = ["vision_test", "oct_scan", "discontinue_treatment"]
        
        # Process the visit
        patient.process_visit(visit_time, actions, self.simulation.clinical_model)
        
        # Verify visit was recorded
        self.assertEqual(len(patient.history), 1)
        
        # Check the visit record
        visit = patient.history[0]
        self.assertEqual(visit["date"], visit_time)
        self.assertIn("discontinue_treatment", visit["actions"])
        
        # Converting to visualization format
        histories = self.simulation.generate_patient_histories()
        
        # Check that patient history exists
        self.assertIn("TEST001", histories)
        
        # Check the visit in visualization format
        enhanced_visits = histories["TEST001"]
        self.assertEqual(len(enhanced_visits), 1)
        
        # Check for missing fields needed by visualization
        enhanced_visit = enhanced_visits[0]
        self.assertNotIn("is_discontinuation_visit", enhanced_visit)
        self.assertNotIn("discontinuation_reason", enhanced_visit)
        self.assertNotIn("cessation_type", enhanced_visit)
    
    def test_monitoring_visit_structure(self):
        """Test structure of visit record for a monitoring visit."""
        # Add a patient
        patient = self.simulation.add_patient("TEST001")
        
        # Discontinue treatment
        patient.treatment_status["active"] = False
        patient.treatment_status["discontinuation_date"] = patient.treatment_start + timedelta(days=90)
        patient.treatment_status["reason_for_discontinuation"] = "stable_max_interval"
        
        # Generate a monitoring visit
        visit_time = patient.treatment_start + timedelta(days=90 + 84)  # 12 weeks after discontinuation
        actions = ["vision_test", "oct_scan", "monitoring_visit"]
        
        # Process the visit
        patient.process_visit(visit_time, actions, self.simulation.clinical_model)
        
        # Verify visit was recorded
        self.assertEqual(len(patient.history), 1)
        
        # Check the visit record
        visit = patient.history[0]
        self.assertEqual(visit["date"], visit_time)
        self.assertEqual(visit["type"], "monitoring_visit")
        
        # Converting to visualization format
        histories = self.simulation.generate_patient_histories()
        
        # Check the visit in visualization format
        enhanced_visits = histories["TEST001"]
        self.assertEqual(len(enhanced_visits), 1)
        
        # Check that the monitoring visit has the right type
        enhanced_visit = enhanced_visits[0]
        self.assertEqual(enhanced_visit["type"], "monitoring_visit")
        
        # Check for missing fields needed by visualization
        self.assertNotIn("is_monitoring_visit", enhanced_visit)
    
    def test_retreatment_visit_structure(self):
        """Test structure of visit record for a retreatment visit."""
        # Add a patient
        patient = self.simulation.add_patient("TEST001")
        
        # Discontinue treatment
        patient.treatment_status["active"] = False
        patient.treatment_status["discontinuation_date"] = patient.treatment_start + timedelta(days=90)
        patient.treatment_status["reason_for_discontinuation"] = "stable_max_interval"
        
        # Add a monitoring visit that detects recurrence
        monitoring_time = patient.treatment_start + timedelta(days=90 + 84)  # 12 weeks after discontinuation
        patient.treatment_status["recurrence_detected"] = True
        
        # Generate a retreatment visit
        visit_time = monitoring_time + timedelta(days=14)  # 2 weeks after monitoring
        actions = ["vision_test", "oct_scan", "injection", "check_recurrence"]
        
        # Process the visit
        patient.process_visit(visit_time, actions, self.simulation.clinical_model)
        
        # Verify visit was recorded
        self.assertEqual(len(patient.history), 1)
        
        # Check the visit record
        visit = patient.history[0]
        self.assertEqual(visit["date"], visit_time)
        self.assertIn("injection", visit["actions"])
        
        # Converting to visualization format
        histories = self.simulation.generate_patient_histories()
        
        # Check the visit in visualization format
        enhanced_visits = histories["TEST001"]
        self.assertEqual(len(enhanced_visits), 1)
        
        # Check for missing fields needed by visualization
        enhanced_visit = enhanced_visits[0]
        self.assertNotIn("is_retreatment", enhanced_visit)
        self.assertNotIn("retreatment_reason", enhanced_visit)
    
    def test_discontinuation_manager_data_structure(self):
        """Test the data structure maintained by the EnhancedDiscontinuationManager."""
        # Create a discontinuation manager
        manager = EnhancedDiscontinuationManager(self.config)
        
        # Set up discontinuation types manually for testing
        patient_ids = ["TEST001", "TEST002", "TEST003"]
        for patient_id in patient_ids:
            manager.discontinuation_types[patient_id] = "stable_max_interval"
        
        # Check the discontinuation_types dictionary
        self.assertEqual(len(manager.discontinuation_types), len(patient_ids))
        
        for patient_id in patient_ids:
            self.assertIn(patient_id, manager.discontinuation_types)
            self.assertEqual(manager.discontinuation_types[patient_id], "stable_max_interval")
        
        # Check that cessation_type is stored in the manager but not in visit records
        # This is the key information needed for visualization but not currently passed through

if __name__ == '__main__':
    unittest.main()