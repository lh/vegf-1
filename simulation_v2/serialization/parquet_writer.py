"""
Parquet serialization for V2 simulation.

Converts FOV (Four Option Version) internal states to TOM (Two Option Model)
for visualization and storage.
"""

from typing import Dict, List, Any
from datetime import datetime
from simulation_v2.core.disease_model import DiseaseState


def fov_to_tom(disease_state: DiseaseState, treatment_given: bool) -> str:
    """
    Convert FOV disease state to TOM treatment decision.
    
    The TOM only cares about whether an injection was given, not why.
    
    Args:
        disease_state: Current FOV disease state
        treatment_given: Whether injection was administered
        
    Returns:
        'inject' or 'no_inject'
    """
    # TOM is purely based on whether treatment was given
    # The disease state determines if treatment SHOULD be given,
    # but actual treatment depends on protocol and capacity
    return 'inject' if treatment_given else 'no_inject'


def serialize_visit(visit: Dict[str, Any]) -> Dict[str, Any]:
    """
    Serialize a single visit for Parquet storage.
    
    Converts FOV internal representation to TOM output format.
    
    Args:
        visit: Visit dictionary with FOV data
        
    Returns:
        Serialized visit with TOM format
    """
    # Convert FOV to TOM
    treatment_decision = fov_to_tom(
        visit['disease_state'],
        visit['treatment_given']
    )
    
    # Handle discontinuation type
    disc_type = visit.get('discontinuation_type')
    if disc_type is None:
        disc_type = 'none'
    
    # Create TOM-compatible output
    serialized = {
        'date': visit['date'],
        'treatment_decision': treatment_decision,
        'vision': visit['vision'],
        'discontinuation_type': disc_type
    }
    
    # Add any additional fields that should pass through
    # but exclude FOV-specific fields
    exclude_fields = {'disease_state', 'treatment_given'}
    for key, value in visit.items():
        if key not in serialized and key not in exclude_fields:
            serialized[key] = value
            
    return serialized


def serialize_patient_visits(
    patient_id: str, 
    visits: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Serialize all visits for a patient.
    
    Args:
        patient_id: Patient identifier
        visits: List of visit dictionaries
        
    Returns:
        List of serialized visits with patient_id added
    """
    serialized_visits = []
    
    for visit in visits:
        serialized = serialize_visit(visit)
        serialized['patient_id'] = patient_id
        serialized_visits.append(serialized)
        
    return serialized_visits