"""
Cost tracker module for economic analysis.

This module tracks and aggregates costs across patients and exports data for analysis.
"""

from typing import Dict, List, Any, Optional
import pandas as pd
from pathlib import Path
from .cost_analyzer import CostAnalyzer, CostEvent


class CostTracker:
    """Tracks and aggregates costs across patients."""
    
    def __init__(self, analyzer: CostAnalyzer):
        """
        Initialize tracker with a cost analyzer.
        
        Args:
            analyzer: CostAnalyzer instance for processing visits
        """
        self.analyzer = analyzer
        self.cost_events: List[CostEvent] = []
        
    def process_simulation_results(self, results: Dict[str, Any]) -> None:
        """
        Process simulation results and extract all costs.
        
        Args:
            results: Simulation results containing patient_histories
        """
        patient_histories = results.get('patient_histories', {})
        
        for patient_id, history in patient_histories.items():
            # Ensure patient_id is in the history
            if isinstance(history, dict) and 'patient_id' not in history:
                history['patient_id'] = patient_id
                
            # Process the patient history
            events = self.analyzer.analyze_patient_history(history)
            self.cost_events.extend(events)
            
    def get_patient_costs(self, patient_id: str) -> pd.DataFrame:
        """
        Get all costs for a specific patient.
        
        Args:
            patient_id: ID of the patient
            
        Returns:
            DataFrame with cost events for the patient
        """
        patient_events = [e for e in self.cost_events if e.patient_id == patient_id]
        
        if not patient_events:
            # Return empty DataFrame with expected columns
            return pd.DataFrame(columns=[
                'time', 'event_type', 'category', 'amount',
                'drug_cost', 'visit_cost', 'phase'
            ])
            
        # Convert events to DataFrame
        data = []
        for event in patient_events:
            row = {
                'time': event.time,
                'event_type': event.event_type,
                'category': event.category,
                'amount': event.amount,
                'drug_cost': event.metadata.get('drug_cost', 0),
                'visit_cost': event.metadata.get('visit_cost', 0),
                'phase': event.metadata.get('phase', 'unknown')
            }
            data.append(row)
            
        return pd.DataFrame(data)
        
    def get_summary_statistics(self) -> Dict[str, Any]:
        """
        Calculate summary statistics across all patients.
        
        Returns:
            Dictionary containing summary statistics
        """
        if not self.cost_events:
            return {}
            
        # Convert events to DataFrame for easier analysis
        df = pd.DataFrame([
            {
                'patient_id': e.patient_id,
                'time': e.time,
                'amount': e.amount,
                'event_type': e.event_type,
                'category': e.category
            }
            for e in self.cost_events
        ])
        
        # Calculate patient-level costs
        patient_costs = df.groupby('patient_id')['amount'].sum()
        
        # Build summary statistics
        summary = {
            'total_patients': df['patient_id'].nunique(),
            'total_cost': df['amount'].sum(),
            'avg_cost_per_patient': patient_costs.mean(),
            'cost_by_type': df.groupby('event_type')['amount'].sum().to_dict(),
            'cost_by_category': df.groupby('category')['amount'].sum().to_dict()
        }
        
        return summary
        
    def export_to_parquet(self, output_path: Path) -> None:
        """
        Export cost data to Parquet format for Streamlit.
        
        Args:
            output_path: Directory to save Parquet files
        """
        if not self.cost_events:
            return
            
        # Create detailed event dataframe
        events_data = []
        for event in self.cost_events:
            row = {
                'patient_id': event.patient_id,
                'time': event.time,
                'event_type': event.event_type,
                'category': event.category,
                'amount': event.amount,
                'drug_cost': event.metadata.get('drug_cost', 0),
                'visit_cost': event.metadata.get('visit_cost', 0),
                'phase': event.metadata.get('phase', 'unknown')
            }
            
            # Add component costs as separate columns
            for component_name, component_cost in event.components.items():
                row[f'component_{component_name}'] = component_cost
                
            events_data.append(row)
            
        events_df = pd.DataFrame(events_data)
        
        # Save detailed events
        events_df.to_parquet(output_path / 'cost_events.parquet', index=False)
        
        # Create patient summary
        patient_summary = events_df.groupby('patient_id').agg({
            'amount': ['sum', 'mean', 'count'],
            'drug_cost': 'sum',
            'visit_cost': 'sum'
        }).reset_index()
        
        # Flatten column names
        patient_summary.columns = [
            'patient_id', 'total_cost', 'avg_cost_per_event',
            'num_events', 'total_drug_cost', 'total_visit_cost'
        ]
        
        # Save patient summary
        patient_summary.to_parquet(output_path / 'cost_summary.parquet', index=False)