"""
Test that UI components don't create nested expanders.

Streamlit doesn't allow expanders to be nested inside other expanders,
which can cause runtime errors that are hard to catch without actually
rendering the components.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, call
import streamlit as st


class TestNoNestedExpanders:
    """Test that components don't create nested expanders"""
    
    def test_import_section_no_nested_expanders(self):
        """Test that import section doesn't create nested expanders on success"""
        # Track expander depth
        expander_depth = 0
        original_expander = st.expander
        
        def mock_expander(*args, **kwargs):
            """Mock expander that tracks nesting depth"""
            nonlocal expander_depth
            expander_depth += 1
            
            if expander_depth > 1:
                raise RuntimeError("Expanders may not be nested inside other expanders")
            
            # Create a context manager that decrements depth on exit
            class ExpanderContext:
                def __enter__(self):
                    return self
                    
                def __exit__(self, *args):
                    nonlocal expander_depth
                    expander_depth -= 1
                    
            return ExpanderContext()
        
        # Mock Streamlit components
        with patch.object(st, 'expander', side_effect=mock_expander), \
             patch.object(st, 'write'), \
             patch.object(st, 'columns', return_value=[MagicMock(), MagicMock(), MagicMock()]), \
             patch.object(st, 'file_uploader', return_value=None), \
             patch.object(st, 'button', return_value=False), \
             patch.object(st, 'container'), \
             patch.object(st, 'success'), \
             patch.object(st, 'info'), \
             patch.object(st, 'progress'), \
             patch.object(st, 'empty'):
            
            from components.import_component import render_import_section
            
            # This should not raise an error
            render_import_section()
            
    def test_import_success_uses_container_not_expander(self):
        """Test that successful import uses container instead of nested expander"""
        # Track what containers are used
        container_calls = []
        expander_calls = []
        
        def track_container(*args, **kwargs):
            container_calls.append(args)
            return MagicMock()
            
        def track_expander(*args, **kwargs):
            expander_calls.append(args)
            return MagicMock()
        
        # Mock a successful import scenario
        mock_file = Mock()
        mock_file.size = 1024 * 1024  # 1MB
        mock_file.name = "test_package.zip"
        mock_file.read.return_value = b"fake_data"
        
        mock_results = Mock()
        mock_results.metadata.sim_id = "imported_test_123"
        mock_results.metadata.protocol_name = "Test Protocol"
        mock_results.metadata.n_patients = 100
        mock_results.metadata.duration_years = 1.0
        mock_results.metadata.engine_type = "abs"
        mock_results.metadata.to_dict.return_value = {
            'sim_id': 'imported_test_123',
            'timestamp': '2023-01-01T00:00:00'
        }
        
        with patch.object(st, 'expander', side_effect=track_expander) as mock_exp, \
             patch.object(st, 'container', side_effect=track_container) as mock_cont, \
             patch.object(st, 'write'), \
             patch.object(st, 'columns', return_value=[MagicMock(), MagicMock(), MagicMock()]), \
             patch.object(st, 'file_uploader', return_value=mock_file), \
             patch.object(st, 'button', return_value=True), \
             patch.object(st, 'success'), \
             patch.object(st, 'info'), \
             patch.object(st, 'progress', return_value=MagicMock()), \
             patch.object(st, 'empty', return_value=MagicMock()), \
             patch.object(st, 'session_state', {}), \
             patch('components.import_component.SimulationPackageManager') as mock_manager, \
             patch('components.import_component.ResultsFactory') as mock_factory, \
             patch('components.import_component.SimulationRegistry') as mock_registry:
            
            # Setup mocks
            mock_manager_instance = mock_manager.return_value
            mock_manager_instance.import_package.return_value = mock_results
            mock_factory.DEFAULT_RESULTS_DIR = Mock()
            mock_registry_instance = mock_registry.return_value
            
            from components.import_component import render_import_section
            
            # Render the import section
            render_import_section()
            
            # Check that we used exactly one expander (the outer one)
            assert len(expander_calls) == 1
            assert "Import Simulation Package" in str(expander_calls[0])
            
            # Check that we used a container for the success details (not a nested expander)
            assert len(container_calls) >= 1  # Should have used container for import details
            
    def test_export_section_structure(self):
        """Test that export section has proper structure without nested expanders"""
        expander_count = 0
        
        def count_expander(*args, **kwargs):
            nonlocal expander_count
            expander_count += 1
            return MagicMock()
        
        with patch.object(st, 'expander', side_effect=count_expander), \
             patch.object(st, 'subheader'), \
             patch.object(st, 'write'), \
             patch.object(st, 'columns', return_value=[MagicMock(), MagicMock()]), \
             patch.object(st, 'button', return_value=False), \
             patch.object(st, 'session_state', {'current_sim_id': 'test_123'}):
            
            from components.export import render_export_section
            
            # Render export section
            render_export_section()
            
            # Export section should not use expanders at all (it uses subheader)
            assert expander_count == 0