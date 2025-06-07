"""
Import functionality for Protocol Manager page.

Provides simulation package import capabilities for analyzing previously exported results.
"""

import streamlit as st
from pathlib import Path
from utils.simulation_package import SimulationPackageManager, SecurityError, PackageValidationError
from core.results.factory import ResultsFactory
from core.storage.registry import SimulationRegistry
import logging

logger = logging.getLogger(__name__)


def render_import_section():
    """Render the import simulation package section"""
    
    with st.expander("📥 Import Simulation Package"):
        st.write("Upload a simulation package to analyse previously exported results.")
        
        # File uploader
        uploaded_file = st.file_uploader(
            "Choose simulation package",
            type=['zip'],
            help="Select a .zip file exported from APE",
            key="import_section_uploader"
        )
        
        if uploaded_file:
            # Show file info
            file_size_mb = uploaded_file.size / (1024 * 1024)
            
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                st.write(f"**File**: {uploaded_file.name}")
            with col2:
                st.write(f"**Size**: {file_size_mb:.1f} MB")
            with col3:
                if st.button("Import Simulation", type="primary"):
                    import_simulation_package(uploaded_file)


def import_simulation_package(uploaded_file):
    """Handle the import of a simulation package"""
    try:
        # Show progress
        progress_container = st.container()
        with progress_container:
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Progress callback
            def update_progress(percent, message):
                progress_bar.progress(int(percent) / 100)
                status_text.text(f"📥 {message}")
            
            try:
                # Read package data
                update_progress(10, "Reading package...")
                package_data = uploaded_file.read()
                
                # Validate package
                update_progress(20, "Validating package...")
                manager = SimulationPackageManager()
                
                # Security validation happens inside import_package
                update_progress(30, "Security checks...")
                
                # Import the package
                update_progress(40, "Extracting data...")
                update_progress(60, "Loading simulation...")
                imported_results = manager.import_package(package_data)
                
                # Save to results system
                update_progress(80, "Saving to database...")
                sim_id = ResultsFactory.save_imported_results(imported_results)
                
                # Register with simulation registry
                update_progress(90, "Registering simulation...")
                registry = SimulationRegistry(ResultsFactory.DEFAULT_RESULTS_DIR)
                
                # Calculate size
                import os
                sim_path = ResultsFactory.DEFAULT_RESULTS_DIR / sim_id
                size_mb = 0
                if sim_path.exists():
                    for file in sim_path.rglob('*'):
                        if file.is_file():
                            size_mb += file.stat().st_size / (1024 * 1024)
                
                # Convert metadata to dict if needed
                metadata_dict = imported_results.metadata.__dict__ if hasattr(imported_results.metadata, '__dict__') else imported_results.metadata
                registry.register_simulation(sim_id, metadata_dict, size_mb)
                
                update_progress(100, "Complete!")
                
                # Clear progress
                progress_bar.empty()
                status_text.empty()
                
                # Success!
                st.success(f"✅ Simulation imported successfully!")
                
                # Update session state
                st.session_state.current_sim_id = sim_id
                st.session_state.imported_simulation = True
                
                # Mark as imported in session state for visual indicators
                if 'imported_simulations' not in st.session_state:
                    st.session_state.imported_simulations = set()
                st.session_state.imported_simulations.add(sim_id)
                
                # Show import details
                with st.expander("📋 Import Details", expanded=True):
                    st.write(f"**New Simulation ID**: `{sim_id}`")
                    st.write(f"**Original ID**: `{imported_results.metadata.sim_id}`")
                    st.write(f"**Protocol**: {imported_results.metadata.protocol_name}")
                    st.write(f"**Patients**: {imported_results.metadata.n_patients:,}")
                    st.write(f"**Duration**: {imported_results.metadata.duration_years} years")
                    st.write(f"**Engine**: {imported_results.metadata.engine_type}")
                    
                    # Navigation options
                    st.info("🎯 The imported simulation is now available for analysis.")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("📊 Go to Analysis", type="primary"):
                            # Navigate to Analysis Overview
                            st.session_state.page = "Analysis Overview"
                            st.rerun()
                    with col2:
                        if st.button("🔄 Import Another"):
                            # Clear the file uploader by rerunning
                            st.rerun()
                
            except Exception as e:
                # Clear progress on error
                progress_bar.empty()
                status_text.empty()
                raise
                
    except SecurityError as e:
        st.error(f"🛡️ Security Error: {str(e)}")
        st.warning("The package failed security validation. This could indicate:")
        st.write("- Corrupted or tampered package file")
        st.write("- Package created by incompatible version")
        st.write("- Malicious content detected")
        logger.warning(f"Security error importing package: {e}")
        
    except PackageValidationError as e:
        st.error(f"📦 Package Error: {str(e)}")
        st.info("The package structure is invalid. Please ensure:")
        st.write("- The file is a valid APE simulation package")
        st.write("- The package was exported from a compatible version")
        st.write("- The file is not corrupted")
        logger.error(f"Package validation error: {e}")
        
    except FileNotFoundError as e:
        st.error("❌ Required files missing from package")
        st.info("The package appears to be incomplete. Try exporting again.")
        logger.error(f"Missing files in package: {e}")
        
    except Exception as e:
        st.error(f"❌ Failed to import package: {str(e)}")
        st.info("💡 If the problem persists, try:")
        st.write("1. Verify the package file is not corrupted")
        st.write("2. Check that the package is from a compatible APE version")
        st.write("3. Ensure you have sufficient disk space")
        logger.error(f"Unexpected error importing package: {e}")


def render_enhanced_import_section():
    """Enhanced import section with additional features"""
    
    st.markdown("### 📥 Import Simulation Package")
    
    # Info about imports
    with st.expander("ℹ️ About Simulation Packages", expanded=False):
        st.write("""
        **Simulation packages** allow you to:
        - Share simulation results with colleagues
        - Archive simulations for long-term storage
        - Transfer simulations between systems
        - Analyse results without re-running simulations
        
        **Package Security**:
        - All packages are validated for security
        - File integrity verified with checksums
        - Malicious content automatically blocked
        """)
    
    # Recent imports (if any)
    if 'imported_simulations' in st.session_state and st.session_state.imported_simulations:
        st.info(f"📌 You have imported {len(st.session_state.imported_simulations)} simulation(s) in this session")
    
    # Main import interface
    uploaded_file = st.file_uploader(
        "Choose simulation package",
        type=['zip'],
        help="Select a .zip file exported from APE",
        key="import_uploader"
    )
    
    if uploaded_file:
        # Validate file before import
        file_size_mb = uploaded_file.size / (1024 * 1024)
        
        # Check file size
        MAX_FILE_SIZE_MB = 500  # 500MB limit for web upload
        if file_size_mb > MAX_FILE_SIZE_MB:
            st.error(f"❌ File too large ({file_size_mb:.1f} MB). Maximum size is {MAX_FILE_SIZE_MB} MB.")
            st.info("For larger files, consider using the command-line import tool.")
            return
        
        # File info card
        with st.container():
            st.markdown("#### 📄 Package Information")
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                st.write(f"**Filename**: `{uploaded_file.name}`")
                # Check filename pattern
                if "APE_simulation_" in uploaded_file.name:
                    st.write("✅ Valid APE package filename")
                else:
                    st.warning("⚠️ Filename doesn't match APE pattern")
            
            with col2:
                st.metric("Size", f"{file_size_mb:.1f} MB")
            
            with col3:
                st.metric("Type", uploaded_file.type)
        
        # Import options
        st.markdown("#### ⚙️ Import Options")
        
        col1, col2 = st.columns([1, 1])
        with col1:
            validate_only = st.checkbox(
                "Validate only", 
                help="Check package validity without importing"
            )
        with col2:
            show_details = st.checkbox(
                "Show import details",
                value=True,
                help="Display detailed information during import"
            )
        
        # Import button
        st.markdown("---")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if validate_only:
                if st.button("🔍 Validate Package", type="primary", use_container_width=True):
                    validate_package_only(uploaded_file, show_details)
            else:
                if st.button("📥 Import Simulation", type="primary", use_container_width=True):
                    import_simulation_package_enhanced(uploaded_file, show_details)


def validate_package_only(uploaded_file, show_details=True):
    """Validate a package without importing it"""
    try:
        with st.spinner("Validating package..."):
            # Read package
            package_data = uploaded_file.read()
            
            # Create manager and validate
            manager = SimulationPackageManager()
            
            # Write to temp file for validation
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp:
                tmp.write(package_data)
                tmp_path = Path(tmp.name)
            
            try:
                # Validate structure
                validation_result = manager.validate_package(tmp_path)
                
                if validation_result['valid']:
                    st.success("✅ Package validation passed!")
                    
                    if show_details:
                        with st.expander("📋 Validation Details", expanded=True):
                            st.write("**Files found**:")
                            for file in validation_result['files_found']:
                                st.write(f"- `{file}`")
                else:
                    st.error("❌ Package validation failed!")
                    for error in validation_result['errors']:
                        st.write(f"- {error}")
                    
                    if validation_result['missing_files']:
                        st.warning("Missing required files:")
                        for file in validation_result['missing_files']:
                            st.write(f"- `{file}`")
                            
            finally:
                # Clean up temp file
                tmp_path.unlink()
                
    except Exception as e:
        st.error(f"❌ Validation error: {str(e)}")


def import_simulation_package_enhanced(uploaded_file, show_details=True):
    """Enhanced import with better error handling and progress"""
    # Delegate to main import function with enhanced features
    import_simulation_package(uploaded_file)
    
    # Additional features could include:
    # - Dry run mode
    # - Partial import options
    # - Conflict resolution (if simulation ID exists)
    # - Batch import support