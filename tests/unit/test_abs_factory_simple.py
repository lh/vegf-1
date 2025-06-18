"""Simplified unit tests for ABS factory logic only."""

import pytest
from datetime import datetime
from simulation.abs_factory import ABSFactory


class TestABSFactoryLogic:
    """Test just the factory selection logic without initializing engines."""
    
    def test_supports_heterogeneity_valid(self):
        """Test heterogeneity detection with valid config."""
        # Mock config with proper structure
        class MockConfig:
            def __init__(self, protocol_dict):
                if isinstance(protocol_dict, dict):
                    self.protocol = protocol_dict
                else:
                    self.protocol = MockProtocol(protocol_dict)
        
        class MockProtocol:
            def __init__(self, data):
                self.data = data
            def to_dict(self):
                return self.data
        
        # Valid heterogeneity config
        valid_config = MockConfig({
            'heterogeneity': {
                'enabled': True,
                'version': '1.0',
                'trajectory_classes': {
                    'good': {'proportion': 0.3, 'parameters': {}},
                    'bad': {'proportion': 0.7, 'parameters': {}}
                }
            }
        })
        
        assert ABSFactory._supports_heterogeneity(valid_config) == True
    
    def test_supports_heterogeneity_disabled(self):
        """Test heterogeneity detection when disabled."""
        class MockConfig:
            protocol = {'heterogeneity': {'enabled': False}}
        
        assert ABSFactory._supports_heterogeneity(MockConfig()) == False
    
    def test_supports_heterogeneity_missing(self):
        """Test heterogeneity detection when missing."""
        class MockConfig:
            protocol = {'name': 'test'}
        
        assert ABSFactory._supports_heterogeneity(MockConfig()) == False
    
    def test_supports_heterogeneity_invalid_proportions(self):
        """Test heterogeneity detection with invalid proportions."""
        class MockConfig:
            def __init__(self):
                self.protocol = MockProtocol()
        
        class MockProtocol:
            def to_dict(self):
                return {
                    'heterogeneity': {
                        'enabled': True,
                        'version': '1.0',
                        'trajectory_classes': {
                            'a': {'proportion': 0.3, 'parameters': {}},
                            'b': {'proportion': 0.4, 'parameters': {}}
                            # Sum = 0.7, not 1.0
                        }
                    }
                }
        
        # Should log warning and return False
        config = MockConfig()
        assert ABSFactory._supports_heterogeneity(config) == False
    
    def test_supports_heterogeneity_empty_classes(self):
        """Test heterogeneity detection with empty trajectory classes."""
        class MockConfig:
            protocol = {
                'heterogeneity': {
                    'enabled': True,
                    'version': '1.0',
                    'trajectory_classes': {}
                }
            }
        
        assert ABSFactory._supports_heterogeneity(MockConfig()) == False
    
    def test_supports_heterogeneity_missing_version(self):
        """Test heterogeneity detection without version."""
        class MockConfig:
            protocol = {
                'heterogeneity': {
                    'enabled': True,
                    'trajectory_classes': {
                        'a': {'proportion': 1.0, 'parameters': {}}
                    }
                }
            }
        
        # Should still work without version
        assert ABSFactory._supports_heterogeneity(MockConfig()) == True
    
    def test_validate_trajectory_proportions(self):
        """Test trajectory proportion validation."""
        # Valid proportions
        classes = {
            'a': {'proportion': 0.25},
            'b': {'proportion': 0.35},
            'c': {'proportion': 0.40}
        }
        assert ABSFactory._validate_trajectory_proportions(classes) == True
        
        # Invalid proportions (sum to 0.99)
        classes = {
            'a': {'proportion': 0.33},
            'b': {'proportion': 0.33},
            'c': {'proportion': 0.33}
        }
        assert ABSFactory._validate_trajectory_proportions(classes) == False
        
        # Invalid proportions (sum to 1.01)  
        classes = {
            'a': {'proportion': 0.34},
            'b': {'proportion': 0.34},
            'c': {'proportion': 0.33}
        }
        assert ABSFactory._validate_trajectory_proportions(classes) == False
    
    def test_engine_selection_messages(self, capsys):
        """Test that appropriate messages are printed."""
        class MockConfig:
            protocol = {'name': 'test'}
            random_seed = 42
        
        # Mock the engine classes to avoid initialization
        class MockABS:
            def __init__(self, config, start_date):
                pass
        
        class MockHetABS:
            def __init__(self, config, start_date):
                pass
        
        # Test standard engine message
        import simulation.abs_factory
        original_abs = simulation.abs_factory.AgentBasedSimulation
        original_het = simulation.abs_factory.HeterogeneousABS
        
        try:
            simulation.abs_factory.AgentBasedSimulation = MockABS
            simulation.abs_factory.HeterogeneousABS = MockHetABS
            
            ABSFactory.create_simulation(MockConfig(), datetime(2023, 1, 1))
            captured = capsys.readouterr()
            assert "→ Standard configuration - using AgentBasedSimulation engine" in captured.out
            
            # Test heterogeneous engine message
            MockConfig.protocol = {
                'heterogeneity': {
                    'enabled': True,
                    'version': '1.0',
                    'trajectory_classes': {
                        'good': {'proportion': 1.0, 'parameters': {}}
                    }
                }
            }
            
            ABSFactory.create_simulation(MockConfig(), datetime(2023, 1, 1))
            captured = capsys.readouterr()
            assert "✓ Heterogeneity configuration detected - using HeterogeneousABS engine" in captured.out
            
        finally:
            # Restore original classes
            simulation.abs_factory.AgentBasedSimulation = original_abs
            simulation.abs_factory.HeterogeneousABS = original_het


if __name__ == '__main__':
    pytest.main([__file__, '-v'])