"""
Loading Phase Implementation

Implements the initial loading phase where patients receive monthly
injections for the first 3 injections before switching to protocol intervals.
"""

from typing import Optional
from datetime import datetime


class LoadingPhaseManager:
    """
    Manages loading phase logic for patients.
    
    Clinical protocols (VIEW, HAWK/HARRIER) show ~7 injections in Year 1,
    achieved through initial monthly loading followed by protocol intervals.
    """
    
    def __init__(self, loading_injections: int = 3, loading_interval_days: int = 28):
        """
        Initialize loading phase manager.
        
        Args:
            loading_injections: Number of injections in loading phase (default: 3)
            loading_interval_days: Days between loading injections (default: 28)
        """
        self.loading_injections = loading_injections
        self.loading_interval_days = loading_interval_days
    
    def get_interval(self, injection_count: int, protocol_interval: int) -> int:
        """
        Get the injection interval based on current injection count.
        
        Args:
            injection_count: Number of injections already given
            protocol_interval: Normal protocol interval in days
            
        Returns:
            Days until next injection
        """
        if injection_count < self.loading_injections:
            return self.loading_interval_days
        return protocol_interval
    
    def is_in_loading_phase(self, injection_count: int) -> bool:
        """
        Check if patient is still in loading phase.
        
        Args:
            injection_count: Number of injections already given
            
        Returns:
            True if still in loading phase
        """
        return injection_count < self.loading_injections
    
    def get_phase_description(self, injection_count: int) -> str:
        """
        Get a description of current phase.
        
        Args:
            injection_count: Number of injections already given
            
        Returns:
            Description of current treatment phase
        """
        if self.is_in_loading_phase(injection_count):
            return f"Loading phase ({injection_count + 1}/{self.loading_injections})"
        return "Maintenance phase"