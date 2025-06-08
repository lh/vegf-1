"""
Memory monitoring utilities for APE V2.

Provides real-time memory usage tracking and warnings to prevent
out-of-memory errors on resource-constrained environments.
"""

import psutil
import os
import gc
from typing import Dict, Tuple, Optional
import streamlit as st
import sys
from pathlib import Path

# Add parent for imports
sys.path.append(str(Path(__file__).parent.parent.parent))
from utils.environment import is_streamlit_cloud, get_memory_limit_mb


class MemoryMonitor:
    """Monitor and report memory usage."""
    
    def __init__(self):
        """Initialize memory monitor."""
        self.process = psutil.Process(os.getpid())
        
        # Set thresholds based on environment
        if is_streamlit_cloud():
            # Streamlit Cloud thresholds
            self.WARNING_THRESHOLD_MB = 500
            self.CRITICAL_THRESHOLD_MB = 700
            self.LIMIT_MB = 1024
            self.USABLE_MB = 700  # Conservative estimate
        else:
            # Local development - more generous thresholds
            total_mb = get_memory_limit_mb()
            self.WARNING_THRESHOLD_MB = int(total_mb * 0.6)
            self.CRITICAL_THRESHOLD_MB = int(total_mb * 0.8)
            self.LIMIT_MB = total_mb
            self.USABLE_MB = int(total_mb * 0.9)
        
    def get_memory_info(self) -> Dict[str, float]:
        """
        Get current memory usage information.
        
        Returns:
            Dictionary with memory stats in MB:
            - used_mb: Memory used by this process
            - available_mb: System memory available
            - total_mb: Total system memory
            - percent: Percentage of system memory used
        """
        # Process memory
        mem_info = self.process.memory_info()
        used_mb = mem_info.rss / (1024 * 1024)
        
        # System memory
        system_mem = psutil.virtual_memory()
        available_mb = system_mem.available / (1024 * 1024)
        total_mb = system_mem.total / (1024 * 1024)
        
        return {
            'used_mb': used_mb,
            'available_mb': available_mb,
            'total_mb': total_mb,
            'percent': system_mem.percent
        }
        
    def check_memory_status(self) -> Tuple[str, str]:
        """
        Check current memory status and return status level and message.
        
        Returns:
            Tuple of (status, message) where status is 'ok', 'warning', or 'critical'
        """
        info = self.get_memory_info()
        used_mb = info['used_mb']
        
        if used_mb > self.CRITICAL_THRESHOLD_MB:
            return ('critical', f"⛔ Critical: Using {used_mb:.0f}MB of memory!")
        elif used_mb > self.WARNING_THRESHOLD_MB:
            return ('warning', f"⚠️ Warning: Using {used_mb:.0f}MB of memory")
        else:
            return ('ok', f"✅ Memory usage: {used_mb:.0f}MB")
            
    def display_in_sidebar(self):
        """Display memory usage in Streamlit sidebar."""
        info = self.get_memory_info()
        status, message = self.check_memory_status()
        
        with st.sidebar:
            st.markdown("### 💾 Memory Usage")
            
            # Color-coded message
            if status == 'critical':
                st.error(message)
            elif status == 'warning':
                st.warning(message)
            else:
                st.success(message)
                
            # Progress bar
            progress = min(info['used_mb'] / self.USABLE_MB, 1.0)
            st.progress(progress, text=f"{info['used_mb']:.0f} / {self.USABLE_MB:.0f} MB")
            
            # Details in expander
            with st.expander("Details"):
                st.text(f"Process: {info['used_mb']:.1f} MB")
                st.text(f"Available: {info['available_mb']:.1f} MB")
                st.text(f"System: {info['percent']:.1f}% used")
                
    def check_simulation_feasibility(self, n_patients: int, duration_years: float) -> Tuple[bool, Optional[str]]:
        """
        Check if a simulation is feasible within memory constraints.
        
        Args:
            n_patients: Planned number of patients
            duration_years: Planned simulation duration
            
        Returns:
            Tuple of (is_feasible, warning_message)
        """
        info = self.get_memory_info()
        current_mb = info['used_mb']
        
        # Estimate additional memory needed
        from ..results.factory import ResultsFactory
        estimate = ResultsFactory.estimate_memory_usage(n_patients, duration_years)
        total_expected_mb = current_mb + estimate['estimated_memory_mb']
        
        if total_expected_mb > self.CRITICAL_THRESHOLD_MB:
            suggestion = (
                f"⚠️ **Memory Constraint**\n\n"
                f"Current usage: {current_mb:.0f}MB\n"
                f"Estimated need: +{estimate['estimated_memory_mb']:.0f}MB\n"
                f"Total: {total_expected_mb:.0f}MB (exceeds {self.CRITICAL_THRESHOLD_MB}MB limit)\n\n"
                f"**Suggestions:**\n"
                f"• Reduce to {int(n_patients * 0.7):,} patients\n"
                f"• Or reduce to {max(1, int(duration_years * 0.7)):.1f} years\n"
                f"• Data will be efficiently stored using Parquet format"
            )
            return (False, suggestion)
            
        elif total_expected_mb > self.WARNING_THRESHOLD_MB:
            warning = (
                f"💡 **Memory Notice**\n"
                f"Expected usage: ~{total_expected_mb:.0f}MB\n"
                f"Approaching memory limit of {self.USABLE_MB}MB"
            )
            return (True, warning)
            
        return (True, None)
        
    def cleanup_memory(self):
        """
        Perform memory cleanup operations.
        
        This includes:
        - Forcing garbage collection
        - Clearing Streamlit caches if needed
        - Closing matplotlib figures
        """
        # Force garbage collection
        gc.collect()
        
        # Clear matplotlib figures
        try:
            import matplotlib.pyplot as plt
            plt.close('all')
        except ImportError:
            pass
            
        # Log cleanup
        before = self.get_memory_info()['used_mb']
        gc.collect()  # Second pass
        after = self.get_memory_info()['used_mb']
        
        if after < before:
            print(f"🧹 Freed {before - after:.1f}MB of memory")
            

def get_memory_usage() -> float:
    """
    Quick function to get current memory usage in MB.
    
    Returns:
        Memory usage in MB
    """
    return psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024)
    

def monitor_function(func):
    """
    Decorator to monitor memory usage of a function.
    
    Usage:
        @monitor_function
        def my_function():
            # Do something memory intensive
            pass
    """
    def wrapper(*args, **kwargs):
        before_mb = get_memory_usage()
        result = func(*args, **kwargs)
        after_mb = get_memory_usage()
        
        delta_mb = after_mb - before_mb
        if delta_mb > 10:  # Only report significant changes
            print(f"📊 {func.__name__}: Memory Δ = +{delta_mb:.1f}MB "
                  f"(now: {after_mb:.1f}MB)")
        
        return result
    return wrapper