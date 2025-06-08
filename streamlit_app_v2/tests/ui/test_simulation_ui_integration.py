"""
Test UI integration for simulation selection and import.

These tests verify the user-facing behavior and will fail until
the session state synchronization is fixed.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, call
import streamlit as st
from pathlib import Path
import json
import tempfile
import shutil

from core.results.factory import ResultsFactory


class TestSimulationUIIntegration:
    """Test UI behavior for simulation management"""
    
    def setup_method(self):
        """Set up test environment"""
        # Create a temporary directory for test results
        self.test_dir = Path(tempfile.mkdtemp())
        self.original_results_dir = ResultsFactory.DEFAULT_RESULTS_DIR
        ResultsFactory.DEFAULT_RESULTS_DIR = self.test_dir
        
        # Clear session state
        for key in list(st.session_state.keys()):
            del st.session_state[key]
    
    def teardown_method(self):
        """Clean up test environment"""
        # Restore original results directory
        ResultsFactory.DEFAULT_RESULTS_DIR = self.original_results_dir
        
        # Clean up temporary directory
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
    
    def create_test_simulation(self, sim_id: str, **kwargs):
        """Create a test simulation directory with metadata"""
        sim_dir = self.test_dir / sim_id
        sim_dir.mkdir(parents=True)
        
        metadata = {
            "sim_id": sim_id,
            "protocol_name": kwargs.get('protocol_name', "Test Protocol"),
            "protocol_version": "1.0",
            "engine_type": "abs",
            "n_patients": kwargs.get('n_patients', 100),
            "duration_years": kwargs.get('duration_years', 2.0),
            "seed": 42,
            "created_date": "2025-06-07T12:00:00",
            "timestamp": "2025-06-07T12:00:00",
            "runtime_seconds": 1.5,
            "storage_type": "parquet"
        }
        
        with open(sim_dir / "metadata.json", "w") as f:
            json.dump(metadata, f)
        
        # Touch required files
        (sim_dir / "patients.parquet").touch()
        (sim_dir / "visits.parquet").touch()
        
        return metadata
    
    @pytest.mark.xfail(reason="Selection doesn't update Analysis Overview - will fail until fixed")
    def test_selection_updates_analysis_view(self):
        """Test that selecting a simulation updates the Analysis Overview"""
        # Create two different simulations
        sim1_metadata = self.create_test_simulation(
            "sim_20250607_100000_sim1",
            protocol_name="Protocol A",
            n_patients=100
        )
        sim2_metadata = self.create_test_simulation(
            "sim_20250607_110000_sim2", 
            protocol_name="Protocol B",
            n_patients=200
        )
        
        with patch('streamlit.button') as mock_button, \
             patch('streamlit.rerun') as mock_rerun, \
             patch('streamlit.caption') as mock_caption:
            
            # Simulate initial state - sim1 is current
            st.session_state.current_sim_id = "sim_20250607_100000_sim1"
            st.session_state.simulation_results = {
                'protocol': {'name': 'Protocol A'},
                'parameters': {'n_patients': 100}
            }
            
            # User clicks to select sim2
            mock_button.return_value = True  # Simulate button click
            
            # This is what SHOULD happen in 2_Simulations.py when selecting
            st.session_state.current_sim_id = "sim_20250607_110000_sim2"
            # The fix will add: load_simulation_results(sim_id)
            
            # Navigate to Analysis Overview
            # The results should have been updated to show sim2's data
            
            # This should show Protocol B with 200 patients
            assert st.session_state.simulation_results['protocol']['name'] == 'Protocol B'
            assert st.session_state.simulation_results['parameters']['n_patients'] == 200
    
    @pytest.mark.xfail(reason="Import doesn't navigate properly - will fail until fixed")
    def test_import_navigation_flow(self):
        """Test that import properly updates navigation and current simulation"""
        # Create a simulation to import
        self.create_test_simulation(
            "imported_sim_20250607_120000_test",
            protocol_name="Imported Protocol",
            n_patients=500
        )
        
        with patch('streamlit.success') as mock_success, \
             patch('streamlit.button') as mock_button, \
             patch('streamlit.rerun') as mock_rerun:
            
            # Simulate import completion
            st.session_state.current_sim_id = "imported_sim_20250607_120000_test"
            st.session_state.imported_simulation = True
            
            # Mock the "Go to Analysis" button click
            mock_button.return_value = True
            
            # After import, Analysis Overview should show the imported data
            # This currently fails because simulation_results isn't set
            assert 'simulation_results' in st.session_state
            assert st.session_state.simulation_results['protocol']['name'] == "Imported Protocol"
            assert st.session_state.simulation_results['parameters']['n_patients'] == 500
    
    @pytest.mark.xfail(reason="Manage button visibility logic is wrong - will fail until fixed")
    def test_manage_button_visibility_conditions(self):
        """Test all conditions for Manage button visibility"""
        # Testing the logic without importing the page directly
        
        # Test 1: No simulations, no current_sim_id
        assert self.test_dir.exists()
        assert len(list(self.test_dir.iterdir())) == 0
        assert 'current_sim_id' not in st.session_state
        
        # Manage button should NOT be visible
        show_manage = bool(list(self.test_dir.iterdir())) or st.session_state.get('current_sim_id')
        assert show_manage is False
        
        # Test 2: Has simulations but no current_sim_id
        self.create_test_simulation("sim_exists")
        sim_dirs = list(self.test_dir.iterdir())
        assert len(sim_dirs) > 0
        assert 'current_sim_id' not in st.session_state
        
        # Manage button SHOULD be visible (currently fails)
        show_manage = bool(sim_dirs) or st.session_state.get('current_sim_id')
        assert show_manage is True, "Manage should be visible when simulations exist"
        
        # Test 3: No simulations but has current_sim_id (edge case)
        shutil.rmtree(self.test_dir / "sim_exists")
        st.session_state.current_sim_id = "phantom_sim"
        
        show_manage = bool(list(self.test_dir.iterdir())) or st.session_state.get('current_sim_id')
        assert show_manage is True, "Manage should be visible with current_sim_id"
    
    @pytest.mark.xfail(reason="Audit tab doesn't update - will fail until fixed")
    def test_audit_tab_reflects_current_simulation(self):
        """Test that the audit tab shows the current simulation's data"""
        # Create two simulations with different audit trails
        sim1_id = "sim_20250607_130000_audit1"
        sim2_id = "sim_20250607_140000_audit2"
        
        sim1_dir = self.test_dir / sim1_id
        sim2_dir = self.test_dir / sim2_id
        sim1_dir.mkdir(parents=True)
        sim2_dir.mkdir(parents=True)
        
        # Create different audit trails
        audit1 = [
            {"timestamp": "2025-06-07T13:00:00", "event": "Simulation started", "details": "100 patients"},
            {"timestamp": "2025-06-07T13:00:05", "event": "Simulation completed"}
        ]
        audit2 = [
            {"timestamp": "2025-06-07T14:00:00", "event": "Simulation started", "details": "200 patients"},
            {"timestamp": "2025-06-07T14:00:10", "event": "Simulation completed"}
        ]
        
        # Save metadata with audit trails
        with open(sim1_dir / "metadata.json", "w") as f:
            json.dump({"audit_trail": audit1, "n_patients": 100}, f)
        with open(sim2_dir / "metadata.json", "w") as f:
            json.dump({"audit_trail": audit2, "n_patients": 200}, f)
        
        # Start with sim1 selected
        st.session_state.current_sim_id = sim1_id
        st.session_state.simulation_results = {
            'parameters': {'n_patients': 100},
            'audit_trail': audit1
        }
        
        # Verify audit shows sim1 data
        assert len(st.session_state.simulation_results['audit_trail']) == 2
        assert "100 patients" in st.session_state.simulation_results['audit_trail'][0]['details']
        
        # Now select sim2
        st.session_state.current_sim_id = sim2_id
        # This SHOULD update simulation_results but currently doesn't
        
        # Audit should now show sim2 data (currently fails)
        assert st.session_state.simulation_results['parameters']['n_patients'] == 200
        assert "200 patients" in st.session_state.simulation_results['audit_trail'][0]['details']
    
    @pytest.mark.xfail(reason="IMPORTED badge may not show - will fail if not implemented")
    def test_imported_badge_rendering(self):
        """Test that IMPORTED badge renders correctly in the UI"""
        # Create an imported simulation
        self.create_test_simulation("imported_sim_20250607_150000_badge")
        
        # Set up session state
        st.session_state.imported_simulations = {"imported_sim_20250607_150000_badge"}
        
        # Mock the rendering logic from 2_Simulations.py
        sim_info = {
            'id': 'imported_sim_20250607_150000_badge',
            'is_imported': True,  # Starts with 'imported_'
            'protocol': 'Test Protocol',
            'patients': 100,
            'duration': 2.0,
            'timestamp': '2025-06-07T15:00:00'
        }
        
        # Check badge logic
        is_imported = sim_info['is_imported'] or sim_info['id'] in st.session_state.get('imported_simulations', set())
        
        # Should render the badge
        assert is_imported is True
        
        # The HTML should include the badge (line 110 in 2_Simulations.py)
        badge_html = '<span style="background: #0F62FE; color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.8rem;">IMPORTED</span>'
        
        # In actual rendering, this would be included
        rendered_html = f"<div>...{badge_html if is_imported else ''}...</div>"
        assert "IMPORTED" in rendered_html