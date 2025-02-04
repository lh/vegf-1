from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from queue import PriorityQueue

@dataclass
class Event:
    time: datetime
    event_type: str
    patient_id: str
    data: Dict[str, Any]
    priority: int = 1

class SimulationClock:
    def __init__(self, start_date: datetime):
        self.current_time = start_date
        self.event_queue = PriorityQueue()
    
    def schedule_event(self, event: Event):
        self.event_queue.put((event.time, event.priority, event))
    
    def get_next_event(self) -> Optional[Event]:
        if self.event_queue.empty():
            return None
        _, _, event = self.event_queue.get()
        self.current_time = event.time
        return event

class BaseSimulation(ABC):
    def __init__(self, start_date: datetime):
        self.clock = SimulationClock(start_date)
        self.metrics: Dict[str, List[Any]] = {}
    
    @abstractmethod
    def process_event(self, event: Event):
        pass
    
    def run(self, until: datetime):
        while True:
            event = self.clock.get_next_event()
            if event is None or event.time > until:
                break
            self.process_event(event)
