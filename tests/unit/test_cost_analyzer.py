"""
Test suite for CostAnalyzer class - following TDD approach.

These tests are written BEFORE the implementation to drive the design.
"""

import pytest
from pathlib import Path
from simulation.economics import CostConfig, CostAnalyzer, CostEvent


class TestCostAnalyzer:
    """Test suite for CostAnalyzer class"""
    
    @pytest.fixture
    def cost_config(self):
        """Load test cost configuration"""
        config_path = Path("tests/fixtures/economics/test_cost_config.yaml")
        return CostConfig.from_yaml(config_path)
    
    @pytest.fixture
    def analyzer(self, cost_config):
        """Create analyzer with test configuration"""
        return CostAnalyzer(cost_config)
    
    def test_analyze_injection_visit_with_metadata(self, analyzer):
        """Test 2.1: Analyze a visit with full metadata"""
        # Given an injection visit with metadata specifying components
        visit = {
            'type': 'injection',
            'time': 0,
            'drug': 'test_drug',
            'patient_id': 'test_001',
            'metadata': {
                'visit_subtype': 'injection_loading',
                'phase': 'loading'
            }
        }
        
        # When I analyze the visit
        cost_event = analyzer.analyze_visit(visit)
        
        # Then I should get a CostEvent with correct details
        assert cost_event is not None
        assert isinstance(cost_event, CostEvent)
        assert cost_event.time == 0
        assert cost_event.patient_id == 'test_001'
        assert cost_event.event_type == 'visit'
        assert cost_event.category == 'injection_loading'
        
        # And the cost should be correct
        # injection_loading has: injection (50) + visual_acuity_test (10) + drug (100) = 160
        assert cost_event.amount == 160.0
        assert cost_event.metadata['drug_cost'] == 100.0
        assert cost_event.metadata['visit_cost'] == 60.0
        assert cost_event.metadata['phase'] == 'loading'
        
        # And component breakdown should be available
        assert 'injection' in cost_event.components
        assert 'visual_acuity_test' in cost_event.components
        assert cost_event.components['injection'] == 50.0
        assert cost_event.components['visual_acuity_test'] == 10.0
    
    def test_infer_components_loading_phase(self, analyzer):
        """Test 2.2: Infer components from context"""
        # Given an injection visit with phase='loading' but no component list
        visit = {
            'type': 'injection',
            'time': 0,
            'metadata': {
                'phase': 'loading'
            }
        }
        
        # When I analyze the visit
        cost_event = analyzer.analyze_visit(visit)
        
        # Then components should be inferred correctly
        assert cost_event is not None
        # Loading phase injection should have injection + visual_acuity_test
        assert cost_event.components['injection'] == 50.0
        assert cost_event.components['visual_acuity_test'] == 10.0
        assert cost_event.metadata['visit_cost'] == 60.0
        
    def test_analyze_visit_without_metadata(self, analyzer):
        """Test 2.3: Handle missing metadata gracefully"""
        # Given a visit with minimal information
        visit = {
            'type': 'monitoring',
            'time': 2
        }
        
        # When I analyze it
        cost_event = analyzer.analyze_visit(visit)
        
        # Then I should get reasonable defaults
        assert cost_event is not None
        assert cost_event.event_type == 'visit'
        assert cost_event.category == 'monitoring'
        # Default monitoring should have reasonable components
        assert len(cost_event.components) > 0
        
    def test_separate_drug_and_visit_costs(self, analyzer):
        """Test 2.4: Calculate drug costs separately from visit costs"""
        # Given an injection visit with a drug
        visit = {
            'type': 'injection',
            'time': 1,
            'drug': 'eylea_2mg',
            'metadata': {
                'visit_subtype': 'injection_virtual',
                'phase': 'maintenance'
            }
        }
        
        # When I analyze it
        cost_event = analyzer.analyze_visit(visit)
        
        # Then drug and visit costs should be tracked separately
        assert cost_event.metadata['drug_cost'] == 800.0  # eylea_2mg cost
        # injection_virtual: injection (50) + oct_scan (25) + virtual_review (15) = 90
        assert cost_event.metadata['visit_cost'] == 90.0
        assert cost_event.amount == 890.0  # Total
        
    def test_analyze_monitoring_with_explicit_components(self, analyzer):
        """Test analyzing a monitoring visit with explicit components"""
        # Given a monitoring visit with components_performed
        visit = {
            'type': 'monitoring',
            'time': 3,
            'patient_id': 'test_002',
            'metadata': {
                'components_performed': ['oct_scan', 'virtual_review']
            }
        }
        
        # When I analyze it
        cost_event = analyzer.analyze_visit(visit)
        
        # Then it should use the explicit components
        assert cost_event is not None
        assert cost_event.components['oct_scan'] == 25.0
        assert cost_event.components['virtual_review'] == 15.0
        assert cost_event.amount == 40.0
        assert cost_event.metadata['drug_cost'] == 0.0
        assert cost_event.metadata['visit_cost'] == 40.0
        
    def test_analyze_patient_history(self, analyzer):
        """Test analyzing a complete patient history"""
        # Given a patient history with multiple visits
        patient_history = {
            'patient_id': 'test_003',
            'visits': [
                {
                    'type': 'injection',
                    'time': 0,
                    'drug': 'test_drug',
                    'metadata': {
                        'visit_subtype': 'injection_loading',
                        'phase': 'loading'
                    }
                },
                {
                    'type': 'monitoring',
                    'time': 1,
                    'metadata': {
                        'components_performed': ['oct_scan', 'virtual_review']
                    }
                }
            ]
        }
        
        # When I process the patient history
        cost_events = analyzer.analyze_patient_history(patient_history)
        
        # Then I should get cost events for each visit
        assert len(cost_events) == 2
        
        # First event (injection)
        assert cost_events[0].patient_id == 'test_003'
        assert cost_events[0].time == 0
        assert cost_events[0].amount == 160.0  # 100 drug + 60 visit
        
        # Second event (monitoring)
        assert cost_events[1].patient_id == 'test_003'
        assert cost_events[1].time == 1
        assert cost_events[1].amount == 40.0  # 25 + 15
        
    def test_visit_without_valid_components(self, analyzer):
        """Test handling visit that results in no components"""
        # Given a visit with unknown type
        visit = {
            'type': 'unknown_type',
            'time': 0
        }
        
        # When I analyze it
        cost_event = analyzer.analyze_visit(visit)
        
        # Then it should handle gracefully
        assert cost_event is None  # No components, no cost event