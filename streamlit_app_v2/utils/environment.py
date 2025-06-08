"""
Environment detection utilities for APE V2.

Detects whether the app is running locally or on Streamlit Cloud
to adjust behavior accordingly.
"""

import os
import streamlit as st


def is_streamlit_cloud() -> bool:
    """
    Detect if the app is running on Streamlit Cloud.
    
    Returns:
        True if running on Streamlit Cloud, False otherwise
    """
    # Streamlit Cloud sets specific environment variables
    # Check multiple indicators to be sure
    indicators = [
        # Streamlit Cloud specific
        os.environ.get('STREAMLIT_SHARING_MODE') == 'true',
        os.environ.get('STREAMLIT_RUNTIME_ENV') == 'cloud',
        # Common cloud indicators
        'streamlit.io' in os.environ.get('STREAMLIT_SERVER_ADDRESS', ''),
        # Streamlit Cloud uses specific paths
        '/mount/src' in os.getcwd(),
        # Additional check for Streamlit Community Cloud
        os.environ.get('STREAMLIT_COMMUNITY_CLOUD') == 'true'
    ]
    
    return any(indicators)


def get_environment_info() -> dict:
    """
    Get detailed environment information.
    
    Returns:
        Dictionary with environment details
    """
    return {
        'is_cloud': is_streamlit_cloud(),
        'platform': os.name,
        'cwd': os.getcwd(),
        'streamlit_version': st.__version__,
        'memory_limit_mb': 1024 if is_streamlit_cloud() else None,
        'env_vars': {
            'STREAMLIT_SHARING_MODE': os.environ.get('STREAMLIT_SHARING_MODE'),
            'STREAMLIT_RUNTIME_ENV': os.environ.get('STREAMLIT_RUNTIME_ENV'),
            'STREAMLIT_SERVER_ADDRESS': os.environ.get('STREAMLIT_SERVER_ADDRESS'),
            'STREAMLIT_COMMUNITY_CLOUD': os.environ.get('STREAMLIT_COMMUNITY_CLOUD')
        }
    }


def should_check_memory_limits() -> bool:
    """
    Determine if memory limit checking should be enabled by default.
    
    Returns:
        True if on Streamlit Cloud, False for local development
    """
    return is_streamlit_cloud()


def get_memory_limit_mb() -> int:
    """
    Get the memory limit for the current environment.
    
    Returns:
        Memory limit in MB (1024 for Streamlit Cloud, 8192 for local as a reasonable default)
    """
    if is_streamlit_cloud():
        return 1024  # Streamlit Cloud free tier limit
    else:
        # For local development, use a higher limit or system memory
        import psutil
        system_memory_mb = psutil.virtual_memory().total / (1024 * 1024)
        # Use 80% of system memory as a reasonable limit
        return int(system_memory_mb * 0.8)