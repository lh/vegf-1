"""Memory management utilities for treatment pattern visualizations.

This module provides decorators and utilities to help manage memory usage
when creating large visualizations with Plotly.
"""

import gc
import functools
from typing import Any, Callable


def with_memory_cleanup(func: Callable) -> Callable:
    """Decorator that performs garbage collection after function execution.
    
    This helps free memory after creating large Plotly figures.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            # Force garbage collection to free memory
            gc.collect()
    
    return wrapper


def clear_plotly_cache():
    """Clear any internal Plotly caches to free memory.
    
    Plotly may cache certain objects internally. This function
    attempts to clear those caches.
    """
    # Force garbage collection
    gc.collect()
    
    # Note: Plotly doesn't expose internal caches directly,
    # but garbage collection helps free unreferenced objects