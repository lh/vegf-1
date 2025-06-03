"""
Enhanced PatientState with cost metadata support.

This module extends the PatientState class to include cost-relevant metadata
in visit records for economic analysis.
"""

from typing import Dict, List, Any
from datetime import datetime
from simulation.patient_state import PatientState


class EnhancedPatientState(PatientState):
    """PatientState with enhanced visit metadata for cost tracking."""
    
    def _record_visit(self, visit_time: datetime, actions: List[str],
                     visit_data: Dict[str, Any]):
        """
        Record visit details with enhanced metadata for cost analysis.
        
        This method extends the base _record_visit to include cost-relevant
        metadata while maintaining backward compatibility.
        """
        # First, call the parent method to ensure all standard fields are set
        super()._record_visit(visit_time, actions, visit_data)
        
        # Get the visit that was just recorded
        visit = self.state['visit_history'][-1]
        
        # Add cost metadata
        metadata = {}
        
        # 1. Components performed - map actions to cost components
        components = self._map_actions_to_components(actions)
        if components:
            metadata['components_performed'] = components
        
        # 2. Visit subtype - determine based on phase and visit type
        visit_subtype = self._determine_visit_subtype(
            visit_data.get('visit_type', 'regular_visit'),
            self.state.get('current_phase', 'loading'),
            actions
        )
        if visit_subtype:
            metadata['visit_subtype'] = visit_subtype
        
        # 3. Drug information for injection visits
        if 'injection' in actions and 'drug' in visit_data:
            metadata['drug'] = visit_data['drug']
        
        # 4. Special events
        if 'special_event' in visit_data:
            metadata['special_event'] = visit_data['special_event']
        
        # 5. Visit number
        metadata['visit_number'] = self.state.get('visit_count', len(self.state['visit_history']))
        
        # 6. Days since last visit
        if len(self.state['visit_history']) > 1:
            previous_visit = self.state['visit_history'][-2]
            days_since = (visit_time - previous_visit['date']).days
            metadata['days_since_last'] = days_since
        else:
            metadata['days_since_last'] = 0
        
        # 7. Phase (include in metadata for easier access)
        metadata['phase'] = self.state.get('current_phase', 'loading')
        
        # Add metadata to the visit record
        visit['metadata'] = metadata
    
    def _map_actions_to_components(self, actions: List[str]) -> List[str]:
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
            'visual_acuity_test': 'visual_acuity_test',
            'pressure_check': 'pressure_check',
            'virtual_review': 'virtual_review',
            'face_to_face_review': 'face_to_face_review',
            'initial_assessment': 'initial_assessment',
            'adverse_event_assessment': 'adverse_event_assessment',
            'fluorescein_angiography': 'fluorescein_angiography'
        }
        
        components = []
        for action in actions:
            if action in action_to_component:
                components.append(action_to_component[action])
        
        return components
    
    def _determine_visit_subtype(self, visit_type: str, phase: str, 
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
        # Injection visits
        if visit_type == 'injection_visit' or 'injection' in actions:
            if phase == 'loading':
                return 'injection_loading'
            elif 'virtual_review' in actions:
                return 'injection_virtual'
            else:
                return 'injection_face_to_face'
        
        # Monitoring visits
        elif visit_type == 'monitoring_visit':
            if 'face_to_face_review' in actions:
                return 'monitoring_face_to_face'
            elif 'virtual_review' in actions:
                return 'monitoring_virtual'
            else:
                # Default monitoring is virtual in modern protocols
                return 'monitoring_virtual'
        
        # Initial visit
        elif visit_type == 'initial_visit':
            return 'initial_assessment'
        
        # Default fallback
        return visit_type