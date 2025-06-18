"""Simulation package for modeling ophthalmic treatment protocols.

This package provides an agent-based simulation (ABS) approach for modeling patient 
treatment pathways in ophthalmology, particularly for anti-VEGF therapies.

Modules
-------
base : Base classes for simulation components
abs : Agent-based simulation implementation

Classes
-------
Event : Base class for simulation events
BaseSimulation : Abstract base simulation class
AgentBasedSimulation : ABS implementation
Patient : Core patient entity class

See Also
--------
simulation.config : Configuration management
simulation.clinical_model : Disease progression modeling
"""

from .base import Event, BaseSimulation
from .abs import AgentBasedSimulation, Patient

__all__ = ['Event', 'BaseSimulation', 'AgentBasedSimulation', 'Patient']
