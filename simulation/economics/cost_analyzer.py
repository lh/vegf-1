"""
Cost analyzer module for economic analysis.

This module analyzes patient visits and calculates associated costs.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from .cost_config import CostConfig
from .visit_enhancer import enhance_visit_with_cost_metadata


@dataclass
class CostEvent:
    """Represents a single cost event in the simulation."""
    
    time: float
    patient_id: str
    event_type: str  # 'visit', 'drug', 'special'
    category: str    # specific drug/visit type
    amount: float
    components: Dict[str, float] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


class CostAnalyzer:
    """Analyzes patient histories and calculates costs."""
    
    def __init__(self, cost_config: CostConfig):
        """
        Initialize analyzer with cost configuration.
        
        Args:
            cost_config: Configuration containing cost data
        """
        self.config = cost_config
        
    def analyze_visit(self, visit: Dict[str, Any]) -> Optional[CostEvent]:
        """
        Analyze a single visit and return cost event.
        
        Args:
            visit: Visit data dictionary
            
        Returns:
            CostEvent if visit has costs, None otherwise
        """
        # Enhance visit with metadata if not present
        if 'metadata' not in visit or not visit.get('metadata'):
            visit = enhance_visit_with_cost_metadata(visit)
        
        # Determine visit components
        components = self._determine_components(visit)
        if not components:
            return None
            
        # Calculate component costs
        component_costs = {}
        visit_cost = 0.0
        
        for component in components:
            cost = self.config.visit_components.get(component, 0.0)
            component_costs[component] = cost
            visit_cost += cost
            
        # Add drug cost if this is an injection
        drug_cost = 0.0
        if 'injection' in components and 'drug' in visit:
            drug_cost = self.config.get_drug_cost(visit['drug'])
            
        total_cost = visit_cost + drug_cost
        
        # Extract metadata
        metadata = visit.get('metadata', {})
        
        return CostEvent(
            time=visit['time'],
            patient_id=visit.get('patient_id', 'unknown'),
            event_type='visit',
            category=metadata.get('visit_subtype', visit.get('type', 'unknown')),
            amount=total_cost,
            components=component_costs,
            metadata={
                'drug_cost': drug_cost,
                'visit_cost': visit_cost,
                'phase': metadata.get('phase', 'unknown')
            }
        )
    
    def _determine_components(self, visit: Dict[str, Any]) -> List[str]:
        """
        Determine visit components from metadata or inference.
        
        Args:
            visit: Visit data
            
        Returns:
            List of component names
        """
        metadata = visit.get('metadata', {})
        
        # Priority 1: Check for explicit components_performed
        if 'components_performed' in metadata:
            return metadata['components_performed']
            
        # Priority 2: Check for visit subtype
        if 'visit_subtype' in metadata:
            visit_subtype = metadata['visit_subtype']
            if visit_subtype in self.config.visit_types:
                return self.config.visit_types[visit_subtype]['components']
                
        # Priority 3: Fallback to inference based on visit type and phase
        return self._infer_components(visit)
    
    def _infer_components(self, visit: Dict[str, Any]) -> List[str]:
        """
        Infer components from visit type and context.
        
        Args:
            visit: Visit data
            
        Returns:
            List of inferred component names
        """
        visit_type = visit.get('type', '')
        phase = visit.get('metadata', {}).get('phase', '')
        
        # Inference rules based on visit type and phase
        if visit_type == 'injection':
            if phase == 'loading':
                # Loading phase: simpler visits
                return ['injection', 'visual_acuity_test']
            else:
                # Maintenance phase: comprehensive monitoring
                return ['injection', 'oct_scan', 'pressure_check', 'virtual_review']
                
        elif visit_type == 'monitoring':
            # Default monitoring components
            return ['oct_scan', 'visual_acuity_test', 'virtual_review']
            
        # Unknown visit type
        return []
    
    def analyze_patient_history(self, patient_history: Dict[str, Any]) -> List[CostEvent]:
        """
        Analyze complete patient history and return all cost events.
        
        Args:
            patient_history: Dictionary containing patient_id and visits
            
        Returns:
            List of CostEvent objects
        """
        cost_events = []
        patient_id = patient_history.get('patient_id', 'unknown')
        
        # Process each visit
        for visit in patient_history.get('visits', []):
            # Ensure patient_id is in visit data
            if 'patient_id' not in visit:
                visit['patient_id'] = patient_id
                
            cost_event = self.analyze_visit(visit)
            if cost_event:
                # Ensure patient_id matches
                cost_event.patient_id = patient_id
                cost_events.append(cost_event)
                
        # TODO: Add special events (e.g., initial assessment, discontinuation)
        # This will be implemented when we have more details about special events
        
        return cost_events