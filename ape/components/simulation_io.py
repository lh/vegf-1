"""
Simulation Import/Export functionality.

Handles creating export packages and importing simulation packages.
"""

import streamlit as st
from pathlib import Path
from typing import Optional
from ape.utils.simulation_package import SimulationPackageManager, SecurityError, PackageValidationError
from ape.core.results.factory import ResultsFactory
from ape.core.storage.registry import SimulationRegistry
from ape.utils.simulation_loader import load_simulation_results


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
            
            # Touch the directory to update its modification time
            # This ensures it appears at the top of the "Recent" list
            import os
            os.utime(sim_path, None)  # Updates access and modification time to current time
            
            # Load the imported simulation
            if load_simulation_results(sim_id):
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
    # Import section first
    st.markdown("**Import**")
    
    # Use a unique key that changes after import to clear the file uploader
    import_key = f"import_uploader_{st.session_state.get('import_count', 0)}"
    
    uploaded_file = st.file_uploader(
        "Import simulation",
        type=['zip'],
        label_visibility="collapsed",
        help="Import a simulation package (.zip)",
        key=import_key
    )
    
    if uploaded_file is not None:
        if handle_import(uploaded_file):
            # Increment import count to change the key and clear the uploader
            st.session_state.import_count = st.session_state.get('import_count', 0) + 1
            st.rerun()
    
    # Export section - only show if simulation is selected
    if st.session_state.get('current_sim_id'):
        st.markdown("**Export**")
        sim_id = st.session_state.get('current_sim_id')
        # Check if simulation exists
        results_path = ResultsFactory.DEFAULT_RESULTS_DIR / sim_id
        if results_path.exists():
            # Show info about current simulation with memorable name if available
            display_text = sim_id[:20] + "..."
            # Try to get memorable name from session state
            if 'simulation_results' in st.session_state and st.session_state.simulation_results:
                results = st.session_state.simulation_results.get('results')
                if results and hasattr(results, 'metadata') and hasattr(results.metadata, 'memorable_name'):
                    memorable_name = results.metadata.memorable_name
                    if memorable_name:
                        display_text = memorable_name
            
            st.markdown(f"<small style='color: #666;'>Current: {display_text}</small>", unsafe_allow_html=True)
            
            # Export button
            package_data = create_export_package(sim_id)
            if package_data:
                st.download_button(
                    label="Export",
                    data=package_data,
                    file_name=f"APE_{sim_id}.zip",
                    mime="application/zip",
                    use_container_width=True,
                    help="Export simulation as portable package"
                )