"""Simulation package for modeling ophthalmic treatment protocols.

This package provides implementations of both discrete event simulation (DES) and
agent-based simulation (ABS) approaches for modeling patient treatment pathways
in ophthalmology, particularly for anti-VEGF therapies.

Modules
-------
base : Base classes for simulation components
des : Discrete event simulation implementation
abs : Agent-based simulation implementation

Classes
-------
Event : Base class for simulation events
BaseSimulation : Abstract base simulation class
DiscreteEventSimulation : DES implementation
AgentBasedSimulation : ABS implementation
Patient : Core patient entity class

See Also
--------
simulation.config : Configuration management
simulation.clinical_model : Disease progression modeling
"""

from .base import Event, BaseSimulation
from .des import DiscreteEventSimulation
from .abs import AgentBasedSimulation, Patient

__all__ = ['Event', 'BaseSimulation', 'DiscreteEventSimulation', 'AgentBasedSimulation', 'Patient']
