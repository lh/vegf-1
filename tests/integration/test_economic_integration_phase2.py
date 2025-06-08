"""
Integration tests for Phase 2 - Visit metadata enhancement.

These tests verify that the cost analysis system works with both
enhanced and non-enhanced visit data from actual simulations.
"""

import pytest
from pathlib import Path
from datetime import datetime
from simulation.economics import (
    CostConfig, 
    CostAnalyzer, 
    CostTracker,
    enhance_visit_with_cost_metadata,
    enhance_patient_history
)


class TestEconomicIntegrationPhase2:
    """Integration tests for visit metadata enhancement"""
    
    @pytest.fixture
    def cost_config(self):
        """Load test cost configuration"""
        config_path = Path("tests/fixtures/economics/test_cost_config.yaml")
        return CostConfig.from_yaml(config_path)
    
    def test_enhance_legacy_visit_data(self, cost_config):
        """Test enhancing visits without metadata"""
        # Given a legacy visit structure (no metadata field)
        legacy_visit = {
            'date': datetime(2025, 1, 1, 10, 0),
            'time': 0,  # Month 0
            'type': 'injection',
            'actions': ['injection', 'oct_scan', 'visual_acuity_test'],
            'vision': 70.0,
            'baseline_vision': 65.0,
            'phase': 'loading',
            'drug': 'eylea_2mg',
            'patient_id': 'patient_001'
        }
        
        # When enhancing the visit
        enhanced_visit = enhance_visit_with_cost_metadata(
            visit=legacy_visit,
            visit_data={'drug': 'eylea_2mg'},
            visit_number=1
        )
        
        # Then metadata should be added
        assert 'metadata' in enhanced_visit
        metadata = enhanced_visit['metadata']
        
        # Check components
        assert 'components_performed' in metadata
        assert set(metadata['components_performed']) == {
            'injection', 'oct_scan', 'visual_acuity_test'
        }
        
        # Check visit subtype
        assert metadata['visit_subtype'] == 'injection_loading'
        
        # Check drug
        assert metadata['drug'] == 'eylea_2mg'
        
        # Check visit number
        assert metadata['visit_number'] == 1
        
        # Original fields should be preserved
        assert enhanced_visit['date'] == datetime(2025, 1, 1, 10, 0)
        assert enhanced_visit['actions'] == ['injection', 'oct_scan', 'visual_acuity_test']
    
    def test_cost_analyzer_with_legacy_data(self, cost_config):
        """Test that CostAnalyzer can handle legacy visit data"""
        # Given a cost analyzer
        analyzer = CostAnalyzer(cost_config)
        
        # And legacy visit data without metadata
        legacy_visit = {
            'time': 0,
            'type': 'injection',
            'actions': ['injection', 'oct_scan'],
            'phase': 'maintenance',
            'drug': 'eylea_2mg',
            'patient_id': 'patient_001'
        }
        
        # When analyzing the visit
        cost_event = analyzer.analyze_visit(legacy_visit)
        
        # Then cost should be calculated correctly
        assert cost_event is not None
        # The visit enhancer sets components based on actions: injection + oct_scan
        # So: injection (50) + oct_scan (25) = 75
        # Plus drug (800) = 875 total
        assert cost_event.amount == 875.0
        assert cost_event.metadata['drug_cost'] == 800.0
        assert cost_event.metadata['visit_cost'] == 75.0
    
    def test_enhance_patient_history(self, cost_config):
        """Test enhancing a complete patient history"""
        # Given a patient history with multiple visits
        patient_history = {
            'patient_id': 'patient_001',
            'visits': [
                {
                    'date': datetime(2025, 1, 1, 10, 0),
                    'time': 0,
                    'type': 'injection',
                    'actions': ['injection', 'visual_acuity_test'],
                    'phase': 'loading',
                    'drug': 'eylea_2mg'
                },
                {
                    'date': datetime(2025, 2, 1, 10, 0),
                    'time': 1,
                    'type': 'injection',
                    'actions': ['injection', 'visual_acuity_test'],
                    'phase': 'loading',
                    'drug': 'eylea_2mg'
                },
                {
                    'date': datetime(2025, 3, 1, 10, 0),
                    'time': 2,
                    'type': 'monitoring',
                    'actions': ['oct_scan', 'virtual_review'],
                    'phase': 'maintenance'
                }
            ]
        }
        
        # When enhancing the history
        enhanced_history = enhance_patient_history(patient_history)
        
        # Then all visits should have metadata
        visits = enhanced_history['visits']
        assert len(visits) == 3
        
        # First visit
        assert visits[0]['metadata']['visit_number'] == 1
        assert visits[0]['metadata']['days_since_last'] == 0
        assert visits[0]['metadata']['visit_subtype'] == 'injection_loading'
        
        # Second visit
        assert visits[1]['metadata']['visit_number'] == 2
        assert visits[1]['metadata']['days_since_last'] == 31  # January has 31 days
        assert visits[1]['metadata']['visit_subtype'] == 'injection_loading'
        
        # Third visit
        assert visits[2]['metadata']['visit_number'] == 3
        assert visits[2]['metadata']['days_since_last'] == 28  # February 2025
        assert visits[2]['metadata']['visit_subtype'] == 'monitoring_virtual'
    
    def test_cost_tracker_with_mixed_data(self, cost_config):
        """Test CostTracker with both enhanced and legacy visits"""
        # Given a cost analyzer and tracker
        analyzer = CostAnalyzer(cost_config)
        tracker = CostTracker(analyzer)
        
        # And simulation results with mixed visit formats
        simulation_results = {
            'patient_histories': {
                # Patient with legacy visits (no metadata)
                'patient_001': {
                    'patient_id': 'patient_001',
                    'visits': [
                        {
                            'time': 0,
                            'type': 'injection',
                            'actions': ['injection', 'visual_acuity_test'],
                            'phase': 'loading',
                            'drug': 'test_drug'
                        }
                    ]
                },
                # Patient with enhanced visits (with metadata)
                'patient_002': {
                    'patient_id': 'patient_002',
                    'visits': [
                        {
                            'time': 0,
                            'type': 'injection',
                            'actions': ['injection', 'oct_scan'],
                            'phase': 'maintenance',
                            'drug': 'eylea_2mg',
                            'metadata': {
                                'components_performed': ['injection', 'oct_scan', 'virtual_review'],
                                'visit_subtype': 'injection_virtual',
                                'drug': 'eylea_2mg'
                            }
                        }
                    ]
                }
            }
        }
        
        # When processing the results
        tracker.process_simulation_results(simulation_results)
        
        # Then both patients should have costs calculated
        assert len(tracker.cost_events) == 2
        
        # Check patient 001 (legacy)
        patient_001_costs = tracker.get_patient_costs('patient_001')
        assert len(patient_001_costs) == 1
        assert patient_001_costs.iloc[0]['amount'] == 160.0  # 100 + 50 + 10
        
        # Check patient 002 (enhanced)
        patient_002_costs = tracker.get_patient_costs('patient_002')
        assert len(patient_002_costs) == 1
        assert patient_002_costs.iloc[0]['amount'] == 890.0  # 800 + 50 + 25 + 15
    
    def test_visit_subtype_determination(self):
        """Test various visit subtype determinations"""
        from simulation.economics import determine_visit_subtype
        
        # Loading injection
        assert determine_visit_subtype(
            'injection_visit', 'loading', ['injection']
        ) == 'injection_loading'
        
        # Virtual injection
        assert determine_visit_subtype(
            'injection_visit', 'maintenance', ['injection', 'virtual_review']
        ) == 'injection_virtual'
        
        # Face-to-face injection
        assert determine_visit_subtype(
            'injection_visit', 'maintenance', ['injection', 'oct_scan']
        ) == 'injection_face_to_face'
        
        # Virtual monitoring
        assert determine_visit_subtype(
            'monitoring_visit', 'maintenance', ['oct_scan', 'virtual_review']
        ) == 'monitoring_virtual'
        
        # Face-to-face monitoring
        assert determine_visit_subtype(
            'monitoring_visit', 'maintenance', ['oct_scan', 'face_to_face_review']
        ) == 'monitoring_face_to_face'
        
        # Initial assessment
        assert determine_visit_subtype(
            'initial_visit', 'loading', ['oct_scan', 'visual_acuity_test']
        ) == 'initial_assessment'
    
    def test_action_mapping(self):
        """Test action to component mapping"""
        from simulation.economics import map_actions_to_components
        
        # Basic mapping
        components = map_actions_to_components(['injection', 'oct_scan'])
        assert set(components) == {'injection', 'oct_scan'}
        
        # Alternative names
        components = map_actions_to_components(['oct', 'va_test', 'f2f_review'])
        assert set(components) == {'oct_scan', 'visual_acuity_test', 'face_to_face_review'}
        
        # Case insensitive
        components = map_actions_to_components(['INJECTION', 'OCT_SCAN'])
        assert set(components) == {'injection', 'oct_scan'}
        
        # Unknown actions are ignored
        components = map_actions_to_components(['injection', 'unknown_action'])
        assert components == ['injection']