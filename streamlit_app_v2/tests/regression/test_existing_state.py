"""
Regression tests for session state handling.

Ensures our memory changes don't break state persistence.
"""

import pytest
import pickle
import json
from datetime import datetime
from pathlib import Path


class TestExistingState:
    """Baseline tests for session state handling."""
    
    def test_simulation_results_serializable(self):
        """Verify simulation results can be pickled (current behavior)."""
        # Mock current session state structure
        mock_results = {
            'results': {
                'patient_histories': {
                    'P0001': {
                        'id': 'P0001',
                        'baseline_vision': 70,
                        'current_vision': 65,
                        'visit_history': []
                    }
                },
                'total_injections': 100,
                'final_vision_mean': 68.5,
                'final_vision_std': 12.3,
                'discontinuation_rate': 0.15
            },
            'protocol': {
                'name': 'Test Protocol',
                'version': '1.0.0',
                'path': '/path/to/protocol.yaml'
            },
            'parameters': {
                'engine': 'abs',
                'n_patients': 100,
                'duration_years': 2.0,
                'seed': 42
            },
            'runtime': 5.2,
            'timestamp': datetime.now().isoformat()
        }
        
        # Should serialize without error
        serialized = pickle.dumps(mock_results)
        deserialized = pickle.loads(serialized)
        
        # Verify structure preserved
        assert deserialized['parameters']['n_patients'] == 100
        assert deserialized['results']['total_injections'] == 100
        assert 'patient_histories' in deserialized['results']
        
    def test_protocol_info_structure(self):
        """Verify protocol info structure is preserved."""
        # Check v2 directory first, then fallback to old location
        protocol_path = Path('protocols/v2/eylea.yaml')
        if not protocol_path.exists():
            protocol_path = Path('protocols/eylea.yaml')
        
        protocol_info = {
            'name': 'Eylea T&E',
            'version': '2.0.0',
            'path': str(protocol_path),
            'description': 'Standard Eylea treat and extend protocol',
            'is_temporary': False
        }
        
        # Should be JSON serializable (for file storage)
        json_str = json.dumps(protocol_info)
        restored = json.loads(json_str)
        
        assert restored['name'] == protocol_info['name']
        assert restored['version'] == protocol_info['version']
        assert restored['path'] == protocol_info['path']
        
    def test_audit_trail_structure(self):
        """Verify audit trail structure."""
        audit_trail = [
            {
                'event': 'protocol_loaded',
                'timestamp': datetime.now().isoformat(),
                'protocol': {
                    'name': 'Test',
                    'version': '1.0',
                    'checksum': 'abc123'
                }
            },
            {
                'event': 'simulation_start',
                'timestamp': datetime.now().isoformat(),
                'parameters': {
                    'n_patients': 100,
                    'duration_years': 2.0
                }
            }
        ]
        
        # Should be serializable
        serialized = pickle.dumps(audit_trail)
        restored = pickle.loads(serialized)
        
        assert len(restored) == 2
        assert restored[0]['event'] == 'protocol_loaded'
        assert restored[1]['event'] == 'simulation_start'
        
    def test_patient_object_pickle(self):
        """Test that patient objects can be pickled."""
        import sys
        sys.path.append(str(Path(__file__).parent.parent.parent.parent))
        
        from simulation_v2.core.patient import Patient
        from simulation_v2.core.disease_model import DiseaseState
        
        # Create a patient with some history
        patient = Patient("P0001", baseline_vision=70)
        patient.record_visit(
            date=datetime.now(),
            disease_state=DiseaseState.ACTIVE,
            treatment_given=True,
            vision=68
        )
        
        # Should pickle/unpickle correctly
        pickled = pickle.dumps(patient)
        restored = pickle.loads(pickled)
        
        assert restored.id == "P0001"
        assert restored.baseline_vision == 70
        assert restored.injection_count == 1
        assert len(restored.visit_history) == 1
        
    def test_results_size_estimation(self):
        """Estimate size of results in memory."""
        import sys
        
        # Create increasingly large mock results
        sizes = []
        for n_patients in [10, 100, 1000]:
            mock_results = {
                'results': {
                    'patient_histories': {}
                }
            }
            
            # Add mock patients
            for i in range(n_patients):
                patient_id = f"P{i:04d}"
                mock_results['results']['patient_histories'][patient_id] = {
                    'id': patient_id,
                    'baseline_vision': 70,
                    'current_vision': 65,
                    'visit_history': [
                        {
                            'date': datetime.now().isoformat(),
                            'treatment_given': True,
                            'vision': 68 + j
                        }
                        for j in range(20)  # ~20 visits per patient
                    ]
                }
            
            # Estimate size
            pickled = pickle.dumps(mock_results)
            size_mb = len(pickled) / (1024 * 1024)
            sizes.append({
                'n_patients': n_patients,
                'size_mb': size_mb,
                'bytes_per_patient': len(pickled) / n_patients
            })
            
        # Log for baseline
        print("\nBaseline memory usage:")
        for size_info in sizes:
            print(f"  {size_info['n_patients']} patients: "
                  f"{size_info['size_mb']:.2f} MB "
                  f"({size_info['bytes_per_patient']:.0f} bytes/patient)")
            
        # Verify growth is roughly linear
        if len(sizes) >= 2:
            growth_rate = sizes[-1]['bytes_per_patient'] / sizes[0]['bytes_per_patient']
            assert 0.8 <= growth_rate <= 1.5, "Memory growth should be roughly linear"