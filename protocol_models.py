from dataclasses import dataclass, field
from typing import List, Dict, Optional

@dataclass
class ProtocolStep:
    step_type: str
    parameters: Dict
    next_step: Optional[str] = None
    conditions: List[Dict] = field(default_factory=list)
    exit_criteria: List[Dict] = field(default_factory=list)
    reassess_interval: Optional[int] = None

@dataclass
class TreatmentProtocol:
    agent: str
    protocol_name: str
    steps: List[Dict]  # Changed from Dict[str, ProtocolStep]
