#!/usr/bin/env python3
"""
Fixed interval protocol for VIEW 2q8 simulation.
"""

from datetime import datetime, timedelta
from simulation_v2.core.protocol import Protocol
from simulation_v2.core.patient import Patient


class FixedIntervalProtocol(Protocol):
    """
    Fixed interval protocol that treats on a regular schedule regardless of disease state.
    
    Used for VIEW 2q8: 3 monthly loading doses, then every 8 weeks.
    """
    
    def __init__(self, loading_doses: int = 3, loading_interval_days: int = 28,
                 maintenance_interval_days: int = 56):
        """
        Initialize fixed interval protocol.
        
        Args:
            loading_doses: Number of initial monthly doses
            loading_interval_days: Days between loading doses (default 28)
            maintenance_interval_days: Days between maintenance doses (default 56)
        """
        self.loading_doses = loading_doses
        self.loading_interval_days = loading_interval_days
        self.maintenance_interval_days = maintenance_interval_days
        
    def should_treat(self, patient: Patient, current_date: datetime) -> bool:
        """
        Always treat at scheduled visits (unless discontinued).
        
        In fixed protocols, we treat regardless of disease state.
        """
        if patient.is_discontinued:
            return False
            
        # Always treat at scheduled visits
        return True
        
    def next_visit_date(self, patient: Patient, current_date: datetime, treated: bool) -> datetime:
        """
        Calculate next visit based on fixed schedule.
        
        - First N visits: loading phase at monthly intervals
        - After loading: fixed maintenance interval
        """
        visit_count = len(patient.visit_history)
        
        if visit_count < self.loading_doses:
            # Still in loading phase
            return current_date + timedelta(days=self.loading_interval_days)
        else:
            # Maintenance phase
            return current_date + timedelta(days=self.maintenance_interval_days)