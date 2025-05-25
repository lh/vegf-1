"""
Test FOV to TOM serialization.

FOV (internal): NAIVE, STABLE, ACTIVE, HIGHLY_ACTIVE
TOM (parquet): 'inject', 'no_inject'
"""

import pytest
import pandas as pd
from datetime import datetime
from simulation_v2.core.disease_model import DiseaseState
from simulation_v2.serialization.parquet_writer import (
    fov_to_tom, 
    serialize_visit,
    serialize_patient_visits
)


class TestFOVToTOM:
    """Test the core FOV to TOM mapping."""
    
    def test_stable_maps_to_no_inject(self):
        """STABLE should map to 'no_inject'."""
        assert fov_to_tom(DiseaseState.STABLE, treatment_given=False) == 'no_inject'
        assert fov_to_tom(DiseaseState.STABLE, treatment_given=True) == 'inject'
        
    def test_active_states_map_based_on_treatment(self):
        """NAIVE, ACTIVE, HIGHLY_ACTIVE map based on treatment given."""
        # When treatment is given
        assert fov_to_tom(DiseaseState.NAIVE, treatment_given=True) == 'inject'
        assert fov_to_tom(DiseaseState.ACTIVE, treatment_given=True) == 'inject'
        assert fov_to_tom(DiseaseState.HIGHLY_ACTIVE, treatment_given=True) == 'inject'
        
        # When treatment is not given (e.g., capacity constraints)
        assert fov_to_tom(DiseaseState.NAIVE, treatment_given=False) == 'no_inject'
        assert fov_to_tom(DiseaseState.ACTIVE, treatment_given=False) == 'no_inject'
        assert fov_to_tom(DiseaseState.HIGHLY_ACTIVE, treatment_given=False) == 'no_inject'


class TestVisitSerialization:
    """Test serialization of individual visits."""
    
    def test_serialize_basic_visit(self):
        """Should serialize visit with FOV to TOM conversion."""
        visit = {
            'date': datetime(2024, 1, 15),
            'disease_state': DiseaseState.ACTIVE,
            'treatment_given': True,
            'vision': 72.5,
            'discontinuation_type': None
        }
        
        serialized = serialize_visit(visit)
        
        # Check TOM conversion
        assert serialized['treatment_decision'] == 'inject'
        
        # Check other fields
        assert serialized['vision'] == 72.5
        assert serialized['date'] == datetime(2024, 1, 15)
        assert serialized['discontinuation_type'] == 'none'
        
        # FOV state should NOT be in output
        assert 'disease_state' not in serialized
        assert 'treatment_given' not in serialized
        
    def test_serialize_with_discontinuation(self):
        """Should handle discontinuation types."""
        visit = {
            'date': datetime(2024, 6, 1),
            'disease_state': DiseaseState.STABLE,
            'treatment_given': False,
            'vision': 75.0,
            'discontinuation_type': 'planned'
        }
        
        serialized = serialize_visit(visit)
        
        assert serialized['treatment_decision'] == 'no_inject'
        assert serialized['discontinuation_type'] == 'planned'
        
    def test_serialize_monitoring_visit(self):
        """Monitoring visits should be no_inject."""
        visit = {
            'date': datetime(2024, 7, 1),
            'disease_state': DiseaseState.ACTIVE,  # Still active
            'treatment_given': False,  # But monitoring only
            'vision': 71.0,
            'discontinuation_type': None,
            'visit_type': 'monitoring'
        }
        
        serialized = serialize_visit(visit)
        
        assert serialized['treatment_decision'] == 'no_inject'
        

class TestPatientSerialization:
    """Test serialization of complete patient histories."""
    
    def test_serialize_patient_history(self):
        """Should serialize full patient history to DataFrame-ready format."""
        patient_visits = [
            {
                'date': datetime(2024, 1, 1),
                'disease_state': DiseaseState.NAIVE,
                'treatment_given': True,
                'vision': 70
            },
            {
                'date': datetime(2024, 2, 1),
                'disease_state': DiseaseState.ACTIVE,
                'treatment_given': True,
                'vision': 72
            },
            {
                'date': datetime(2024, 3, 1),
                'disease_state': DiseaseState.STABLE,
                'treatment_given': False,
                'vision': 73
            }
        ]
        
        serialized = serialize_patient_visits('P001', patient_visits)
        
        assert len(serialized) == 3
        assert all(v['patient_id'] == 'P001' for v in serialized)
        assert serialized[0]['treatment_decision'] == 'inject'
        assert serialized[1]['treatment_decision'] == 'inject'
        assert serialized[2]['treatment_decision'] == 'no_inject'
        
    def test_create_parquet_dataframe(self):
        """Should create DataFrame suitable for Parquet."""
        patients_data = {
            'P001': [
                {
                    'date': datetime(2024, 1, 1),
                    'disease_state': DiseaseState.ACTIVE,
                    'treatment_given': True,
                    'vision': 70
                }
            ],
            'P002': [
                {
                    'date': datetime(2024, 1, 1),
                    'disease_state': DiseaseState.STABLE,
                    'treatment_given': False,
                    'vision': 75
                }
            ]
        }
        
        # This would be in the actual serialization module
        all_visits = []
        for patient_id, visits in patients_data.items():
            all_visits.extend(serialize_patient_visits(patient_id, visits))
            
        df = pd.DataFrame(all_visits)
        
        # Check DataFrame structure
        assert len(df) == 2
        assert set(df.columns) == {
            'patient_id', 'date', 'treatment_decision', 
            'vision', 'discontinuation_type'
        }
        assert df['treatment_decision'].tolist() == ['inject', 'no_inject']
        
        # Should be Parquet-compatible (no enums)
        assert df['treatment_decision'].dtype == 'object'  # string
        assert df['vision'].dtype == 'float64'