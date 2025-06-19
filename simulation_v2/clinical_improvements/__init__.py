"""
Clinical Improvements Module for V2 Simulation Engine

This module provides optional clinical improvements that can be enabled
via feature flags. All improvements are designed to run in parallel with
existing functionality without breaking changes.
"""

from .config import ClinicalImprovements
from .patient_wrapper import ImprovedPatientWrapper

__all__ = ['ClinicalImprovements', 'ImprovedPatientWrapper']