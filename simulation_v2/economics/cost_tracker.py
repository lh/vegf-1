"""
Cost tracker module for V2 simulations.

Tracks and aggregates costs across patients with native V2 support.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import pandas as pd
from pathlib import Path
from collections import defaultdict

from .cost_analyzer import CostAnalyzerV2, CostEvent
from .financial_results import (
    FinancialResults, PatientCostSummary, CostBreakdown
)


class CostTrackerV2:
    """Tracks and aggregates costs for V2 simulations."""
    
    def __init__(self, analyzer: CostAnalyzerV2):
        """
        Initialize tracker with a V2 cost analyzer.
        
        Args:
            analyzer: V2 cost analyzer instance
        """
        self.analyzer = analyzer
        self.events: Dict[str, List[CostEvent]] = {}
        self._processed_results = None
        
    def process_v2_results(self, results: 'SimulationResults') -> None:
        """
        Process V2 simulation results directly.
        
        Args:
            results: V2 SimulationResults object
        """
        # Clear previous events
        self.events.clear()
        
        # Store reference to results for VA calculations
        self._processed_results = results
        
        # Process each patient
        for patient_id, patient in results.patient_histories.items():
            patient_events = self.analyzer.analyze_patient(patient)
            self.events[patient_id] = patient_events
            
    def get_financial_results(self, cost_config_name: str = "Unknown") -> FinancialResults:
        """
        Calculate comprehensive financial results.
        
        Args:
            cost_config_name: Name of the cost configuration used
            
        Returns:
            FinancialResults object with all metrics
        """
        if not self.events:
            # Return empty results
            return FinancialResults(
                total_cost=0.0,
                total_patients=0,
                cost_per_patient=0.0,
                total_injections=0,
                cost_per_injection=0.0,
                total_va_change=0.0,
                cost_per_letter_gained=None,
                cost_breakdown=CostBreakdown(),
                patient_costs={},
                cost_config_name=cost_config_name
            )
        
        # Calculate aggregates
        total_cost = 0.0
        total_patients = len(self.events)
        total_injections = 0
        
        # Breakdowns
        cost_by_type = defaultdict(float)
        cost_by_category = defaultdict(float)
        cost_by_phase = defaultdict(float)
        cost_by_component = defaultdict(float)
        
        # Patient summaries
        patient_costs = {}
        
        # Time series
        monthly_costs = defaultdict(float)
        
        for patient_id, events in self.events.items():
            patient_total = 0.0
            patient_visits = 0
            patient_injections = 0
            patient_drug_costs = 0.0
            patient_visit_costs = 0.0
            patient_special_costs = 0.0
            
            for event in events:
                # Update totals
                total_cost += event.amount
                patient_total += event.amount
                
                # Update breakdowns
                cost_by_type[event.event_type] += event.amount
                cost_by_category[event.category] += event.amount
                cost_by_phase[event.metadata.get('phase', 'unknown')] += event.amount
                
                # Component breakdown
                for component, cost in event.components.items():
                    cost_by_component[component] += cost
                
                # Track injections
                if event.metadata.get('treatment_given') or 'injection' in event.components:
                    total_injections += 1
                    patient_injections += 1
                
                # Patient-specific breakdowns
                if event.event_type == 'visit':
                    patient_visits += 1
                    patient_visit_costs += event.metadata.get('visit_cost', 0)
                    patient_drug_costs += event.metadata.get('drug_cost', 0)
                elif event.event_type == 'special':
                    patient_special_costs += event.amount
                
                # Time series (month from simulation start)
                if hasattr(event.date, 'timestamp'):
                    # Real datetime
                    start_date = datetime(2024, 1, 1)  # Default start
                    months_elapsed = (event.date.year - start_date.year) * 12 + event.date.month - start_date.month
                else:
                    # Assume days from start
                    months_elapsed = int(event.date / 30)
                
                monthly_costs[months_elapsed] += event.amount
            
            # Create patient summary
            patient_costs[patient_id] = PatientCostSummary(
                patient_id=patient_id,
                total_cost=patient_total,
                visit_costs=patient_visit_costs,
                drug_costs=patient_drug_costs,
                special_event_costs=patient_special_costs,
                injection_count=patient_injections,
                visit_count=patient_visits,
                cost_per_injection=patient_total / patient_injections if patient_injections > 0 else 0,
                cost_per_visit=patient_total / patient_visits if patient_visits > 0 else 0
            )
        
        # Calculate cumulative costs
        sorted_months = sorted(monthly_costs.keys())
        cumulative_costs = []
        cumulative_total = 0.0
        for month in sorted_months:
            cumulative_total += monthly_costs[month]
            cumulative_costs.append(cumulative_total)
        
        # Calculate VA change if we have results
        total_va_change = 0.0
        cost_per_letter_gained = None
        
        if self._processed_results and hasattr(self._processed_results, 'patient_histories'):
            # Calculate total VA change
            for patient in self._processed_results.patient_histories.values():
                if hasattr(patient, 'baseline_vision') and hasattr(patient, 'current_vision'):
                    total_va_change += (patient.current_vision - patient.baseline_vision)
            
            # Calculate cost per letter gained
            if total_va_change > 0:
                cost_per_letter_gained = total_cost / total_va_change
        
        # Create results
        return FinancialResults(
            total_cost=total_cost,
            total_patients=total_patients,
            cost_per_patient=total_cost / total_patients if total_patients > 0 else 0,
            total_injections=total_injections,
            cost_per_injection=total_cost / total_injections if total_injections > 0 else 0,
            total_va_change=total_va_change,
            cost_per_letter_gained=cost_per_letter_gained,
            cost_breakdown=CostBreakdown(
                by_type=dict(cost_by_type),
                by_category=dict(cost_by_category),
                by_phase=dict(cost_by_phase),
                by_component=dict(cost_by_component)
            ),
            patient_costs=patient_costs,
            monthly_costs=dict(monthly_costs),
            cumulative_costs=cumulative_costs,
            cost_config_name=cost_config_name
        )
    
    def export_to_parquet(self, output_path: Path) -> None:
        """
        Export cost data to Parquet for analysis.
        
        Args:
            output_path: Directory to save Parquet files
        """
        if not self.events:
            return
            
        # Create output directory
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Create events dataframe
        all_events = []
        for patient_id, events in self.events.items():
            for event in events:
                event_dict = {
                    'patient_id': patient_id,
                    'date': event.date,
                    'event_type': event.event_type,
                    'category': event.category,
                    'amount': event.amount,
                    'drug_cost': event.metadata.get('drug_cost', 0),
                    'visit_cost': event.metadata.get('visit_cost', 0),
                    'phase': event.metadata.get('phase', 'unknown'),
                    'disease_state': event.metadata.get('disease_state', 'unknown'),
                    'treatment_given': event.metadata.get('treatment_given', False)
                }
                
                # Add component costs as separate columns
                for component, cost in event.components.items():
                    event_dict[f'component_{component}'] = cost
                    
                all_events.append(event_dict)
        
        # Save events
        events_df = pd.DataFrame(all_events)
        events_df.to_parquet(output_path / 'cost_events.parquet', index=False)
        
        # Create patient summary
        financial_results = self.get_financial_results()
        
        patient_summaries = []
        for patient_id, summary in financial_results.patient_costs.items():
            patient_summaries.append(summary.to_dict())
        
        summary_df = pd.DataFrame(patient_summaries)
        summary_df.to_parquet(output_path / 'patient_cost_summary.parquet', index=False)