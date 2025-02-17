import pytest
from datetime import datetime, timedelta
from simulation.agent_state import AgentState

@pytest.fixture
def agent_state():
    """Create a basic agent state for testing"""
    start_time = datetime(2024, 1, 1)
    risk_factors = {
        "age": 70,
        "smoking": 0.5,
        "genetic_risk": 0.3
    }
    return AgentState("test_patient", "test_protocol", 60.0, start_time, risk_factors)

def test_agent_state_initialization(agent_state):
    """Test proper initialization of agent state"""
    assert agent_state.patient_id == "test_patient"
    assert agent_state.state["protocol"] == "test_protocol"
    assert agent_state.state["current_vision"] == 60.0
    assert agent_state.state["treatment_adherence"] == 1.0
    assert agent_state.state["missed_appointments"] == 0
    assert isinstance(agent_state.state["disease_progression_rate"], float)
    assert isinstance(agent_state.state["quality_of_life"], float)
    assert "treatment_outcomes" in agent_state.state

def test_disease_progression_calculation(agent_state):
    """Test disease progression rate calculation"""
    progression_rate = agent_state._calculate_progression_rate()
    assert progression_rate > 0.1  # Should be higher than base rate due to risk factors
    assert progression_rate < 0.3  # Should be reasonably bounded

def test_quality_of_life_calculation(agent_state):
    """Test quality of life score calculation"""
    qol = agent_state._calculate_qol()
    assert 0 <= qol <= 1  # Should be normalized between 0 and 1
    
    # Test QoL changes with treatment burden
    agent_state.state["injections"] = 6
    new_qol = agent_state._calculate_qol()
    assert new_qol < qol  # Should decrease with more injections

def test_treatment_decision_making(agent_state):
    """Test treatment decision making process"""
    current_time = datetime(2024, 2, 1)
    
    # Test initial decision (should likely attend with good adherence)
    will_attend, actions = agent_state.make_treatment_decision(current_time)
    assert isinstance(will_attend, bool)
    assert isinstance(actions, list)
    if will_attend:
        assert "vision_test" in actions
        assert "oct_scan" in actions
    
    # Test decision with reduced adherence
    agent_state.state["treatment_adherence"] = 0.5
    agent_state.state["injections"] = 8
    will_attend, actions = agent_state.make_treatment_decision(current_time)
    assert isinstance(will_attend, bool)
    if not will_attend:
        assert agent_state.state["missed_appointments"] > 0

def test_needs_injection_determination(agent_state):
    """Test injection need determination"""
    current_time = datetime(2024, 2, 1)
    
    # Should need injection initially
    assert agent_state._needs_injection(current_time) is True
    
    # Process a visit with injection
    agent_state.process_visit(current_time, ["injection"])
    
    # Test after recent injection
    assert agent_state._needs_injection(current_time) is False
    
    # Test with vision decline
    agent_state.state["current_vision"] = 50.0  # Significant decline
    assert agent_state._needs_injection(current_time) is True

def test_outcome_updates(agent_state):
    """Test outcome tracking and updates"""
    current_time = datetime(2024, 2, 1)
    
    # Initial state
    agent_state.update_outcomes(current_time)
    metrics = agent_state.get_outcome_metrics()
    
    assert "vision_change" in metrics
    assert "quality_of_life" in metrics
    assert "treatment_adherence" in metrics
    assert "disease_progression_rate" in metrics
    
    # Test after some treatment
    agent_state.process_visit(current_time, ["injection"])
    agent_state.update_outcomes(current_time + timedelta(weeks=4))
    new_metrics = agent_state.get_outcome_metrics()
    
    assert new_metrics["total_injections"] == 1
    assert new_metrics["total_visits"] == 1
    assert "treatment_outcomes" in new_metrics

def test_visit_processing(agent_state):
    """Test visit processing with agent-specific updates"""
    visit_time = datetime(2024, 2, 1)
    
    # Process a visit with multiple actions
    visit_data = agent_state.process_visit(visit_time, ["vision_test", "oct_scan", "injection"])
    
    assert "vision_change" in visit_data
    assert "oct_findings" in visit_data
    assert "actions_performed" in visit_data
    assert agent_state.state["visits"] == 1
    assert agent_state.state["injections"] == 1
    
    # Check visit history
    assert len(agent_state.visit_history) == 1
    assert agent_state.visit_history[0]["date"] == visit_time.replace(second=0, microsecond=0)
