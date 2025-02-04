import pytest
from datetime import datetime, timedelta
from protocol_models import (
    PhaseType, ActionType, DecisionType, VisitType,
    TreatmentDecision, LoadingPhase, MaintenancePhase,
    ExtensionPhase, DiscontinuationPhase, TreatmentProtocol
)

def test_visit_type_creation():
    """Test creation and validation of visit types"""
    # Test valid visit type
    visit = VisitType(
        name="test_visit",
        required_actions=[ActionType.VISION_TEST, ActionType.OCT_SCAN],
        optional_actions=[ActionType.INJECTION],
        decisions=[DecisionType.NURSE_CHECK]
    )
    assert visit.validate()
    
    # Test invalid visit type (no name)
    invalid_visit = VisitType(
        name="",
        required_actions=[ActionType.VISION_TEST]
    )
    assert not invalid_visit.validate()

def test_treatment_decision():
    """Test treatment decision evaluation"""
    decision = TreatmentDecision(
        metric="vision",
        comparator=">=",
        value=70,
        action="continue"
    )
    
    assert decision.evaluate(75)  # Above threshold
    assert decision.evaluate(70)  # At threshold
    assert not decision.evaluate(65)  # Below threshold
    
    # Test baseline comparison
    baseline_decision = TreatmentDecision(
        metric="vision",
        comparator=">=",
        value="baseline",
        action="continue"
    )
    assert baseline_decision.evaluate(65)  # Should handle baseline specially

def test_loading_phase():
    """Test loading phase behavior"""
    phase = LoadingPhase(
        phase_type=PhaseType.LOADING,
        duration_weeks=12,
        visit_interval_weeks=4,
        required_treatments=3
    )
    
    # Test visit processing
    state = {"treatments_in_phase": 1}
    updated = phase.process_visit(state)
    
    assert updated["treatments_in_phase"] == 2
    assert updated["next_visit_weeks"] == 4
    assert not updated.get("phase_complete", False)
    
    # Test completion
    state = {"treatments_in_phase": 2}
    updated = phase.process_visit(state)
    assert updated["phase_complete"]

def test_maintenance_phase():
    """Test maintenance phase behavior"""
    phase = MaintenancePhase(
        phase_type=PhaseType.MAINTENANCE,
        duration_weeks=None,
        visit_interval_weeks=8,
        min_interval_weeks=4,
        max_interval_weeks=12,
        interval_adjustment_weeks=2
    )
    
    # Test interval extension
    state = {
        "current_interval": 8,
        "disease_activity": "stable"
    }
    updated = phase.process_visit(state)
    assert updated["next_visit_weeks"] == 10
    
    # Test interval reduction
    state["disease_activity"] = "active"
    updated = phase.process_visit(state)
    assert updated["next_visit_weeks"] == 6  # Reduces by 2*adjustment_weeks (4 weeks)

def test_extension_phase():
    """Test extension phase behavior"""
    phase = ExtensionPhase(
        phase_type=PhaseType.EXTENSION,
        duration_weeks=None,
        visit_interval_weeks=12,
        min_interval_weeks=4,
        max_interval_weeks=16,
        interval_adjustment_weeks=2
    )
    
    # Test conservative extension
    state = {
        "current_interval": 12,
        "disease_activity": "stable"
    }
    updated = phase.process_visit(state)
    assert updated["next_visit_weeks"] == 13  # Only increase by 1 week
    
    # Test aggressive reduction on activity
    state["disease_activity"] = "active"
    updated = phase.process_visit(state)
    assert updated["next_visit_weeks"] == 7  # Reduces by 3*adjustment_weeks (6 weeks)
    assert updated["phase_complete"]  # Should exit to maintenance

def test_protocol_phase_transitions():
    """Test protocol phase transitions"""
    protocol = TreatmentProtocol(
        agent="test_agent",
        protocol_name="test_protocol",
        version="1.0",
        description="Test protocol",
        phases={
            "loading": LoadingPhase(
                phase_type=PhaseType.LOADING,
                duration_weeks=12,
                visit_interval_weeks=4,
                required_treatments=3
            ),
            "maintenance": MaintenancePhase(
                phase_type=PhaseType.MAINTENANCE,
                duration_weeks=None,
                visit_interval_weeks=8,
                min_interval_weeks=4,
                max_interval_weeks=12,
                interval_adjustment_weeks=2
            )
        },
        parameters={},
        discontinuation_criteria=[]
    )
    
    # Test initial phase
    initial = protocol.get_initial_phase()
    assert initial.phase_type == PhaseType.LOADING
    
    # Test phase transition
    next_phase = protocol.get_next_phase(initial)
    assert next_phase.phase_type == PhaseType.MAINTENANCE
    
    # Test phase completion
    state = {"treatments_in_phase": 3, "weeks_in_phase": 12}
    assert initial.is_complete(state)

def test_protocol_validation():
    """Test protocol configuration validation"""
    # Valid protocol
    valid_protocol = TreatmentProtocol(
        agent="test_agent",
        protocol_name="test_protocol",
        version="1.0",
        description="Test protocol",
        phases={
            "loading": LoadingPhase(
                phase_type=PhaseType.LOADING,
                duration_weeks=12,
                visit_interval_weeks=4,
                required_treatments=3
            )
        },
        parameters={},
        discontinuation_criteria=[]
    )
    assert valid_protocol.validate()
    
    # Invalid protocol (no loading phase)
    invalid_protocol = TreatmentProtocol(
        agent="test_agent",
        protocol_name="test_protocol",
        version="1.0",
        description="Test protocol",
        phases={
            "maintenance": MaintenancePhase(
                phase_type=PhaseType.MAINTENANCE,
                duration_weeks=None,
                visit_interval_weeks=8,
                min_interval_weeks=4,
                max_interval_weeks=12,
                interval_adjustment_weeks=2
            )
        },
        parameters={},
        discontinuation_criteria=[]
    )
    assert not invalid_protocol.validate()
