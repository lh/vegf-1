"""
Integration tests for the enhanced discontinuation model with ABS implementation.

This module contains tests that verify the enhanced discontinuation model works correctly
with the Agent-Based Simulation (ABS) implementation, testing different discontinuation types,
monitoring schedules, clinician variation, and end-to-end patient pathways.
"""

import unittest
import sys
import os
from datetime import datetime, timedelta
import numpy as np
from unittest.mock import patch, MagicMock

# Add the parent directory to the path so we can import the simulation modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from simulation.config import SimulationConfig
from treat_and_extend_abs import TreatAndExtendABS, run_treat_and_extend_abs
from simulation.enhanced_discontinuation_manager import EnhancedDiscontinuationManager
from simulation.clinician import Clinician, ClinicianManager

class EnhancedDiscontinuationABSTest(unittest.TestCase):
    """Test cases for enhanced discontinuation in ABS implementation."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Set fixed random seed for reproducibility
        np.random.seed(42)
        
        # Load default test configuration
        self.config_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "configs",
            "test_abs_default.yaml"
        )
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        
        # Use the enhanced discontinuation config as a base if it exists
        try:
            self.config = SimulationConfig.from_yaml("protocols/simulation_configs/enhanced_discontinuation.yaml")
        except:
            # Create a basic config if the enhanced discontinuation config doesn't exist
            self.config = SimulationConfig.from_yaml("eylea_literature_based")
        
        # Override simulation parameters for faster tests
        self.config.duration_days = 365  # 1 year
        self.config.num_patients = 10    # Small number of patients
        self.config.random_seed = 42     # Fixed seed
    
    def _run_simulation(self, config=None, duration_days=None, num_patients=None):
        """Run an ABS simulation with the given configuration."""
        if config is None:
            config = self.config
        
        if duration_days is not None:
            config.duration_days = duration_days
        
        if num_patients is not None:
            config.num_patients = num_patients
        
        # Create and run simulation
        sim = TreatAndExtendABS(config)
        return sim.run()
    
    def _count_discontinuations_by_type(self, patient_histories):
        """Count discontinuations by type in patient histories."""
        counts = {
            "stable_max_interval": 0,
            "random_administrative": 0,
            "treatment_duration": 0,
            "premature": 0,
            "total": 0
        }
        
        for patient_id, visits in patient_histories.items():
            for visit in visits:
                if "treatment_status" in visit and visit.get("treatment_status", {}).get("cessation_type"):
                    cessation_type = visit["treatment_status"]["cessation_type"]
                    counts[cessation_type] = counts.get(cessation_type, 0) + 1
                    counts["total"] += 1
                    break  # Count each patient only once
        
        return counts
    
    def _count_monitoring_visits(self, patient_histories):
        """Count monitoring visits in patient histories."""
        monitoring_visits = 0
        
        for patient_id, visits in patient_histories.items():
            for visit in visits:
                if visit.get("type") == "monitoring_visit":
                    monitoring_visits += 1
        
        return monitoring_visits
    
    def _count_retreatments(self, patient_histories):
        """Count retreatments in patient histories."""
        retreatments = 0
        
        for patient_id, visits in patient_histories.items():
            # Look for transitions from monitoring to active treatment
            was_monitoring = False
            for visit in visits:
                if visit.get("type") == "monitoring_visit":
                    was_monitoring = True
                elif was_monitoring and visit.get("type") == "regular_visit":
                    retreatments += 1
                    was_monitoring = False
        
        return retreatments
    
    def test_stable_max_interval_discontinuation(self):
        """Test that patients who meet stable max interval criteria are discontinued."""
        # Modify config to force stable max interval discontinuation
        self.config.parameters["discontinuation"]["criteria"]["stable_max_interval"]["probability"] = 1.0
        self.config.parameters["discontinuation"]["criteria"]["random_administrative"]["annual_probability"] = 0.0
        self.config.parameters["discontinuation"]["criteria"]["treatment_duration"]["probability"] = 0.0
        self.config.parameters["discontinuation"]["criteria"]["premature"]["probability_factor"] = 0.0
        
        # Run simulation for 2 years to ensure patients reach max interval
        patient_histories = self._run_simulation(duration_days=730)
        
        # Count discontinuations by type
        counts = self._count_discontinuations_by_type(patient_histories)
        
        # Verify that some patients were discontinued with stable_max_interval
        self.assertGreater(counts["stable_max_interval"], 0)
        self.assertEqual(counts["random_administrative"], 0)
        self.assertEqual(counts["treatment_duration"], 0)
        self.assertEqual(counts["premature"], 0)
        self.assertEqual(counts["total"], counts["stable_max_interval"])
    
    def test_random_administrative_discontinuation(self):
        """Test that administrative discontinuations occur at the expected rate."""
        # Modify config to force administrative discontinuation
        self.config.parameters["discontinuation"]["criteria"]["stable_max_interval"]["probability"] = 0.0
        self.config.parameters["discontinuation"]["criteria"]["random_administrative"]["annual_probability"] = 1.0
        self.config.parameters["discontinuation"]["criteria"]["treatment_duration"]["probability"] = 0.0
        self.config.parameters["discontinuation"]["criteria"]["premature"]["probability_factor"] = 0.0
        
        # Run simulation
        patient_histories = self._run_simulation()
        
        # Count discontinuations by type
        counts = self._count_discontinuations_by_type(patient_histories)
        
        # Verify that some patients were discontinued with random_administrative
        self.assertEqual(counts["stable_max_interval"], 0)
        self.assertGreater(counts["random_administrative"], 0)
        self.assertEqual(counts["treatment_duration"], 0)
        self.assertEqual(counts["premature"], 0)
        self.assertEqual(counts["total"], counts["random_administrative"])
    
    def test_treatment_duration_discontinuation(self):
        """Test that duration-based discontinuations occur after the threshold period."""
        # Modify config to force treatment duration discontinuation
        self.config.parameters["discontinuation"]["criteria"]["stable_max_interval"]["probability"] = 0.0
        self.config.parameters["discontinuation"]["criteria"]["random_administrative"]["annual_probability"] = 0.0
        self.config.parameters["discontinuation"]["criteria"]["treatment_duration"]["threshold_weeks"] = 26  # 6 months
        self.config.parameters["discontinuation"]["criteria"]["treatment_duration"]["probability"] = 1.0
        self.config.parameters["discontinuation"]["criteria"]["premature"]["probability_factor"] = 0.0
        
        # Run simulation
        patient_histories = self._run_simulation()
        
        # Count discontinuations by type
        counts = self._count_discontinuations_by_type(patient_histories)
        
        # Verify that some patients were discontinued with treatment_duration
        self.assertEqual(counts["stable_max_interval"], 0)
        self.assertEqual(counts["random_administrative"], 0)
        self.assertGreater(counts["treatment_duration"], 0)
        self.assertEqual(counts["premature"], 0)
        self.assertEqual(counts["total"], counts["treatment_duration"])
    
    def test_premature_discontinuation(self):
        """Test that premature discontinuations can occur before max interval is reached."""
        # Modify config to force premature discontinuation
        self.config.parameters["discontinuation"]["criteria"]["stable_max_interval"]["probability"] = 0.0
        self.config.parameters["discontinuation"]["criteria"]["random_administrative"]["annual_probability"] = 0.0
        self.config.parameters["discontinuation"]["criteria"]["treatment_duration"]["probability"] = 0.0
        self.config.parameters["discontinuation"]["criteria"]["premature"]["min_interval_weeks"] = 8
        self.config.parameters["discontinuation"]["criteria"]["premature"]["probability_factor"] = 10.0
        
        # Ensure clinicians are enabled with non-adherent profile
        self.config.parameters["clinicians"]["enabled"] = True
        self.config.parameters["clinicians"]["profiles"]["non_adherent"]["protocol_adherence_rate"] = 0.0
        self.config.parameters["clinicians"]["profiles"]["non_adherent"]["probability"] = 1.0
        
        # Run simulation
        patient_histories = self._run_simulation()
        
        # Count discontinuations by type
        counts = self._count_discontinuations_by_type(patient_histories)
        
        # Verify that some patients were discontinued prematurely
        self.assertEqual(counts["stable_max_interval"], 0)
        self.assertEqual(counts["random_administrative"], 0)
        self.assertEqual(counts["treatment_duration"], 0)
        self.assertGreater(counts["premature"], 0)
        self.assertEqual(counts["total"], counts["premature"])
    
    def test_no_monitoring_for_administrative_cessation(self):
        """Test that administrative cessation results in no monitoring visits."""
        # Modify config to force administrative discontinuation
        self.config.parameters["discontinuation"]["criteria"]["stable_max_interval"]["probability"] = 0.0
        self.config.parameters["discontinuation"]["criteria"]["random_administrative"]["annual_probability"] = 1.0
        self.config.parameters["discontinuation"]["criteria"]["treatment_duration"]["probability"] = 0.0
        self.config.parameters["discontinuation"]["criteria"]["premature"]["probability_factor"] = 0.0
        
        # Ensure cessation_types mapping is correct
        if "cessation_types" not in self.config.parameters["discontinuation"]["monitoring"]:
            self.config.parameters["discontinuation"]["monitoring"]["cessation_types"] = {
                "random_administrative": "none"
            }
        else:
            self.config.parameters["discontinuation"]["monitoring"]["cessation_types"]["random_administrative"] = "none"
        
        # Run simulation
        patient_histories = self._run_simulation()
        
        # Count discontinuations and monitoring visits
        counts = self._count_discontinuations_by_type(patient_histories)
        monitoring_visits = self._count_monitoring_visits(patient_histories)
        
        # Verify that patients were discontinued but no monitoring visits occurred
        self.assertGreater(counts["random_administrative"], 0)
        self.assertEqual(monitoring_visits, 0)
    
    def test_planned_monitoring_schedule(self):
        """Test that planned cessation results in the correct monitoring schedule."""
        # Modify config to force stable max interval discontinuation
        self.config.parameters["discontinuation"]["criteria"]["stable_max_interval"]["probability"] = 1.0
        self.config.parameters["discontinuation"]["criteria"]["random_administrative"]["annual_probability"] = 0.0
        self.config.parameters["discontinuation"]["criteria"]["treatment_duration"]["probability"] = 0.0
        self.config.parameters["discontinuation"]["criteria"]["premature"]["probability_factor"] = 0.0
        
        # Ensure cessation_types mapping is correct
        if "cessation_types" not in self.config.parameters["discontinuation"]["monitoring"]:
            self.config.parameters["discontinuation"]["monitoring"]["cessation_types"] = {
                "stable_max_interval": "planned"
            }
        else:
            self.config.parameters["discontinuation"]["monitoring"]["cessation_types"]["stable_max_interval"] = "planned"
        
        # Define expected monitoring schedule
        planned_schedule = self.config.parameters["discontinuation"]["monitoring"]["planned"]["follow_up_schedule"]
        
        # Run simulation for 2 years to ensure patients reach max interval and have monitoring visits
        patient_histories = self._run_simulation(duration_days=730)
        
        # Count discontinuations and monitoring visits
        counts = self._count_discontinuations_by_type(patient_histories)
        monitoring_visits = self._count_monitoring_visits(patient_histories)
        
        # Verify that patients were discontinued and monitoring visits occurred
        self.assertGreater(counts["stable_max_interval"], 0)
        self.assertGreater(monitoring_visits, 0)
        
        # Verify monitoring schedule by checking intervals between discontinuation and monitoring visits
        for patient_id, visits in patient_histories.items():
            # Find discontinuation visit
            discontinuation_visit = None
            for i, visit in enumerate(visits):
                if visit.get("treatment_status", {}).get("cessation_type") == "stable_max_interval":
                    discontinuation_visit = visit
                    discontinuation_index = i
                    break
            
            if discontinuation_visit:
                # Count monitoring visits and check their timing
                monitoring_indices = []
                for i, visit in enumerate(visits):
                    if i > discontinuation_index and visit.get("type") == "monitoring_visit":
                        monitoring_indices.append(i)
                
                # Verify number of monitoring visits matches expected schedule
                # Note: Some visits might not occur if they're scheduled after the simulation end
                self.assertLessEqual(len(monitoring_indices), len(planned_schedule))
                
                # If we have monitoring visits, check the first one's timing
                if monitoring_indices:
                    first_monitoring_visit = visits[monitoring_indices[0]]
                    discontinuation_date = discontinuation_visit["date"]
                    monitoring_date = first_monitoring_visit["date"]
                    
                    # Calculate weeks between discontinuation and first monitoring visit
                    weeks_diff = (monitoring_date - discontinuation_date).days / 7
                    
                    # Verify it's close to the first scheduled follow-up
                    # Allow some flexibility due to scheduling constraints
                    self.assertAlmostEqual(weeks_diff, planned_schedule[0], delta=2)
    
    def test_clinician_influence_on_retreatment(self):
        """Test that clinician risk tolerance affects retreatment decisions."""
        # Modify config to force stable max interval discontinuation
        self.config.parameters["discontinuation"]["criteria"]["stable_max_interval"]["probability"] = 1.0
        self.config.parameters["discontinuation"]["criteria"]["random_administrative"]["annual_probability"] = 0.0
        self.config.parameters["discontinuation"]["criteria"]["treatment_duration"]["probability"] = 0.0
        self.config.parameters["discontinuation"]["criteria"]["premature"]["probability_factor"] = 0.0
        
        # Set high recurrence probability
        self.config.parameters["discontinuation"]["recurrence"]["planned"]["base_annual_rate"] = 0.9
        
        # Run two simulations: one with conservative clinicians, one with non-conservative
        
        # 1. Conservative clinicians (more likely to retreat)
        self.config.parameters["clinicians"]["enabled"] = True
        self.config.parameters["clinicians"]["profiles"]["adherent"]["protocol_adherence_rate"] = 1.0
        self.config.parameters["clinicians"]["profiles"]["adherent"]["probability"] = 1.0
        self.config.parameters["clinicians"]["profiles"]["adherent"]["characteristics"]["conservative_retreatment"] = True
        
        conservative_histories = self._run_simulation(duration_days=730)
        conservative_retreatments = self._count_retreatments(conservative_histories)
        
        # 2. Non-conservative clinicians (less likely to retreat)
        self.config.parameters["clinicians"]["profiles"]["adherent"]["characteristics"]["conservative_retreatment"] = False
        
        non_conservative_histories = self._run_simulation(duration_days=730)
        non_conservative_retreatments = self._count_retreatments(non_conservative_histories)
        
        # Verify that conservative clinicians have more retreatments
        self.assertGreaterEqual(conservative_retreatments, non_conservative_retreatments)
    
    def test_stable_discontinuation_monitoring_recurrence_retreatment_pathway(self):
        """Test patient pathway: stable discontinuation → monitoring → recurrence → retreatment."""
        # Modify config to force stable max interval discontinuation
        self.config.parameters["discontinuation"]["criteria"]["stable_max_interval"]["probability"] = 1.0
        self.config.parameters["discontinuation"]["criteria"]["random_administrative"]["annual_probability"] = 0.0
        self.config.parameters["discontinuation"]["criteria"]["treatment_duration"]["probability"] = 0.0
        self.config.parameters["discontinuation"]["criteria"]["premature"]["probability_factor"] = 0.0
        
        # Set high recurrence probability and detection probability
        self.config.parameters["discontinuation"]["recurrence"]["planned"]["base_annual_rate"] = 0.9
        self.config.parameters["discontinuation"]["monitoring"]["recurrence_detection_probability"] = 1.0
        
        # Set high retreatment probability
        self.config.parameters["discontinuation"]["retreatment"]["probability"] = 1.0
        
        # Run simulation for 2 years to ensure patients reach max interval and have monitoring visits
        patient_histories = self._run_simulation(duration_days=730)
        
        # Count discontinuations and retreatments
        counts = self._count_discontinuations_by_type(patient_histories)
        retreatments = self._count_retreatments(patient_histories)
        
        # Verify that patients were discontinued and retreated
        self.assertGreater(counts["stable_max_interval"], 0)
        self.assertGreater(retreatments, 0)
        
        # Verify the complete pathway for at least one patient
        pathway_verified = False
        for patient_id, visits in patient_histories.items():
            # Check for the sequence: regular visit → discontinuation → monitoring visit → retreatment
            discontinuation_index = None
            monitoring_index = None
            retreatment_index = None
            
            for i, visit in enumerate(visits):
                if visit.get("treatment_status", {}).get("cessation_type") == "stable_max_interval":
                    discontinuation_index = i
                elif discontinuation_index is not None and visit.get("type") == "monitoring_visit":
                    monitoring_index = i
                elif monitoring_index is not None and visit.get("type") == "regular_visit":
                    retreatment_index = i
                    break
            
            if discontinuation_index is not None and monitoring_index is not None and retreatment_index is not None:
                pathway_verified = True
                break
        
        self.assertTrue(pathway_verified, "No patient followed the complete pathway")

if __name__ == '__main__':
    unittest.main()
