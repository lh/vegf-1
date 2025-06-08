"""
Cost analyzer module for V2 economic analysis.

This module analyzes V2 patient visits and calculates associated costs.
Native V2 support with no backward compatibility requirements.
"""

from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from datetime import datetime
from .cost_config import CostConfig


@dataclass
class CostEvent:
    """Represents a single cost event in the simulation."""
    
    date: datetime  # V2 uses datetime, not float
    patient_id: str
    event_type: str  # 'visit', 'drug', 'special'
    category: str    # specific drug/visit type
    amount: float
    components: Dict[str, float] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


class CostAnalyzerV2:
    """Analyzes V2 patient data and calculates costs."""
    
    def __init__(self, cost_config: CostConfig):
        """
        Initialize analyzer with cost configuration.
        
        Args:
            cost_config: Configuration containing cost data
        """
        self.config = cost_config
        
    def analyze_visit(self, visit: Dict[str, Any]) -> Optional[CostEvent]:
        """
        Analyze a single V2 visit and return cost event.
        
        Args:
            visit: V2 visit data dictionary with 'date', 'disease_state', etc.
            
        Returns:
            CostEvent if visit has costs, None otherwise
        """
        # Extract V2 fields
        visit_date = visit.get('date')
        if not visit_date:
            return None
            
        # Handle V2 disease state enum
        disease_state = visit.get('disease_state')
        if hasattr(disease_state, 'name'):
            disease_state_str = disease_state.name.lower()
        else:
            disease_state_str = str(disease_state).lower() if disease_state else 'unknown'
        
        # Determine visit components from metadata
        metadata = visit.get('metadata', {})
        components = self._determine_components(visit, metadata)
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
        if visit.get('treatment_given') or 'injection' in components:
            drug_name = metadata.get('drug', 'eylea_2mg')  # Default drug
            drug_cost = self.config.get_drug_cost(drug_name)
            
        total_cost = visit_cost + drug_cost
        
        return CostEvent(
            date=visit_date,
            patient_id=visit.get('patient_id', 'unknown'),
            event_type='visit',
            category=metadata.get('visit_subtype', 'regular_visit'),
            amount=total_cost,
            components=component_costs,
            metadata={
                'drug_cost': drug_cost,
                'visit_cost': visit_cost,
                'phase': metadata.get('phase', 'unknown'),
                'disease_state': disease_state_str,
                'treatment_given': visit.get('treatment_given', False)
            }
        )
    
    def _determine_components(self, visit: Dict[str, Any], metadata: Dict[str, Any]) -> List[str]:
        """
        Determine visit components for V2 visits.
        
        Args:
            visit: V2 visit data
            metadata: Visit metadata
            
        Returns:
            List of component names
        """
        # Priority 1: Check for explicit components_performed
        if 'components_performed' in metadata:
            return metadata['components_performed']
            
        # Priority 2: Check for visit subtype in metadata
        if 'visit_subtype' in metadata:
            visit_subtype = metadata['visit_subtype']
            if visit_subtype in self.config.visit_types:
                return self.config.visit_types[visit_subtype]['components']
                
        # Priority 3: Build from V2 visit data
        components = []
        
        # All visits have basic monitoring
        components.extend(['vision_test', 'oct_scan'])
        
        # Add injection if treatment given
        if visit.get('treatment_given'):
            components.append('injection')
            
        # Add additional components based on phase
        phase = metadata.get('phase', 'maintenance')
        if phase == 'loading':
            # Loading phase is simpler
            pass
        else:
            # Maintenance phase may have additional monitoring
            if not visit.get('treatment_given'):
                components.append('virtual_review')
                
        return components
    
    def analyze_patient(self, patient: 'Patient') -> List[CostEvent]:
        """
        Analyze V2 Patient object directly.
        
        Args:
            patient: V2 Patient object with visit_history
            
        Returns:
            List of CostEvent objects
        """
        cost_events = []
        
        # Process each visit in patient's history
        for visit in patient.visit_history:
            # Ensure patient_id is in visit data
            if 'patient_id' not in visit:
                visit = visit.copy()
                visit['patient_id'] = patient.id
                
            cost_event = self.analyze_visit(visit)
            if cost_event:
                # Ensure patient_id matches
                cost_event.patient_id = patient.id
                cost_events.append(cost_event)
                
        # Add special events if patient was discontinued
        if patient.is_discontinued and patient.discontinuation_date:
            # Add discontinuation administrative cost
            disc_event = CostEvent(
                date=patient.discontinuation_date,
                patient_id=patient.id,
                event_type='special',
                category='discontinuation_admin',
                amount=self.config.special_events.get('discontinuation_admin', 50.0),
                components={'admin': self.config.special_events.get('discontinuation_admin', 50.0)},
                metadata={
                    'discontinuation_type': patient.discontinuation_type,
                    'reason': patient.discontinuation_reason
                }
            )
            cost_events.append(disc_event)
        
        return cost_events
    
    def analyze_simulation_results(self, results: 'SimulationResults') -> List[CostEvent]:
        """
        Analyze V2 SimulationResults directly.
        
        Args:
            results: V2 SimulationResults object
            
        Returns:
            List of all CostEvent objects
        """
        all_events = []
        
        for patient_id, patient in results.patient_histories.items():
            patient_events = self.analyze_patient(patient)
            all_events.extend(patient_events)
            
        return all_events