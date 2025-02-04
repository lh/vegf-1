from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from queue import PriorityQueue

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
    protocol_event: Optional['ProtocolEvent'] = None

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
    
    @abstractmethod
    def process_event(self, event: Event):
        pass
    
    def run(self, until: datetime):
        while True:
            event = self.clock.get_next_event()
            if event is None or event.time > until:
                break
            self.process_event(event)
