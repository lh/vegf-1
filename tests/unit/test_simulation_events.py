import pytest
from unittest.mock import Mock
from datetime import datetime, timedelta
from simulation.base import Event, ProtocolEvent, SimulationClock
from protocol_models import (
    PhaseType, ActionType, DecisionType, VisitType,
    ProtocolPhase, TreatmentProtocol
)

@pytest.fixture
def start_date():
    return datetime(2023, 1, 1)

@pytest.fixture
def basic_event(start_date):
    return Event(
        time=start_date,
        event_type="test",
        patient_id="TEST001",
        data={"test": "value"}
    )

@pytest.fixture
def mock_visit_type():
    return VisitType(
        name="test_visit",
        required_actions=[ActionType.VISION_TEST, ActionType.OCT_SCAN],
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

@pytest.fixture
def protocol_event(start_date, mock_phase):
    mock_protocol = Mock(spec=TreatmentProtocol)
    return Event.create_protocol_event(
        time=start_date,
        patient_id="TEST001",
        phase_type=PhaseType.LOADING,
        action="test_action",
        data={"test": "value"},
        phase=mock_phase,
        protocol=mock_protocol
    )

class TestEventCreation:
    def test_basic_event_creation(self, start_date):
        event = Event(
            time=start_date,
            event_type="test",
            patient_id="TEST001",
            data={"test": "value"}
        )
        
        assert event.time == start_date
        assert event.event_type == "test"
        assert event.patient_id == "TEST001"
        assert event.data == {"test": "value"}
        assert event.priority == 1  # Default priority
        assert event.protocol_event is None
        assert event.phase is None
        assert event.protocol is None

    def test_protocol_event_creation(self, start_date, mock_phase):
        mock_protocol = Mock(spec=TreatmentProtocol)
        event = Event.create_protocol_event(
            time=start_date,
            patient_id="TEST001",
            phase_type=PhaseType.LOADING,
            action="test_action",
            data={"test": "value"},
            priority=2,
            phase=mock_phase,
            protocol=mock_protocol
        )
        
        assert event.time == start_date
        assert event.event_type == "protocol_test_action"
        assert event.patient_id == "TEST001"
        assert event.data == {"test": "value"}
        assert event.priority == 2
        assert isinstance(event.protocol_event, ProtocolEvent)
        assert event.protocol_event.phase_type == PhaseType.LOADING
        assert event.protocol_event.action == "test_action"
        assert event.phase == mock_phase
        assert event.protocol == mock_protocol

class TestEventActions:
    def test_get_visit_type_no_phase(self, basic_event):
        assert basic_event.get_visit_type() is None

    def test_get_visit_type_with_phase(self, start_date):
        mock_phase = Mock(spec=ProtocolPhase)
        mock_visit_type = Mock(spec=VisitType)
        mock_phase.visit_type = mock_visit_type
        
        event = Event(
            time=start_date,
            event_type="test",
            patient_id="TEST001",
            data={},
            phase=mock_phase
        )
        
        assert event.get_visit_type() == mock_visit_type

    def test_get_required_actions(self, start_date):
        mock_phase = Mock(spec=ProtocolPhase)
        mock_visit_type = Mock(spec=VisitType)
        mock_visit_type.required_actions = [ActionType.VISION_TEST, ActionType.OCT_SCAN]
        mock_phase.visit_type = mock_visit_type
        
        event = Event(
            time=start_date,
            event_type="test",
            patient_id="TEST001",
            data={},
            phase=mock_phase
        )
        
        actions = event.get_required_actions()
        assert len(actions) == 2
        assert ActionType.VISION_TEST in actions
        assert ActionType.OCT_SCAN in actions

    def test_get_optional_actions(self, start_date):
        mock_phase = Mock(spec=ProtocolPhase)
        mock_visit_type = Mock(spec=VisitType)
        mock_visit_type.optional_actions = [ActionType.INJECTION]
        mock_phase.visit_type = mock_visit_type
        
        event = Event(
            time=start_date,
            event_type="test",
            patient_id="TEST001",
            data={},
            phase=mock_phase
        )
        
        actions = event.get_optional_actions()
        assert len(actions) == 1
        assert ActionType.INJECTION in actions

class TestEventComparison:
    def test_event_ordering(self, start_date):
        event1 = Event(
            time=start_date,
            event_type="test1",
            patient_id="TEST001",
            data={},
            priority=1
        )
        event2 = Event(
            time=start_date + timedelta(days=1),
            event_type="test2",
            patient_id="TEST001",
            data={},
            priority=1
        )
        event3 = Event(
            time=start_date,
            event_type="test3",
            patient_id="TEST001",
            data={},
            priority=2
        )
        
        # Test chronological ordering
        assert event1.time < event2.time
        
        # Create a SimulationClock to test actual event ordering
        clock = SimulationClock(start_date)
        clock.schedule_event(event3)
        clock.schedule_event(event1)
        
        # Higher priority (lower number) should come first
        next_event = clock.get_next_event()
        assert next_event.priority == 1
        next_event = clock.get_next_event()
        assert next_event.priority == 2
