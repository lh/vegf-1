"""Unit tests for the RealisticVisionModel.

This module contains tests to verify that the RealisticVisionModel
produces realistic and variable vision outcomes, including:
1. Natural vision decline over time
2. Vision fluctuations
3. Ceiling effects
4. Patient-specific response factors
5. Non-responder probability
6. Vision decline between injections
"""

import unittest
import numpy as np
from simulation.vision_models import RealisticVisionModel

class TestRealisticVisionModel(unittest.TestCase):
    """Tests for the RealisticVisionModel."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.model = RealisticVisionModel()
        # Set a fixed seed for reproducible tests
        np.random.seed(42)
        
    def test_vision_fluctuation(self):
        """Test that vision measurements include random fluctuations."""
        # Create a basic state
        state = {
            "current_vision": 65,
            "patient_id": "test_patient",
            "interval": 4
        }
        
        # Multiple test runs should give different results due to fluctuation
        results = []
        for _ in range(10):
            vision_change, _ = self.model.calculate_vision_change(
                state=state,
                actions=[],  # No actions, so only fluctuation should occur
                phase="maintenance"
            )
            results.append(vision_change)
        
        # Check that results aren't all the same (fluctuation exists)
        self.assertTrue(len(set(results)) > 1,
                        "Vision measurements should show fluctuations")
        
        # Check that fluctuations are within a reasonable range
        # Vision fluctuation is set to 1.0, so most values should be within ±3
        self.assertTrue(all(abs(r) < 3 for r in results),
                       "Fluctuations should be within a reasonable range")
        
    def test_natural_decline(self):
        """Test that vision naturally declines without treatment."""
        # Create a basic state
        state = {
            "current_vision": 65,
            "patient_id": "test_patient",
            "interval": 8  # 8 weeks since last visit
        }
        
        # Run test with no injection in maintenance phase
        vision_change, _ = self.model.calculate_vision_change(
            state=state,
            actions=[],  # No injection
            phase="maintenance"
        )
        
        # Expect natural decline due to disease progression
        # Natural decline rate is 0.15 letters per week * 8 weeks = -1.2 letters
        # Plus random fluctuation, so should be negative on average
        self.assertLess(vision_change, 0,
                       "Vision should naturally decline without treatment")
        
    def test_ceiling_effect(self):
        """Test that vision improvements diminish as vision approaches ceiling."""
        # Compare vision change for patients with different baseline vision
        low_vision = {
            "current_vision": 30,
            "patient_id": "low_vision_patient",
            "interval": 4
        }
        
        high_vision = {
            "current_vision": 80,
            "patient_id": "high_vision_patient",
            "interval": 4
        }
        
        # Same patient response factor for fair comparison
        self.model.patient_response_factors["low_vision_patient"] = 1.0
        self.model.patient_response_factors["high_vision_patient"] = 1.0
        
        # Run tests with injection in loading phase
        low_vision_change, _ = self.model.calculate_vision_change(
            state=low_vision,
            actions=["injection"],
            phase="loading"
        )
        
        high_vision_change, _ = self.model.calculate_vision_change(
            state=high_vision,
            actions=["injection"],
            phase="loading"
        )
        
        # Expect smaller improvement for patient with high baseline vision
        self.assertGreater(low_vision_change, high_vision_change,
                          "Patient with lower vision should have greater improvement")
        
    def test_patient_response_variability(self):
        """Test that patients have variable responses to treatment."""
        # Create multiple patients
        patient_count = 20
        patient_states = [
            {
                "current_vision": 65,
                "patient_id": f"patient_{i}",
                "interval": 4
            } for i in range(patient_count)
        ]
        
        # Get vision changes with injection in loading phase
        vision_changes = []
        for state in patient_states:
            change, _ = self.model.calculate_vision_change(
                state=state,
                actions=["injection"],
                phase="loading"
            )
            vision_changes.append(change)
        
        # Check that there's significant variation between patients
        variance = np.var(vision_changes)
        self.assertGreater(variance, 3.0,
                          "Patient responses should show significant variation")
        
        # Check for non-responders (very low vision improvement)
        non_responder_count = sum(1 for c in vision_changes if c < 1.0)
        self.assertGreater(non_responder_count, 0,
                          "Some patients should be non-responders")
        
    def test_maintenance_vs_loading(self):
        """Test that maintenance phase has smaller vision improvements than loading."""
        # Create a patient state
        state = {
            "current_vision": 65,
            "patient_id": "test_patient",
            "interval": 4
        }
        
        # Fix response factor for consistent comparison
        self.model.patient_response_factors["test_patient"] = 1.0
        
        # Get vision changes for loading and maintenance phases
        loading_changes = []
        maintenance_changes = []
        
        for _ in range(20):  # Multiple trials for statistical comparison
            loading_change, _ = self.model.calculate_vision_change(
                state=state,
                actions=["injection"],
                phase="loading"
            )
            loading_changes.append(loading_change)
            
            maintenance_change, _ = self.model.calculate_vision_change(
                state=state,
                actions=["injection"],
                phase="maintenance"
            )
            maintenance_changes.append(maintenance_change)
        
        # Expect loading phase to have larger vision improvements on average
        self.assertGreater(np.mean(loading_changes), np.mean(maintenance_changes),
                          "Loading phase should have larger vision improvements")
        
    def test_fluid_detection(self):
        """Test that fluid detection probability is influenced by factors."""
        # Create a patient state
        state = {
            "current_vision": 65,
            "patient_id": "test_patient",
            "interval": 4
        }
        
        # Count fluid detection occurrences for different scenarios
        loading_injection_fluid = 0
        maintenance_no_injection_fluid = 0
        trials = 100
        
        for _ in range(trials):
            _, loading_fluid = self.model.calculate_vision_change(
                state=state,
                actions=["injection"],
                phase="loading"
            )
            if loading_fluid:
                loading_injection_fluid += 1
                
            _, maintenance_fluid = self.model.calculate_vision_change(
                state=state,
                actions=[],  # No injection
                phase="maintenance"
            )
            if maintenance_fluid:
                maintenance_no_injection_fluid += 1
        
        # Expect higher fluid detection in maintenance with no injection
        self.assertGreater(maintenance_no_injection_fluid, loading_injection_fluid,
                          "Maintenance phase without injection should have more fluid detection")
        
if __name__ == '__main__':
    unittest.main()