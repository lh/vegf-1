"""
Cost metadata enhancer for PatientState visits.

This module provides a function that can be attached to PatientState instances
to automatically add cost-relevant metadata to visits as they are recorded.

DEPRECATED: This module is for V1 simulations only. For simulation_v2, use
simulation_v2.economics.cost_enhancer.create_v2_cost_enhancer() instead.
"""

import warnings

from typing import Dict, Any, List
from datetime import datetime


def create_cost_metadata_enhancer():
    """
    Create a metadata enhancer function for cost tracking.
    
    This function returns a callable that can be attached to PatientState
    instances as the visit_metadata_enhancer attribute.
    
    DEPRECATED: Use simulation_v2.economics.cost_enhancer.create_v2_cost_enhancer()
    for V2 simulations.
    
    Returns:
    --------
    function
        A function that enhances visit records with cost metadata
    """
    warnings.warn(
        "create_cost_metadata_enhancer is deprecated for V1 simulations only. "
        "For simulation_v2, use simulation_v2.economics.cost_enhancer.create_v2_cost_enhancer() instead.",
        DeprecationWarning,
        stacklevel=2
    )
    
    def enhance_visit_for_costs(visit_record: Dict[str, Any], 
                               visit_data: Dict[str, Any],
                               patient_state: Any) -> Dict[str, Any]:
        """
        Enhance a visit record with cost-relevant metadata.
        
        This function is called by PatientState._record_visit to add
        metadata needed for cost analysis.
        
        Parameters:
        -----------
        visit_record : Dict[str, Any]
            The visit record being created
        visit_data : Dict[str, Any]
            Additional visit data passed to _record_visit
        patient_state : PatientState
            The patient state instance
            
        Returns:
        --------
        Dict[str, Any]
            Enhanced visit record with metadata
        """
        # Initialize metadata if not present
        if 'metadata' not in visit_record:
            visit_record['metadata'] = {}
        
        metadata = visit_record['metadata']
        
        # 1. Map actions to cost components
        if 'actions' in visit_record:
            components = _map_actions_to_components(visit_record['actions'])
            if components:
                metadata['components_performed'] = components
        
        # 2. Determine visit subtype
        visit_type = visit_record.get('type', 'regular_visit')
        phase = visit_record.get('phase', patient_state.state.get('current_phase', 'loading'))
        actions = visit_record.get('actions', [])
        
        visit_subtype = _determine_visit_subtype(visit_type, phase, actions)
        if visit_subtype:
            metadata['visit_subtype'] = visit_subtype
        
        # 3. Drug information for injection visits
        if 'injection' in actions:
            # Check visit_data first, then visit_record, then patient state
            if 'drug' in visit_data:
                metadata['drug'] = visit_data['drug']
            elif 'drug' in visit_record:
                metadata['drug'] = visit_record['drug']
            elif hasattr(patient_state, 'drug') and patient_state.drug:
                metadata['drug'] = patient_state.drug
        
        # 4. Special events
        if 'special_event' in visit_data:
            metadata['special_event'] = visit_data['special_event']
        
        # 5. Visit number
        visit_count = len(patient_state.state.get('visit_history', [])) + 1
        metadata['visit_number'] = visit_count
        
        # 6. Days since last visit
        if patient_state.state.get('visit_history'):
            last_visit = patient_state.state['visit_history'][-1]
            if 'date' in last_visit and 'date' in visit_record:
                current_date = visit_record['date']
                previous_date = last_visit['date']
                
                if isinstance(current_date, datetime) and isinstance(previous_date, datetime):
                    days_since = (current_date - previous_date).days
                    metadata['days_since_last'] = days_since
                else:
                    metadata['days_since_last'] = 0
        else:
            metadata['days_since_last'] = 0
        
        # 7. Include phase in metadata for easier access
        metadata['phase'] = phase
        
        # 8. Treatment interval if available
        if 'interval' in visit_record:
            metadata['interval_weeks'] = visit_record['interval']
        elif hasattr(patient_state, 'disease_activity') and patient_state.disease_activity:
            metadata['interval_weeks'] = patient_state.disease_activity.get('current_interval')
        
        return visit_record
    
    return enhance_visit_for_costs


def _map_actions_to_components(actions: List[str]) -> List[str]:
    """
    Map simulation actions to cost components.
    
    Parameters:
    -----------
    actions : List[str]
        Actions performed during the visit
        
    Returns:
    --------
    List[str]
        Cost components corresponding to the actions
    """
    # Mapping from simulation actions to cost components
    action_to_component = {
        'injection': 'injection',
        'oct_scan': 'oct_scan',
        'oct': 'oct_scan',
        'visual_acuity_test': 'visual_acuity_test',
        'vision_test': 'visual_acuity_test',
        'va_test': 'visual_acuity_test',
        'pressure_check': 'pressure_check',
        'iop_check': 'pressure_check',
        'virtual_review': 'virtual_review',
        'face_to_face_review': 'face_to_face_review',
        'f2f_review': 'face_to_face_review',
        'initial_assessment': 'initial_assessment',
        'adverse_event_assessment': 'adverse_event_assessment',
        'fluorescein_angiography': 'fluorescein_angiography',
        'fa': 'fluorescein_angiography'
    }
    
    components = []
    seen = set()  # To avoid duplicates
    
    for action in actions:
        # Normalize action name
        action_lower = action.lower().replace('-', '_').replace(' ', '_')
        if action_lower in action_to_component:
            component = action_to_component[action_lower]
            if component not in seen:
                components.append(component)
                seen.add(component)
    
    return components


def _determine_visit_subtype(visit_type: str, phase: str, actions: List[str]) -> str:
    """
    Determine the specific visit subtype for cost calculation.
    
    Parameters:
    -----------
    visit_type : str
        Base visit type
    phase : str
        Current treatment phase
    actions : List[str]
        Actions performed
        
    Returns:
    --------
    str
        Visit subtype for cost lookup
    """
    # Normalize actions for comparison
    actions_lower = [a.lower() for a in actions]
    
    # Injection visits (specific type)
    if visit_type == 'injection_visit':
        if phase == 'loading':
            return 'injection_loading'
        elif 'virtual_review' in actions_lower:
            return 'injection_virtual'
        else:
            # Default injection is face-to-face in most protocols
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
    elif visit_type == 'initial_visit' or 'initial' in visit_type:
        return 'initial_assessment'
    
    # Regular visits - need to infer from actions
    elif visit_type == 'regular_visit':
        if 'injection' in actions_lower:
            if phase == 'loading':
                return 'injection_loading'
            elif 'virtual_review' in actions_lower:
                return 'injection_virtual'
            else:
                # For regular visits without explicit review type, default to virtual
                return 'injection_virtual'
        else:
            return 'monitoring_virtual'  # Default for non-injection visits
    
    # Default fallback
    return visit_type