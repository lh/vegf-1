from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timedelta
from queue import PriorityQueue
from protocol_models import TreatmentProtocol, ProtocolPhase, PhaseType

@dataclass
class ProtocolEvent:
    """Protocol-specific event data"""
    phase_type: PhaseType
    action: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    result: Optional[Dict[str, Any]] = None

class SimulationEnvironment:
    def __init__(self, start_date: datetime):
        self.current_time = start_date
        self.global_state: Dict[str, Any] = {}

@dataclass
class Event:
    time: datetime
    event_type: str
    patient_id: str 
    data: Dict[str, Any]
    priority: int = 1
    protocol_event: Optional[ProtocolEvent] = None

    @classmethod
    def create_protocol_event(cls, 
                            time: datetime,
                            patient_id: str,
                            phase_type: PhaseType,
                            action: str,
                            data: Dict[str, Any] = None,
                            priority: int = 1) -> 'Event':
        """Create a protocol-specific event"""
        protocol_event = ProtocolEvent(
            phase_type=phase_type,
            action=action,
            parameters=data or {}
        )
        return cls(
            time=time,
            event_type=f"protocol_{action}",
            patient_id=patient_id,
            data=data or {},
            priority=priority,
            protocol_event=protocol_event
        )

class SimulationClock:
    def __init__(self, start_date: datetime):
        self.current_time = start_date
        self.event_queue = PriorityQueue()
        self._counter = 0  # Add a counter for tie-breaking
    
    def schedule_event(self, event: Event):
        # Create a comparable tuple with (time, priority, counter) as the sort key
        # The counter ensures FIFO behavior for events with same time/priority
        self._counter += 1
        self.event_queue.put((event.time, event.priority, self._counter, event))
    
    def get_next_event(self) -> Optional[Event]:
        if self.event_queue.empty():
            return None
        time, _, _, event = self.event_queue.get()
        self.current_time = time
        return event

class BaseSimulation(ABC):
    def __init__(self, start_date: datetime, environment: Optional[SimulationEnvironment] = None):
        self.clock = SimulationClock(start_date)
        self.metrics: Dict[str, List[Any]] = {}
        self.environment = environment or SimulationEnvironment(start_date)
        self.protocols: Dict[str, TreatmentProtocol] = {}
    
    @abstractmethod
    def process_event(self, event: Event):
        """Process a simulation event"""
        pass
    
    def run(self, until: datetime):
        """Run simulation until specified datetime"""
        while True:
            event = self.clock.get_next_event()
            if event is None or event.time > until:
                break
            self.process_event(event)
            
    def register_protocol(self, protocol_type: str, protocol: TreatmentProtocol):
        """Register a protocol for use in the simulation"""
        self.protocols[protocol_type] = protocol
        
    def get_protocol(self, protocol_type: str) -> Optional[TreatmentProtocol]:
        """Get a registered protocol by type"""
        return self.protocols.get(protocol_type)
        
    def schedule_protocol_event(self, 
                              time: datetime,
                              patient_id: str,
                              phase_type: PhaseType,
                              action: str,
                              data: Dict[str, Any] = None,
                              priority: int = 1):
        """Schedule a protocol-specific event"""
        event = Event.create_protocol_event(
            time=time,
            patient_id=patient_id,
            phase_type=phase_type,
            action=action,
            data=data,
            priority=priority
        )
        self.clock.schedule_event(event)
