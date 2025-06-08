"""
Cost metadata enhancer for V2 simulation Patient visits.

This module provides a function that can be attached to V2 Patient instances
to automatically add cost-relevant metadata to visits as they are recorded.
"""

from typing import Dict, Any, List
from datetime import datetime


def create_cost_metadata_enhancer():
    """
    Create a metadata enhancer function for cost tracking in V2 simulations.
    
    This function returns a callable that enhances visit records with
    cost-relevant metadata for V2 Patient instances.
    
    Returns:
    --------
    function
        A function that enhances visit records with cost metadata
    """
    
    def enhance_visit_for_costs(visit_record: Dict[str, Any], 
                               visit_data: Dict[str, Any],
                               patient: Any) -> Dict[str, Any]:
        """
        Enhance a visit record with cost-relevant metadata for V2.
        
        This function adds metadata needed for cost analysis to V2 visits.
        
        Parameters:
        -----------
        visit_record : Dict[str, Any]
            The visit record being created
        visit_data : Dict[str, Any]
            Additional visit data with context
        patient : Patient
            The V2 patient instance
            
        Returns:
        --------
        Dict[str, Any]
            Enhanced visit record with metadata
        """
        # Initialize metadata if not present
        if 'metadata' not in visit_record:
            visit_record['metadata'] = {}
        
        metadata = visit_record['metadata']
        
        # 1. Determine visit phase based on visit number
        visit_number = visit_data.get('visit_number', len(patient.visit_history) + 1)
        phase = 'loading' if visit_number <= 3 else 'maintenance'
        metadata['phase'] = phase
        
        # 2. Map treatment to cost components
        components = []
        
        # All visits have vision test and OCT scan
        components.extend(['vision_test', 'oct_scan'])
        
        # Add injection if treatment given
        if visit_record.get('treatment_given', False):
            components.append('injection')
        
        # Monitoring visits might have additional imaging
        if visit_data.get('is_monitoring', False):
            components.append('fundus_photography')
        
        metadata['components_performed'] = components
        
        # 3. Determine visit subtype
        visit_type = 'regular_visit'
        if visit_data.get('is_monitoring', False):
            visit_type = 'monitoring_visit'
        elif patient.is_discontinued:
            visit_type = 'monitoring_visit'
        
        # Combine type and phase for subtype
        visit_subtype = f"{phase}_{visit_type}"
        metadata['visit_subtype'] = visit_subtype
        
        # 4. Drug information for injection visits
        if visit_record.get('treatment_given', False):
            # Get drug from protocol or default
            protocol_name = visit_data.get('protocol_name', 'Unknown')
            if 'eylea' in protocol_name.lower():
                if '8mg' in protocol_name.lower():
                    drug = 'eylea_8mg'
                else:
                    drug = 'eylea_2mg'  # Default Eylea
            else:
                drug = 'eylea_2mg'  # Default for now
            
            metadata['drug'] = drug
        
        # 5. Add disease state information
        disease_state = visit_record.get('disease_state')
        if disease_state:
            # Convert enum to string if needed
            if hasattr(disease_state, 'name'):
                metadata['disease_state'] = disease_state.name.lower()
            else:
                metadata['disease_state'] = str(disease_state).lower()
        
        # 6. Add discontinuation information if relevant
        if patient.is_discontinued:
            metadata['is_discontinued'] = True
            metadata['discontinuation_type'] = patient.discontinuation_type
        
        # 7. Add interval information if available
        if hasattr(patient, 'current_interval_days'):
            metadata['interval_days'] = patient.current_interval_days
        
        return visit_record
    
    return enhance_visit_for_costs


def _map_actions_to_components(actions: List[str]) -> List[str]:
    """
    Map simulation actions to cost components.
    
    Parameters:
    -----------
    actions : List[str]
        List of action names from simulation
        
    Returns:
    --------
    List[str]
        List of cost component names
    """
    # Direct mapping for most actions
    action_to_component = {
        'injection': 'injection',
        'vision_test': 'vision_test',
        'oct_scan': 'oct_scan',
        'fundus_photography': 'fundus_photography',
        'fluorescein_angiography': 'fluorescein_angiography',
        'consultation': 'consultation'
    }
    
    components = []
    for action in actions:
        if action in action_to_component:
            components.append(action_to_component[action])
    
    return components