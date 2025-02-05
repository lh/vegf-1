import pytest
from unittest.mock import Mock
from datetime import datetime, timedelta
from simulation.base import (
    SimulationEnvironment, SimulationClock, BaseSimulation,
    Event, ProtocolEvent
)
from protocol_models import PhaseType, TreatmentProtocol, ProtocolPhase

@pytest.fixture
def start_date():
    return datetime(2023, 1, 1)

@pytest.fixture
def environment(start_date):
    return SimulationEnvironment(start_date)

@pytest.fixture
def clock(start_date):
    return SimulationClock(start_date)

@pytest.fixture
def mock_visit_type():
    return VisitType(
        name="test_visit",
        required_actions=[ActionType.VISION_TEST],
        optional_actions=[ActionType.INJECTION],
        decisions=[DecisionType.NURSE_CHECK],
        duration_minutes=30
    )

@pytest.fixture
def mock_phase(mock_visit_type):
    mock = Mock(spec=ProtocolPhase)
    mock.phase_type = PhaseType.LOADING
    mock.visit_type = mock_visit_type
    return mock

class TestSimulationEnvironment:
    def test_init(self, start_date):
        env = SimulationEnvironment(start_date)
        assert env.current_time == start_date
        assert env.global_state == {}

    def test_global_state_modification(self, environment):
        environment.global_state['test'] = 'value'
        assert environment.global_state['test'] == 'value'

class TestSimulationClock:
    def test_init(self, start_date):
        clock = SimulationClock(start_date)
        assert clock.current_time == start_date
        assert clock._counter == 0

    def test_event_scheduling(self, clock):
        event1 = Event(
            time=clock.current_time + timedelta(days=1),
            event_type="test",
            patient_id="TEST001",
            data={},
            priority=1
        )
        event2 = Event(
            time=clock.current_time + timedelta(days=2),
            event_type="test",
            patient_id="TEST001",
            data={},
            priority=1
        )
        
        clock.schedule_event(event2)
        clock.schedule_event(event1)
        
        # Events should come out in chronological order
        next_event = clock.get_next_event()
        assert next_event.time == clock.current_time + timedelta(days=1)
        
        next_event = clock.get_next_event()
        assert next_event.time == clock.current_time + timedelta(days=2)

    def test_priority_ordering(self, clock):
        # Create events with same time but different priorities
        time = clock.current_time + timedelta(days=1)
        event1 = Event(time=time, event_type="test", patient_id="TEST001", data={}, priority=2)
        event2 = Event(time=time, event_type="test", patient_id="TEST001", data={}, priority=1)
        
        clock.schedule_event(event2)
        clock.schedule_event(event1)
        
        # Higher priority (lower number) should come first
        assert clock.get_next_event().priority == 1
        assert clock.get_next_event().priority == 2

    def test_empty_queue(self, clock):
        assert clock.get_next_event() is None

class TestEvent:
    def test_create_protocol_event(self, start_date):
        event = Event.create_protocol_event(
            time=start_date,
            patient_id="TEST001",
            phase_type=PhaseType.LOADING,
            action="test_action",
            data={"test": "value"},
            priority=1
        )
        
        assert event.time == start_date
        assert event.patient_id == "TEST001"
        assert event.event_type == "protocol_test_action"
        assert event.protocol_event.phase_type == PhaseType.LOADING
        assert event.protocol_event.action == "test_action"
        assert event.protocol_event.parameters == {"test": "value"}

    def test_get_visit_type(self, start_date):
        # Create mock phase with visit type
        mock_phase = Mock(spec=ProtocolPhase)
        mock_visit_type = Mock()
        mock_phase.visit_type = mock_visit_type
        
        event = Event(
            time=start_date,
            event_type="test",
            patient_id="TEST001",
            data={},
            phase=mock_phase
        )
        
        assert event.get_visit_type() == mock_visit_type

class MockSimulation(BaseSimulation):
    def process_event(self, event: Event):
        """Mock implementation of process_event"""
        self.last_processed_event = event

class TestBaseSimulation:
    def test_init(self, start_date):
        sim = MockSimulation(start_date)
        assert isinstance(sim.clock, SimulationClock)
        assert sim.metrics == {}
        assert isinstance(sim.environment, SimulationEnvironment)

    def test_protocol_registration(self, start_date):
        sim = MockSimulation(start_date)
        mock_protocol = Mock(spec=TreatmentProtocol)
        
        sim.register_protocol("test_protocol", mock_protocol)
        assert sim.get_protocol("test_protocol") == mock_protocol
        assert sim.get_protocol("nonexistent") is None

    def test_run_until(self, start_date):
        sim = MockSimulation(start_date)
        end_date = start_date + timedelta(days=7)
        
        # Schedule some test events
        event1 = Event(
            time=start_date + timedelta(days=1),
            event_type="test",
            patient_id="TEST001",
            data={}
        )
        event2 = Event(
            time=start_date + timedelta(days=10),  # Beyond end date
            event_type="test",
            patient_id="TEST001",
            data={}
        )
        
        sim.clock.schedule_event(event1)
        sim.clock.schedule_event(event2)
        
        # Run simulation
        sim.run(end_date)
        
        # Only first event should have been processed
        assert sim.clock.current_time == start_date + timedelta(days=1)
