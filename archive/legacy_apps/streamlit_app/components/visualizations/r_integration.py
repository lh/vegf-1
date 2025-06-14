"""
R-based visualization integration for the APE Streamlit application.

This module provides functions to create high-quality visualizations using R/ggplot2,
with a progressive enhancement approach that shows matplotlib visualizations first
and then replaces them with R-based visualizations when ready.
"""

import os
import subprocess
import tempfile
import logging
import pandas as pd
import streamlit as st
import time
from typing import Dict, Any, Optional, List, Tuple, Union

from streamlit_app.components.visualizations.common import (
    is_r_available,
    check_r_packages,
    install_r_packages,
    get_r_script_path,
    dataframe_to_temp_csv,
    VisualizationTimer,
    create_unique_filename
)
from streamlit_app.components.visualizations.matplotlib_viz import (
    create_enrollment_visualization_matplotlib,
    create_va_over_time_plot_matplotlib,
    create_dual_timeframe_plot_matplotlib
)
from streamlit_app.components.visualizations.cache import get_cache

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_r_visualization(
    data_path: str,
    output_path: str,
    viz_type: str,
    width: int = 10,
    height: int = 5,
    dpi: int = 120,
    theme: str = "tufte",
    debug: bool = False
) -> bool:
    """Run R script to create a visualization.

    Parameters
    ----------
    data_path : str
        Path to the data CSV file
    output_path : str
        Path to save the output visualization
    viz_type : str
        Type of visualization to create
    width : int, optional
        Width of the output in inches, by default 10
    height : int, optional
        Height of the output in inches, by default 5
    dpi : int, optional
        Resolution of the output in DPI, by default 120
    theme : str, optional
        Visualization theme, by default "tufte"

    Returns
    -------
    bool
        True if successful, False otherwise
    """
    # Check if R is available
    if not is_r_available():
        logger.warning("R is not installed, skipping R visualization")
        return False

    # Check if required R packages are installed
    if not check_r_packages():
        logger.warning("Missing required R packages, attempting to install...")
        if not install_r_packages():
            logger.error("Failed to install required R packages, skipping R visualization")
            return False

    # Get R script path
    r_script_path = get_r_script_path()

    # Check if R script exists
    if not os.path.exists(r_script_path):
        logger.error(f"R script not found at {r_script_path}")
        return False

    # Check if data file exists
    if not os.path.exists(data_path):
        logger.error(f"Data file not found at {data_path}")
        return False

    # Check if output directory exists
    output_dir = os.path.dirname(output_path)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
        logger.info(f"Created output directory: {output_dir}")

    try:
        # Run R script to create visualization
        # Use the original format of passing arguments separately
        r_command = [
            "Rscript", r_script_path,
            "--data", data_path,
            "--output", output_path,
            "--type", viz_type,
            "--width", str(width),
            "--height", str(height),
            "--dpi", str(dpi),
            "--theme", theme
        ]

        logger.info(f"Running R command: {' '.join(r_command)}")

        with VisualizationTimer(f"R visualization ({viz_type})"):
            # If debug mode is enabled, print the R script output to the console
            if debug:
                print(f"Running R command: {' '.join(r_command)}")
                result = subprocess.run(
                    r_command,
                    capture_output=True,
                    text=True,
                    check=False
                )
                print(f"R stdout: {result.stdout}")
                print(f"R stderr: {result.stderr}")
            else:
                result = subprocess.run(
                    r_command,
                    capture_output=True,
                    text=True,
                    check=False
                )

        # Check if R script executed successfully
        if result.returncode == 0 and os.path.exists(output_path):
            logger.info(f"R visualization created successfully at {output_path}")
            # Check file size to ensure it's a valid image
            file_size = os.path.getsize(output_path)
            if file_size < 100:  # Very small file might indicate an error
                logger.error(f"R visualization file seems too small ({file_size} bytes), may be invalid")
                return False
            return True
        else:
            logger.error(f"Error running R script: {result.stderr}")
            # Print a snippet of the CSV data
            try:
                with open(data_path, 'r') as f:
                    data_head = f.read(1000)  # Read first 1000 characters
                logger.info(f"Data file preview: {data_head}")
            except Exception as e:
                logger.error(f"Error reading data file: {e}")

            # Log R output
            logger.info(f"R stdout: {result.stdout}")
            logger.info(f"R stderr: {result.stderr}")
            return False
    except Exception as e:
        logger.error(f"Error creating R visualization: {e}")
        # Try to get traceback
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False


def render_enrollment_visualization(enrollment_df: pd.DataFrame, use_r: bool = True) -> None:
    """Render patient enrollment visualization using both matplotlib and R.

    This function first shows a matplotlib visualization immediately,
    then attempts to replace it with a higher-quality R visualization
    if R is available. This provides a responsive experience with
    progressive enhancement.

    Parameters
    ----------
    enrollment_df : pandas.DataFrame
        DataFrame with 'patient_id' and 'enrollment_date' columns
    use_r : bool, optional
        Whether to use R for visualization (if available), by default True
    """
    # Create a unique ID for this visualization
    viz_id = f"enrollment_{int(time.time())}"
    
    # First, create placeholder for the visualization
    viz_placeholder = st.empty()
    
    # Get visualization cache
    cache = get_cache()
    
    # Check if we have a cached version (using enrollment data hash)
    cached_viz = cache.get_cached_visualization(
        viz_type="enrollment",
        data=enrollment_df,
        parameters={}
    )
    
    if cached_viz:
        # Use cached visualization
        viz_placeholder.image(cached_viz)
        return
    
    # Immediately show matplotlib visualization
    with VisualizationTimer("Matplotlib enrollment visualization"):
        fig = create_enrollment_visualization_matplotlib(enrollment_df)
        viz_placeholder.pyplot(fig)
    
        # Cache the matplotlib visualization
        temp_path = os.path.join(tempfile.gettempdir(), f"{viz_id}_mpl.png")
        fig.savefig(temp_path, dpi=80, bbox_inches='tight')
        cache.cache_matplotlib_figure(
            viz_type="enrollment",
            fig=fig,
            data=enrollment_df,
            parameters={}
        )
    
    # Now try to create R visualization in the background - only if use_r is True
    if use_r:
        try:
            # Create a thread to generate R visualization
            import threading

            def generate_r_viz():
                try:
                    # Create temporary directory for R data and output
                    temp_dir, csv_path = dataframe_to_temp_csv(enrollment_df, "enrollment")
                    output_path = os.path.join(temp_dir, f"enrollment_{viz_id}.png")

                    # Run R script to create visualization
                    # Pass debug mode to show detailed output
                    debug_mode = st.session_state.get("debug_mode_toggle", False)

                    # Log attempt to create R visualization
                    logger.info(f"Attempting to create R visualization with debug_mode={debug_mode}")
                    logger.info(f"R visualization input: {csv_path}")
                    logger.info(f"R visualization output: {output_path}")

                    success = run_r_visualization(
                        data_path=csv_path,
                        output_path=output_path,
                        viz_type="enrollment",
                        width=10,
                        height=5,
                        dpi=120,
                        debug=debug_mode
                    )

                    if success and os.path.exists(output_path):
                        # Log successful R visualization creation
                        logger.info(f"R visualization created at {output_path}")

                        # Check if file exists and has content
                        file_size = os.path.getsize(output_path)
                        logger.info(f"R visualization file size: {file_size} bytes")

                        if file_size > 100:  # Must be a real image, not empty/error file
                            # Cache the R visualization
                            cached_path = cache.cache_visualization(
                                viz_type="enrollment",
                                data=enrollment_df,
                                file_path=output_path,
                                parameters={},
                                format="png",
                                width=10,
                                height=5,
                                dpi=120
                            )

                            # Log this step
                            logger.info(f"Cached R visualization at {cached_path}")

                            # Update the placeholder with R visualization - simpler approach
                            logger.info(f"Replacing matplotlib visualization with R visualization at {cached_path}")

                            # Use the placeholder directly - this simpler approach worked before
                            viz_placeholder.image(cached_path)
                            logger.info(f"Successfully updated visualization with R version")

                            # Show success message in debug mode
                            if debug_mode:
                                st.success("R visualization successfully generated and displayed")
                        else:
                            logger.error(f"R visualization file seems empty or corrupt (size: {file_size} bytes)")
                            if debug_mode:
                                st.warning("R visualization file was created but appears to be empty or corrupt")
                except Exception as e:
                    logger.error(f"Error in R visualization thread: {e}")

            # Start thread to generate R visualization - this approach worked before
            # Using a background thread allows Streamlit to continue rendering
            r_thread = threading.Thread(target=generate_r_viz)
            r_thread.daemon = True
            r_thread.start()
            logger.info(f"Started R visualization thread for enrollment visualization")
        except Exception as e:
            logger.error(f"Error starting R visualization thread: {e}")


def render_va_over_time_visualization(results: Dict[str, Any], simulation_id: Optional[str] = None) -> None:
    """Render visual acuity over time visualization using both matplotlib and R.
    
    Parameters
    ----------
    results : Dict[str, Any]
        Simulation results containing mean_va_data
    simulation_id : str, optional
        Simulation ID for caching, by default None
    """
    # Create a unique ID for this visualization
    viz_id = f"va_over_time_{int(time.time())}"
    
    # First, create placeholder for the visualization
    viz_placeholder = st.empty()
    
    # Get visualization cache
    cache = get_cache()
    
    # Extract data for visualization
    if "mean_va_data" not in results or not results["mean_va_data"]:
        viz_placeholder.warning("No visual acuity data available")
        return
    
    va_data = results["mean_va_data"]
    
    # Prepare data for R
    va_df = pd.DataFrame([
        {"time": point.get("time", 0) if isinstance(point, dict) else getattr(point, "time", 0),
         "visual_acuity": point.get("visual_acuity", 0) if isinstance(point, dict) else getattr(point, "visual_acuity", 0)}
        for point in va_data
    ])
    
    # Check if we have a cached version
    cached_viz = cache.get_cached_visualization(
        viz_type="va_over_time",
        data=va_df,
        parameters={},
        simulation_id=simulation_id
    )
    
    if cached_viz:
        # Use cached visualization
        viz_placeholder.image(cached_viz)
        return
    
    # Immediately show matplotlib visualization
    with VisualizationTimer("Matplotlib VA visualization"):
        fig = create_va_over_time_plot_matplotlib(results)
        viz_placeholder.pyplot(fig)
    
        # Cache the matplotlib visualization
        temp_path = os.path.join(tempfile.gettempdir(), f"{viz_id}_mpl.png")
        fig.savefig(temp_path, dpi=80, bbox_inches='tight')
        cache.cache_matplotlib_figure(
            viz_type="va_over_time",
            fig=fig,
            data=va_df,
            parameters={},
            simulation_id=simulation_id
        )
    
    # Now try to create R visualization in the background
    try:
        # Create a thread to generate R visualization
        import threading
        
        def generate_r_viz():
            try:
                # Create temporary directory for R data and output
                temp_dir, csv_path = dataframe_to_temp_csv(va_df, "va_over_time")
                output_path = os.path.join(temp_dir, f"va_over_time_{viz_id}.png")
                
                # Run R script to create visualization
                success = run_r_visualization(
                    data_path=csv_path,
                    output_path=output_path,
                    viz_type="va_over_time",
                    width=10,
                    height=5,
                    dpi=120
                )
                
                if success and os.path.exists(output_path):
                    # Cache the R visualization
                    cached_path = cache.cache_visualization(
                        viz_type="va_over_time",
                        data=va_df,
                        file_path=output_path,
                        parameters={},
                        simulation_id=simulation_id,
                        format="png",
                        width=10,
                        height=5,
                        dpi=120
                    )
                    
                    # Update the placeholder with R visualization
                    viz_placeholder.image(cached_path)
            except Exception as e:
                logger.error(f"Error in R visualization thread: {e}")
        
        # Start thread to generate R visualization
        r_thread = threading.Thread(target=generate_r_viz)
        r_thread.daemon = True
        r_thread.start()
        
    except Exception as e:
        logger.error(f"Error starting R visualization thread: {e}")
        # Keep the matplotlib visualization


def render_dual_timeframe_visualization(results: Dict[str, Any], simulation_id: Optional[str] = None) -> None:
    """Render dual timeframe visualization using both matplotlib and R.
    
    Parameters
    ----------
    results : Dict[str, Any]
        Simulation results containing calendar_time_va and patient_time_va
    simulation_id : str, optional
        Simulation ID for caching, by default None
    """
    # Create a unique ID for this visualization
    viz_id = f"dual_timeframe_{int(time.time())}"
    
    # First, create placeholder for the visualization
    viz_placeholder = st.empty()
    
    # Get visualization cache
    cache = get_cache()
    
    # Check if we have the required data
    if "calendar_time_va" not in results or "patient_time_va" not in results:
        viz_placeholder.warning("No dual timeframe data available")
        return
    
    # Prepare data for R
    calendar_data = results["calendar_time_va"]
    patient_data = results["patient_time_va"]
    
    # Create DataFrame with both calendar and patient time data
    dual_df = pd.DataFrame([
        {"calendar_time": point["month"], "calendar_va": point["mean_va"],
         "patient_time": 0, "patient_va": 0}
        for point in calendar_data
    ])
    
    # Add patient time data
    patient_df = pd.DataFrame([
        {"calendar_time": 0, "calendar_va": 0,
         "patient_time": point["week"], "patient_va": point["mean_va"]}
        for point in patient_data
    ])
    
    # Combine dataframes
    dual_df = pd.concat([dual_df, patient_df], ignore_index=True)
    
    # Check if we have a cached version
    cached_viz = cache.get_cached_visualization(
        viz_type="dual_timeframe",
        data=dual_df,
        parameters={},
        simulation_id=simulation_id
    )
    
    if cached_viz:
        # Use cached visualization
        viz_placeholder.image(cached_viz)
        return
    
    # Immediately show matplotlib visualization
    with VisualizationTimer("Matplotlib dual timeframe visualization"):
        fig = create_dual_timeframe_plot_matplotlib(results)
        viz_placeholder.pyplot(fig)
    
        # Cache the matplotlib visualization
        temp_path = os.path.join(tempfile.gettempdir(), f"{viz_id}_mpl.png")
        fig.savefig(temp_path, dpi=80, bbox_inches='tight')
        cache.cache_matplotlib_figure(
            viz_type="dual_timeframe",
            fig=fig,
            data=dual_df,
            parameters={},
            simulation_id=simulation_id
        )
    
    # Now try to create R visualization in the background
    try:
        # Create a thread to generate R visualization
        import threading
        
        def generate_r_viz():
            try:
                # Create temporary directory for R data and output
                temp_dir, csv_path = dataframe_to_temp_csv(dual_df, "dual_timeframe")
                output_path = os.path.join(temp_dir, f"dual_timeframe_{viz_id}.png")
                
                # Run R script to create visualization
                success = run_r_visualization(
                    data_path=csv_path,
                    output_path=output_path,
                    viz_type="dual_timeframe",
                    width=12,
                    height=5,
                    dpi=120
                )
                
                if success and os.path.exists(output_path):
                    # Cache the R visualization
                    cached_path = cache.cache_visualization(
                        viz_type="dual_timeframe",
                        data=dual_df,
                        file_path=output_path,
                        parameters={},
                        simulation_id=simulation_id,
                        format="png",
                        width=12,
                        height=5,
                        dpi=120
                    )
                    
                    # Update the placeholder with R visualization
                    viz_placeholder.image(cached_path)
            except Exception as e:
                logger.error(f"Error in R visualization thread: {e}")
        
        # Start thread to generate R visualization
        r_thread = threading.Thread(target=generate_r_viz)
        r_thread.daemon = True
        r_thread.start()
        
    except Exception as e:
        logger.error(f"Error starting R visualization thread: {e}")
        # Keep the matplotlib visualization