"""
Test that resource configuration is properly saved and loaded.
"""

import json
import tempfile
from pathlib import Path
from datetime import datetime, date

from simulation_v2.economics.resource_tracker import ResourceTracker, load_resource_config
from ape.core.storage.writer import ParquetWriter
from ape.core.results.parquet import ParquetResults
from ape.core.results.base import SimulationMetadata


def test_resource_config_persistence():
    """Test that resource configuration is saved and loaded correctly."""
    
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        output_dir = Path(temp_dir)
        
        # 1. Create a resource tracker with specific configuration
        config_path = Path(__file__).parent / 'protocols' / 'resources' / 'nhs_standard_resources.yaml'
        config = load_resource_config(str(config_path))
        resource_tracker = ResourceTracker(config)
        
        # Track some visits to generate data
        resource_tracker.track_visit(
            date(2024, 1, 15),
            'injection_only',
            'P001',
            injection_given=True,
            oct_performed=False
        )
        
        resource_tracker.track_visit(
            date(2024, 1, 15),
            'decision_with_injection',
            'P002',
            injection_given=True,
            oct_performed=True
        )
        
        # 2. Create a mock results object with the resource tracker
        class MockResults:
            def __init__(self):
                self.resource_tracker = resource_tracker
                self.patient_histories = {'P001': MockPatient(), 'P002': MockPatient()}
                self.total_injections = 2
                self.final_vision_mean = 70.0
                self.final_vision_std = 5.0
                self.discontinuation_rate = 0.0
        
        class MockPatient:
            def __init__(self):
                self.enrollment_date = datetime(2024, 1, 1)
                self.baseline_vision = 70
                self.current_vision = 72
                self.current_state = 'active'
                self.injection_count = 1
                self.visit_history = [
                    {'date': datetime(2024, 1, 15), 'vision': 72, 'treatment_given': True}
                ]
                self.is_discontinued = False
        
        mock_results = MockResults()
        
        # 3. Save using ParquetWriter
        writer = ParquetWriter(output_dir)
        writer.write_simulation_results(mock_results)
        
        # 4. Verify resource_config.json was created
        config_file = output_dir / 'resource_config.json'
        assert config_file.exists(), f"Resource config file not found at {config_file}"
        
        # Check contents
        with open(config_file, 'r') as f:
            saved_config = json.load(f)
        
        print("\nSaved configuration:")
        print(f"Roles: {list(saved_config['roles'].keys())}")
        print(f"Session parameters: {saved_config['session_parameters']}")
        print(f"Visit requirements: {list(saved_config['visit_requirements'].keys())}")
        
        # Verify key components are present
        assert 'roles' in saved_config
        assert 'injector' in saved_config['roles']
        assert saved_config['roles']['injector']['capacity_per_session'] == 14
        
        assert 'session_parameters' in saved_config
        assert saved_config['session_parameters']['sessions_per_day'] == 2
        
        assert 'visit_requirements' in saved_config
        assert 'injection_only' in saved_config['visit_requirements']
        
        # 5. Load using ParquetResults
        metadata = SimulationMetadata(
            sim_id='test-001',
            protocol_name='Test Protocol',
            protocol_version='1.0',
            engine_type='abs',
            n_patients=2,
            duration_years=1.0,
            seed=42,
            timestamp=datetime.now(),
            runtime_seconds=1.0,
            storage_type='parquet',
            memorable_name='test-sim'
        )
        
        # Save metadata
        with open(output_dir / 'metadata.json', 'w') as f:
            json.dump(metadata.to_dict(), f)
        
        # Load results
        loaded_results = ParquetResults(metadata, output_dir)
        
        # 6. Verify resource tracker was loaded correctly
        assert loaded_results.resource_tracker is not None, "Resource tracker not loaded"
        
        # Check configuration was loaded
        assert hasattr(loaded_results.resource_tracker, 'roles')
        assert 'injector' in loaded_results.resource_tracker.roles
        assert loaded_results.resource_tracker.roles['injector']['capacity_per_session'] == 14
        
        # Check calculate_sessions_needed works
        sessions_needed = loaded_results.resource_tracker.calculate_sessions_needed(
            date(2024, 1, 15), 'injector'
        )
        # We had 2 injection procedures, capacity is 14 per session
        expected_sessions = 2 / 14
        assert abs(sessions_needed - expected_sessions) < 0.01, \
            f"Expected {expected_sessions} sessions, got {sessions_needed}"
        
        print("\n✅ All tests passed!")
        print(f"Successfully loaded resource tracker with {len(loaded_results.resource_tracker.roles)} roles")
        print(f"Calculate sessions needed: {sessions_needed:.2f} sessions for 2 procedures")


if __name__ == "__main__":
    test_resource_config_persistence()