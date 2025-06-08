"""
Simulation Import/Export functionality.

Handles creating export packages and importing simulation packages.
"""

import streamlit as st
from pathlib import Path
from typing import Optional
from utils.simulation_package import SimulationPackageManager, SecurityError, PackageValidationError
from core.results.factory import ResultsFactory
from core.storage.registry import SimulationRegistry
from utils.simulation_loader import load_simulation_results


@st.cache_data
def create_export_package(sim_id: str) -> bytes:
    """Create export package for a simulation"""
    try:
        # Load simulation results
        results_path = ResultsFactory.DEFAULT_RESULTS_DIR / sim_id
        results = ResultsFactory.load_results(results_path)
        
        # Create package
        manager = SimulationPackageManager()
        package_data = manager.create_package(results)
        
        return package_data
    except Exception as e:
        st.error(f"Failed to create package: {str(e)}")
        return b""


def handle_import(uploaded_file) -> bool:
    """
    Handle simulation package import.
    
    Returns:
        bool: True if import was successful, False otherwise
    """
    try:
        with st.spinner("Importing simulation..."):
            # Read package data
            package_data = uploaded_file.read()
            
            # Import the package
            manager = SimulationPackageManager()
            imported_results = manager.import_package(package_data)
            
            # Get the sim_id from imported results
            sim_id = imported_results.metadata.sim_id
            
            # Register with simulation registry
            registry = SimulationRegistry(ResultsFactory.DEFAULT_RESULTS_DIR)
            
            # Calculate size
            import os
            sim_path = ResultsFactory.DEFAULT_RESULTS_DIR / sim_id
            size_mb = 0
            if sim_path.exists():
                for file in sim_path.rglob('*'):
                    if file.is_file():
                        size_mb += file.stat().st_size / (1024 * 1024)
            
            # Convert metadata to dict
            metadata_dict = imported_results.metadata.to_dict()
            registry.register_simulation(sim_id, metadata_dict, size_mb)
            
            # Load the imported simulation
            if load_simulation_results(sim_id):
                # Mark as imported
                if 'imported_simulations' not in st.session_state:
                    st.session_state.imported_simulations = set()
                st.session_state.imported_simulations.add(sim_id)
                
                st.success("Simulation imported successfully!")
                return True
            else:
                st.error("Failed to load imported simulation")
                return False
                
    except SecurityError as e:
        st.error(f"Security Error: {str(e)}")
        return False
    except PackageValidationError as e:
        st.error(f"Package Error: {str(e)}")
        return False
    except Exception as e:
        st.error(f"Import failed: {str(e)}")
        return False


def render_manage_section():
    """Render the manage section UI (1/4 width)"""
    # Upload section first
    uploaded_file = st.file_uploader(
        "",
        type=['zip'],
        label_visibility="collapsed",
        help="Upload a simulation package (.zip)"
    )
    
    if uploaded_file is not None:
        if handle_import(uploaded_file):
            st.rerun()
    
    # Download section - only show if simulation is selected
    if st.session_state.get('current_sim_id'):
        sim_id = st.session_state.get('current_sim_id')
        # Check if simulation exists
        results_path = ResultsFactory.DEFAULT_RESULTS_DIR / sim_id
        if results_path.exists():
            # Show info about current simulation
            st.markdown(f"<small style='color: #666;'>Current: {sim_id[:20]}...</small>", unsafe_allow_html=True)
            
            # Carbon-styled download button
            package_data = create_export_package(sim_id)
            if package_data:
                st.download_button(
                    label="Download",
                    data=package_data,
                    file_name=f"APE_{sim_id}.zip",
                    mime="application/zip",
                    use_container_width=True,
                    help="Download simulation as portable package"
                )