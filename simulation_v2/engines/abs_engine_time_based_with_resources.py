"""
Time-based ABS engine with integrated resource tracking.

Extends the parameter-driven engine to track resource usage and costs
for economic and workload analysis.
"""

from datetime import datetime
from typing import Dict, Optional, Any
from pathlib import Path

from simulation_v2.engines.abs_engine_time_based_with_params import ABSEngineTimeBasedWithParams
from simulation_v2.economics.resource_tracker import ResourceTracker, load_resource_config
from simulation_v2.economics.visit_classifier import VisitClassifier
from simulation_v2.core.patient import Patient


class ABSEngineTimeBasedWithResources(ABSEngineTimeBasedWithParams):
    """
    Time-based ABS engine with resource tracking for economic analysis.
    
    Tracks actual resource usage during simulation based on visit types.
    NO ESTIMATES - only tracks what actually happens.
    """
    
    def __init__(self, resource_config: Optional[Dict[str, Any]] = None, 
                 resource_config_path: Optional[str] = None, *args, **kwargs):
        """
        Initialize with resource tracking.
        
        Args:
            resource_config: Resource configuration dictionary
            resource_config_path: Path to resource configuration YAML
            *args, **kwargs: Arguments for parent class
        """
        super().__init__(*args, **kwargs)
        
        # Initialize resource tracking
        # Get weekend working configuration from protocol spec if available
        allow_saturday = False
        allow_sunday = False
        if hasattr(self, 'protocol_spec'):
            allow_saturday = getattr(self.protocol_spec, 'allow_saturday_visits', False)
            allow_sunday = getattr(self.protocol_spec, 'allow_sunday_visits', False)
        
        if resource_config:
            self.resource_tracker = ResourceTracker(resource_config, allow_saturday, allow_sunday)
        elif resource_config_path:
            config = load_resource_config(resource_config_path)
            self.resource_tracker = ResourceTracker(config, allow_saturday, allow_sunday)
        else:
            # Default to NHS standard resources
            default_path = Path(__file__).parent.parent.parent / 'protocols' / 'resources' / 'nhs_standard_resources.yaml'
            if default_path.exists():
                config = load_resource_config(str(default_path))
                self.resource_tracker = ResourceTracker(config, allow_saturday, allow_sunday)
            else:
                self.resource_tracker = None
        
        # Initialize visit classifier based on protocol type
        protocol_type = self._determine_protocol_type()
        self.visit_classifier = VisitClassifier(protocol_type) if protocol_type else None
        
        # Track visit numbers for each patient
        self.patient_visit_numbers = {}
    
    def _determine_protocol_type(self) -> Optional[str]:
        """Determine if this is T&E or T&T protocol."""
        if hasattr(self, 'protocol_spec') and hasattr(self.protocol_spec, 'name'):
            name = self.protocol_spec.name.lower()
            if 'treat_and_extend' in name or 't&e' in name or 'tae' in name:
                return 'T&E'
            elif 'treat_and_treat' in name or 't&t' in name or 'tnt' in name:
                return 'T&T'
        
        # Try to infer from protocol behavior
        if hasattr(self, 'protocol') and hasattr(self.protocol, 'extension_days'):
            # T&E has extension capability, T&T doesn't
            if self.protocol.extension_days > 0:
                return 'T&E'
            else:
                return 'T&T'
        
        return None
    
    def _track_visit_resources(self, patient_id: str, visit_date: datetime, 
                             injection_given: bool, visit_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Track resources for a visit if resource tracking is enabled.
        
        Args:
            patient_id: Patient identifier
            visit_date: Date of visit
            injection_given: Whether injection was administered
            visit_data: Additional visit data
            
        Returns:
            Visit record with costs and resources, or None if tracking disabled
        """
        if not self.resource_tracker or not self.visit_classifier:
            return None
        
        # Get visit number for this patient
        if patient_id not in self.patient_visit_numbers:
            self.patient_visit_numbers[patient_id] = 0
        self.patient_visit_numbers[patient_id] += 1
        visit_number = self.patient_visit_numbers[patient_id]
        
        # Calculate days since treatment start
        patient = self.patients[patient_id]
        days_since_start = (visit_date - patient.enrollment_date).days
        
        # Determine visit type
        is_assessment = (visit_number == 4)  # Post-loading assessment
        is_annual = self._is_annual_review(days_since_start)
        
        visit_type = self.visit_classifier.get_visit_type(
            visit_number, days_since_start, is_assessment, is_annual
        )
        
        # Determine what procedures were performed
        oct_performed = 'decision' in visit_type
        
        # Track the visit
        try:
            visit_record = self.resource_tracker.track_visit(
                visit_date.date(),
                visit_type,
                patient_id,
                injection_given,
                oct_performed
            )
            return visit_record
        except ValueError as e:
            # Skip weekend visits or other invalid dates
            print(f"Warning: Could not track visit: {e}")
            return None
    
    def _is_annual_review(self, days_since_start: int) -> bool:
        """Determine if this is an annual review visit."""
        # Annual reviews at 12, 24, 36 months etc.
        # Allow ±30 days window
        months_since_start = days_since_start / 30.44  # Average days per month
        
        for year in range(1, 10):  # Check up to 10 years
            target_months = year * 12
            if abs(months_since_start - target_months) < 1:
                return True
        
        return False
    
    def _process_visit(self, patient: Patient, visit_date: datetime) -> bool:
        """Override to add resource tracking."""
        # Call parent implementation to handle the visit
        injection_given = super()._process_visit(patient, visit_date)
        
        # Track resources for this visit
        if self.resource_tracker and self.visit_classifier:
            visit_data = {
                'disease_state': patient.current_state,
                'vision': patient.current_vision
            }
            
            self._track_visit_resources(
                patient.id,
                visit_date,
                injection_given=injection_given,
                visit_data=visit_data
            )
        
        return injection_given
    
    def get_resource_results(self) -> Dict[str, Any]:
        """
        Get resource tracking results.
        
        Returns:
            Dictionary containing:
            - daily_workload: Resource usage by date and role
            - total_costs: Cost breakdown
            - workload_summary: Summary statistics
            - bottlenecks: Identified capacity issues
        """
        if not self.resource_tracker:
            return {}
        
        return {
            'daily_workload': dict(self.resource_tracker.daily_usage),
            'total_costs': self.resource_tracker.get_total_costs(),
            'workload_summary': self.resource_tracker.get_workload_summary(),
            'bottlenecks': self.resource_tracker.identify_bottlenecks(),
            'visits': self.resource_tracker.visits
        }
    
    def run(self, duration_years: float) -> Any:
        """
        Run simulation with resource tracking.
        
        Args:
            duration_years: Simulation duration in years
            
        Returns:
            SimulationResults with additional resource data
        """
        # Run base simulation
        results = super().run(duration_years)
        
        # Add resource tracking results
        if self.resource_tracker:
            # Attach the resource tracker itself for direct access
            results.resource_tracker = self.resource_tracker
            
            resource_results = self.get_resource_results()
            
            # Add to results object
            results.resource_usage = resource_results.get('daily_workload', {})
            results.total_costs = resource_results.get('total_costs', {})
            results.workload_summary = resource_results.get('workload_summary', {})
            results.bottlenecks = resource_results.get('bottlenecks', [])
            results.visit_records = resource_results.get('visits', [])
            
            # Calculate average cost per patient
            if results.patient_count > 0 and results.total_costs:
                # Account for varying enrollment times
                total_patient_months = 0
                for patient_id, patient in self.patients.items():
                    if patient.visit_history and len(patient.visit_history) > 0:
                        # Get first and last visit times
                        first_visit = patient.visit_history[0]
                        last_visit = patient.visit_history[-1]
                        
                        # Calculate months from enrollment to last visit
                        days = (last_visit['date'] - patient.enrollment_date).days
                        months = days / 30.44
                        if months > 0:
                            total_patient_months += months
                
                if total_patient_months > 0:
                    results.average_cost_per_patient_year = (
                        results.total_costs.get('total', 0) / (total_patient_months / 12)
                    )
                else:
                    results.average_cost_per_patient_year = 0
        
        return results