from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from enum import Enum, auto

class PhaseType(Enum):
    """Types of protocol phases"""
    LOADING = auto()
    MAINTENANCE = auto()
    EXTENSION = auto()
    DISCONTINUATION = auto()

@dataclass
class ProtocolPhase:
    """A phase within a treatment protocol"""
    phase_type: PhaseType
    duration_weeks: Optional[int]
    visit_interval_weeks: int
    required_treatments: Optional[int] = None
    min_interval_weeks: Optional[int] = None
    max_interval_weeks: Optional[int] = None
    interval_adjustment_weeks: Optional[int] = None
    entry_criteria: List[Dict] = field(default_factory=list)
    exit_criteria: List[Dict] = field(default_factory=list)
    extension_criteria: List[Dict] = field(default_factory=list)
    reduction_criteria: List[Dict] = field(default_factory=list)

@dataclass
class TreatmentProtocol:
    """Complete definition of a treatment protocol"""
    agent: str
    protocol_name: str
    version: str
    description: str
    phases: Dict[str, ProtocolPhase]
    discontinuation_criteria: List[Dict] = field(default_factory=list)
    
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
