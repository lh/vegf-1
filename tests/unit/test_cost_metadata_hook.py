"""
Test the minimal hook integration for cost metadata.

This ensures the hook works correctly and doesn't break existing functionality.
"""

import pytest
from datetime import datetime
from simulation.patient_state import PatientState
from simulation.economics import create_cost_metadata_enhancer


class TestCostMetadataHook:
    """Test suite for the minimal hook approach"""
    
    def test_patient_state_works_without_enhancer(self):
        """Test that PatientState works normally without the enhancer"""
        # Given a patient state without enhancer
        patient = PatientState(
            patient_id="test_001",
            protocol_name="test_protocol",
            initial_vision=70.0,
            start_time=datetime(2025, 1, 1)
        )
        
        # When recording a visit
        visit_time = datetime(2025, 1, 15)
        actions = ['injection', 'oct_scan']
        visit_data = {
            'visit_type': 'injection_visit',
            'drug': 'eylea_2mg',
            'baseline_vision': 70.0,
            'vision': 72.0,
            'disease_state': 'ACTIVE'
        }
        
        # Record visit (should work without error)
        patient._record_visit(visit_time, actions, visit_data)
        
        # Then visit should be recorded normally
        assert len(patient.state['visit_history']) == 1
        visit = patient.state['visit_history'][0]
        
        # Standard fields should exist
        assert visit['date'] == visit_time.replace(second=0, microsecond=0)
        assert visit['actions'] == actions
        assert visit['type'] == 'injection_visit'
        
        # But no metadata field (since no enhancer)
        assert 'metadata' not in visit
    
    def test_patient_state_with_cost_enhancer(self):
        """Test that PatientState works with the cost enhancer attached"""
        # Given a patient state with cost enhancer
        patient = PatientState(
            patient_id="test_002",
            protocol_name="test_protocol",
            initial_vision=70.0,
            start_time=datetime(2025, 1, 1)
        )
        
        # Attach the cost metadata enhancer
        patient.visit_metadata_enhancer = create_cost_metadata_enhancer()
        
        # When recording a visit
        visit_time = datetime(2025, 1, 15)
        actions = ['injection', 'oct_scan', 'visual_acuity_test']
        visit_data = {
            'visit_type': 'injection_visit',
            'drug': 'eylea_2mg',
            'baseline_vision': 70.0,
            'vision': 72.0,
            'disease_state': 'ACTIVE'
        }
        
        patient._record_visit(visit_time, actions, visit_data)
        
        # Then visit should have metadata
        assert len(patient.state['visit_history']) == 1
        visit = patient.state['visit_history'][0]
        
        # Standard fields should still exist
        assert visit['date'] == visit_time.replace(second=0, microsecond=0)
        assert visit['actions'] == actions
        assert visit['type'] == 'injection_visit'
        
        # And metadata should be added
        assert 'metadata' in visit
        metadata = visit['metadata']
        
        # Check cost components
        assert 'components_performed' in metadata
        assert set(metadata['components_performed']) == {
            'injection', 'oct_scan', 'visual_acuity_test'
        }
        
        # Check visit subtype
        assert metadata['visit_subtype'] == 'injection_loading'  # Default phase is loading
        
        # Check drug
        assert metadata['drug'] == 'eylea_2mg'
        
        # Check visit number
        assert metadata['visit_number'] == 1
        
        # Check days since last
        assert metadata['days_since_last'] == 0  # First visit
    
    def test_enhancer_preserves_existing_fields(self):
        """Test that the enhancer doesn't modify existing visit fields"""
        # Given a patient with enhancer
        patient = PatientState(
            patient_id="test_003",
            protocol_name="test_protocol",
            initial_vision=65.0,
            start_time=datetime(2025, 1, 1)
        )
        patient.visit_metadata_enhancer = create_cost_metadata_enhancer()
        
        # Set specific state values
        patient.state['current_phase'] = 'maintenance'
        patient.state['current_vision'] = 68.0
        patient.state['disease_state'] = 'STABLE'
        
        # When recording a visit with all fields
        visit_time = datetime(2025, 2, 1)
        actions = ['injection', 'virtual_review']
        visit_data = {
            'visit_type': 'injection_visit',
            'drug': 'eylea_8mg',
            'baseline_vision': 65.0,
            'vision': 68.0,
            'disease_state': 'STABLE',
            'special_event': 'protocol_switch'
        }
        
        patient._record_visit(visit_time, actions, visit_data)
        
        # Then all original fields should be preserved
        visit = patient.state['visit_history'][0]
        assert visit['date'] == visit_time.replace(second=0, microsecond=0)
        assert visit['actions'] == actions
        assert visit['vision'] == 68.0
        assert visit['baseline_vision'] == 65.0
        assert visit['phase'] == 'maintenance'
        assert visit['type'] == 'injection_visit'
        assert visit['disease_state'] == 'STABLE'
        
        # And metadata should be correct
        assert visit['metadata']['visit_subtype'] == 'injection_virtual'
        assert visit['metadata']['drug'] == 'eylea_8mg'
        assert visit['metadata']['special_event'] == 'protocol_switch'
    
    def test_days_since_last_calculation(self):
        """Test that days_since_last is calculated correctly"""
        # Given a patient with enhancer
        patient = PatientState(
            patient_id="test_004",
            protocol_name="test_protocol",
            initial_vision=70.0,
            start_time=datetime(2025, 1, 1)
        )
        patient.visit_metadata_enhancer = create_cost_metadata_enhancer()
        
        # Record first visit
        visit1_time = datetime(2025, 1, 1)
        patient._record_visit(
            visit1_time,
            ['injection'],
            {'visit_type': 'injection_visit', 'drug': 'eylea_2mg'}
        )
        
        # Record second visit 28 days later
        visit2_time = datetime(2025, 1, 29)
        patient._record_visit(
            visit2_time,
            ['injection'],
            {'visit_type': 'injection_visit', 'drug': 'eylea_2mg'}
        )
        
        # Check metadata
        visit1 = patient.state['visit_history'][0]
        visit2 = patient.state['visit_history'][1]
        
        assert visit1['metadata']['days_since_last'] == 0
        assert visit2['metadata']['days_since_last'] == 28
        assert visit2['metadata']['visit_number'] == 2
    
    def test_component_mapping_variations(self):
        """Test that various action names map correctly to components"""
        # Given a patient with enhancer
        patient = PatientState(
            patient_id="test_005",
            protocol_name="test_protocol",
            initial_vision=70.0,
            start_time=datetime(2025, 1, 1)
        )
        patient.visit_metadata_enhancer = create_cost_metadata_enhancer()
        
        # Test various action name variations
        actions = ['oct', 'vision_test', 'iop_check', 'f2f_review']
        patient._record_visit(
            datetime(2025, 1, 1),
            actions,
            {'visit_type': 'monitoring_visit'}
        )
        
        # Check that components are mapped correctly
        visit = patient.state['visit_history'][0]
        components = visit['metadata']['components_performed']
        
        assert 'oct_scan' in components  # 'oct' -> 'oct_scan'
        assert 'visual_acuity_test' in components  # 'vision_test' -> 'visual_acuity_test'
        assert 'pressure_check' in components  # 'iop_check' -> 'pressure_check'
        assert 'face_to_face_review' in components  # 'f2f_review' -> 'face_to_face_review'
    
    def test_visit_subtype_determination(self):
        """Test various visit subtype determinations"""
        patient = PatientState(
            patient_id="test_006",
            protocol_name="test_protocol",
            initial_vision=70.0,
            start_time=datetime(2025, 1, 1)
        )
        patient.visit_metadata_enhancer = create_cost_metadata_enhancer()
        
        # Test 1: Loading injection
        patient.state['current_phase'] = 'loading'
        patient._record_visit(
            datetime(2025, 1, 1),
            ['injection'],
            {'visit_type': 'injection_visit'}
        )
        assert patient.state['visit_history'][-1]['metadata']['visit_subtype'] == 'injection_loading'
        
        # Test 2: Virtual monitoring
        patient.state['current_phase'] = 'maintenance'
        patient._record_visit(
            datetime(2025, 2, 1),
            ['oct_scan', 'virtual_review'],
            {'visit_type': 'monitoring_visit'}
        )
        assert patient.state['visit_history'][-1]['metadata']['visit_subtype'] == 'monitoring_virtual'
        
        # Test 3: Face-to-face monitoring
        patient._record_visit(
            datetime(2025, 3, 1),
            ['oct_scan', 'face_to_face_review'],
            {'visit_type': 'monitoring_visit'}
        )
        assert patient.state['visit_history'][-1]['metadata']['visit_subtype'] == 'monitoring_face_to_face'
        
        # Test 4: Regular visit with injection (maintenance) - defaults to virtual
        patient._record_visit(
            datetime(2025, 4, 1),
            ['injection', 'oct_scan'],
            {'visit_type': 'regular_visit'}
        )
        assert patient.state['visit_history'][-1]['metadata']['visit_subtype'] == 'injection_virtual'