"""Base classes and components for discrete event simulation.

This module provides the fundamental building blocks for discrete event simulation,
including event management, simulation clock, and protocol handling. It defines
the base classes that specific simulation implementations will extend.

Notes
-----
Key components:
- Event: Represents discrete simulation events with timing and data
- SimulationClock: Manages event scheduling and time progression  
- BaseSimulation: Abstract base class for all simulation implementations
- ProtocolEvent: Protocol-specific event data structure
- SimulationEnvironment: Global simulation state container
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timedelta
from queue import PriorityQueue
from protocol_models import (
    TreatmentProtocol, ProtocolPhase, PhaseType,
    VisitType, ActionType, DecisionType
)

@dataclass
class ProtocolEvent:
    """Protocol-specific event data.

    Represents an event that is specific to a treatment protocol, containing
    information about the phase, action, and associated parameters.

    Parameters
    ----------
    phase_type : PhaseType
        Type of protocol phase this event belongs to (e.g., INITIAL, MAINTENANCE)
    action : str
        Action to be performed (e.g., 'inject', 'assess', 'adjust_interval')
    parameters : Dict[str, Any], optional
        Additional parameters for the action (default: {})
    result : Optional[Dict[str, Any]], optional
        Results from executing the action (default: None)

    Examples
    --------
    >>> event = ProtocolEvent(
    ...     phase_type=PhaseType.MAINTENANCE,
    ...     action='inject',
    ...     parameters={'drug': 'eylea', 'dose': 2.0}
    ... )
    """
    phase_type: PhaseType
    action: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    result: Optional[Dict[str, Any]] = None

class SimulationEnvironment:
    """Global simulation environment.

    Maintains global state and timing information for the simulation.

    Parameters
    ----------
    start_date : datetime
        Start date and time for the simulation

    Attributes
    ----------
    current_time : datetime
        Current simulation time
    global_state : Dict[str, Any]
        Dictionary storing global simulation state including:
        - resource_availability: Dict of resource counts
        - queue_lengths: Dict of patient queue lengths
        - statistics: Aggregated simulation metrics

    Notes
    -----
    The environment provides shared state across all simulation components
    and patients. It should be used for system-wide properties rather than
    patient-specific state.
    """
    def __init__(self, start_date: datetime):
        self.current_time = start_date
        self.global_state: Dict[str, Any] = {}

@dataclass
class Event:
    """Simulation event.

    Represents a discrete event in the simulation with timing, type, and associated data.

    Parameters
    ----------
    time : datetime
        When the event occurs
    event_type : str
        Type of event (e.g., 'arrival', 'treatment', 'assessment')
    patient_id : str
        ID of the patient this event relates to
    data : Dict[str, Any], optional
        Additional event data (default: {})
    priority : int, optional
        Event priority (lower numbers = higher priority) (default: 1)
    protocol_event : Optional[ProtocolEvent], optional
        Associated protocol-specific event data (default: None)
    phase : Optional[ProtocolPhase], optional
        Treatment phase this event belongs to (default: None)
    protocol : Optional[TreatmentProtocol], optional
        Treatment protocol this event belongs to (default: None)

    Attributes
    ----------
    _hash : int
        Internal hash value for event comparison

    Notes
    -----
    Events are comparable and hashable based on their time, type, and patient_id.
    This enables proper ordering in priority queues and event lists.

    Examples
    --------
    >>> event = Event(
    ...     time=datetime(2023, 1, 1),
    ...     event_type='treatment',
    ...     patient_id='pat123',
    ...     data={'drug': 'eylea', 'dose': 2.0}
    ... )
    """
    time: datetime
    event_type: str
    patient_id: str 
    data: Dict[str, Any] = field(default_factory=dict)
    priority: int = 1
    protocol_event: Optional[ProtocolEvent] = None
    phase: Optional[ProtocolPhase] = None
    protocol: Optional[TreatmentProtocol] = None
    _hash: int = field(init=False, repr=False)

    def __post_init__(self):
        self._hash = hash((self.time, self.event_type, self.patient_id))

    def __hash__(self):
        return self._hash

    def __eq__(self, other):
        if not isinstance(other, Event):
            return NotImplemented
        return (self.time, self.event_type, self.patient_id) == (other.time, other.event_type, other.patient_id)

    @classmethod
    def create_protocol_event(cls, 
                            time: datetime,
                            patient_id: str,
                            phase_type: PhaseType,
                            action: str,
                            data: Dict[str, Any] = None,
                            priority: int = 1,
                            phase: Optional[ProtocolPhase] = None,
                            protocol: Optional[TreatmentProtocol] = None) -> 'Event':
        """
        Create a protocol-specific event with phase and protocol context.

        Parameters
        ----------
        time : datetime
            When the event occurs
        patient_id : str
            ID of the patient
        phase_type : PhaseType
            Type of protocol phase
        action : str
            Action to be performed
        data : Dict[str, Any], optional
            Additional event data
        priority : int, optional
            Event priority
        phase : Optional[ProtocolPhase], optional
            Treatment phase
        protocol : Optional[TreatmentProtocol], optional
            Treatment protocol

        Returns
        -------
        Event
            New protocol event
        """
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
            protocol_event=protocol_event,
            phase=phase,
            protocol=protocol
        )

    def get_visit_type(self) -> Optional[VisitType]:
        """
        Get visit type from phase if available.

        Returns
        -------
        Optional[VisitType]
            Visit type if phase is set, None otherwise
        """
        if self.phase:
            return self.phase.visit_type
        return None

    def get_required_actions(self) -> List[ActionType]:
        """
        Get required actions from visit type.

        Returns
        -------
        List[ActionType]
            List of required actions for this visit type
        """
        visit_type = self.get_visit_type()
        if visit_type:
            return visit_type.required_actions
        return []

    def get_optional_actions(self) -> List[ActionType]:
        """
        Get optional actions from visit type.

        Returns
        -------
        List[ActionType]
            List of optional actions for this visit type
        """
        visit_type = self.get_visit_type()
        if visit_type:
            return visit_type.optional_actions
        return []

    def get_decisions(self) -> List[DecisionType]:
        """
        Get decisions from visit type.

        Returns
        -------
        List[DecisionType]
            List of decisions required for this visit type
        """
        visit_type = self.get_visit_type()
        if visit_type:
            return visit_type.decisions
        return []

class SimulationClock:
    """
    Manages simulation time and event scheduling.

    Maintains ordered list of events and handles event scheduling with proper
    temporal ordering and priority handling.

    Parameters
    ----------
    start_date : datetime
        Start date and time for the simulation

    Attributes
    ----------
    current_time : datetime
        Current simulation time
    end_date : Optional[datetime]
        End date for the simulation
    event_list : List
        Ordered list of pending events
    _counter : int
        Counter for tie-breaking event ordering
    """
    def __init__(self, start_date: datetime):
        self.current_time = start_date
        self.end_date = None  # Will be set when simulation runs
        self.event_list = []
        self._counter = 0  # Add a counter for tie-breaking
    
    def schedule_event(self, event: Event):
        """
        Schedule an event with proper ordering by time and priority.

        Parameters
        ----------
        event : Event
            Event to schedule

        Notes
        -----
        Events are ordered by:
        1. Time (earlier events first)
        2. Priority (lower numbers = higher priority)
        3. Insertion order (tie-breaker)
        """
        self._counter += 1
        # Create event tuple
        event_tuple = (
            event.time,  # Primary sort by time
            event.priority,  # Secondary sort by priority
            self._counter,  # Tertiary sort by insertion order
            event
        )
        
        # Find insertion point using binary search
        left, right = 0, len(self.event_list)
        while left < right:
            mid = (left + right) // 2
            # Compare full tuples for proper ordering
            if self.event_list[mid] <= event_tuple:
                left = mid + 1
            else:
                right = mid
                
        # Insert at the correct position
        self.event_list.insert(left, event_tuple)
        
        # Safety check - verify event is not beyond end date
        if hasattr(self, 'end_date') and event.time > self.end_date:
            self.event_list.pop()
            return
    
    def get_next_event(self) -> Optional[Event]:
        """
        Get next event without updating clock time.

        Returns
        -------
        Optional[Event]
            Next event in chronological order, or None if no events remain
        """
        if not self.event_list:
            return None
        # Get the next event but don't update time until it's processed
        _, _, _, event = self.event_list.pop(0)
        return event

class BaseSimulation(ABC):
    """
    Abstract base class for simulations.

    Provides core simulation functionality including event processing,
    protocol management, and simulation execution control.

    Parameters
    ----------
    start_date : datetime
        Start date and time for the simulation
    environment : Optional[SimulationEnvironment], optional
        Simulation environment, creates new one if not provided

    Attributes
    ----------
    clock : SimulationClock
        Manages simulation time and events
    metrics : Dict[str, List[Any]]
        Stores simulation metrics
    environment : SimulationEnvironment
        Global simulation environment
    protocols : Dict[str, TreatmentProtocol]
        Registered treatment protocols
    """
    def __init__(self, start_date: datetime, environment: Optional[SimulationEnvironment] = None):
        self.clock = SimulationClock(start_date)
        self.metrics: Dict[str, List[Any]] = {}
        self.environment = environment or SimulationEnvironment(start_date)
        self.protocols: Dict[str, TreatmentProtocol] = {}
    
    @abstractmethod
    def process_event(self, event: Event):
        """
        Process a simulation event.

        Parameters
        ----------
        event : Event
            Event to process

        Notes
        -----
        This method must be implemented by concrete simulation classes.
        """
        pass
    
    def run(self, until: datetime):
        """
        Run simulation until specified datetime.

        Parameters
        ----------
        until : datetime
            End date and time for the simulation

        Notes
        -----
        - Processes events chronologically until end time is reached
        - Prints progress indicators (dots) for each simulated week
        - Includes safety limit to prevent infinite loops
        """
        self.clock.end_date = until  # Set end date in clock
        start_time = self.clock.current_time
        total_weeks = (until - start_time).days / 7
        current_week = 0
        last_week = -1
        max_events = 100000  # Safety limit to prevent infinite loops
        event_count = 0

        while event_count < max_events:
            event_count += 1
            event = self.clock.get_next_event()
            if event is None:
                print(f"\nSimulation complete after {event_count} events")
                return
            if event.time > until:
                # Put the event back in the queue if it's beyond our end time
                self.clock.schedule_event(event)
                print(f"\nReached end time after {event_count} events")
                return

            # Update clock time when processing the event
            self.clock.current_time = event.time
            
            # Print progress dot for each week
            current_week = (event.time - start_time).days / 7
            if int(current_week) > last_week:
                print(".", end="", flush=True)
                if int(current_week) % 52 == 0:  # New line every year
                    print(f" Year {int(current_week/52)} (Week {int(current_week)})")
                last_week = int(current_week)
            
            self.process_event(event)
            
    def register_protocol(self, protocol_type: str, protocol: TreatmentProtocol):
        """
        Register a protocol for use in the simulation.

        Parameters
        ----------
        protocol_type : str
            Identifier for the protocol type
        protocol : TreatmentProtocol
            Protocol instance to register
        """
        self.protocols[protocol_type] = protocol
        
    def get_protocol(self, protocol_type: str) -> Optional[TreatmentProtocol]:
        """
        Get a registered protocol by type.

        Parameters
        ----------
        protocol_type : str
            Identifier for the protocol type

        Returns
        -------
        Optional[TreatmentProtocol]
            Registered protocol or None if not found
        """
        return self.protocols.get(protocol_type)
        
    def schedule_protocol_event(self, 
                              time: datetime,
                              patient_id: str,
                              phase_type: PhaseType,
                              action: str,
                              data: Dict[str, Any] = None,
                              priority: int = 1):
        """
        Schedule a protocol-specific event.

        Parameters
        ----------
        time : datetime
            When the event should occur
        patient_id : str
            ID of the patient
        phase_type : PhaseType
            Type of protocol phase
        action : str
            Action to be performed
        data : Dict[str, Any], optional
            Additional event data
        priority : int, optional
            Event priority
        """
        event = Event.create_protocol_event(
            time=time,
            patient_id=patient_id,
            phase_type=phase_type,
            action=action,
            data=data,
            priority=priority
        )
        self.clock.schedule_event(event)
