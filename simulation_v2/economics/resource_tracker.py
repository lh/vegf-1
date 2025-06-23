"""
Resource tracking for economic and workload analysis.

Tracks actual resource usage during simulations based on visit types.
NO ESTIMATES OR FALLBACKS - only tracks what actually happens.
"""

from collections import defaultdict
from datetime import datetime, date
from typing import Dict, List, Optional, Any
import math
import yaml
from pathlib import Path


class ResourceTracker:
    """Track resource usage during simulation."""
    
    def __init__(self, resource_config: Dict[str, Any]):
        """
        Initialize resource tracker with configuration.
        
        Args:
            resource_config: Dictionary containing roles, visit requirements, etc.
        """
        if not resource_config:
            raise ValueError("Resource configuration cannot be empty")
            
        self.roles = resource_config['resources']['roles']
        self.visit_requirements = resource_config['resources']['visit_requirements']
        self.session_parameters = resource_config['resources']['session_parameters']
        self.costs = resource_config['costs']
        
        # Daily usage tracking: date -> role -> count
        self.daily_usage = defaultdict(lambda: defaultdict(int))
        
        # Visit tracking for cost calculation
        self.visits = []
        
        # Validate configuration
        self._validate_config()
    
    def _validate_config(self) -> None:
        """Validate resource configuration has required fields."""
        required_roles = ['injector', 'injector_assistant', 'vision_tester', 
                         'oct_operator', 'decision_maker']
        for role in required_roles:
            if role not in self.roles:
                raise ValueError(f"Missing required role: {role}")
                
        required_visit_types = ['injection_only', 'decision_with_injection', 'decision_only']
        for vtype in required_visit_types:
            if vtype not in self.visit_requirements:
                raise ValueError(f"Missing required visit type: {vtype}")
    
    def track_visit(self, visit_date: date, visit_type: str, patient_id: str,
                   injection_given: bool = False, oct_performed: bool = False) -> Dict[str, Any]:
        """
        Track resource usage for a visit.
        
        Args:
            visit_date: Date of the visit
            visit_type: Type of visit (injection_only, decision_with_injection, decision_only)
            patient_id: Patient identifier
            injection_given: Whether injection was administered
            oct_performed: Whether OCT scan was performed
            
        Returns:
            Visit record with costs and resources used
            
        Raises:
            KeyError: If visit_type is unknown
            ValueError: If data is missing or invalid
        """
        if visit_type not in self.visit_requirements:
            raise KeyError(f"Unknown visit type: {visit_type}")
            
        if visit_date.weekday() >= 5:  # Saturday = 5, Sunday = 6
            raise ValueError(f"Visit scheduled on weekend: {visit_date}")
        
        # Get resource requirements for this visit type
        requirements = self.visit_requirements[visit_type]['roles_needed']
        
        # Track resource usage
        for role, count in requirements.items():
            self.daily_usage[visit_date][role] += count
        
        # Calculate costs
        visit_costs = self._calculate_visit_costs(visit_type, injection_given, oct_performed)
        
        # Create visit record
        visit_record = {
            'date': visit_date,
            'patient_id': patient_id,
            'visit_type': visit_type,
            'injection_given': injection_given,
            'oct_performed': oct_performed,
            'costs': visit_costs,
            'resources_used': dict(requirements)  # Copy to avoid reference issues
        }
        
        self.visits.append(visit_record)
        
        return visit_record
    
    def _calculate_visit_costs(self, visit_type: str, injection_given: bool, 
                             oct_performed: bool) -> Dict[str, float]:
        """Calculate costs for a visit based on procedures performed."""
        costs = {}
        
        # Drug cost if injection given
        if injection_given:
            costs['drug'] = self.costs['drugs']['aflibercept_2mg']['unit_cost']
            costs['injection_procedure'] = self.costs['procedures']['intravitreal_injection']['unit_cost']
        
        # Assessment cost for decision visits
        if 'decision' in visit_type:
            costs['consultation'] = self.costs['procedures']['outpatient_assessment']['unit_cost']
        
        # OCT cost if performed
        if oct_performed:
            costs['oct_scan'] = self.costs['procedures']['oct_scan']['unit_cost']
            
        return costs
    
    def get_daily_usage(self, query_date: date) -> Dict[str, int]:
        """
        Get resource usage for a specific date.
        
        Args:
            query_date: Date to query
            
        Returns:
            Dictionary of role -> count for the date
            
        Raises:
            ValueError: If no data exists for the date
        """
        if query_date not in self.daily_usage:
            raise ValueError(f"No visit data available for {query_date}")
            
        return dict(self.daily_usage[query_date])
    
    def calculate_sessions_needed(self, query_date: date, role: str) -> float:
        """
        Calculate sessions needed for a role on a date.
        
        Args:
            query_date: Date to calculate for
            role: Role to calculate sessions for
            
        Returns:
            Number of sessions needed (can be fractional)
            
        Raises:
            ValueError: If no data exists or role is unknown
        """
        if role not in self.roles:
            raise ValueError(f"Unknown role: {role}")
            
        daily_usage = self.get_daily_usage(query_date)
        
        if role not in daily_usage:
            return 0.0
            
        daily_count = daily_usage[role]
        capacity = self.roles[role]['capacity_per_session']
        
        return daily_count / capacity
    
    def get_all_dates_with_visits(self) -> List[date]:
        """Get all dates that have visits scheduled."""
        return sorted(self.daily_usage.keys())
    
    def get_total_costs(self) -> Dict[str, float]:
        """Calculate total costs across all visits."""
        total_costs = defaultdict(float)
        
        for visit in self.visits:
            for cost_type, amount in visit['costs'].items():
                total_costs[cost_type] += amount
                
        total_costs['total'] = sum(total_costs.values())
        
        return dict(total_costs)
    
    def get_workload_summary(self) -> Dict[str, Any]:
        """Generate workload summary statistics."""
        summary = {
            'total_visits': len(self.visits),
            'visits_by_type': defaultdict(int),
            'peak_daily_demand': {},
            'average_daily_demand': {},
            'total_sessions_needed': {},
            'dates_with_visits': len(self.daily_usage)
        }
        
        # Count visits by type
        for visit in self.visits:
            summary['visits_by_type'][visit['visit_type']] += 1
        
        # Calculate demand statistics by role
        for role in self.roles:
            daily_demands = []
            total_procedures = 0
            
            for date_usage in self.daily_usage.values():
                if role in date_usage:
                    daily_demands.append(date_usage[role])
                    total_procedures += date_usage[role]
            
            if daily_demands:
                summary['peak_daily_demand'][role] = max(daily_demands)
                summary['average_daily_demand'][role] = sum(daily_demands) / len(daily_demands)
                
                # Total sessions needed
                capacity = self.roles[role]['capacity_per_session']
                summary['total_sessions_needed'][role] = math.ceil(total_procedures / capacity)
            else:
                summary['peak_daily_demand'][role] = 0
                summary['average_daily_demand'][role] = 0
                summary['total_sessions_needed'][role] = 0
        
        return summary
    
    def identify_bottlenecks(self) -> List[Dict[str, Any]]:
        """Identify resource bottlenecks (days where capacity is exceeded)."""
        bottlenecks = []
        
        for check_date in self.get_all_dates_with_visits():
            for role, capacity_info in self.roles.items():
                sessions_needed = self.calculate_sessions_needed(check_date, role)
                sessions_available = self.session_parameters['sessions_per_day']
                
                if sessions_needed > sessions_available:
                    bottlenecks.append({
                        'date': check_date,
                        'role': role,
                        'sessions_needed': sessions_needed,
                        'sessions_available': sessions_available,
                        'overflow': sessions_needed - sessions_available,
                        'procedures_affected': self.daily_usage[check_date][role]
                    })
        
        return bottlenecks


def load_resource_config(config_path: str) -> Dict[str, Any]:
    """
    Load resource configuration from YAML file.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Configuration dictionary
        
    Raises:
        FileNotFoundError: If config file doesn't exist
        yaml.YAMLError: If config file is invalid
    """
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Resource configuration not found: {config_path}")
        
    with open(path, 'r') as f:
        config = yaml.safe_load(f)
        
    if not config:
        raise ValueError("Resource configuration file is empty")
        
    return config