import pytest
from datetime import datetime
from protocol_parser import ProtocolParser
from protocol_models import TreatmentProtocol, PhaseType
from validation.config_validator import ConfigValidator, ConfigurationError
from simulation.config import SimulationConfig

def test_protocol_loading():
    """Test loading and validating protocol configuration"""
    parser = ProtocolParser()
    config = parser.load_simulation_config("test_simulation")
    
    assert isinstance(config.protocol, TreatmentProtocol)
    assert config.protocol.agent == "eylea"
    assert "loading" in config.protocol.phases
    assert "maintenance" in config.protocol.phases
    
def test_protocol_phase_validation():
    """Test validation of protocol phase configurations"""
    parser = ProtocolParser()
    config = parser.load_simulation_config("test_simulation")
    
    # Test loading phase requirements
    loading_phase = config.protocol.phases["loading"]
    assert loading_phase.phase_type == PhaseType.LOADING
    assert loading_phase.duration_weeks is not None
    assert loading_phase.visit_interval_weeks is not None
    assert loading_phase.required_treatments is not None
    
    # Test maintenance phase requirements
    maintenance_phase = config.protocol.phases["maintenance"]
    assert maintenance_phase.phase_type == PhaseType.MAINTENANCE
    assert maintenance_phase.visit_interval_weeks is not None
    assert maintenance_phase.min_interval_weeks is not None
    assert maintenance_phase.max_interval_weeks is not None
    
def test_parameter_validation():
    """Test validation of protocol parameters"""
    parser = ProtocolParser()
    config = parser.load_simulation_config("test_simulation")
    
    # Test required parameter sections
    params = config.parameters
    assert "vision" in params
    assert "treatment_response" in params
    assert "resources" in params
    
    # Test vision parameters
    vision_params = config.get_vision_params()
    assert "baseline_mean" in vision_params
    assert "measurement_noise_sd" in vision_params
    assert "max_letters" in vision_params
    assert "min_letters" in vision_params
    
    # Test treatment response parameters
    loading_params = config.get_loading_phase_params()
    assert "vision_improvement_mean" in loading_params
    assert "vision_improvement_sd" in loading_params
    
def test_invalid_configurations():
    """Test handling of invalid configurations"""
    validator = ConfigValidator()
    
    # Test missing required phases
    invalid_protocol = {
        "name": "Invalid Protocol",
        "version": "1.0",
        "description": "Missing required phases",
        "phases": {
            "maintenance": {
                "visit_interval_weeks": 8,
                "min_interval_weeks": 4,
                "max_interval_weeks": 12
            }
        }
    }
    
    assert not validator.validate_protocol_definition(invalid_protocol)
    assert any("Missing required phases" in str(err) for err in validator.errors)
    
    # Test invalid parameter structure
    invalid_params = {
        "protocol_specific": {
            "vision": "invalid_type"  # Should be a dict
        }
    }
    
    with pytest.raises(ValueError):
        parser = ProtocolParser()
        parser._load_parameter_set("eylea", "standard")  # Use existing file

def test_simulation_config_validation():
    """Test validation of complete simulation configuration"""
    config = SimulationConfig.from_yaml("test_simulation")
    
    assert config.duration_days > 0
    assert config.num_patients > 0
    assert isinstance(config.start_date, datetime)
    assert config.protocol.validate()
