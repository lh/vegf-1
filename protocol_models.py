"""Core models for defining and managing ophthalmic treatment protocols.

This module provides classes for modeling complete treatment protocols including
phases, visit types, clinical actions, and decision criteria. It forms the foundation
for protocol-driven clinical simulations and analysis.

Key Features
------------
- Phase-based protocol modeling (loading, maintenance, extension, discontinuation)
- Configurable visit types with required/optional actions
- Decision criteria with evaluation logic
- Protocol validation and phase transition management
- State processing for each protocol phase

Classes Overview
---------------
PhaseType : Enum of protocol phase types
ActionType : Enum of clinical actions (tests, scans, treatments)
DecisionType : Enum of clinical decision points
VisitType : Definition of a visit's structure and requirements
TreatmentDecision : Criteria for treatment decisions
ProtocolPhase : Abstract base class for protocol phases
TreatmentProtocol : Complete protocol definition and management

Examples
--------
>>> from protocol_models import *
>>> loading = LoadingPhase(
...     duration_weeks=12,
...     visit_interval_weeks=4,
...     required_treatments=3
... )
>>> protocol = TreatmentProtocol(
...     agent="Aflibercept",
...     protocol_name="Standard AMD Protocol",
...     version="1.0",
...     phases={"loading": loading},
...     parameters={}
... )

Notes
-----
- All time values are in weeks
- Phase transitions are validated against sequence rules
- Decision criteria support complex evaluation logic
- State dictionaries track patient progress through protocol
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Union, Type
from datetime import datetime, timedelta
from enum import Enum, auto
from abc import ABC, abstractmethod

class PhaseType(Enum):
    """Types of protocol phases"""
    LOADING = auto()
    MAINTENANCE = auto()
    EXTENSION = auto()
    DISCONTINUATION = auto()

class ActionType(Enum):
    """Types of clinical actions"""
    VISION_TEST = "vision_test"
    OCT_SCAN = "oct_scan" 
    INJECTION = "injection"
    CONSULTATION = "consultation"

class DecisionType(Enum):
    """Types of clinical decisions"""
    NURSE_CHECK = "nurse_vision_check"
    DOCTOR_REVIEW = "doctor_treatment_decision"
    OCT_REVIEW = "doctor_oct_review"

@dataclass
class VisitType:
    """Definition of a visit type"""
    name: str
    required_actions: List[ActionType]
    optional_actions: List[ActionType] = field(default_factory=list)
    decisions: List[DecisionType] = field(default_factory=list)
    duration_minutes: int = 30

    def validate(self) -> bool:
        """Validate visit type configuration"""
        if not self.name or not self.required_actions:
            return False
        return True

@dataclass
class TreatmentDecision:
    """Definition of a treatment decision with validation"""
    metric: str  # The metric to evaluate (e.g., 'vision', 'oct_thickness')
    comparator: str  # Comparison operator ('==', '>=', '<=', '>', '<')
    value: Any  # Target value or reference (e.g., 'baseline', 15, 'stable')
    action: str  # Action to take ('continue', 'extend', 'reduce', 'stop')
    priority: int = 1  # Priority level for multiple decisions
    
    def evaluate(self, value: Any) -> bool:
        """Evaluate decision against a value"""
        if self.value == "baseline":
            # Handle baseline comparisons differently
            return True  # Placeholder - implement baseline logic
        
        if self.comparator == "==":
            return value == self.value
        elif self.comparator == ">=":
            return value >= self.value
        elif self.comparator == "<=":
            return value <= self.value
        elif self.comparator == ">":
            return value > self.value
        elif self.comparator == "<":
            return value < self.value
        return False

@dataclass
class ProtocolPhase(ABC):
    """Abstract base class for protocol phases"""
    phase_type: PhaseType
    duration_weeks: Optional[int]
    visit_interval_weeks: int
    required_treatments: Optional[int] = None
    min_interval_weeks: Optional[int] = None
    max_interval_weeks: Optional[int] = None
    interval_adjustment_weeks: Optional[int] = None
    entry_criteria: List[TreatmentDecision] = field(default_factory=list)
    exit_criteria: List[TreatmentDecision] = field(default_factory=list)
    visit_type: VisitType = field(default_factory=lambda: VisitType(
        name="standard",
        required_actions=[ActionType.VISION_TEST, ActionType.OCT_SCAN]
    ))

    @abstractmethod
    def process_visit(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process a visit in this phase and return updated state"""
        pass

    @abstractmethod
    def is_complete(self, state: Dict[str, Any]) -> bool:
        """Check if phase completion criteria are met"""
        pass

    def evaluate_criteria(self, state: Dict[str, Any], criteria: List[TreatmentDecision]) -> bool:
        """Evaluate a list of criteria against current state"""
        for criterion in criteria:
            value = state.get(criterion.metric)
            if value is None:
                continue
            if not criterion.evaluate(value):
                return False
        return True

    def can_enter(self, state: Dict[str, Any]) -> bool:
        """Check if phase entry criteria are met"""
        return self.evaluate_criteria(state, self.entry_criteria)

    def should_exit(self, state: Dict[str, Any]) -> bool:
        """Check if phase exit criteria are met"""
        return self.evaluate_criteria(state, self.exit_criteria)

@dataclass
class LoadingPhase(ProtocolPhase):
    """Loading phase specific implementation"""
    def __post_init__(self):
        self.phase_type = PhaseType.LOADING
        if not self.visit_type:
            self.visit_type = VisitType(
                name="loading",
                required_actions=[ActionType.VISION_TEST, ActionType.OCT_SCAN, ActionType.INJECTION],
                decisions=[DecisionType.NURSE_CHECK, DecisionType.DOCTOR_REVIEW]
            )

    def process_visit(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process loading phase visit"""
        treatments = state.get("treatments_in_phase", 0)
        state["treatments_in_phase"] = treatments + 1
        
        # Always schedule next loading dose at fixed interval
        state["next_visit_weeks"] = self.visit_interval_weeks
        
        # Check if loading phase complete
        if self.is_complete(state):
            state["phase_complete"] = True
            
        return state

    def is_complete(self, state: Dict[str, Any]) -> bool:
        """Check if loading phase complete (3 injections given)"""
        required = self.required_treatments if self.required_treatments else 3
        return state.get("treatments_in_phase", 0) >= required

@dataclass
class MaintenancePhase(ProtocolPhase):
    """Maintenance phase specific implementation"""
    def __post_init__(self):
        self.phase_type = PhaseType.MAINTENANCE
        if not self.visit_type:
            self.visit_type = VisitType(
                name="maintenance",
                required_actions=[ActionType.VISION_TEST, ActionType.OCT_SCAN],
                optional_actions=[ActionType.INJECTION],
                decisions=[DecisionType.NURSE_CHECK, DecisionType.DOCTOR_REVIEW]
            )

    def process_visit(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process maintenance phase visit"""
        current_interval = state.get("current_interval", self.visit_interval_weeks)
        disease_active = state.get("disease_activity") == "active"
        
        # Adjust interval based on disease activity
        if disease_active:
            new_interval = max(
                self.min_interval_weeks,
                current_interval - 2 * self.interval_adjustment_weeks  # Double reduction when active
            )
        else:
            new_interval = min(
                self.max_interval_weeks,
                current_interval + self.interval_adjustment_weeks
            )
            
        state["current_interval"] = new_interval
        state["next_visit_weeks"] = new_interval
        
        return state

    def is_complete(self, state: Dict[str, Any]) -> bool:
        """Maintenance phase continues until exit criteria are met"""
        return self.evaluate_criteria(state, self.exit_criteria)

@dataclass
class ExtensionPhase(ProtocolPhase):
    """Extension phase specific implementation"""
    def __post_init__(self):
        self.phase_type = PhaseType.EXTENSION
        if not self.visit_type:
            self.visit_type = VisitType(
                name="extension",
                required_actions=[ActionType.VISION_TEST, ActionType.OCT_SCAN],
                optional_actions=[ActionType.INJECTION],
                decisions=[DecisionType.NURSE_CHECK, DecisionType.DOCTOR_REVIEW]
            )

    def process_visit(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process extension phase visit"""
        current_interval = state.get("current_interval", self.visit_interval_weeks)
        disease_active = state.get("disease_activity") == "active"
        
        # More conservative interval adjustments in extension phase
        if disease_active:
            # Return to maintenance phase on disease activity
            state["phase_complete"] = True
            state["next_phase"] = "maintenance"
            new_interval = max(
                self.min_interval_weeks,
                current_interval - 3 * self.interval_adjustment_weeks  # Triple reduction for aggressive response
            )
        else:
            # Slower extension in this phase
            new_interval = min(
                self.max_interval_weeks,
                current_interval + self.interval_adjustment_weeks // 2  # Half increase
            )
            
        state["current_interval"] = new_interval
        state["next_visit_weeks"] = new_interval
        
        return state

    def is_complete(self, state: Dict[str, Any]) -> bool:
        """Extension phase completes when returning to maintenance"""
        return state.get("phase_complete", False)

@dataclass
class DiscontinuationPhase(ProtocolPhase):
    """Discontinuation phase specific implementation"""
    def __post_init__(self):
        self.phase_type = PhaseType.DISCONTINUATION
        if not self.visit_type:
            self.visit_type = VisitType(
                name="discontinuation",
                required_actions=[ActionType.VISION_TEST, ActionType.OCT_SCAN],
                decisions=[DecisionType.NURSE_CHECK, DecisionType.DOCTOR_REVIEW]
            )

    def process_visit(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process discontinuation phase visit"""
        # Always schedule follow-up at fixed interval
        state["next_visit_weeks"] = self.visit_interval_weeks
        
        # Check if monitoring should continue
        if self.is_complete(state):
            state["protocol_complete"] = True
            
        return state

    def is_complete(self, state: Dict[str, Any]) -> bool:
        """Discontinuation phase completes when protocol discontinuation criteria met"""
        return self.evaluate_criteria(state, self.exit_criteria)

@dataclass
class TreatmentProtocol:
    """Complete definition of a treatment protocol with phase management"""
    agent: str
    protocol_name: str
    version: str
    description: str
    phases: Dict[str, ProtocolPhase]
    parameters: Dict[str, Any]
    discontinuation_criteria: List[TreatmentDecision] = field(default_factory=list)
    
    def get_initial_phase(self) -> Optional[ProtocolPhase]:
        """Get the initial protocol phase (usually loading)"""
        for phase in self.phases.values():
            if phase.phase_type == PhaseType.LOADING:
                return phase
        return next(iter(self.phases.values()), None)
    
    def get_next_phase(self, current_phase: ProtocolPhase) -> Optional[ProtocolPhase]:
        """Get the next phase in the protocol sequence"""
        # Define standard phase sequence
        phase_sequence = [
            PhaseType.LOADING,
            PhaseType.MAINTENANCE,
            PhaseType.EXTENSION,
            PhaseType.DISCONTINUATION
        ]
        
        try:
            current_idx = phase_sequence.index(current_phase.phase_type)
            # Look for next phase in sequence
            for next_type in phase_sequence[current_idx + 1:]:
                for phase in self.phases.values():
                    if phase.phase_type == next_type:
                        return phase
        except ValueError:
            pass
        return None

    def should_discontinue(self, state: Dict[str, Any]) -> bool:
        """Check if discontinuation criteria are met"""
        for criterion in self.discontinuation_criteria:
            if criterion.action == "stop":
                if self._evaluate_criterion(state, criterion):
                    return True
        return False

    def _evaluate_criterion(self, state: Dict[str, Any], criterion: TreatmentDecision) -> bool:
        """Evaluate a single criterion"""
        value = state.get(criterion.metric)
        if value is None:
            return False
        return criterion.evaluate(value)
        
    def validate(self) -> bool:
        """Validate protocol configuration"""
        # Check required phases
        if not any(p.phase_type == PhaseType.LOADING for p in self.phases.values()):
            return False
            
        # Validate phase sequence
        current = self.get_initial_phase()
        while current:
            if not current.visit_type.validate():
                return False
            current = self.get_next_phase(current)
            
        return True
        
    def validate_phase_transition(self, current_phase: ProtocolPhase, 
                                next_phase: ProtocolPhase,
                                state: Dict[str, Any]) -> bool:
        """Validate if transition between phases is allowed"""
        # Check phase sequence
        phase_sequence = [
            PhaseType.LOADING,
            PhaseType.MAINTENANCE,
            PhaseType.EXTENSION,
            PhaseType.DISCONTINUATION
        ]
        try:
            current_idx = phase_sequence.index(current_phase.phase_type)
            next_idx = phase_sequence.index(next_phase.phase_type)
            if next_idx <= current_idx:
                return False  # Can't go backwards in sequence
        except ValueError:
            return False
            
        # Check completion criteria
        if not current_phase.is_complete(state):
            return False
            
        # Check entry criteria for next phase
        if not next_phase.can_enter(state):
            return False
            
        return True

    def process_phase_transition(self, current_phase: ProtocolPhase, 
                               state: Dict[str, Any]) -> Optional[ProtocolPhase]:
        """Handle transition between protocol phases"""
        # Get next phase
        next_phase = self.get_next_phase(current_phase)
        if not next_phase:
            return None
            
        # Validate transition
        if not self.validate_phase_transition(current_phase, next_phase, state):
            return None
            
        # Initialize next phase state
        state["phase_complete"] = False
        state["treatments_in_phase"] = 0
        state["weeks_in_phase"] = 0
        
        return next_phase
