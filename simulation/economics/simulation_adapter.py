"""
Adapter module for integrating cost tracking with existing simulations.

This module provides adapters and wrappers to add cost tracking capabilities
to existing ABS and DES simulations without modifying their core code.

DEPRECATED: This module is for V1 simulations only. For simulation_v2, use
simulation_v2.economics.EconomicsIntegration for cleaner integration.
"""

import warnings

from typing import Dict, List, Any, Optional
from datetime import datetime
from .visit_enhancer import enhance_visit_with_cost_metadata
from .cost_analyzer import CostAnalyzer
from .cost_tracker import CostTracker


class SimulationCostAdapter:
    """
    Adapter for adding cost tracking to simulation results.
    
    This adapter processes simulation results and enhances them with cost data
    without modifying the original simulation code.
    
    DEPRECATED: For V2 simulations, use simulation_v2.economics.EconomicsIntegration.
    """
    
    def __init__(self, cost_analyzer: CostAnalyzer):
        """
        Initialize adapter with a cost analyzer.
        
        Args:
            cost_analyzer: CostAnalyzer instance for calculating costs
        """
        warnings.warn(
            "SimulationCostAdapter is deprecated for V1 simulations only. "
            "For simulation_v2, use simulation_v2.economics.EconomicsIntegration.",
            DeprecationWarning,
            stacklevel=2
        )
        
        self.analyzer = cost_analyzer
        self.tracker = CostTracker(cost_analyzer)
    
    def process_simulation_results(self, simulation_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process simulation results and add cost data.
        
        This method:
        1. Enhances visit records with cost metadata
        2. Calculates costs for all visits
        3. Adds cost summary to results
        
        Args:
            simulation_results: Raw simulation results
            
        Returns:
            Enhanced results with cost data
        """
        # Create a copy to avoid modifying the original
        enhanced_results = simulation_results.copy()
        
        # Process patient histories
        if 'patient_histories' in enhanced_results:
            enhanced_histories = {}
            
            for patient_id, history in enhanced_results['patient_histories'].items():
                # Enhance the patient history
                enhanced_history = self._enhance_patient_history(history, patient_id)
                enhanced_histories[patient_id] = enhanced_history
            
            enhanced_results['patient_histories'] = enhanced_histories
        
        # Calculate costs using the tracker
        self.tracker.process_simulation_results(enhanced_results)
        
        # Add cost summary to results
        enhanced_results['cost_summary'] = self.tracker.get_summary_statistics()
        enhanced_results['cost_events'] = self._serialize_cost_events()
        
        return enhanced_results
    
    def _enhance_patient_history(self, history: Dict[str, Any], patient_id: str) -> Dict[str, Any]:
        """
        Enhance a single patient history with cost metadata.
        
        Args:
            history: Patient history data
            patient_id: Patient identifier
            
        Returns:
            Enhanced patient history
        """
        enhanced_history = history.copy()
        
        # Ensure patient_id is in the history
        if 'patient_id' not in enhanced_history:
            enhanced_history['patient_id'] = patient_id
        
        # Process visits if they exist
        if 'visits' in enhanced_history:
            enhanced_visits = []
            previous_visit = None
            
            for i, visit in enumerate(enhanced_history['visits']):
                # Prepare visit data for enhancement
                visit_data = {}
                
                # Extract drug information if present
                if 'drug' in visit:
                    visit_data['drug'] = visit['drug']
                elif 'injection' in visit.get('actions', []):
                    # Try to get drug from history level
                    if 'drug' in enhanced_history:
                        visit_data['drug'] = enhanced_history['drug']
                
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
        
        # Handle visit_history format (used by PatientState)
        elif 'visit_history' in enhanced_history:
            enhanced_visits = []
            previous_visit = None
            
            for i, visit in enumerate(enhanced_history['visit_history']):
                # Convert date to time if needed
                if 'date' in visit and 'time' not in visit:
                    if isinstance(visit['date'], datetime):
                        # Convert to months from start
                        visit['time'] = i  # Simple approximation
                
                # Prepare visit data
                visit_data = {}
                if 'drug' in visit:
                    visit_data['drug'] = visit['drug']
                
                # Enhance the visit
                enhanced_visit = enhance_visit_with_cost_metadata(
                    visit=visit,
                    visit_data=visit_data,
                    previous_visit=previous_visit,
                    visit_number=i + 1
                )
                
                enhanced_visits.append(enhanced_visit)
                previous_visit = enhanced_visit
            
            enhanced_history['visit_history'] = enhanced_visits
        
        return enhanced_history
    
    def _serialize_cost_events(self) -> List[Dict[str, Any]]:
        """
        Serialize cost events for storage/export.
        
        Returns:
            List of serialized cost event dictionaries
        """
        serialized_events = []
        
        for event in self.tracker.cost_events:
            serialized_event = {
                'time': event.time,
                'patient_id': event.patient_id,
                'event_type': event.event_type,
                'category': event.category,
                'amount': event.amount,
                'components': event.components,
                'metadata': event.metadata
            }
            serialized_events.append(serialized_event)
        
        return serialized_events
    
    def get_patient_cost_summary(self, patient_id: str) -> Dict[str, Any]:
        """
        Get cost summary for a specific patient.
        
        Args:
            patient_id: Patient identifier
            
        Returns:
            Dictionary with patient cost summary
        """
        patient_costs_df = self.tracker.get_patient_costs(patient_id)
        
        if patient_costs_df.empty:
            return {
                'total_cost': 0,
                'drug_costs': 0,
                'visit_costs': 0,
                'num_visits': 0,
                'avg_cost_per_visit': 0
            }
        
        return {
            'total_cost': patient_costs_df['amount'].sum(),
            'drug_costs': patient_costs_df['drug_cost'].sum(),
            'visit_costs': patient_costs_df['visit_cost'].sum(),
            'num_visits': len(patient_costs_df),
            'avg_cost_per_visit': patient_costs_df['amount'].mean()
        }