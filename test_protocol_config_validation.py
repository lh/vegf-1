import pytest
from datetime import datetime
from protocols.protocol_parser import ProtocolParser
from protocol_models import TreatmentProtocol, PhaseType
from validation.config_validator import ConfigValidator, ConfigurationError
from simulation.config import SimulationConfig

def test_protocol_loading():
    """
    Test loading and validating protocol configuration.
    
    This test verifies that the protocol parser correctly loads a test simulation
    configuration and creates a valid TreatmentProtocol object with the expected
    properties and phases.
    
    Checks:
    - Protocol is a TreatmentProtocol instance
    - Protocol has the correct agent name
    - Protocol contains required loading and maintenance phases
    """
    parser = ProtocolParser()
    config = parser.load_simulation_config("test_simulation")
    
    assert isinstance(config.protocol, TreatmentProtocol)
    assert config.protocol.agent == "eylea"
    assert "loading" in config.protocol.phases
    assert "maintenance" in config.protocol.phases
    
def test_protocol_phase_validation():
    """
    Test validation of protocol phase configurations.
    
    This test verifies that the protocol phases (loading and maintenance) have
    the correct properties and required attributes for their respective phase types.
    
    Checks:
    - Loading phase has the correct phase type
    - Loading phase has required duration, visit interval, and treatment count
    - Maintenance phase has the correct phase type
    - Maintenance phase has required visit interval and min/max interval settings
    """
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
    """
    Test validation of protocol parameters.
    
    This test verifies that the protocol configuration contains all required
    parameter sections and that each section contains the necessary parameters
    with appropriate values.
    
    Checks:
    - Configuration contains required sections (vision, treatment_response, resources)
    - Vision parameters section contains required fields
    - Treatment response parameters section contains required fields
    """
    parser = ProtocolParser()
    config = parser.load_simulation_config("test_simulation")
    
    # Test required parameter sections
    params = config.parameters
    assert "vision" in params
    assert "treatment_response" in params
    assert "resources" in params
    
    # Test vision parameters
    vision_params = config.parameters["vision"]
    assert "baseline_mean" in vision_params
    assert "measurement_noise_sd" in vision_params
    assert "max_letters" in vision_params
    assert "min_letters" in vision_params
    
    # Test treatment response parameters
    loading_params = config.parameters["treatment_response"]["loading_phase"]
    assert "vision_improvement_mean" in loading_params
    assert "vision_improvement_sd" in loading_params
    
def test_invalid_configurations():
    """
    Test handling of invalid configurations.
    
    This test verifies that the validation system correctly identifies and rejects
    invalid protocol configurations, raising appropriate errors with descriptive
    messages.
    
    Checks:
    - Validator rejects protocols missing required phases
    - Validator reports appropriate error messages
    - Parser raises ValueError for invalid parameter formats
    """
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
    
    parser = ProtocolParser()
    with pytest.raises(ValueError, match="Invalid parameter format"):
        parser._load_parameter_set("eylea", "invalid")

def test_simulation_config_validation():
    """
    Test validation of complete simulation configuration.
    
    This test verifies that a complete simulation configuration can be loaded from
    YAML and that it contains valid values for all required fields.
    
    Checks:
    - Configuration has positive duration days
    - Configuration has positive patient count
    - Start date is a valid datetime object
    - Protocol validates successfully
    """
    config = SimulationConfig.from_yaml("test_simulation")
    
    assert config.duration_days > 0
    assert config.num_patients > 0
    assert isinstance(config.start_date, datetime)
    assert config.protocol.validate()
