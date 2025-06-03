"""
Financial results data structures for V2 simulations.

Provides type-safe results with proper serialization support.
"""

from dataclasses import dataclass, asdict, field
from typing import Dict, List, Optional, Any
from datetime import datetime


@dataclass
class PatientCostSummary:
    """Cost summary for an individual patient."""
    
    patient_id: str
    total_cost: float
    visit_costs: float
    drug_costs: float
    special_event_costs: float
    injection_count: int
    visit_count: int
    cost_per_injection: float
    cost_per_visit: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)


@dataclass
class CostBreakdown:
    """Detailed cost breakdown by various categories."""
    
    by_type: Dict[str, float] = field(default_factory=dict)  # visit, drug, special
    by_category: Dict[str, float] = field(default_factory=dict)  # specific visit types
    by_phase: Dict[str, float] = field(default_factory=dict)  # loading, maintenance
    by_component: Dict[str, float] = field(default_factory=dict)  # injection, oct_scan, etc.
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)


@dataclass
class FinancialResults:
    """
    Financial analysis results for V2 simulations.
    
    This is the primary output of economic analysis, containing
    aggregate statistics and patient-level details.
    """
    
    # Summary statistics
    total_cost: float
    total_patients: int
    cost_per_patient: float
    total_injections: int
    cost_per_injection: float
    
    # Clinical-economic metrics
    total_va_change: float
    cost_per_letter_gained: Optional[float]
    
    # Detailed breakdowns
    cost_breakdown: CostBreakdown
    
    # Patient-level data
    patient_costs: Dict[str, PatientCostSummary]
    
    # Time-based analysis
    monthly_costs: Dict[int, float] = field(default_factory=dict)
    cumulative_costs: List[float] = field(default_factory=list)
    
    # Metadata
    analysis_date: datetime = field(default_factory=datetime.now)
    currency: str = "GBP"
    cost_config_name: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'summary': {
                'total_cost': self.total_cost,
                'total_patients': self.total_patients,
                'cost_per_patient': self.cost_per_patient,
                'total_injections': self.total_injections,
                'cost_per_injection': self.cost_per_injection,
                'total_va_change': self.total_va_change,
                'cost_per_letter_gained': self.cost_per_letter_gained
            },
            'breakdown': self.cost_breakdown.to_dict(),
            'patient_costs': {
                pid: summary.to_dict() 
                for pid, summary in self.patient_costs.items()
            },
            'time_series': {
                'monthly_costs': self.monthly_costs,
                'cumulative_costs': self.cumulative_costs
            },
            'metadata': {
                'analysis_date': self.analysis_date.isoformat(),
                'currency': self.currency,
                'cost_config_name': self.cost_config_name
            }
        }
    
    def get_summary_text(self) -> str:
        """Generate a text summary of key metrics."""
        lines = [
            f"Financial Analysis Summary",
            f"========================",
            f"Total patients: {self.total_patients}",
            f"Total cost: {self.currency}{self.total_cost:,.2f}",
            f"Cost per patient: {self.currency}{self.cost_per_patient:,.2f}",
            f"Total injections: {self.total_injections}",
            f"Cost per injection: {self.currency}{self.cost_per_injection:,.2f}"
        ]
        
        if self.cost_per_letter_gained is not None:
            lines.append(f"Cost per letter gained: {self.currency}{self.cost_per_letter_gained:,.2f}")
        
        return "\n".join(lines)
    
    def compare_with(self, other: 'FinancialResults') -> Dict[str, float]:
        """
        Compare this result with another (e.g., different protocols).
        
        Args:
            other: Another FinancialResults to compare with
            
        Returns:
            Dictionary of differences (positive = this is higher)
        """
        return {
            'total_cost_diff': self.total_cost - other.total_cost,
            'cost_per_patient_diff': self.cost_per_patient - other.cost_per_patient,
            'cost_per_injection_diff': self.cost_per_injection - other.cost_per_injection,
            'cost_per_letter_diff': (
                (self.cost_per_letter_gained or 0) - (other.cost_per_letter_gained or 0)
            )
        }