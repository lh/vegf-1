import yaml
from pathlib import Path

def load_protocol(agent: str, protocol_name: str) -> TreatmentProtocol:
    path = Path(f"protocols/{agent.lower()}.yaml")
    with open(path) as f:
        data = yaml.safe_load(f)
    
    protocol_data = next(p for p in data["protocols"] if p["name"] == protocol_name)
    return TreatmentProtocol(
        agent=data["agent"],
        protocol_name=protocol_name,
        steps={step["name"]: ProtocolStep(**step) for step in protocol_data["steps"]}
    )
