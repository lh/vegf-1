"""Unit tests for vision data recording functionality."""

import unittest
from datetime import datetime, timedelta
from simulation.patient_state import PatientState
from simulation.clinical_model import ClinicalModel
from simulation.abs import AgentBasedSimulation, Event
from simulation.config import SimulationConfig
from ape.protocols.protocol_parser import ProtocolParser

class ConfigWrapper:
    """Simple wrapper to provide clinical model parameters."""
    def __init__(self, clinical_model_params, end_date=None):
        self.clinical_model_params = clinical_model_params
        self.end_date = end_date or datetime(2024, 1, 1)
        
    def get_clinical_model_params(self):
        # Default parameters
        default_params = {
            'vision_change': {
                'base_change': {
                    'NAIVE': {'injection': [5, 2], 'no_injection': [0, 0.5]},
                    'STABLE': {'injection': [1, 0.5], 'no_injection': [-0.5, 0.5]},
                    'ACTIVE': {'injection': [3, 1.5], 'no_injection': [-2, 1]},
                    'HIGHLY_ACTIVE': {'injection': [2, 1], 'no_injection': [-3, 1]}
                },
                'time_factor': {'max_weeks': 52},
                'ceiling_factor': {'max_vision': 85},
                'measurement_noise': [0, 2]
            },
            'disease_states': ['NAIVE', 'STABLE', 'ACTIVE', 'HIGHLY_ACTIVE'],
            'transition_probabilities': {
                'NAIVE': {'NAIVE': 0.0, 'STABLE': 0.3, 'ACTIVE': 0.6, 'HIGHLY_ACTIVE': 0.1},
                'STABLE': {'STABLE': 0.7, 'ACTIVE': 0.3, 'HIGHLY_ACTIVE': 0.0},
                'ACTIVE': {'STABLE': 0.2, 'ACTIVE': 0.7, 'HIGHLY_ACTIVE': 0.1},
                'HIGHLY_ACTIVE': {'STABLE': 0.1, 'ACTIVE': 0.3, 'HIGHLY_ACTIVE': 0.6}
            }
        }
        
        # Merge with provided parameters
        params = self.clinical_model_params.copy()
        if 'vision_change' in params:
            if 'base_change' in params['vision_change']:
                default_params['vision_change']['base_change'].update(params['vision_change']['base_change'])
            params['vision_change'] = {**default_params['vision_change'], **params['vision_change']}
        else:
            params['vision_change'] = default_params['vision_change']
            
        # Add disease states and transition probabilities if not present
        if 'disease_states' not in params:
            params['disease_states'] = default_params['disease_states']
        if 'transition_probabilities' not in params:
            params['transition_probabilities'] = default_params['transition_probabilities']
            
        return params
        
    def get_simulation_params(self):
        return {
            "end_date": self.end_date
        }
        
    def get_vision_params(self):
        return {
            "baseline_mean": 65,
            "measurement_noise_sd": 2,
            "max_letters": 85,
            "min_letters": 0,
            "improvement_ceiling": 5,
            "headroom_factor": 0.2
        }
        
    def get_treatment_discontinuation_params(self):
        """
        Get treatment discontinuation parameters.
        
        Returns
        -------
        Dict[str, Any]
            Empty dictionary for test purposes
        """
        return {}

class TestVisionRecording(unittest.TestCase):
    def setUp(self):
        # Load test config using ProtocolParser
        parser = ProtocolParser(base_path="protocols")  # Use default protocol directory
        self.config = parser.load_simulation_config("tests/data/test_vision_config")
        
        # Set up dates
        self.start_date = datetime(2023, 1, 1)
        
        # Create a wrapper with the clinical model parameters
        clinical_model_params = self.config.parameters.get("clinical_model", {})
        config_wrapper = ConfigWrapper(clinical_model_params, self.start_date + timedelta(days=365))
        self.clinical_model = ClinicalModel(config_wrapper)

    def test_vision_data_recording(self):
        """Test that baseline and post-treatment vision are recorded correctly."""
        # Initialize patient with 70 ETDRS letters
        patient_state = PatientState("test123", "treat_and_extend", 70, self.start_date)
        
        # Add treatment_status and disease_state to patient_state to support new clinical model
        patient_state.state["treatment_status"] = {
            "active": True,
            "weeks_since_discontinuation": 0,
            "monitoring_schedule": 12,
            "recurrence_detected": False,
            "discontinuation_date": None,
            "reason_for_discontinuation": None
        }
        
        # Set disease state explicitly to NAIVE (the default state for new patients)
        patient_state.state["disease_state"] = "NAIVE"
        
        # Add required fields for vision change calculation
        patient_state.state["injections"] = 0
        patient_state.state["last_recorded_injection"] = 0
        patient_state.state["weeks_since_last_injection"] = 0
        
        # Create a custom clinical model that doesn't transition disease states
        # This avoids the issue with missing vision change parameters for other states
        class TestClinicalModel(ClinicalModel):
            def simulate_disease_progression(self, current_state):
                # Always return NAIVE state to avoid transitions
                return current_state
        
        # Create a test clinical model
        test_clinical_model = TestClinicalModel(self.clinical_model.config)
        
        # Create test visit event
        event = Event(
            time=self.start_date + timedelta(days=30),
            event_type="visit",
            patient_id="test123",
            data={
                "visit_type": "injection_visit",
                "actions": ["vision_test", "injection"]
            },
            priority=1
        )

        # Process visit and get results
        visit_data = patient_state.process_visit(event.time, event.data['actions'], test_clinical_model)
        
        # Verify vision data
        self.assertEqual(visit_data['baseline_vision'], 70)
        # Vision may not always improve due to randomness, but should be recorded
        self.assertIsNotNone(visit_data['new_vision'])
        self.assertIn('disease_state', visit_data)
        
        # Verify visit record contains both vision values
        self.assertEqual(len(patient_state.visit_history), 1)
        visit_record = patient_state.visit_history[0]
        self.assertEqual(visit_record['vision'], visit_data['new_vision'])
        self.assertEqual(visit_record.get('baseline_vision'), 70)

    def test_abs_vision_recording(self):
        """Test ABS correctly records vision data in patient history."""
        # Create a new ConfigWrapper for the ABS simulation
        clinical_model_params = self.config.parameters.get("clinical_model", {})
        config_wrapper = ConfigWrapper(clinical_model_params, self.start_date + timedelta(days=365))
        
        # Create a custom clinical model that doesn't transition disease states
        class TestClinicalModel(ClinicalModel):
            def simulate_disease_progression(self, current_state):
                # Always return NAIVE state to avoid transitions
                return current_state
        
        # Create a test clinical model
        test_clinical_model = TestClinicalModel(config_wrapper)
    
        # Use the wrapper instead of the config
        sim = AgentBasedSimulation(config_wrapper, self.start_date)
        sim.add_patient("test123", "treat_and_extend")
        
        # Set disease state explicitly to NAIVE (the default state for new patients)
        sim.agents["test123"].state.state["disease_state"] = "NAIVE"
        
        # Replace the clinical model with our test model
        sim.clinical_model = test_clinical_model
        
        # Create test visit event
        event = Event(
            time=self.start_date + timedelta(days=30),
            event_type="visit",
            patient_id="test123",
            data={
                "visit_type": "injection_visit",
                "actions": ["vision_test", "injection"]
            },
            priority=1
        )

        # Process event
        sim.process_event(event)
        
        # Verify history record
        patient = sim.agents["test123"]
        self.assertEqual(len(patient.history), 1)
        visit_record = patient.history[0]
        self.assertIn('baseline_vision', visit_record)
        self.assertIn('vision', visit_record)
        # Vision may change up or down due to disease progression and randomness
        self.assertIsNotNone(visit_record['vision'])
        self.assertIsNotNone(visit_record['baseline_vision'])

if __name__ == "__main__":
    unittest.main()
