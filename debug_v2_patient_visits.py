#!/usr/bin/env python3
"""Debug script to check V2 patient visit structure."""

import sys
import json
from pathlib import Path
from datetime import datetime

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Import V2 simulation components
from simulation_v2.protocols.protocol_spec import ProtocolSpecification
from simulation_v2.core.disease_model import DiseaseModel
from simulation_v2.core.protocol import StandardProtocol

# Import enhanced engines with cost support
from simulation_v2.engines.abs_engine_with_costs import ABSEngineWithCosts
from simulation.economics.cost_metadata_enhancer_v2 import create_cost_metadata_enhancer


def main():
    """Run a minimal simulation to check visit structure."""
    
    # Load protocol
    protocol_path = Path("streamlit_app_v2/protocols/eylea.yaml")
    protocol_spec = ProtocolSpecification.from_yaml(protocol_path)
    
    # Create components
    disease_model = DiseaseModel(
        transition_probabilities=protocol_spec.disease_transitions,
        treatment_effect_multipliers=protocol_spec.treatment_effect_on_transitions,
        seed=42
    )
    
    protocol = StandardProtocol(
        min_interval_days=protocol_spec.min_interval_days,
        max_interval_days=protocol_spec.max_interval_days,
        extension_days=protocol_spec.extension_days,
        shortening_days=protocol_spec.shortening_days
    )
    protocol.name = protocol_spec.name
    
    # Create cost metadata enhancer
    cost_metadata_enhancer = create_cost_metadata_enhancer()
    
    # Create engine with just 1 patient
    engine = ABSEngineWithCosts(
        disease_model=disease_model,
        protocol=protocol,
        n_patients=1,
        seed=42,
        visit_metadata_enhancer=cost_metadata_enhancer
    )
    
    # Run for 6 months
    results = engine.run(0.5)
    
    # Check patient visit structure
    print("\n=== PATIENT VISIT STRUCTURE ===")
    
    for patient_id, patient in results.patient_histories.items():
        print(f"\nPatient: {patient_id}")
        print(f"Baseline vision: {patient.baseline_vision}")
        print(f"Total visits: {len(patient.visit_history)}")
        
        for i, visit in enumerate(patient.visit_history[:3]):  # First 3 visits
            print(f"\nVisit {i+1}:")
            print(f"  Date: {visit.get('date')}")
            print(f"  Disease state: {visit.get('disease_state')}")
            print(f"  Treatment given: {visit.get('treatment_given')}")
            print(f"  Vision: {visit.get('vision')}")
            print(f"  Metadata: {json.dumps(visit.get('metadata', {}), indent=4)}")
            
            # Check what fields are actually in the visit
            print(f"  All keys: {list(visit.keys())}")
    
    # Save sample data
    output_dir = Path("output/debug")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Extract one patient's data
    sample_patient_id = list(results.patient_histories.keys())[0]
    sample_patient = results.patient_histories[sample_patient_id]
    
    sample_data = {
        'patient_id': sample_patient_id,
        'baseline_vision': sample_patient.baseline_vision,
        'visits': sample_patient.visit_history
    }
    
    # Custom JSON encoder for datetime and enums
    def json_encoder(obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif hasattr(obj, 'name'):  # Enum
            return obj.name
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
    
    with open(output_dir / "sample_v2_patient.json", 'w') as f:
        json.dump(sample_data, f, indent=2, default=json_encoder)
    
    print(f"\nSample data saved to: {output_dir / 'sample_v2_patient.json'}")


if __name__ == "__main__":
    main()