"""
Cost metadata enhancer for V2 simulations.

Provides functions to enhance visit records with cost-relevant metadata.
"""

from typing import Dict, Any, Callable, Optional, List


def create_v2_cost_enhancer(cost_config: Optional['CostConfig'] = None,
                           protocol_name: str = "Unknown") -> Callable:
    """
    Create a cost metadata enhancer for V2 simulations.
    
    This function returns a callable that enhances visit records with
    cost-relevant metadata for V2 Patient instances.
    
    Args:
        cost_config: Optional cost configuration for drug information
        protocol_name: Name of the protocol being used
        
    Returns:
        Function that enhances visit records with cost metadata
    """
    
    def enhance_visit(visit: Dict[str, Any], patient: 'Patient') -> Dict[str, Any]:
        """
        Enhance a V2 visit record with cost-relevant metadata.
        
        Args:
            visit: The visit record being created
            patient: The V2 patient instance
            
        Returns:
            Enhanced visit record with metadata
        """
        # Create a copy to avoid modifying the original
        enhanced_visit = visit.copy()
        
        # Initialize metadata if not present
        if 'metadata' not in enhanced_visit:
            enhanced_visit['metadata'] = {}
        
        metadata = enhanced_visit['metadata']
        
        # 1. Determine visit phase based on visit number
        visit_number = len(patient.visit_history) + 1  # +1 because this visit isn't added yet
        phase = 'loading' if visit_number <= 3 else 'maintenance'
        metadata['phase'] = phase
        metadata['visit_number'] = visit_number
        
        # 2. Map treatment to cost components
        components = []
        
        # All visits have basic monitoring
        components.extend(['vision_test', 'oct_scan'])
        
        # Add injection if treatment given
        if visit.get('treatment_given', False):
            components.append('injection')
        
        # Additional components based on phase and context
        if phase == 'loading':
            # Loading phase visits are simpler
            pass
        else:
            # Maintenance phase may have additional monitoring
            if not visit.get('treatment_given', False):
                # Monitoring visit without injection
                components.append('virtual_review')
            else:
                # Injection visit might include pressure check
                components.append('pressure_check')
        
        # Special handling for monitoring visits
        if patient.is_discontinued and not visit.get('treatment_given', False):
            # Post-discontinuation monitoring
            components = ['vision_test', 'oct_scan', 'fundus_photography']
            metadata['is_monitoring'] = True
        
        metadata['components_performed'] = components
        
        # 3. Determine visit subtype
        if patient.is_discontinued:
            visit_subtype = f"{phase}_monitoring_visit"
        elif visit.get('treatment_given', False):
            visit_subtype = f"{phase}_injection_visit"
        else:
            visit_subtype = f"{phase}_monitoring_visit"
            
        metadata['visit_subtype'] = visit_subtype
        
        # 4. Drug information for injection visits
        if visit.get('treatment_given', False):
            # Determine drug from protocol name
            if 'eylea' in protocol_name.lower():
                if '8mg' in protocol_name.lower():
                    drug = 'eylea_8mg'
                else:
                    drug = 'eylea_2mg'  # Default Eylea
            elif 'avastin' in protocol_name.lower():
                drug = 'avastin'
            elif 'lucentis' in protocol_name.lower():
                drug = 'lucentis'
            else:
                drug = 'eylea_2mg'  # Default
            
            metadata['drug'] = drug
        
        # 5. Add disease state information as string
        disease_state = visit.get('disease_state')
        if disease_state and hasattr(disease_state, 'name'):
            metadata['disease_state'] = disease_state.name.lower()
        
        # 6. Add patient context
        metadata['baseline_vision'] = patient.baseline_vision
        metadata['vision_change'] = visit.get('vision', 0) - patient.baseline_vision
        
        # 7. Add discontinuation context if relevant
        if patient.is_discontinued:
            metadata['is_discontinued'] = True
            metadata['discontinuation_type'] = patient.discontinuation_type
            metadata['weeks_since_discontinuation'] = None
            if patient.discontinuation_date and visit.get('date'):
                days_since = (visit['date'] - patient.discontinuation_date).days
                metadata['weeks_since_discontinuation'] = days_since / 7.0
        
        # 8. Add interval information
        if hasattr(patient, 'current_interval_days'):
            metadata['interval_days'] = patient.current_interval_days
            metadata['interval_weeks'] = patient.current_interval_days / 7.0
        
        # 9. Add injection history
        metadata['total_injections_to_date'] = patient.injection_count
        if visit.get('treatment_given', False):
            metadata['total_injections_to_date'] += 1  # Include this injection
        
        return enhanced_visit
    
    return enhance_visit