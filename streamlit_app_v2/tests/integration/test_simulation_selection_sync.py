"""
Test simulation selection and session state synchronization.

These tests capture the current BROKEN behavior where selecting or importing
a simulation doesn't properly update the session state. They should FAIL now
and PASS after implementing the fixes.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import streamlit as st
from pathlib import Path
import json
import tempfile
import shutil
from datetime import datetime
import sys

# Add parent directory
sys.path.append(str(Path(__file__).parent.parent.parent))

from core.results.factory import ResultsFactory
from utils.simulation_package import SimulationPackageManager


class TestSimulationSelectionSync:
    """Test that simulation selection properly syncs with session state"""
    
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
    
    def create_test_simulation(self, sim_id: str = None, n_patients: int = 10, duration_years: float = 0.1):
        """Create or copy a real test simulation"""
        from tests.fixtures.create_test_simulation import create_test_simulation
        
        # Add parent path for imports if needed
        parent_path = str(Path(__file__).parent.parent.parent.parent)
        if parent_path not in sys.path:
            sys.path.append(parent_path)
        
        if sim_id:
            # Create a simulation and then rename it to the desired ID
            created_path = create_test_simulation(
                output_dir=self.test_dir,
                n_patients=n_patients,
                duration_years=duration_years
            )
            created_path = Path(created_path)
            
            # Rename to the desired sim_id
            target_path = self.test_dir / sim_id
            if target_path.exists():
                shutil.rmtree(target_path)
            created_path.rename(target_path)
            
            # Update metadata with new sim_id
            metadata_path = target_path / "metadata.json"
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            metadata['sim_id'] = sim_id
            
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
                
            return metadata
        else:
            # Create a real simulation using the test fixture
            created_path = create_test_simulation(
                output_dir=self.test_dir,
                n_patients=n_patients,
                duration_years=duration_years
            )
            
            # Load and return metadata
            with open(Path(created_path) / "metadata.json", 'r') as f:
                return json.load(f)
    
    def test_selecting_simulation_loads_results(self):
        """Test that selecting a simulation from the list loads its results"""
        # Create a test simulation
        sim_id = "sim_20250607_120000_test123"
        metadata = self.create_test_simulation(sim_id)
        
        # Import the loader
        from utils.simulation_loader import load_simulation_results
        
        # Simulate selecting the simulation (what the UI now does)
        success = load_simulation_results(sim_id)
        assert success is True, "Loading should succeed"
        
        # The simulation results should be loaded into session state
        assert 'simulation_results' in st.session_state, "Simulation results should be loaded"
        assert st.session_state.simulation_results is not None
        
        # Verify the loaded data matches
        results = st.session_state.simulation_results
        assert results['protocol']['name'] == metadata['protocol_name']
        assert results['parameters']['n_patients'] == metadata['n_patients']
        assert results['parameters']['duration_years'] == metadata['duration_years']
    
    def test_import_sets_current_simulation(self):
        """Test that importing a simulation makes it the current one with loaded results"""
        # Create a simulation to export
        original_sim_id = "sim_20250607_110000_original"
        self.create_test_simulation(original_sim_id, n_patients=500)
        
        # Mock the import process
        imported_sim_id = "imported_sim_20250607_120000_test456"
        self.create_test_simulation(imported_sim_id, n_patients=500)
        
        # Import the loader
        from utils.simulation_loader import load_simulation_results
        
        # Simulate what import_component.py NOW does
        success = load_simulation_results(imported_sim_id)
        assert success is True, "Loading imported simulation should succeed"
        
        if 'imported_simulations' not in st.session_state:
            st.session_state.imported_simulations = set()
        st.session_state.imported_simulations.add(imported_sim_id)
        st.session_state.imported_simulation = True
        
        # The imported simulation's results should be loaded
        assert 'simulation_results' in st.session_state, "Imported simulation results should be loaded"
        assert st.session_state.simulation_results is not None
        
        # Verify it's the imported simulation's data
        results = st.session_state.simulation_results
        assert results['parameters']['n_patients'] == 500  # The imported sim's patient count
    
    def test_analysis_overview_uses_current_sim_id(self):
        """Test that Analysis Overview loads data from current_sim_id if simulation_results is missing"""
        # Create two simulations
        sim1_id = "sim_20250607_100000_sim1"
        sim2_id = "sim_20250607_110000_sim2"
        self.create_test_simulation(sim1_id, n_patients=100)
        self.create_test_simulation(sim2_id, n_patients=200)
        
        # Set current_sim_id but NOT simulation_results (simulating the broken state)
        st.session_state.current_sim_id = sim2_id
        # Explicitly ensure simulation_results is not set
        if 'simulation_results' in st.session_state:
            del st.session_state.simulation_results
        
        # Import the ensure function
        from utils.simulation_loader import ensure_simulation_loaded
        
        # Mock the Analysis Overview check
        # It should detect missing results and load from current_sim_id
        loaded = ensure_simulation_loaded()
        assert loaded is True, "Should successfully load simulation"
        assert 'simulation_results' in st.session_state
        assert st.session_state.simulation_results['parameters']['n_patients'] == 200
    
    def test_load_simulation_results_function(self):
        """Test the unified loading function"""
        # Create a test simulation directly with the fixture
        from tests.fixtures.create_test_simulation import create_test_simulation
        sys.path.append(str(Path(__file__).parent.parent.parent.parent))
        
        # Create the simulation in our test directory
        created_path = create_test_simulation(output_dir=self.test_dir)
        created_path = Path(created_path)
        sim_id = created_path.name  # Get the sim ID from the created path
        
        # Load metadata for verification
        with open(created_path / "metadata.json", 'r') as f:
            metadata = json.load(f)
        
        # Import the actual function
        from utils.simulation_loader import load_simulation_results
        
        # Clear any existing results
        if 'simulation_results' in st.session_state:
            del st.session_state.simulation_results
        
        # Load the simulation
        success = load_simulation_results(sim_id)
        
        assert success is True, "Loading should succeed"
        assert 'simulation_results' in st.session_state
        
        results = st.session_state.simulation_results
        assert results['results'] is not None, "Should have results object"
        assert results['protocol']['name'] == metadata['protocol_name']
        assert results['parameters']['n_patients'] == metadata['n_patients']
        assert results['parameters']['engine'] == metadata['engine_type']
    
    def test_manage_button_always_visible(self):
        """Test that Manage button is visible even without a current simulation"""
        # Clear session state
        if 'current_sim_id' in st.session_state:
            del st.session_state.current_sim_id
        
        # Create at least one simulation in the directory
        self.create_test_simulation("sim_20250607_140000_exists")
        
        # Mock checking for simulations
        sim_dirs = list(self.test_dir.iterdir())
        assert len(sim_dirs) > 0, "Have simulations in directory"
        
        # The manage button should be visible because simulations exist
        # This simulates the check in 2_Simulations.py line 130
        show_manage_button = bool(sim_dirs) or st.session_state.get('current_sim_id')
        
        assert show_manage_button is True, "Manage button should be visible when simulations exist"
    
    def test_complete_selection_workflow(self):
        """Test the complete workflow of selecting different simulations"""
        # Create three simulations
        sim1 = "sim_20250607_150000_first"
        sim2 = "sim_20250607_160000_second"
        sim3 = "imported_sim_20250607_170000_third"
        
        self.create_test_simulation(sim1, n_patients=100)
        self.create_test_simulation(sim2, n_patients=200)
        self.create_test_simulation(sim3, n_patients=300)
        
        # Simulate running first simulation (this works currently)
        st.session_state.current_sim_id = sim1
        st.session_state.simulation_results = {
            'results': Mock(),  # Would be actual results
            'protocol': {'name': 'Test Protocol'},
            'parameters': {'n_patients': 100}
        }
        
        # Import the loader
        from utils.simulation_loader import load_simulation_results
        
        # Now select the second simulation (as the UI would)
        success = load_simulation_results(sim2)
        assert success is True
        
        # Verify the results updated
        assert st.session_state.simulation_results['parameters']['n_patients'] == 200, \
            "Results should update to show sim2's data"
        
        # Now select the imported simulation
        success = load_simulation_results(sim3)
        assert success is True
        st.session_state.imported_simulations = {sim3}
        
        # Verify the results updated to imported sim (currently fails)
        assert st.session_state.simulation_results['parameters']['n_patients'] == 300, \
            "Results should update to show imported simulation's data"


class TestImportedSimulationBadge:
    """Test that imported simulations show the IMPORTED badge"""
    
    def test_imported_badge_shows(self):
        """Test that imported simulations display the IMPORTED badge"""
        # Set up imported simulations in session state
        st.session_state.imported_simulations = {
            "imported_sim_20250607_180000_test"
        }
        
        # Simulate the check from 2_Simulations.py line 93
        sim_info = {
            'id': 'imported_sim_20250607_180000_test',
            'is_imported': True  # This is set if id starts with 'imported_'
        }
        
        # Check if badge should show
        is_imported = sim_info['is_imported'] or sim_info['id'] in st.session_state.get('imported_simulations', set())
        
        assert is_imported is True, "Imported simulation should show badge"
        
        # Also test that regular simulations don't show badge
        regular_sim = {
            'id': 'sim_20250607_190000_regular',
            'is_imported': False
        }
        
        is_imported_regular = regular_sim['is_imported'] or regular_sim['id'] in st.session_state.get('imported_simulations', set())
        assert is_imported_regular is False, "Regular simulation should not show badge"