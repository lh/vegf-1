"""
Reports page for the APE Streamlit application.

This module handles generating and displaying reports from simulation results.
"""

import os
import tempfile
import streamlit as st
import pandas as pd
import json

from streamlit_app.components.layout import display_logo_and_title
from streamlit_app.utils.session_state import get_simulation_results, get_debug_mode
from streamlit_app.models.report import Report, ReportGenerator
from streamlit_app.models.simulation_results import SimulationResults
from streamlit_app.components.visualizations.export import get_exporter

# Import Quarto utilities conditionally
try:
    from streamlit_app.quarto_utils import get_quarto, render_quarto_report
except ImportError:
    # Define fallbacks 
    def get_quarto():
        """Fallback for get_quarto."""
        return None
    
    def render_quarto_report(quarto_path, qmd_path, output_dir, data_path, 
                             output_format, include_code=False, include_appendix=True):
        """Fallback for render_quarto_report."""
        return None


def display_reports_page():
    """Display the reports page for generating reports from simulation results."""
    display_logo_and_title("Generate Reports")
    
    # Ensure Quarto is available for document rendering
    quarto_path = get_quarto()
    visualization_exporter = get_exporter()
    
    if not quarto_path:
        st.error("Quarto is not available. Reports cannot be generated.")
        st.info("""
        To use report generation features, please install Quarto:
        
        1. Download from: [https://quarto.org/docs/download/](https://quarto.org/docs/download/)
        2. Follow the installation instructions for your platform
        3. Restart the application after installation
        """)
    else:
        st.success(f"Quarto is available at: {quarto_path}")
        
        st.subheader("Generate Simulation Report")
        st.markdown("""
        Generate a comprehensive report of the simulation results. The report will include
        detailed statistics, visualizations, and analysis of the enhanced discontinuation model.
        """)
        
        # Report options
        report_format = st.radio(
            "Report Format",
            ["HTML", "PDF", "Word"],
            horizontal=True,
            help="Select the output format for the report",
            key="report_format_radio"
        )
        
        include_code = st.checkbox(
            "Include Code",
            value=False,
            help="Include the code used to generate the visualizations in the report",
            key="include_code_checkbox"
        )
        
        include_appendix = st.checkbox(
            "Include Appendix",
            value=True,
            help="Include additional details and methodology in an appendix",
            key="include_appendix_checkbox"
        )
        
        # Get debug mode
        debug_mode = get_debug_mode()
        
        # Generate report button
        if st.button("Generate Report", type="primary", key="generate_report_button", help="Generate a detailed report of simulation results"):
            # Check if we have simulation results
            results = get_simulation_results()
            
            if results is None:
                st.warning("Please run a simulation first before generating a report.")
            else:
                # Convert dictionary results to SimulationResults object if needed
                if isinstance(results, dict):
                    try:
                        results = SimulationResults.from_dict(results)
                    except Exception as e:
                        if debug_mode:
                            st.error(f"Error converting results to structured format: {str(e)}")
                        results = results  # Keep using dictionary format
                
                with st.spinner("Generating report..."):
                    try:
                        # Create temporary directory for report
                        with tempfile.TemporaryDirectory() as tmp_dir:
                            # Check if these are sample results
                            if isinstance(results, dict) and results.get("is_sample", False):
                                st.warning("⚠️ **Sample Data**: This report will use sample data, not actual simulation outputs.")
                                st.info("The actual simulation module couldn't be loaded. The report will still be generated but with simulated data.")
                            
                            # Create report generator
                            report_generator = ReportGenerator(
                                output_dir=tmp_dir,
                                include_code=include_code,
                                include_appendix=include_appendix
                            )
                            
                            # Generate report
                            simulation_id = results.simulation_id if hasattr(results, "simulation_id") else None
                            
                            # Get output format
                            output_format = report_format.lower()
                            
                            # Generate report data model
                            report = report_generator.generate_simulation_report(results)
                            
                            # Export visualizations if available
                            if simulation_id:
                                viz_dir = os.path.join(tmp_dir, "visualizations")
                                os.makedirs(viz_dir, exist_ok=True)
                                
                                # Export visualizations for the report
                                exported_viz = visualization_exporter.export_for_report(
                                    simulation_id=simulation_id,
                                    output_dir=viz_dir,
                                    format=output_format if output_format != "word" else "png",
                                    dpi=300
                                )
                                
                                # Add visualizations to report
                                for viz_type, viz_path in exported_viz.items():
                                    report.add_visualization(viz_type, viz_path)
                            
                            # Save report data model
                            report_data_path = os.path.join(tmp_dir, "report_data.json")
                            report.save(report_data_path)
                            
                            # Define paths
                            qmd_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                                    "reports", "simulation_report.qmd")
                            
                            # Check if the Quarto template exists
                            if not os.path.exists(qmd_path):
                                st.error("Quarto template not found. Please ensure the reports directory exists.")
                                st.info(f"Expected template at: {qmd_path}")
                                return
                            
                            # Render report using Quarto
                            report_path = render_quarto_report(
                                quarto_path,
                                qmd_path,
                                tmp_dir,
                                report_data_path,
                                output_format,
                                include_code=include_code,
                                include_appendix=include_appendix
                            )
                            
                            # Show success and provide download button
                            if report_path and os.path.exists(report_path):
                                st.success("Report generated successfully!")
                                
                                # Read the report file
                                with open(report_path, "rb") as f:
                                    report_data = f.read()
                                
                                # Create a download button
                                file_extension = output_format if output_format != "html" else "html"
                                st.download_button(
                                    label=f"Download {report_format} Report",
                                    data=report_data,
                                    file_name=f"enhanced_discontinuation_report.{file_extension}",
                                    mime=f"application/{file_extension}",
                                    key="download_report_button"
                                )
                                
                                # Preview for HTML reports
                                if output_format == "html" and os.path.getsize(report_path) < 5 * 1024 * 1024:  # 5MB limit
                                    with st.expander("Preview Report"):
                                        # Read HTML content
                                        with open(report_path, "r", encoding="utf-8") as f:
                                            html_content = f.read()
                                        
                                        # Display using iframe
                                        st.components.v1.html(html_content, height=600, scrolling=True)
                            else:
                                st.error("Failed to generate report.")
                    except Exception as e:
                        st.error(f"Error generating report: {str(e)}")
                        if debug_mode:
                            st.exception(e)

        # Information about exported visualizations
        with st.expander("About Visualization Caching for Reports"):
            st.markdown("""
            ### Visualization Caching System
            
            The APE application uses an advanced visualization caching system that:
            
            1. **Stores visualizations persistently** - Visualizations are cached on disk and can be reused across sessions
            2. **Avoids regeneration** - Expensive visualizations (especially R-based) are only generated once
            3. **Supports multiple formats** - The same visualization can be exported in various formats for different report types
            4. **Links visualizations to simulations** - Each visualization is associated with its source simulation
            
            This ensures that reports can be generated quickly without regenerating visualizations, and that
            all visualizations remain available even if you run multiple simulations.
            """)
            
            # Show visualization cache statistics if in debug mode
            if debug_mode:
                try:
                    cache = get_exporter()._exporter_instance.cache
                    if cache and hasattr(cache, "metadata") and cache.metadata:
                        st.subheader("Visualization Cache Statistics")
                        
                        # Count by visualization type
                        viz_types = {}
                        for key, meta in cache.metadata.items():
                            viz_type = meta.viz_type
                            viz_types[viz_type] = viz_types.get(viz_type, 0) + 1
                        
                        # Create a dataframe
                        stats_df = pd.DataFrame([
                            {"Visualization Type": viz_type, "Count": count}
                            for viz_type, count in viz_types.items()
                        ])
                        
                        # Show the dataframe
                        st.dataframe(stats_df)
                        
                        # Show cache info
                        st.markdown(f"**Total Cached Visualizations:** {len(cache.metadata)}")
                        st.markdown(f"**Cache Directory:** {cache.cache_dir}")
                except Exception as e:
                    st.warning(f"Could not retrieve cache statistics: {str(e)}")


if __name__ == "__main__":
    # This allows the page to be run directly for testing
    import sys
    import os
    
    # Add parent directory to path so imports work
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # Set up basic Streamlit configuration
    st.set_page_config(page_title="Reports Test", layout="wide")
    
    # Display the reports page
    display_reports_page()