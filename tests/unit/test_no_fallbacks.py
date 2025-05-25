"""Test that the system fails fast without fallbacks when dependencies are missing."""

import pytest
import sys
from unittest.mock import patch


class TestNoFallbacks:
    """Test that imports fail fast without fallbacks."""
    
    def test_simulation_runner_fails_without_color_system(self):
        """Test that simulation_runner fails to import without color system."""
        # Remove the color system module from sys.modules if it exists
        modules_to_remove = [
            'visualization.color_system',
            'visualization.chart_templates', 
            'streamlit_app.simulation_runner'
        ]
        
        for module in modules_to_remove:
            if module in sys.modules:
                del sys.modules[module]
        
        # Mock the import to fail
        with patch('builtins.__import__', side_effect=ImportError("No module named 'visualization.color_system'")):
            with pytest.raises(ImportError, match="No module named 'visualization.color_system'"):
                import streamlit_app.simulation_runner
    
    def test_chart_templates_fails_without_color_system(self):
        """Test that chart_templates fails to import without color system."""
        # Remove modules from sys.modules if they exist
        modules_to_remove = [
            'visualization.color_system',
            'visualization.chart_templates'
        ]
        
        for module in modules_to_remove:
            if module in sys.modules:
                del sys.modules[module]
        
        # Mock the import to fail
        with patch('builtins.__import__', side_effect=ImportError("No module named 'visualization.color_system'")):
            with pytest.raises(ImportError, match="No module named 'visualization.color_system'"):
                import visualization.chart_templates