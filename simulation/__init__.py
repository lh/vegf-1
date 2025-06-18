"""
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
WARNING: DEPRECATED - DO NOT USE FOR NEW DEVELOPMENT

This module is part of the OLD simulation framework (v1).
APE uses simulation_v2 exclusively.

For new development, use:
  - simulation_v2/ for all simulation engines
  - ape/ for APE-specific components

This code is retained for:
  - Historical reference
  - Understanding legacy implementations
  
Last used: Pre-2024
Replaced by: simulation_v2/
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

DEPRECATED: Legacy simulation package - DO NOT USE

This entire package has been superseded by simulation_v2.
See simulation_v2/README.md for current implementation.

Original description:
Simulation package for modeling ophthalmic treatment protocols.
Provided implementations of both discrete event simulation (DES) and
agent-based simulation (ABS) approaches for modeling patient treatment pathways
in ophthalmology, particularly for anti-VEGF therapies.
"""

import warnings

# Emit deprecation warning on import
warnings.warn(
    "\n" + "="*70 + "\n"
    "DEPRECATION WARNING: You are importing from the old simulation framework.\n"
    "This package (simulation/) is deprecated and should not be used.\n\n"
    "Use simulation_v2/ instead for all new development.\n"
    "APE exclusively uses simulation_v2.\n"
    + "="*70 + "\n",
    DeprecationWarning,
    stacklevel=2
)

from .base import Event, BaseSimulation
from .des import DiscreteEventSimulation
from .abs import AgentBasedSimulation, Patient

__all__ = ['Event', 'BaseSimulation', 'DiscreteEventSimulation', 'AgentBasedSimulation', 'Patient']
