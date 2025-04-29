"""Unit tests for vision data recording functionality."""

import unittest
from datetime import datetime, timedelta
from simulation.patient_state import PatientState
from simulation.clinical_model import ClinicalModel
from simulation.abs import AgentBasedSimulation, Event
from simulation.config import SimulationConfig
from protocols.protocol_parser import ProtocolParser

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
        visit_data = patient_state.process_visit(event.time, event.data['actions'], self.clinical_model)
        
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
    
        # Use the wrapper instead of the config
        sim = AgentBasedSimulation(config_wrapper, self.start_date)
        sim.add_patient("test123", "treat_and_extend")
        
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
