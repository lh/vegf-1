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
    """Definition of a treatment decision"""
    metric: str
    comparator: str
    value: Any
    action: str
    priority: int = 1

@dataclass
class ProtocolPhase:
    """Base class for protocol phases"""
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
        required_actions=["vision_test", "oct_scan"]
    ))

    def is_complete(self, state: Dict[str, Any]) -> bool:
        """Check if phase completion criteria are met"""
        if self.duration_weeks and state.get("weeks_in_phase", 0) >= self.duration_weeks:
            return True
        if self.required_treatments and state.get("treatments_in_phase", 0) >= self.required_treatments:
            return True
        return False

    def evaluate_criteria(self, state: Dict[str, Any], criteria: List[TreatmentDecision]) -> bool:
        """Evaluate a list of criteria against current state"""
        for criterion in criteria:
            value = state.get(criterion.metric)
            if value is None:
                continue
            if not self._compare_values(value, criterion.comparator, criterion.value):
                return False
        return True

    def _compare_values(self, actual: Any, comparator: str, expected: Any) -> bool:
        """Compare values using specified comparator"""
        if comparator == "==":
            return actual == expected
        elif comparator == ">=":
            return actual >= expected
        elif comparator == "<=":
            return actual <= expected
        elif comparator == ">":
            return actual > expected
        elif comparator == "<":
            return actual < expected
        return False

@dataclass
class LoadingPhase(ProtocolPhase):
    """Loading phase specific implementation"""
    def __post_init__(self):
        self.phase_type = PhaseType.LOADING
        if not self.visit_type:
            self.visit_type = VisitType(
                name="loading",
                required_actions=["vision_test", "oct_scan", "injection"],
                decisions=["nurse_vision_check", "doctor_treatment_decision"]
            )

@dataclass
class MaintenancePhase(ProtocolPhase):
    """Maintenance phase specific implementation"""
    def __post_init__(self):
        self.phase_type = PhaseType.MAINTENANCE
        if not self.visit_type:
            self.visit_type = VisitType(
                name="maintenance",
                required_actions=["vision_test", "oct_scan"],
                optional_actions=["injection"],
                decisions=["nurse_vision_check", "doctor_treatment_decision"]
            )

@dataclass
class TreatmentProtocol:
    """Complete definition of a treatment protocol"""
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
        phase_sequence = list(self.phases.values())
        try:
            current_idx = phase_sequence.index(current_phase)
            if current_idx + 1 < len(phase_sequence):
                return phase_sequence[current_idx + 1]
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
