from pathlib import Path
from typing import Dict, Any, List, Optional, Type
import yaml
from dataclasses import dataclass
from validation.config_validator import ConfigValidator, ConfigurationError
from protocol_models import (
    TreatmentProtocol, ProtocolPhase, LoadingPhase, MaintenancePhase,
    ExtensionPhase, DiscontinuationPhase, VisitType, TreatmentDecision,
    ActionType, DecisionType, PhaseType
)

@dataclass
class SimulationConfig:
    name: str
    protocol_agent: str
    protocol_type: str
    parameter_set: str
    simulation_type: str
    duration_days: int
    num_patients: int
    random_seed: int
    save_results: bool
    database: str
    plots: bool
    verbose: bool
    start_date: str
    description: str
    protocol: Optional[TreatmentProtocol] = None
    parameters: Optional[Dict[str, Any]] = None

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

def _create_visit_type(visit_data: Dict) -> VisitType:
    """Create VisitType object from dictionary data"""
    return VisitType(
        name=visit_data["name"],
        required_actions=[ActionType(action) for action in visit_data.get("required_actions", [])],
        optional_actions=[ActionType(action) for action in visit_data.get("optional_actions", [])],
        decisions=[DecisionType(decision) for decision in visit_data.get("decisions", [])],
        duration_minutes=visit_data.get("duration_minutes", 30)
    )

def _create_treatment_decision(decision_data: Dict) -> TreatmentDecision:
    """Create TreatmentDecision object from dictionary data"""
    return TreatmentDecision(
        metric=decision_data["metric"],
        comparator=decision_data["comparator"],
        value=decision_data["value"],
        action=decision_data.get("action", "continue"),
        priority=decision_data.get("priority", 1)
    )

def _create_protocol_phase(phase_data: Dict, phase_type: PhaseType) -> ProtocolPhase:
    """Create appropriate ProtocolPhase object based on phase type"""
    phase_classes: Dict[PhaseType, Type[ProtocolPhase]] = {
        PhaseType.LOADING: LoadingPhase,
        PhaseType.MAINTENANCE: MaintenancePhase,
        PhaseType.EXTENSION: ExtensionPhase,
        PhaseType.DISCONTINUATION: DiscontinuationPhase
    }
    
    phase_class = phase_classes[phase_type]
    
    # Convert visit type if present
    visit_type = None
    if "visit_type" in phase_data:
        visit_type = _create_visit_type(phase_data["visit_type"])
        
    # Convert criteria lists if present
    entry_criteria = [
        _create_treatment_decision(d) 
        for d in phase_data.get("entry_criteria", [])
    ]
    exit_criteria = [
        _create_treatment_decision(d) 
        for d in phase_data.get("exit_criteria", [])
    ]
    
    return phase_class(
        phase_type=phase_type,
        duration_weeks=phase_data.get("duration_weeks"),
        visit_interval_weeks=phase_data["visit_interval_weeks"],
        required_treatments=phase_data.get("required_treatments"),
        min_interval_weeks=phase_data.get("min_interval_weeks"),
        max_interval_weeks=phase_data.get("max_interval_weeks"),
        interval_adjustment_weeks=phase_data.get("interval_adjustment_weeks"),
        entry_criteria=entry_criteria,
        exit_criteria=exit_criteria,
        visit_type=visit_type
    )

class ProtocolParser:
    """Parser for protocol configurations that creates protocol objects"""
    
    def __init__(self, base_path: str = "protocols"):
        self.base_path = Path(base_path)
        self.validator = ConfigValidator()
        self.base_parameters = self._load_base_parameters()
        
    def _create_visit_type(self, visit_data: Dict) -> VisitType:
        """Create VisitType object from dictionary data"""
        return VisitType(
            name=visit_data["name"],
            required_actions=[ActionType(action) for action in visit_data.get("required_actions", [])],
            optional_actions=[ActionType(action) for action in visit_data.get("optional_actions", [])],
            decisions=[DecisionType(decision) for decision in visit_data.get("decisions", [])],
            duration_minutes=visit_data.get("duration_minutes", 30)
        )
        
    def _create_treatment_decision(self, decision_data: Dict) -> TreatmentDecision:
        """Create TreatmentDecision object from dictionary data"""
        return TreatmentDecision(
            metric=decision_data["metric"],
            comparator=decision_data["comparator"],
            value=decision_data["value"],
            action=decision_data.get("action", "continue"),
            priority=decision_data.get("priority", 1)
        )
    
    def _load_base_parameters(self) -> Dict:
        """Load and validate base parameters file"""
        with open(self.base_path / "base_parameters.yaml") as f:
            params = yaml.safe_load(f)
            
        if not self.validator.validate_base_parameters(params):
            raise ValueError(f"Invalid base parameters: {self.validator.errors}")
            
        return params
    
    def _create_protocol_phase(self, phase_data: Dict[str, Any], phase_type: str) -> ProtocolPhase:
        """Create appropriate protocol phase object from YAML data"""
        phase_types = {
            "loading": (PhaseType.LOADING, LoadingPhase),
            "maintenance": (PhaseType.MAINTENANCE, MaintenancePhase),
            "extension": (PhaseType.EXTENSION, ExtensionPhase),
            "discontinuation": (PhaseType.DISCONTINUATION, DiscontinuationPhase)
        }
        
        if phase_type not in phase_types:
            raise ValueError(f"Unknown phase type: {phase_type}")
            
        phase_enum, phase_class = phase_types[phase_type]
        
        # Create visit type if specified
        visit_type = None
        if "visit_type" in phase_data:
            visit_type = self._create_visit_type(phase_data["visit_type"])
            
        # Convert criteria to TreatmentDecision objects
        entry_criteria = [
            self._create_treatment_decision(d) 
            for d in phase_data.get("entry_criteria", [])
        ]
        exit_criteria = [
            self._create_treatment_decision(d) 
            for d in phase_data.get("exit_criteria", [])
        ]
        
        return phase_class(
            phase_type=phase_enum,
            duration_weeks=phase_data.get("duration_weeks"),
            visit_interval_weeks=phase_data["visit_interval_weeks"],
            required_treatments=phase_data.get("required_treatments"),
            min_interval_weeks=phase_data.get("min_interval_weeks"),
            max_interval_weeks=phase_data.get("max_interval_weeks"),
            interval_adjustment_weeks=phase_data.get("interval_adjustment_weeks"),
            entry_criteria=entry_criteria,
            exit_criteria=exit_criteria,
            visit_type=visit_type
        )

    def _load_protocol_definition(self, agent: str, protocol_type: str) -> TreatmentProtocol:
        """Load and create protocol object from YAML definition"""
        path = self.base_path / "protocol_definitions" / agent / f"{protocol_type}.yaml"
        with open(path) as f:
            protocol_data = yaml.safe_load(f)
            
        if not self.validator.validate_protocol_definition(protocol_data):
            raise ValueError(f"Invalid protocol definition: {self.validator.errors}")
            
        # Validate phase definitions
        if not self._validate_protocol_phases(protocol_data.get("phases", {})):
            raise ValueError(f"Invalid phase definitions: {self.validator.errors}")
            
        # Create phase objects with proper type mapping
        phases = {}
        phase_mapping = {
            "loading": PhaseType.LOADING,
            "maintenance": PhaseType.MAINTENANCE,
            "extension": PhaseType.EXTENSION,
            "discontinuation": PhaseType.DISCONTINUATION
        }
        
        for phase_name, phase_data in protocol_data.get("phases", {}).items():
            if phase_name not in phase_mapping:
                raise ValueError(f"Unknown phase type: {phase_name}")
                
            phase_type = phase_mapping[phase_name]
            phases[phase_name] = self._create_protocol_phase(phase_data, phase_type)
            
        # Convert discontinuation criteria with validation
        discontinuation_criteria = []
        for criterion in protocol_data.get("discontinuation_criteria", []):
            try:
                decision = self._create_treatment_decision(criterion)
                if decision.action not in ["stop", "consider_stop"]:
                    raise ValueError(f"Invalid discontinuation action: {decision.action}")
                discontinuation_criteria.append(decision)
            except Exception as e:
                raise ValueError(f"Invalid discontinuation criterion: {str(e)}")
        
        # Create protocol object
        protocol = TreatmentProtocol(
            agent=agent,
            protocol_name=protocol_data["name"],
            version=protocol_data["version"],
            description=protocol_data["description"],
            phases=phases,
            parameters=self._load_parameter_set(agent, protocol_type),
            discontinuation_criteria=discontinuation_criteria
        )
        
        # Validate complete protocol
        if not protocol.validate():
            raise ValueError("Protocol validation failed")
            
        return protocol
    
    def _validate_protocol_phases(self, phases: Dict[str, Dict]) -> bool:
        """Validate protocol phase definitions"""
        required_phases = {"loading", "maintenance"}
        phase_types = set(phases.keys())
        
        if not all(phase in phase_types for phase in required_phases):
            self.validator.errors.append(
                ConfigurationError("protocol_definition", 
                                 f"Missing required phases: {required_phases - phase_types}")
            )
            return False
            
        # Validate each phase
        for phase_name, phase_data in phases.items():
            if not self._validate_phase_definition(phase_name, phase_data):
                return False
                
        return True
        
    def _validate_phase_definition(self, phase_name: str, phase_data: Dict) -> bool:
        """Validate individual phase definition"""
        required_fields = {
            "loading": {"duration_weeks", "visit_interval_weeks", "required_treatments"},
            "maintenance": {"visit_interval_weeks", "min_interval_weeks", "max_interval_weeks"}
        }
        
        if phase_name in required_fields:
            missing_fields = required_fields[phase_name] - set(phase_data.keys())
            if missing_fields:
                self.validator.errors.append(
                    ConfigurationError("protocol_definition",
                                     f"Phase {phase_name} missing fields: {missing_fields}")
                )
                return False
                
        return True
        
    def _load_parameter_set(self, agent: str, parameter_set: str) -> Dict[str, Any]:
        """Load and validate parameter set and merge with base parameters"""
        path = self.base_path / "parameter_sets" / agent / f"{parameter_set}.yaml"
        with open(path) as f:
            params = yaml.safe_load(f)
            
        if not self.validator.validate_parameter_set(params):
            raise ValueError(f"Invalid parameter set: {self.validator.errors}")
        
        # Deep copy base parameters to avoid modifying original
        merged = self.base_parameters.copy()
        
        # Merge protocol specific parameters with validation
        protocol_params = params.get("protocol_specific", {})
        for category, values in protocol_params.items():
            if not isinstance(values, dict):
                raise ValueError(f"Invalid parameter format for {category}")
                
            if category in merged:
                if isinstance(merged[category], dict):
                    merged[category].update(values)
                else:
                    merged[category] = values
            else:
                merged[category] = values
                
        return merged
    
    def load_simulation_config(self, config_name: str) -> SimulationConfig:
        """Load simulation configuration and create protocol objects"""
        path = self.base_path / "simulation_configs" / f"{config_name}.yaml"
        with open(path) as f:
            config = yaml.safe_load(f)
            
        if not self.validator.validate_simulation_config(config):
            raise ValueError(f"Invalid simulation config: {self.validator.errors}")
            
        # Load and create protocol object with validation
        protocol = self._load_protocol_definition(
            config["protocol"]["agent"],
            config["protocol"]["type"]
        )
        
        if not protocol.validate():
            raise ValueError("Invalid protocol configuration")
            
        # Load and merge parameters with validation
        parameters = self._load_parameter_set(
            config["protocol"]["agent"],
            config["protocol"]["parameter_set"]
        )
        
        return SimulationConfig(
            name=config["name"],
            description=config["description"],
            protocol_agent=config["protocol"]["agent"],
            protocol_type=config["protocol"]["type"],
            parameter_set=config["protocol"]["parameter_set"],
            simulation_type=config["simulation"]["type"],
            duration_days=config["simulation"]["duration_days"],
            num_patients=config["simulation"]["num_patients"],
            random_seed=config["simulation"]["random_seed"],
            save_results=config["output"]["save_results"],
            database=config["output"]["database"],
            plots=config["output"]["plots"],
            verbose=config["output"]["verbose"],
            start_date=config["simulation"]["start_date"],
            protocol=protocol,  # Now passing protocol object
            parameters=parameters  # Now passing merged parameters
        )
    
    def get_full_configuration(self, config_name: str) -> Dict[str, Any]:
        """Get complete configuration with protocol objects"""
        config = self.load_simulation_config(config_name)
        
        return {
            "config": config,
            "protocol": config.protocol,  # Already a TreatmentProtocol object
            "parameters": config.parameters  # Already merged parameters
        }

def load_protocol(config_name: str) -> Dict[str, Any]:
    """Legacy support function"""
    parser = ProtocolParser()
    return parser.get_full_configuration(config_name)
