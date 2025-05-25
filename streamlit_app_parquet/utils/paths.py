"""
Path utilities for consistent path resolution across different environments.

This module provides functions to resolve paths correctly whether running
locally from project root or in cloud deployments.
"""

import os
from pathlib import Path
import streamlit as st


def get_project_root() -> Path:
    """
    Get the project root directory.
    
    Returns:
        Path: The project root directory
    """
    # If we're in streamlit_app_parquet/pages/, go up two levels
    current_file = Path(__file__).resolve()
    
    # Check if we're in the streamlit_app_parquet subdirectory
    if "streamlit_app_parquet" in current_file.parts:
        # Find the project root (parent of streamlit_app_parquet)
        for parent in current_file.parents:
            if parent.name == "streamlit_app_parquet":
                return parent.parent
    
    # Otherwise, assume we're running from project root
    return Path.cwd()


def get_streamlit_app_dir() -> Path:
    """
    Get the streamlit app directory.
    
    Returns:
        Path: The streamlit_app_parquet directory
    """
    root = get_project_root()
    app_dir = root / "streamlit_app_parquet"
    
    # If streamlit_app_parquet doesn't exist, we might be inside it already
    if not app_dir.exists() and (root / "app.py").exists():
        return root
    
    return app_dir


def get_output_dir() -> Path:
    """
    Get the output directory for results.
    
    Returns:
        Path: The output directory
    """
    # First try relative to streamlit app
    app_dir = get_streamlit_app_dir()
    output_dir = app_dir / "output"
    
    if output_dir.exists():
        return output_dir
    
    # Otherwise try relative to project root
    root = get_project_root()
    output_dir = root / "output"
    
    if output_dir.exists():
        return output_dir
    
    # Create it if it doesn't exist
    output_dir = app_dir / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def get_parquet_results_dir() -> Path:
    """
    Get the directory containing Parquet results.
    
    Returns:
        Path: The parquet_results directory
    """
    output_dir = get_output_dir()
    parquet_dir = output_dir / "parquet_results"
    
    # Create if it doesn't exist
    parquet_dir.mkdir(parents=True, exist_ok=True)
    
    return parquet_dir


def get_simulation_module_path() -> Path:
    """
    Get the path to the simulation module.
    
    Returns:
        Path: The simulation module directory
    """
    root = get_project_root()
    return root / "simulation"


def get_protocols_path() -> Path:
    """
    Get the path to the protocols directory.
    
    Returns:
        Path: The protocols directory
    """
    root = get_project_root()
    return root / "protocols"


def debug_paths():
    """
    Display debug information about paths.
    
    Useful for troubleshooting path issues in different environments.
    """
    st.write("### Path Debug Information")
    st.write(f"**Current Working Directory:** `{Path.cwd()}`")
    st.write(f"**Project Root:** `{get_project_root()}`")
    st.write(f"**Streamlit App Dir:** `{get_streamlit_app_dir()}`")
    st.write(f"**Output Dir:** `{get_output_dir()}`")
    st.write(f"**Parquet Results Dir:** `{get_parquet_results_dir()}`")
    st.write(f"**Parquet Dir Exists:** {get_parquet_results_dir().exists()}")
    
    parquet_dir = get_parquet_results_dir()
    if parquet_dir.exists():
        files = list(parquet_dir.glob("*.parquet"))
        st.write(f"**Parquet Files Found:** {len(files)}")
        if files:
            st.write("**Sample Files:**")
            for f in files[:5]:
                st.write(f"  - {f.name}")