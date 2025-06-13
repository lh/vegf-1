"""
Test suite for CostConfig class - following TDD approach.

These tests are written BEFORE the implementation to drive the design.
"""

import pytest
from pathlib import Path
from simulation.economics import CostConfig


class TestCostConfig:
    """Test suite for CostConfig class"""
    
    @pytest.fixture
    def test_config_path(self):
        """Path to test configuration file"""
        return Path("tests/fixtures/economics/test_cost_config.yaml")
    
    @pytest.fixture
    def loaded_config(self, test_config_path):
        """Loaded test configuration"""
        return CostConfig.from_yaml(test_config_path)
    
    def test_load_cost_config_from_yaml(self, test_config_path):
        """Test 1.1: Load basic cost configuration"""
        # When I load a cost configuration from YAML
        config = CostConfig.from_yaml(test_config_path)
        
        # Then I should get a valid CostConfig object
        assert config is not None
        assert hasattr(config, 'metadata')
        assert hasattr(config, 'drug_costs')
        assert hasattr(config, 'visit_components')
        assert hasattr(config, 'visit_types')
        assert hasattr(config, 'special_events')
        
        # And the metadata should be correct
        assert config.metadata['name'] == "Test Cost Configuration"
        assert config.metadata['currency'] == "GBP"
        assert config.metadata['version'] == "1.0"
        
    def test_get_drug_cost(self, loaded_config):
        """Test 1.2: Access drug costs"""
        # When I request cost for a known drug
        test_drug_cost = loaded_config.get_drug_cost('test_drug')
        eylea_cost = loaded_config.get_drug_cost('eylea_2mg')
        
        # Then I should get the correct costs
        assert test_drug_cost == 100.0
        assert eylea_cost == 800.0
        
        # When I request cost for an unknown drug
        unknown_cost = loaded_config.get_drug_cost('unknown_drug')
        
        # Then I should get 0.0 as a safe default
        assert unknown_cost == 0.0
        
    def test_calculate_visit_cost_from_components(self, loaded_config):
        """Test 1.3: Calculate visit costs from ape.components"""
        # When I request cost for a visit type composed of components
        test_visit_cost = loaded_config.get_visit_cost('test_visit')
        
        # Then I should get the sum of all components
        # test_visit has: injection (50) + oct_scan (25) = 75
        assert test_visit_cost == 75.0
        
        # When I request cost for another visit type
        injection_virtual_cost = loaded_config.get_visit_cost('injection_virtual')
        
        # Then I should get the correct sum
        # injection_virtual has: injection (50) + oct_scan (25) + virtual_review (15) = 90
        assert injection_virtual_cost == 90.0
        
    def test_visit_cost_with_override(self, loaded_config):
        """Test 1.4: Handle cost overrides"""
        # When I request cost for a visit with an override
        override_cost = loaded_config.get_visit_cost('visit_with_override')
        
        # Then I should get the override value, not the component sum
        assert override_cost == 200.0
        
        # And verify that the components would sum to a different value
        components = loaded_config.visit_types['visit_with_override']['components']
        component_sum = sum(loaded_config.visit_components[c] for c in components)
        assert component_sum == 75.0  # injection (50) + oct_scan (25)
        assert override_cost != component_sum
        
    def test_get_visit_cost_unknown_type(self, loaded_config):
        """Test edge case: Request cost for unknown visit type"""
        # When I request cost for an unknown visit type
        unknown_cost = loaded_config.get_visit_cost('unknown_visit_type')
        
        # Then I should get 0.0 as a safe default
        assert unknown_cost == 0.0
        
    def test_special_event_costs(self, loaded_config):
        """Test access to special event costs"""
        # When I access special event costs
        initial_assessment_cost = loaded_config.special_events['initial_assessment']
        
        # Then I should get the correct value
        assert initial_assessment_cost == 100.0