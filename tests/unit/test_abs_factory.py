"""Unit tests for ABS factory and engine selection."""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from simulation.abs_factory import ABSFactory
from simulation.abs import AgentBasedSimulation
from simulation.config import SimulationConfig


class TestABSFactory:
    """Test automatic engine selection based on configuration."""
    
    def test_factory_selects_standard_engine(self):
        """Test factory returns standard engine for standard config."""
        # Create mock config without heterogeneity
        config = Mock(spec=SimulationConfig)
        config.protocol = {'name': 'test_protocol'}
        
        # Mock the ClinicalModel to avoid initialization issues
        with patch('simulation.abs.ClinicalModel'), \
             patch('builtins.print') as mock_print:
            sim = ABSFactory.create_simulation(config, datetime(2023, 1, 1))
        
        # Verify standard engine selected
        assert isinstance(sim, AgentBasedSimulation)
        assert sim.__class__.__name__ == 'AgentBasedSimulation'
        mock_print.assert_called_with("→ Standard configuration - using AgentBasedSimulation engine")
    
    def test_factory_selects_heterogeneous_engine(self):
        """Test factory returns heterogeneous engine when appropriate."""
        # Create config with valid heterogeneity section
        config = Mock(spec=SimulationConfig)
        config.protocol = Mock()
        config.protocol.to_dict.return_value = {
            'name': 'test_protocol',
            'heterogeneity': {
                'enabled': True,
                'version': '1.0',
                'trajectory_classes': {
                    'good_responders': {
                        'proportion': 0.25,
                        'parameters': {}
                    },
                    'moderate_decliners': {
                        'proportion': 0.40,
                        'parameters': {}
                    },
                    'poor_responders': {
                        'proportion': 0.35,
                        'parameters': {}
                    }
                }
            }
        }
        config.random_seed = 42
        
        # Create simulation
        with patch('simulation.abs.ClinicalModel'), \
             patch('builtins.print') as mock_print:
            sim = ABSFactory.create_simulation(config, datetime(2023, 1, 1))
        
        # Verify heterogeneous engine selected
        assert sim.__class__.__name__ == 'HeterogeneousABS'
        mock_print.assert_called_with("✓ Heterogeneity configuration detected - using HeterogeneousABS engine")
    
    def test_factory_with_disabled_heterogeneity(self):
        """Test factory returns standard engine when heterogeneity disabled."""
        # Create config with disabled heterogeneity
        config = Mock(spec=SimulationConfig)
        config.protocol = {
            'name': 'test_protocol',
            'heterogeneity': {
                'enabled': False,
                'version': '1.0'
            }
        }
        
        # Create simulation
        with patch('simulation.abs.ClinicalModel'), \
             patch('builtins.print') as mock_print:
            sim = ABSFactory.create_simulation(config, datetime(2023, 1, 1))
        
        # Verify standard engine selected
        assert isinstance(sim, AgentBasedSimulation)
        mock_print.assert_called_with("→ Standard configuration - using AgentBasedSimulation engine")
    
    def test_factory_invalid_trajectory_proportions(self):
        """Test factory falls back to standard engine on invalid proportions."""
        # Create config with invalid proportions (don't sum to 1)
        config = Mock(spec=SimulationConfig)
        config.protocol = Mock()
        config.protocol.to_dict.return_value = {
            'name': 'test_protocol',
            'heterogeneity': {
                'enabled': True,
                'version': '1.0',
                'trajectory_classes': {
                    'class1': {'proportion': 0.3, 'parameters': {}},
                    'class2': {'proportion': 0.4, 'parameters': {}}
                    # Sum = 0.7, not 1.0
                }
            }
        }
        
        # Create simulation
        with patch('simulation.abs.ClinicalModel'), \
             patch('builtins.print') as mock_print:
            sim = ABSFactory.create_simulation(config, datetime(2023, 1, 1))
        
        # Verify standard engine selected with warning
        assert isinstance(sim, AgentBasedSimulation)
        # Check warning was printed
        calls = [str(call) for call in mock_print.call_args_list]
        assert any('proportions sum to' in str(call) for call in calls)
    
    def test_factory_missing_required_fields(self):
        """Test factory handles missing required fields gracefully."""
        # Create config missing trajectory_classes
        config = Mock(spec=SimulationConfig)
        config.protocol = {
            'name': 'test_protocol',
            'heterogeneity': {
                'enabled': True,
                'version': '1.0'
                # Missing trajectory_classes
            }
        }
        
        # Create simulation
        with patch('simulation.abs.ClinicalModel'), \
             patch('builtins.print') as mock_print:
            sim = ABSFactory.create_simulation(config, datetime(2023, 1, 1))
        
        # Verify standard engine selected with warning
        assert isinstance(sim, AgentBasedSimulation)
        calls = [str(call) for call in mock_print.call_args_list]
        assert any('missing' in str(call) for call in calls)
    
    def test_supports_heterogeneity_validation(self):
        """Test heterogeneity validation logic."""
        # Valid configuration
        valid_config = {
            'heterogeneity': {
                'enabled': True,
                'version': '1.0',
                'trajectory_classes': {
                    'a': {'proportion': 0.5, 'parameters': {}},
                    'b': {'proportion': 0.5, 'parameters': {}}
                }
            }
        }
        
        config = Mock()
        config.protocol = valid_config
        
        assert ABSFactory._supports_heterogeneity(config) == True
        
        # Test various invalid configurations
        invalid_configs = [
            # No heterogeneity section
            {},
            # Disabled
            {'heterogeneity': {'enabled': False}},
            # Missing version
            {'heterogeneity': {'enabled': True, 'trajectory_classes': {}}},
            # Empty trajectory classes
            {'heterogeneity': {'enabled': True, 'version': '1.0', 'trajectory_classes': {}}},
            # Invalid proportions
            {
                'heterogeneity': {
                    'enabled': True,
                    'version': '1.0',
                    'trajectory_classes': {
                        'a': {'proportion': 0.3, 'parameters': {}},
                        'b': {'proportion': 0.3, 'parameters': {}}
                    }
                }
            }
        ]
        
        for invalid in invalid_configs:
            config.protocol = invalid
            assert ABSFactory._supports_heterogeneity(config) == False


if __name__ == '__main__':
    pytest.main([__file__, '-v'])