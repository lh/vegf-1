from dataclasses import dataclass
from typing import List, Dict, Optional

@dataclass
class ProtocolStep:
    step_type: str
    parameters: Dict
    conditions: List[Dict]
    next_step: Optional[str]
    exit_criteria: List[Dict]
    reassess_interval: Optional[int]

@dataclass
class TreatmentProtocol:
    agent: str
    protocol_name: str
    steps: Dict[str, ProtocolStep]
