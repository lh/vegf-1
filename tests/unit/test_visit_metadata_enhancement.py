"""
Test suite for visit metadata enhancement - Phase 2 of economic analysis.

These tests ensure that visit records contain the necessary metadata
for cost analysis while maintaining backward compatibility.

Note: These tests require the cost metadata enhancer to be attached to
PatientState instances, as we're using a minimal hook approach.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch
from simulation.patient_state import PatientState
from simulation.economics import CostConfig, CostAnalyzer, create_cost_metadata_enhancer


class TestVisitMetadataEnhancement:
    """Test suite for adding cost metadata to visit records"""
    
    @pytest.fixture
    def mock_patient_state(self):
        """Create a mock patient state for testing with cost enhancer"""
        patient = PatientState(
            patient_id="test_patient_001",
            protocol_name="test_protocol",
            initial_vision=65.0,
            start_time=datetime(2025, 1, 1)
        )
        # Attach the cost metadata enhancer
        patient.visit_metadata_enhancer = create_cost_metadata_enhancer()
        
        # Update state to test values
        patient.state['current_vision'] = 70.0
        patient.state['baseline_vision'] = 65.0
        patient.state['current_phase'] = 'loading'
        patient.state['disease_state'] = 'ACTIVE'
        patient.state['visit_count'] = 3
        return patient
    
    def test_visit_record_includes_metadata_field(self, mock_patient_state):
        """Test 2.1: Visit records should include metadata field"""
        # Given a patient state
        patient = mock_patient_state
        
        # When recording a visit
        visit_time = datetime(2025, 1, 1, 10, 0)
        actions = ['injection', 'oct_scan']
        visit_data = {
            'visit_type': 'injection_visit',
            'drug': 'eylea_2mg'
        }
        
        # Record the visit (this will call the enhanced _record_visit)
        patient._record_visit(visit_time, actions, visit_data)
        
        # Then the visit should have metadata field
        assert len(patient.visit_history) == 1
        visit = patient.visit_history[0]
        assert 'metadata' in visit
        assert isinstance(visit['metadata'], dict)
    
    def test_metadata_contains_components_performed(self, mock_patient_state):
        """Test 2.2: Metadata should contain components_performed based on actions"""
        # Given a patient state
        patient = mock_patient_state
        
        # When recording an injection visit with specific actions
        visit_time = datetime(2025, 1, 1, 10, 0)
        actions = ['injection', 'oct_scan', 'visual_acuity_test']
        visit_data = {
            'visit_type': 'injection_visit',
            'drug': 'eylea_2mg'
        }
        
        patient._record_visit(visit_time, actions, visit_data)
        
        # Then metadata should contain the components
        visit = patient.visit_history[0]
        assert 'components_performed' in visit['metadata']
        assert set(visit['metadata']['components_performed']) == {
            'injection', 'oct_scan', 'visual_acuity_test'
        }
    
    def test_metadata_contains_visit_subtype(self, mock_patient_state):
        """Test 2.3: Metadata should contain visit_subtype based on phase and type"""
        # Given a patient in loading phase
        patient = mock_patient_state
        patient.state['current_phase'] = 'loading'
        
        # When recording an injection visit
        visit_time = datetime(2025, 1, 1, 10, 0)
        actions = ['injection', 'visual_acuity_test']
        visit_data = {
            'visit_type': 'injection_visit',
            'drug': 'eylea_2mg'
        }
        
        patient._record_visit(visit_time, actions, visit_data)
        
        # Then metadata should contain appropriate visit_subtype
        visit = patient.visit_history[0]
        assert 'visit_subtype' in visit['metadata']
        assert visit['metadata']['visit_subtype'] == 'injection_loading'
    
    def test_metadata_includes_drug_for_injection(self, mock_patient_state):
        """Test 2.4: Metadata should include drug information for injection visits"""
        # Given a patient
        patient = mock_patient_state
        
        # When recording an injection visit with drug
        visit_time = datetime(2025, 1, 1, 10, 0)
        actions = ['injection']
        visit_data = {
            'visit_type': 'injection_visit',
            'drug': 'eylea_8mg'
        }
        
        patient._record_visit(visit_time, actions, visit_data)
        
        # Then metadata should contain drug information
        visit = patient.visit_history[0]
        assert 'drug' in visit['metadata']
        assert visit['metadata']['drug'] == 'eylea_8mg'
    
    def test_virtual_review_components(self, mock_patient_state):
        """Test 2.5: Virtual review visits should have appropriate components"""
        # Given a patient in maintenance phase
        patient = mock_patient_state
        patient.state['current_phase'] = 'maintenance'
        
        # When recording a monitoring visit with virtual review
        visit_time = datetime(2025, 1, 1, 10, 0)
        actions = ['oct_scan', 'virtual_review']
        visit_data = {
            'visit_type': 'monitoring_visit'
        }
        
        patient._record_visit(visit_time, actions, visit_data)
        
        # Then metadata should reflect virtual review
        visit = patient.visit_history[0]
        assert 'visit_subtype' in visit['metadata']
        assert visit['metadata']['visit_subtype'] == 'monitoring_virtual'
        assert 'virtual_review' in visit['metadata']['components_performed']
    
    def test_face_to_face_review_components(self, mock_patient_state):
        """Test 2.6: Face-to-face visits should have appropriate components"""
        # Given a patient
        patient = mock_patient_state
        
        # When recording a face-to-face monitoring visit
        visit_time = datetime(2025, 1, 1, 10, 0)
        actions = ['oct_scan', 'visual_acuity_test', 'pressure_check', 'face_to_face_review']
        visit_data = {
            'visit_type': 'monitoring_visit'
        }
        
        patient._record_visit(visit_time, actions, visit_data)
        
        # Then metadata should reflect face-to-face review
        visit = patient.visit_history[0]
        assert 'visit_subtype' in visit['metadata']
        assert visit['metadata']['visit_subtype'] == 'monitoring_face_to_face'
        assert 'face_to_face_review' in visit['metadata']['components_performed']
    
    def test_backward_compatibility_preserved(self, mock_patient_state):
        """Test 2.7: Existing visit fields should remain unchanged"""
        # Given a patient
        patient = mock_patient_state
        
        # When recording a visit
        visit_time = datetime(2025, 1, 1, 10, 0)
        actions = ['injection', 'oct_scan']
        visit_data = {
            'visit_type': 'injection_visit',
            'drug': 'eylea_2mg',
            'baseline_vision': 65.0
        }
        
        patient._record_visit(visit_time, actions, visit_data)
        
        # Then all existing fields should be present
        visit = patient.visit_history[0]
        assert visit['date'] == visit_time.replace(second=0, microsecond=0)
        assert visit['actions'] == actions
        assert visit['vision'] == 70.0
        assert visit['baseline_vision'] == 65.0
        assert visit['phase'] == 'loading'
        assert visit['type'] == 'injection_visit'
        assert visit['disease_state'] == 'ACTIVE'
        assert 'treatment_status' in visit
    
    def test_special_event_metadata(self, mock_patient_state):
        """Test 2.8: Special events should be captured in metadata"""
        # Given a patient
        patient = mock_patient_state
        
        # When recording an initial assessment
        visit_time = datetime(2025, 1, 1, 10, 0)
        actions = ['oct_scan', 'visual_acuity_test', 'initial_assessment']
        visit_data = {
            'visit_type': 'initial_visit',
            'special_event': 'initial_assessment'
        }
        
        patient._record_visit(visit_time, actions, visit_data)
        
        # Then metadata should capture the special event
        visit = patient.visit_history[0]
        assert 'special_event' in visit['metadata']
        assert visit['metadata']['special_event'] == 'initial_assessment'
    
    def test_cost_analyzer_can_process_enhanced_visits(self, mock_patient_state):
        """Test 2.9: CostAnalyzer should work with enhanced visit metadata"""
        # Given a cost configuration and analyzer
        config = CostConfig(
            metadata={'name': 'Test Config', 'currency': 'GBP'},
            drug_costs={'eylea_2mg': 800.0},
            visit_components={
                'injection': 150.0,
                'oct_scan': 75.0,
                'visual_acuity_test': 25.0
            },
            visit_types={},
            special_events={}
        )
        analyzer = CostAnalyzer(config)
        
        # And a patient with enhanced visit metadata
        patient = mock_patient_state
        visit_time = datetime(2025, 1, 1, 10, 0)
        actions = ['injection', 'oct_scan', 'visual_acuity_test']
        visit_data = {
            'visit_type': 'injection_visit',
            'drug': 'eylea_2mg'
        }
        
        patient._record_visit(visit_time, actions, visit_data)
        
        # When analyzing the visit
        visit = patient.visit_history[0]
        # Convert datetime to float for analyzer
        visit_for_analysis = visit.copy()
        visit_for_analysis['time'] = 0.0  # Month 0
        visit_for_analysis['patient_id'] = patient.patient_id
        visit_for_analysis['drug'] = visit['metadata']['drug']
        
        cost_event = analyzer.analyze_visit(visit_for_analysis)
        
        # Then cost should be calculated correctly
        assert cost_event is not None
        assert cost_event.amount == 1050.0  # 800 (drug) + 150 + 75 + 25
        assert cost_event.metadata['drug_cost'] == 800.0
        assert cost_event.metadata['visit_cost'] == 250.0
    
    def test_visit_number_tracking(self, mock_patient_state):
        """Test 2.10: Metadata should include visit number for tracking"""
        # Given a patient
        patient = mock_patient_state
        
        # Record multiple visits
        for i in range(3):
            patient._record_visit(
                datetime(2025, 1, i+1),
                ['oct_scan'],
                {'visit_type': 'monitoring_visit'}
            )
        
        # Check visit numbers
        assert patient.visit_history[0]['metadata']['visit_number'] == 1
        assert patient.visit_history[1]['metadata']['visit_number'] == 2
        assert patient.visit_history[2]['metadata']['visit_number'] == 3
    
    def test_days_since_last_visit(self, mock_patient_state):
        """Test 2.11: Metadata should track days since last visit"""
        # Given a patient with a previous visit
        patient = mock_patient_state
        
        # First visit
        visit_time_1 = datetime(2025, 1, 1, 10, 0)
        patient._record_visit(visit_time_1, ['injection'], {'visit_type': 'injection_visit'})
        
        # Second visit 28 days later
        visit_time_2 = datetime(2025, 1, 29, 10, 0)
        patient._record_visit(visit_time_2, ['injection'], {'visit_type': 'injection_visit'})
        
        # Then second visit should track days since last
        second_visit = patient.visit_history[1]
        assert 'days_since_last' in second_visit['metadata']
        assert second_visit['metadata']['days_since_last'] == 28