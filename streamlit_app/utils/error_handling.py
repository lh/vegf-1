"""
Error handling utilities for the APE Streamlit application.

This module provides standardized error handling and display components
for the application, with different detail levels for regular mode vs. debug mode.
"""

import traceback
import sys
import logging
from typing import Optional, Dict, Any, Callable, TypeVar, Union
import streamlit as st

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Type variables for generic function wrappers
T = TypeVar('T')
R = TypeVar('R')

class AppError(Exception):
    """Base exception class for application errors."""
    
    def __init__(self, message: str, details: Optional[str] = None, error_code: Optional[str] = None):
        """Initialize AppError.
        
        Parameters
        ----------
        message : str
            User-friendly error message
        details : str, optional
            Detailed error information, by default None
        error_code : str, optional
            Error code for tracking/categorization, by default None
        """
        self.message = message
        self.details = details
        self.error_code = error_code
        super().__init__(message)


class SimulationError(AppError):
    """Exception class for simulation-related errors."""
    
    def __init__(
        self, 
        message: str, 
        details: Optional[str] = None, 
        error_code: Optional[str] = None,
        simulation_params: Optional[Dict[str, Any]] = None
    ):
        """Initialize SimulationError.
        
        Parameters
        ----------
        message : str
            User-friendly error message
        details : str, optional
            Detailed error information, by default None
        error_code : str, optional
            Error code for tracking/categorization, by default None
        simulation_params : Dict[str, Any], optional
            Simulation parameters that caused the error, by default None
        """
        self.simulation_params = simulation_params
        super().__init__(message, details, error_code)


class VisualizationError(AppError):
    """Exception class for visualization-related errors."""
    
    def __init__(
        self, 
        message: str, 
        details: Optional[str] = None, 
        error_code: Optional[str] = None,
        viz_type: Optional[str] = None
    ):
        """Initialize VisualizationError.
        
        Parameters
        ----------
        message : str
            User-friendly error message
        details : str, optional
            Detailed error information, by default None
        error_code : str, optional
            Error code for tracking/categorization, by default None
        viz_type : str, optional
            Type of visualization that caused the error, by default None
        """
        self.viz_type = viz_type
        super().__init__(message, details, error_code)


def display_error(
    error: Union[Exception, str],
    title: str = "An error occurred",
    debug_mode: bool = False
) -> None:
    """Display an error message in the Streamlit UI.
    
    Parameters
    ----------
    error : Union[Exception, str]
        The error to display
    title : str, optional
        Title for the error message, by default "An error occurred"
    debug_mode : bool, optional
        Whether to show detailed error information, by default False
    """
    # Convert string errors to exceptions
    if isinstance(error, str):
        error = AppError(error)
    
    # Get error details
    error_type = type(error).__name__
    error_message = str(error)
    
    # Get detailed error information if available
    details = getattr(error, 'details', None)
    if details is None:
        details = ''.join(traceback.format_exception(type(error), error, error.__traceback__))
    
    # Log the error
    logger.error(f"{error_type}: {error_message}")
    if debug_mode:
        logger.error(f"Details: {details}")
    
    # Display the error
    st.error(f"**{title}**")
    
    # Show different levels of detail based on debug mode
    if debug_mode:
        with st.expander("Error Details", expanded=True):
            st.write(f"**Error Type:** {error_type}")
            st.write(f"**Error Message:** {error_message}")
            
            # Show additional info for specific error types
            if isinstance(error, SimulationError) and error.simulation_params:
                st.write("**Simulation Parameters:**")
                st.json(error.simulation_params)
            
            if isinstance(error, VisualizationError) and error.viz_type:
                st.write(f"**Visualization Type:** {error.viz_type}")
            
            # Show full traceback
            st.code(details)
    else:
        # Simplified view for non-debug mode
        st.write(error_message)
        
        # Show troubleshooting suggestions
        if isinstance(error, SimulationError):
            st.info("""
            **Troubleshooting suggestions:**
            - Try reducing the population size
            - Try a different simulation type (ABS or DES)
            - Check that all required fields are filled in correctly
            - Try enabling debug mode for more detailed error information
            """)
        elif isinstance(error, VisualizationError):
            st.info("""
            **Troubleshooting suggestions:**
            - Check that simulation results are valid
            - Try running the simulation again
            - Try enabling debug mode for more detailed error information
            """)


def wrap_function_with_error_handling(
    func: Callable[..., R],
    error_title: str = "An error occurred",
    fallback_value: Optional[R] = None
) -> Callable[..., Optional[R]]:
    """Wrap a function with standardized error handling.
    
    Parameters
    ----------
    func : Callable
        The function to wrap
    error_title : str, optional
        Title for the error message, by default "An error occurred"
    fallback_value : Any, optional
        Value to return if an error occurs, by default None
    
    Returns
    -------
    Callable
        Wrapped function with error handling
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # Get debug mode status
            debug_mode = st.session_state.get("debug_mode_toggle", False)
            
            # Display the error
            display_error(e, title=error_title, debug_mode=debug_mode)
            
            # Return fallback value
            return fallback_value
    
    return wrapper