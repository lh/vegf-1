"""
Enhanced ABS engine with cost tracking support.

This extends the V2 ABS engine to include cost metadata enhancement
for economic analysis while maintaining all V2 discontinuation features.
"""

from typing import Dict, List, Optional, Callable, Any
from datetime import datetime

from simulation_v2.core.patient import Patient
from simulation_v2.core.disease_model import DiseaseModel
from simulation_v2.core.protocol import Protocol
from simulation_v2.core.discontinuation_profile import DiscontinuationProfile

from .abs_engine_v2 import ABSEngineV2


class ABSEngineWithCosts(ABSEngineV2):
    """
    Enhanced ABS engine with cost tracking integration.
    
    Extends V2 ABS engine to support cost metadata enhancement
    while maintaining all discontinuation and clinical features.
    """
    
    def __init__(
        self,
        disease_model: DiseaseModel,
        protocol: Protocol,
        n_patients: int,
        seed: Optional[int] = None,
        discontinuation_profile: Optional[DiscontinuationProfile] = None,
        visit_metadata_enhancer: Optional[Callable] = None
    ):
        """
        Initialize ABS engine with cost tracking support.
        
        Args:
            disease_model: Disease state transition model
            protocol: Treatment protocol
            n_patients: Number of patients to simulate
            seed: Random seed for reproducibility
            discontinuation_profile: Profile for discontinuation behavior
            visit_metadata_enhancer: Function to enhance visit metadata for costs
        """
        super().__init__(disease_model, protocol, n_patients, seed, discontinuation_profile)
        
        # Store the metadata enhancer
        self.visit_metadata_enhancer = visit_metadata_enhancer
        
        # Add enhancer to all patients
        if self.visit_metadata_enhancer:
            for patient in self.patients.values():
                patient.visit_metadata_enhancer = self.visit_metadata_enhancer
    
    def _process_treatment_visit(
        self, 
        patient: Patient, 
        current_date: datetime
    ) -> bool:
        """
        Process a regular treatment visit with cost metadata enhancement.
        
        Args:
            patient: Patient to process
            current_date: Current simulation date
            
        Returns:
            Whether injection was given
        """
        # Disease progression
        new_state = self.disease_model.progress(
            patient.current_state,
            days_since_injection=patient.days_since_last_injection_at(current_date)
        )
        
        # Treatment decision
        should_treat = self.protocol.should_treat(patient, current_date)
        
        # Vision change
        vision_change = self._calculate_vision_change(
            patient.current_state,
            new_state,
            should_treat
        )
        new_vision = max(0, min(100, patient.current_vision + vision_change))
        
        # Prepare visit data for enhancement
        visit_data = {
            'date': current_date,
            'disease_state': new_state,
            'treatment_given': should_treat,
            'vision': new_vision,
            'visit_number': len(patient.visit_history) + 1,
            'protocol_name': self.protocol.name if hasattr(self.protocol, 'name') else 'Unknown'
        }
        
        # Record visit with enhanced metadata
        self._record_enhanced_visit(patient, visit_data, current_date, new_state, should_treat, new_vision)
        
        return should_treat
    
    def _process_monitoring_visit(
        self,
        patient: Patient,
        current_date: datetime
    ) -> None:
        """
        Process a monitoring visit with cost metadata enhancement.
        
        Args:
            patient: Patient to monitor
            current_date: Current simulation date
        """
        # Disease can still progress
        new_state = self.disease_model.progress(
            patient.current_state,
            days_since_injection=patient.days_since_last_injection_at(current_date)
        )
        
        # Vision typically declines without treatment
        vision_change = self._calculate_vision_change(
            patient.current_state,
            new_state,
            treated=False
        )
        new_vision = max(0, min(100, patient.current_vision + vision_change))
        
        # Prepare visit data for enhancement
        visit_data = {
            'date': current_date,
            'disease_state': new_state,
            'treatment_given': False,
            'vision': new_vision,
            'visit_number': len(patient.visit_history) + 1,
            'is_monitoring': True,
            'protocol_name': self.protocol.name if hasattr(self.protocol, 'name') else 'Unknown'
        }
        
        # Record monitoring visit with enhanced metadata
        self._record_enhanced_visit(patient, visit_data, current_date, new_state, False, new_vision)
        
        # Check for retreatment
        from simulation_v2.core.disease_model import DiseaseState
        has_fluid = (new_state in [DiseaseState.ACTIVE, DiseaseState.HIGHLY_ACTIVE])
        should_retreat, retreat_reason = self.discontinuation_manager.evaluate_retreatment(
            patient, has_fluid, current_date
        )
        
        if should_retreat:
            patient.restart_treatment(current_date)
    
    def _record_enhanced_visit(
        self,
        patient: Patient,
        visit_data: Dict[str, Any],
        date: datetime,
        disease_state: 'DiseaseState',
        treatment_given: bool,
        vision: int
    ) -> None:
        """
        Record visit with metadata enhancement support.
        
        Args:
            patient: Patient object
            visit_data: Visit data for enhancement
            date: Visit date
            disease_state: Current disease state
            treatment_given: Whether treatment was given
            vision: Current vision
        """
        # Create base visit record
        visit_record = {
            'date': date,
            'disease_state': disease_state,
            'treatment_given': treatment_given,
            'vision': vision
        }
        
        # Apply metadata enhancement if available
        if self.visit_metadata_enhancer:
            # Create enhanced record
            enhanced_record = self.visit_metadata_enhancer(visit_record.copy(), visit_data, patient)
            
            # Update patient's visit history with enhanced record
            patient.visit_history.append(enhanced_record)
            
            # Update patient state
            patient.current_state = disease_state
            patient.current_vision = vision
            
            # Update first visit date if needed
            if patient.first_visit_date is None:
                patient.first_visit_date = date
            
            # Update injection tracking
            if treatment_given:
                patient.injection_count += 1
                patient._last_injection_date = date
        else:
            # Fall back to standard recording
            patient.record_visit(date, disease_state, treatment_given, vision)