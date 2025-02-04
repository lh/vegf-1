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
            
        # Create phase objects
        phases = {}
        for phase_name, phase_data in protocol_data.get("phases", {}).items():
            phases[phase_name] = self._create_protocol_phase(phase_data, phase_name)
            
        # Convert discontinuation criteria
        discontinuation_criteria = [
            self._create_treatment_decision(d)
            for d in protocol_data.get("discontinuation_criteria", [])
        ]
        
        return TreatmentProtocol(
            agent=agent,
            protocol_name=protocol_data["name"],
            version=protocol_data["version"],
            description=protocol_data["description"],
            phases=phases,
            parameters=self._load_parameter_set(agent, protocol_type),
            discontinuation_criteria=discontinuation_criteria
        )
    
    def _load_parameter_set(self, agent: str, parameter_set: str) -> Dict:
        """Load and validate parameter set and merge with base parameters"""
        path = self.base_path / "parameter_sets" / agent / f"{parameter_set}.yaml"
        with open(path) as f:
            params = yaml.safe_load(f)
            
        if not self.validator.validate_parameter_set(params):
            raise ValueError(f"Invalid parameter set: {self.validator.errors}")
        
        # Deep copy base parameters to avoid modifying original
        merged = self.base_parameters.copy()
        
        # Merge protocol specific parameters
        protocol_params = params.get("protocol_specific", {})
        for category, values in protocol_params.items():
            if category in merged:
                merged[category].update(values)
            else:
                merged[category] = values
                
        return merged
    
    def load_simulation_config(self, config_name: str) -> SimulationConfig:
        """Load simulation configuration"""
        path = self.base_path / "simulation_configs" / f"{config_name}.yaml"
        with open(path) as f:
            config = yaml.safe_load(f)
        
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
            start_date=config["simulation"]["start_date"]
        )
    
    def get_full_configuration(self, config_name: str) -> Dict[str, Any]:
        """Get complete configuration including protocol and parameters"""
        config = self.load_simulation_config(config_name)
        protocol = self._load_protocol_definition(config.protocol_agent, config.protocol_type)
        parameters = self._load_parameter_set(config.protocol_agent, config.parameter_set)
        
        return {
            "config": config,
            "protocol": protocol,
            "parameters": parameters
        }

def load_protocol(config_name: str) -> Dict[str, Any]:
    """Legacy support function"""
    parser = ProtocolParser()
    return parser.get_full_configuration(config_name)
