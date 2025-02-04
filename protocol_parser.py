import yaml
from pathlib import Path
from protocol_models import TreatmentProtocol
from typing import Dict

def load_protocol(agent: str, protocol_name: str) -> TreatmentProtocol:
    path = Path(f"protocols/{agent.lower()}.yaml")
    with open(path) as f:
        data = yaml.safe_load(f)
    
    if protocol_name not in data["protocols"]:
        raise ValueError(f"Protocol {protocol_name} not found")
        
    protocol_data = data["protocols"][protocol_name]
    return TreatmentProtocol(
        agent=data["agent"],
        protocol_name=protocol_name,
        steps=protocol_data["steps"]
    )
