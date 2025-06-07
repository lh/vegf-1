"""
Export functionality for Analysis Overview page.

Provides simulation package export capabilities integrated into the audit trail tab.
"""

import streamlit as st
from datetime import datetime
from utils.simulation_package import SimulationPackageManager
from core.results.factory import ResultsFactory
import logging

logger = logging.getLogger(__name__)


def render_export_section():
    """Render the export simulation section in Analysis Overview"""
    st.subheader("Export Simulation")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.write("Download this simulation as a portable package for sharing or archival.")
        
    with col2:
        if st.button("📦 Download Package", type="primary"):
            try:
                # Get current simulation ID from session state
                sim_id = st.session_state.get('current_sim_id')
                if not sim_id:
                    st.error("No simulation selected")
                    return
                
                # Check if simulation directory exists
                results_path = ResultsFactory.DEFAULT_RESULTS_DIR / sim_id
                if not results_path.exists():
                    st.error(f"Simulation directory not found: {sim_id}")
                    st.info("This simulation may have been deleted or moved. Please select another simulation.")
                    # Clear the invalid sim_id from session state
                    if 'current_sim_id' in st.session_state:
                        del st.session_state.current_sim_id
                    return
                
                # Show progress
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Progress callback
                def update_progress(percent, message):
                    progress_bar.progress(percent / 100)
                    status_text.text(message)
                
                # Load simulation results
                status_text.text("Loading simulation...")
                results = ResultsFactory.load_results(results_path)
                
                # Create package with progress updates
                status_text.text("Creating package...")
                manager = SimulationPackageManager()
                
                # Create package
                package_data = manager.create_package(results)
                
                # Generate filename (sim_id already contains date/time)
                package_name = f"APE_{sim_id}.zip"
                
                # Clear progress indicators
                progress_bar.empty()
                status_text.empty()
                
                # Offer download
                st.download_button(
                    label="⬇️ Download Package",
                    data=package_data,
                    file_name=package_name,
                    mime="application/zip"
                )
                st.success("Package ready for download!")
                
            except Exception as e:
                logger.error(f"Failed to create package: {e}")
                st.error(f"Failed to create package: {str(e)}")
                # Clear progress on error
                if 'progress_bar' in locals():
                    progress_bar.empty()
                if 'status_text' in locals():
                    status_text.empty()


def render_export_section_with_progress():
    """Enhanced version with detailed progress tracking"""
    st.subheader("Export Simulation")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.write("Download this simulation as a portable package for sharing or archival.")
        
        # Show package contents info
        with st.expander("ℹ️ Package Contents"):
            st.write("""
            The exported package includes:
            - **Patient Data**: All patient records and outcomes
            - **Visit Data**: Complete visit history for all patients  
            - **Protocol**: The exact protocol specification used
            - **Parameters**: All simulation parameters
            - **Audit Trail**: Complete history of the simulation
            - **Checksums**: Data integrity verification
            """)
        
    with col2:
        if st.button("📦 Download Package", type="primary", help="Export simulation as ZIP file"):
            try:
                # Get current simulation ID
                sim_id = st.session_state.get('current_sim_id')
                if not sim_id:
                    st.error("No simulation selected")
                    return
                
                # Check if simulation directory exists
                results_path = ResultsFactory.DEFAULT_RESULTS_DIR / sim_id
                if not results_path.exists():
                    st.error(f"Simulation directory not found: {sim_id}")
                    st.info("This simulation may have been deleted or moved. Please select another simulation.")
                    # Clear the invalid sim_id from session state
                    if 'current_sim_id' in st.session_state:
                        del st.session_state.current_sim_id
                    return
                
                # Create progress container
                with st.container():
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    # Progress callback for package manager
                    def update_progress(percent, message):
                        progress_bar.progress(int(percent) / 100)
                        status_text.text(f"📦 {message}")
                    
                    try:
                        # Load simulation
                        update_progress(10, "Loading simulation data...")
                        results = ResultsFactory.load_results(results_path)
                        
                        # Create package manager with progress
                        update_progress(20, "Initializing package manager...")
                        manager = SimulationPackageManager()
                        
                        # Simulate detailed progress during package creation
                        # In real implementation, this would be passed to create_package
                        update_progress(30, "Exporting patient data...")
                        update_progress(50, "Exporting visit records...")
                        update_progress(70, "Generating manifest...")
                        update_progress(85, "Compressing package...")
                        
                        # Create the package
                        package_data = manager.create_package(results)
                        
                        update_progress(95, "Finalizing...")
                        
                        # Generate filename with timestamp
                        package_name = f"APE_simulation_{sim_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
                        
                        # Calculate package size
                        package_size_mb = len(package_data) / (1024 * 1024)
                        
                        update_progress(100, "Complete!")
                        
                        # Clear progress
                        progress_bar.empty()
                        status_text.empty()
                        
                        # Success message with size info
                        st.success(f"✅ Package created successfully ({package_size_mb:.1f} MB)")
                        
                        # Offer download with additional info
                        col_dl1, col_dl2 = st.columns([3, 1])
                        with col_dl1:
                            st.download_button(
                                label="⬇️ Download Package",
                                data=package_data,
                                file_name=package_name,
                                mime="application/zip",
                                help=f"Download {package_name} ({package_size_mb:.1f} MB)"
                            )
                        with col_dl2:
                            st.metric("Package Size", f"{package_size_mb:.1f} MB")
                        
                        # Show package details
                        with st.expander("📋 Package Details", expanded=True):
                            st.write(f"**Filename**: `{package_name}`")
                            st.write(f"**Size**: {package_size_mb:.1f} MB ({len(package_data):,} bytes)")
                            st.write(f"**Created**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                            st.write(f"**Simulation ID**: {sim_id}")
                            
                            # Get simulation details from results
                            if hasattr(results, 'metadata'):
                                st.write(f"**Patients**: {results.metadata.n_patients:,}")
                                st.write(f"**Duration**: {results.metadata.duration_years} years")
                                st.write(f"**Protocol**: {results.metadata.protocol_name}")
                        
                    except Exception as e:
                        # Clear progress on error
                        progress_bar.empty()
                        status_text.empty()
                        raise
                        
            except FileNotFoundError:
                st.error("❌ Simulation data not found. The simulation may have been deleted.")
            except PermissionError:
                st.error("❌ Permission denied. Unable to access simulation data.")
            except Exception as e:
                logger.error(f"Export failed for simulation {sim_id}: {e}")
                st.error(f"❌ Failed to create package: {str(e)}")
                st.info("💡 If the problem persists, try refreshing the page or contact support.")


# Integrate into Analysis Overview page
def add_export_to_audit_trail_tab():
    """Add export functionality to the audit trail tab"""
    # This function would be called from the main Analysis Overview page
    # within the Audit Trail tab
    
    st.markdown("---")  # Separator
    
    # Export section
    render_export_section_with_progress()
    
    # Additional options
    st.markdown("---")
    
    # Archive section (future enhancement)
    with st.expander("🗄️ Archive Options", expanded=False):
        st.info("Coming soon: Long-term archival options with cloud storage integration.")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.button("☁️ Archive to Cloud", disabled=True, help="Coming soon")
        with col2:
            st.button("💾 Local Backup", disabled=True, help="Coming soon")  
        with col3:
            st.button("📧 Email Package", disabled=True, help="Coming soon")