"""
Visit enhancer module for adding cost metadata to existing visit records.

This module provides functions to enhance visit records with cost-relevant
metadata without modifying the core simulation classes.
"""

from typing import Dict, List, Any
from datetime import datetime


def enhance_visit_with_cost_metadata(visit: Dict[str, Any], 
                                   visit_data: Dict[str, Any] = None,
                                   previous_visit: Dict[str, Any] = None,
                                   visit_number: int = None) -> Dict[str, Any]:
    """
    Enhance a visit record with cost-relevant metadata.
    
    This function adds metadata needed for cost analysis to an existing
    visit record without modifying the original structure.
    
    Parameters
    ----------
    visit : Dict[str, Any]
        The visit record to enhance
    visit_data : Dict[str, Any], optional
        Additional visit data (e.g., drug information)
    previous_visit : Dict[str, Any], optional
        Previous visit record for calculating time intervals
    visit_number : int, optional
        Visit number in the sequence
        
    Returns
    -------
    Dict[str, Any]
        Enhanced visit record with metadata field
    """
    # Create a copy to avoid modifying the original
    enhanced_visit = visit.copy()
    
    # Initialize metadata if not present
    if 'metadata' not in enhanced_visit:
        enhanced_visit['metadata'] = {}
    
    metadata = enhanced_visit['metadata']
    
    # 1. Components performed - map actions to cost components
    if 'actions' in visit:
        components = map_actions_to_components(visit['actions'])
        if components:
            metadata['components_performed'] = components
    
    # 2. Visit subtype - determine based on phase and visit type
    visit_type = visit.get('type', 'regular_visit')
    phase = visit.get('phase', 'loading')
    actions = visit.get('actions', [])
    
    visit_subtype = determine_visit_subtype(visit_type, phase, actions)
    if visit_subtype:
        metadata['visit_subtype'] = visit_subtype
    
    # 3. Drug information
    if visit_data and 'drug' in visit_data:
        metadata['drug'] = visit_data['drug']
    elif 'injection' in actions:
        # Try to infer drug from visit data
        if 'drug' in visit:
            metadata['drug'] = visit['drug']
    
    # 4. Special events
    if visit_data and 'special_event' in visit_data:
        metadata['special_event'] = visit_data['special_event']
    
    # 5. Visit number
    if visit_number is not None:
        metadata['visit_number'] = visit_number
    
    # 6. Days since last visit
    if previous_visit and 'date' in visit and 'date' in previous_visit:
        current_date = visit['date']
        previous_date = previous_visit['date']
        
        # Handle both datetime and float (months) formats
        if isinstance(current_date, datetime) and isinstance(previous_date, datetime):
            days_since = (current_date - previous_date).days
        elif isinstance(current_date, (int, float)) and isinstance(previous_date, (int, float)):
            # Assume months, convert to approximate days
            days_since = int((current_date - previous_date) * 30.44)
        else:
            days_since = 0
            
        metadata['days_since_last'] = days_since
    else:
        metadata['days_since_last'] = 0
    
    # 7. Phase (include in metadata for easier access)
    metadata['phase'] = phase
    
    return enhanced_visit


def map_actions_to_components(actions: List[str]) -> List[str]:
    """
    Map simulation actions to cost components.
    
    Parameters
    ----------
    actions : List[str]
        Actions performed during the visit
        
    Returns
    -------
    List[str]
        Cost components corresponding to the actions
    """
    # Mapping from simulation actions to cost components
    action_to_component = {
        'injection': 'injection',
        'oct_scan': 'oct_scan',
        'oct': 'oct_scan',  # Alternative name
        'visual_acuity_test': 'visual_acuity_test',
        'va_test': 'visual_acuity_test',  # Alternative name
        'pressure_check': 'pressure_check',
        'iop_check': 'pressure_check',  # Alternative name
        'virtual_review': 'virtual_review',
        'face_to_face_review': 'face_to_face_review',
        'f2f_review': 'face_to_face_review',  # Alternative name
        'initial_assessment': 'initial_assessment',
        'adverse_event_assessment': 'adverse_event_assessment',
        'fluorescein_angiography': 'fluorescein_angiography',
        'fa': 'fluorescein_angiography'  # Alternative name
    }
    
    components = []
    for action in actions:
        # Normalize action name
        action_lower = action.lower().replace('-', '_').replace(' ', '_')
        if action_lower in action_to_component:
            component = action_to_component[action_lower]
            if component not in components:  # Avoid duplicates
                components.append(component)
    
    return components


def determine_visit_subtype(visit_type: str, phase: str, 
                           actions: List[str]) -> str:
    """
    Determine the specific visit subtype for cost calculation.
    
    Parameters
    ----------
    visit_type : str
        Base visit type (e.g., 'injection_visit', 'monitoring_visit')
    phase : str
        Current treatment phase
    actions : List[str]
        Actions performed during the visit
        
    Returns
    -------
    str
        Visit subtype for cost lookup
    """
    # Normalize actions for comparison
    actions_lower = [a.lower() for a in actions]
    
    # Injection visits
    if visit_type == 'injection_visit' or 'injection' in actions_lower:
        if phase == 'loading':
            return 'injection_loading'
        elif 'virtual_review' in actions_lower:
            return 'injection_virtual'
        else:
            return 'injection_face_to_face'
    
    # Monitoring visits
    elif visit_type == 'monitoring_visit' or visit_type == 'monitoring':
        if 'face_to_face_review' in actions_lower or 'f2f_review' in actions_lower:
            return 'monitoring_face_to_face'
        elif 'virtual_review' in actions_lower:
            return 'monitoring_virtual'
        else:
            # Default monitoring is virtual in modern protocols
            return 'monitoring_virtual'
    
    # Initial visit
    elif visit_type == 'initial_visit':
        return 'initial_assessment'
    
    # Default fallback
    return visit_type


def enhance_patient_history(patient_history: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enhance all visits in a patient history with cost metadata.
    
    Parameters
    ----------
    patient_history : Dict[str, Any]
        Patient history containing visits
        
    Returns
    -------
    Dict[str, Any]
        Enhanced patient history with metadata in all visits
    """
    enhanced_history = patient_history.copy()
    
    visits = enhanced_history.get('visits', [])
    if not visits:
        return enhanced_history
    
    # Enhance each visit
    enhanced_visits = []
    previous_visit = None
    
    for i, visit in enumerate(visits):
        # Get any additional data that might be stored separately
        visit_data = {}
        if 'drug' in patient_history:
            visit_data['drug'] = patient_history['drug']
        
        # Enhance the visit
        enhanced_visit = enhance_visit_with_cost_metadata(
            visit=visit,
            visit_data=visit_data,
            previous_visit=previous_visit,
            visit_number=i + 1
        )
        
        enhanced_visits.append(enhanced_visit)
        previous_visit = enhanced_visit
    
    enhanced_history['visits'] = enhanced_visits
    return enhanced_history