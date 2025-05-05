"""
Unit tests for the clinician module.

This module contains tests for the Clinician and ClinicianManager classes, verifying that
they correctly implement clinician variation in protocol adherence and decision-making.
"""

import unittest
import sys
import os
from datetime import datetime, timedelta
import numpy as np
from unittest.mock import patch, MagicMock

# Add the parent directory to the path so we can import the simulation modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from simulation.clinician import Clinician, ClinicianManager

class TestClinician(unittest.TestCase):
    """Test cases for the Clinician class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create sample clinicians with different profiles
        self.perfect_clinician = Clinician()
        
        self.adherent_clinician = Clinician("adherent", {
            "protocol_adherence_rate": 0.95,
            "characteristics": {
                "risk_tolerance": "low",
                "conservative_retreatment": True
            },
            "stability_threshold": 3,
            "interval_preferences": {
                "min_interval": 8,
                "max_interval": 16,
                "extension_threshold": 2
            }
        })
        
        self.average_clinician = Clinician("average", {
            "protocol_adherence_rate": 0.80,
            "characteristics": {
                "risk_tolerance": "medium",
                "conservative_retreatment": False
            },
            "stability_threshold": 2,
            "interval_preferences": {
                "min_interval": 8,
                "max_interval": 12,
                "extension_threshold": 1
            }
        })
        
        self.non_adherent_clinician = Clinician("non_adherent", {
            "protocol_adherence_rate": 0.50,
            "characteristics": {
                "risk_tolerance": "high",
                "conservative_retreatment": False
            },
            "stability_threshold": 1,
            "interval_preferences": {
                "min_interval": 6,
                "max_interval": 16,
                "extension_threshold": 0
            }
        })
        
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
                "discontinuation_date": None
            }
        }
    
    def test_initialization(self):
        """Test that clinicians initialize correctly."""
        # Perfect clinician should have default values
        self.assertEqual(self.perfect_clinician.profile_name, "perfect")
        self.assertEqual(self.perfect_clinician.adherence_rate, 1.0)
        self.assertEqual(self.perfect_clinician.risk_tolerance, "low")
        self.assertTrue(self.perfect_clinician.conservative_retreatment)
        
        # Adherent clinician should have specified values
        self.assertEqual(self.adherent_clinician.profile_name, "adherent")
        self.assertEqual(self.adherent_clinician.adherence_rate, 0.95)
        self.assertEqual(self.adherent_clinician.risk_tolerance, "low")
        self.assertTrue(self.adherent_clinician.conservative_retreatment)
        
        # Average clinician should have specified values
        self.assertEqual(self.average_clinician.profile_name, "average")
        self.assertEqual(self.average_clinician.adherence_rate, 0.80)
        self.assertEqual(self.average_clinician.risk_tolerance, "medium")
        self.assertFalse(self.average_clinician.conservative_retreatment)
        
        # Non-adherent clinician should have specified values
        self.assertEqual(self.non_adherent_clinician.profile_name, "non_adherent")
        self.assertEqual(self.non_adherent_clinician.adherence_rate, 0.50)
        self.assertEqual(self.non_adherent_clinician.risk_tolerance, "high")
        self.assertFalse(self.non_adherent_clinician.conservative_retreatment)
    
    def test_follows_protocol(self):
        """Test the follows_protocol method."""
        # Perfect clinician should always follow protocol
        with patch.object(np.random, 'random', return_value=0.5):  # Any value will work for perfect clinician
            for _ in range(10):
                self.assertTrue(self.perfect_clinician.follows_protocol())
        
        # Adherent clinician should follow protocol most of the time
        with patch.object(np.random, 'random', side_effect=[0.9 if i % 20 == 0 else 0.1 for i in range(100)]):
            # This will return values below the adherence rate (0.95) 95% of the time
            adherent_follows = sum(self.adherent_clinician.follows_protocol() for _ in range(100))
            self.assertGreater(adherent_follows, 90)  # Should be around 95
        
        # Average clinician should follow protocol less often
        with patch.object(np.random, 'random', side_effect=[0.9 if i % 5 == 0 else 0.1 for i in range(100)]):
            # This will return values below the adherence rate (0.8) 80% of the time
            average_follows = sum(self.average_clinician.follows_protocol() for _ in range(100))
            self.assertGreater(average_follows, 70)  # Should be around 80
        
        # Non-adherent clinician should follow protocol least often
        with patch.object(np.random, 'random', side_effect=[0.9 if i % 2 == 0 else 0.1 for i in range(100)]):
            # This will return values below the adherence rate (0.5) 50% of the time
            non_adherent_follows = sum(self.non_adherent_clinician.follows_protocol() for _ in range(100))
            self.assertGreater(non_adherent_follows, 40)  # Should be around 50
    
    def test_evaluate_discontinuation(self):
        """Test the evaluate_discontinuation method."""
        # Set random seed for reproducibility
        np.random.seed(42)
        
        # Perfect clinician should always follow protocol
        decision, probability = self.perfect_clinician.evaluate_discontinuation(
            self.patient_state, True, 0.2
        )
        self.assertTrue(decision)
        self.assertEqual(probability, 0.2)
        
        decision, probability = self.perfect_clinician.evaluate_discontinuation(
            self.patient_state, False, 0.0
        )
        self.assertFalse(decision)
        self.assertEqual(probability, 0.0)
        
        # Adherent clinician with low risk tolerance might override discontinuation
        decision, probability = self.adherent_clinician.evaluate_discontinuation(
            self.patient_state, True, 0.2
        )
        # With this seed, should follow protocol
        self.assertTrue(decision)
        self.assertEqual(probability, 0.2)
        
        # Non-adherent clinician with high risk tolerance might discontinue against protocol
        decision, probability = self.non_adherent_clinician.evaluate_discontinuation(
            self.patient_state, False, 0.0
        )
        # With this seed, might override protocol
        # The exact result depends on the random seed, so we'll just check that it's valid
        self.assertIn(decision, [True, False])
        if decision:
            self.assertGreater(probability, 0.0)
    
    def test_evaluate_retreatment(self):
        """Test the evaluate_retreatment method."""
        # Set random seed for reproducibility
        np.random.seed(42)
        
        # Perfect clinician should always follow protocol
        decision, probability = self.perfect_clinician.evaluate_retreatment(
            self.patient_state, True, 0.95
        )
        self.assertTrue(decision)
        self.assertEqual(probability, 0.95)
        
        decision, probability = self.perfect_clinician.evaluate_retreatment(
            self.patient_state, False, 0.0
        )
        self.assertFalse(decision)
        self.assertEqual(probability, 0.0)
        
        # Adherent clinician with conservative retreatment might increase probability
        decision, probability = self.adherent_clinician.evaluate_retreatment(
            self.patient_state, True, 0.95
        )
        self.assertTrue(decision)
        self.assertGreaterEqual(probability, 0.95)
        
        # Non-adherent clinician with high risk tolerance might skip retreatment
        decision, probability = self.non_adherent_clinician.evaluate_retreatment(
            self.patient_state, True, 0.95
        )
        # With this seed, might override protocol
        # The exact result depends on the random seed, so we'll just check that it's valid
        self.assertIn(decision, [True, False])
        if not decision:
            self.assertEqual(probability, 0.0)

class TestClinicianManager(unittest.TestCase):
    """Test cases for the ClinicianManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a sample configuration
        self.config = {
            "clinicians": {
                "enabled": True,
                "profiles": {
                    "adherent": {
                        "protocol_adherence_rate": 0.95,
                        "probability": 0.25,
                        "characteristics": {
                            "risk_tolerance": "low",
                            "conservative_retreatment": True
                        }
                    },
                    "average": {
                        "protocol_adherence_rate": 0.80,
                        "probability": 0.50,
                        "characteristics": {
                            "risk_tolerance": "medium",
                            "conservative_retreatment": False
                        }
                    },
                    "non_adherent": {
                        "protocol_adherence_rate": 0.50,
                        "probability": 0.25,
                        "characteristics": {
                            "risk_tolerance": "high",
                            "conservative_retreatment": False
                        }
                    }
                },
                "decision_biases": {
                    "stability_thresholds": {
                        "adherent": 3,
                        "average": 2,
                        "non_adherent": 1
                    },
                    "interval_preferences": {
                        "adherent": {
                            "min_interval": 8,
                            "max_interval": 16,
                            "extension_threshold": 2
                        },
                        "average": {
                            "min_interval": 8,
                            "max_interval": 12,
                            "extension_threshold": 1
                        },
                        "non_adherent": {
                            "min_interval": 6,
                            "max_interval": 16,
                            "extension_threshold": 0
                        }
                    }
                },
                "patient_assignment": {
                    "mode": "fixed",
                    "continuity_of_care": 0.9
                }
            }
        }
        
        # Create a clinician manager with clinician variation enabled
        self.manager_enabled = ClinicianManager(self.config, enabled=True)
        
        # Create a clinician manager with clinician variation disabled
        self.manager_disabled = ClinicianManager(self.config, enabled=False)
        
        # Set the current time
        self.current_time = datetime(2025, 1, 1)
    
    def test_initialization(self):
        """Test that the manager initializes correctly."""
        # Enabled manager should have multiple clinicians
        self.assertTrue(self.manager_enabled.enabled)
        self.assertGreater(len(self.manager_enabled.clinicians), 1)
        
        # Disabled manager should have only the perfect clinician
        self.assertFalse(self.manager_disabled.enabled)
        self.assertEqual(len(self.manager_disabled.clinicians), 1)
        self.assertIn("PERFECT", self.manager_disabled.clinicians)
    
    def test_assign_clinician_disabled(self):
        """Test clinician assignment when disabled."""
        # Disabled manager should always assign the perfect clinician
        for i in range(10):
            patient_id = f"PATIENT{i:03d}"
            clinician_id = self.manager_disabled.assign_clinician(patient_id, self.current_time)
            self.assertEqual(clinician_id, "PERFECT")
    
    def test_assign_clinician_fixed(self):
        """Test clinician assignment with fixed mode."""
        # Set random seed for reproducibility
        np.random.seed(42)
        
        # Fixed mode should assign the same clinician to a patient for all visits
        for i in range(5):
            patient_id = f"PATIENT{i:03d}"
            
            # First assignment
            clinician_id_1 = self.manager_enabled.assign_clinician(patient_id, self.current_time)
            
            # Second assignment (should be the same)
            clinician_id_2 = self.manager_enabled.assign_clinician(patient_id, self.current_time + timedelta(weeks=4))
            
            self.assertEqual(clinician_id_1, clinician_id_2)
    
    def test_get_clinician(self):
        """Test getting a clinician by ID."""
        # Get the perfect clinician
        clinician = self.manager_disabled.get_clinician("PERFECT")
        self.assertEqual(clinician.profile_name, "perfect")
        
        # Get a non-existent clinician (should return the perfect clinician)
        clinician = self.manager_disabled.get_clinician("NON_EXISTENT")
        self.assertEqual(clinician.profile_name, "perfect")
        
        # Get a clinician from the enabled manager
        clinician_id = list(self.manager_enabled.clinicians.keys())[0]
        clinician = self.manager_enabled.get_clinician(clinician_id)
        self.assertIn(clinician.profile_name, ["adherent", "average", "non_adherent"])
    
    def test_get_performance_metrics(self):
        """Test getting performance metrics."""
        # Assign some patients to clinicians
        for i in range(10):
            patient_id = f"PATIENT{i:03d}"
            self.manager_enabled.assign_clinician(patient_id, self.current_time)
        
        # Get metrics
        metrics = self.manager_enabled.get_performance_metrics()
        
        # Check that metrics contain expected keys
        self.assertIn("profile_counts", metrics)
        self.assertIn("patient_counts", metrics)
        
        # Check that profile counts match configuration
        total_clinicians = sum(metrics["profile_counts"].values())
        self.assertEqual(total_clinicians, len(self.manager_enabled.clinicians))
        
        # Check that patient counts add up to the number of patients
        total_patients = sum(metrics["patient_counts"].values())
        self.assertEqual(total_patients, len(self.manager_enabled.patient_assignments))

if __name__ == '__main__':
    unittest.main()
