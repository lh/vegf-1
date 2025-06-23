"""
Enhanced cost tracker with visit type classification and workload tracking.

This module extends the base cost tracking functionality to support:
- Visit type classification (injection-only vs full assessment)
- Workload metrics (injections vs decision-maker visits)
- NHS HRG-aligned cost calculations
- Cost per avoided injection metrics
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field
from collections import defaultdict
import pandas as pd

from .cost_config import CostConfig
from .cost_analyzer import CostAnalyzerV2, CostEvent
from .financial_results import FinancialResults, PatientCostSummary, CostBreakdown


class VisitType(Enum):
    """Types of visits in the simulation."""
    INITIAL_ASSESSMENT = "initial_assessment"
    LOADING_INJECTION = "loading_injection"
    LOADING_FINAL = "loading_final"  # Last loading visit with assessment
    TAE_ASSESSMENT = "tae_assessment"  # T&E full assessment
    TNT_INJECTION_ONLY = "tnt_injection_only"  # T&T nurse-led
    TNT_ASSESSMENT = "tnt_assessment"  # T&T annual assessment
    MONITORING_ONLY = "monitoring_only"  # No injection
    MONITORING_VIRTUAL = "monitoring_virtual"  # Virtual review
    DISCONTINUATION = "discontinuation"


@dataclass
class VisitCostBreakdown:
    """Detailed cost breakdown for a visit."""
    visit_type: VisitType
    visit_date: datetime
    drug_cost: float = 0.0
    injection_cost: float = 0.0
    oct_cost: float = 0.0
    consultation_cost: float = 0.0
    other_costs: float = 0.0
    
    @property
    def total_cost(self) -> float:
        return sum([
            self.drug_cost, 
            self.injection_cost, 
            self.oct_cost,
            self.consultation_cost, 
            self.other_costs
        ])
    
    @property
    def procedure_cost(self) -> float:
        """Non-drug costs."""
        return self.total_cost - self.drug_cost
    
    @property
    def has_injection(self) -> bool:
        return self.injection_cost > 0 or self.drug_cost > 0
    
    @property
    def has_decision_maker(self) -> bool:
        """Whether visit requires clinical decision-making."""
        return self.visit_type in [
            VisitType.INITIAL_ASSESSMENT,
            VisitType.LOADING_FINAL,
            VisitType.TAE_ASSESSMENT,
            VisitType.TNT_ASSESSMENT,
            VisitType.MONITORING_ONLY,
            VisitType.MONITORING_VIRTUAL
        ]


@dataclass
class WorkloadMetrics:
    """Task-based workload tracking for capacity planning."""
    month: datetime
    total_visits: int = 0
    injections: int = 0
    decision_visits: int = 0
    oct_scans: int = 0
    virtual_reviews: int = 0
    
    @property
    def injection_tasks(self) -> int:
        """Number of injection tasks required."""
        return self.injections
    
    @property
    def decision_tasks(self) -> int:
        """Number of clinical decision tasks required."""
        return self.decision_visits
    
    @property
    def imaging_tasks(self) -> int:
        """Number of imaging tasks required."""
        return self.oct_scans
        
    @property
    def admin_tasks(self) -> int:
        """Number of administrative tasks (one per visit)."""
        return self.total_visits


@dataclass
class EnhancedPatientCostRecord:
    """Extended patient cost record with visit details."""
    patient_id: str
    visits: List[VisitCostBreakdown] = field(default_factory=list)
    total_drug_cost: float = 0.0
    total_procedure_cost: float = 0.0
    total_injections: int = 0
    total_decision_visits: int = 0
    months_in_treatment: float = 0.0
    baseline_vision: Optional[float] = None
    final_vision: Optional[float] = None
    
    @property
    def total_cost(self) -> float:
        return self.total_drug_cost + self.total_procedure_cost
    
    @property
    def vision_change(self) -> Optional[float]:
        if self.baseline_vision is not None and self.final_vision is not None:
            return self.final_vision - self.baseline_vision
        return None
    
    @property
    def cost_per_injection(self) -> float:
        if self.total_injections > 0:
            return self.total_cost / self.total_injections
        return 0.0
    
    @property
    def cost_per_letter_gained(self) -> Optional[float]:
        if self.vision_change and self.vision_change > 0:
            return self.total_cost / self.vision_change
        return None


class EnhancedCostTracker:
    """Enhanced cost tracker with visit classification and workload metrics."""
    
    def __init__(self, cost_config: CostConfig, protocol_type: str = "treat_and_extend"):
        """
        Initialize enhanced tracker.
        
        Args:
            cost_config: Cost configuration with NHS HRG values
            protocol_type: "treat_and_extend" or "fixed" (for T&T)
        """
        self.cost_config = cost_config
        self.protocol_type = protocol_type
        self.patient_records: Dict[str, EnhancedPatientCostRecord] = {}
        self.workload_timeline: Dict[datetime, WorkloadMetrics] = {}
        
        # Drug selection (can be changed dynamically)
        self.active_drug = "eylea_2mg_biosimilar"
        
    def set_drug_type(self, drug_name: str) -> None:
        """Change the active drug for cost calculations."""
        if drug_name in self.cost_config.drug_costs:
            self.active_drug = drug_name
        else:
            raise ValueError(f"Unknown drug: {drug_name}")
    
    def determine_visit_type(self, patient: Any, visit_number: int, 
                           is_annual_assessment: bool = False) -> VisitType:
        """
        Determine visit type based on protocol and visit number.
        
        Args:
            patient: Patient object
            visit_number: 0-based visit index
            is_annual_assessment: For T&T, whether this is an annual assessment
            
        Returns:
            VisitType enum value
        """
        # Initial visit
        if visit_number == 0:
            return VisitType.INITIAL_ASSESSMENT
        
        # Loading phase (assuming 3 loading doses)
        loading_doses = 3
        if visit_number < loading_doses - 1:
            return VisitType.LOADING_INJECTION
        elif visit_number == loading_doses - 1:
            return VisitType.LOADING_FINAL
        
        # Maintenance phase
        if self.protocol_type == "treat_and_extend":
            return VisitType.TAE_ASSESSMENT
        else:  # fixed/T&T
            if is_annual_assessment:
                return VisitType.TNT_ASSESSMENT
            else:
                return VisitType.TNT_INJECTION_ONLY
    
    def calculate_visit_cost(self, visit_type: VisitType, 
                           injection_given: bool) -> VisitCostBreakdown:
        """
        Calculate detailed cost breakdown for a visit.
        
        Args:
            visit_type: Type of visit
            injection_given: Whether injection was administered
            
        Returns:
            VisitCostBreakdown with all cost components
        """
        breakdown = VisitCostBreakdown(
            visit_type=visit_type,
            visit_date=datetime.now()  # Will be updated by caller
        )
        
        # Map visit types to cost config entries
        visit_config_map = {
            VisitType.INITIAL_ASSESSMENT: "initial_assessment",
            VisitType.LOADING_INJECTION: "loading_injection",
            VisitType.LOADING_FINAL: "loading_final",
            VisitType.TAE_ASSESSMENT: "tae_assessment",
            VisitType.TNT_INJECTION_ONLY: "tnt_injection_only",
            VisitType.TNT_ASSESSMENT: "monitoring_only",  # No injection
            VisitType.MONITORING_ONLY: "monitoring_only",
            VisitType.MONITORING_VIRTUAL: "monitoring_virtual"
        }
        
        config_key = visit_config_map.get(visit_type, "tae_assessment")
        
        if injection_given:
            # Drug cost
            breakdown.drug_cost = self.cost_config.get_drug_cost(self.active_drug)
            
            # Injection administration
            breakdown.injection_cost = self.cost_config.get_component_cost(
                "injection_administration"
            )
        
        # OCT scan (for assessment visits)
        if visit_type in [VisitType.INITIAL_ASSESSMENT, VisitType.LOADING_FINAL,
                         VisitType.TAE_ASSESSMENT, VisitType.TNT_ASSESSMENT,
                         VisitType.MONITORING_ONLY, VisitType.MONITORING_VIRTUAL]:
            breakdown.oct_cost = self.cost_config.get_component_cost("oct_scan")
        
        # Consultation cost
        if visit_type == VisitType.INITIAL_ASSESSMENT:
            breakdown.consultation_cost = self.cost_config.get_component_cost(
                "consultant_first"
            )
        elif visit_type in [VisitType.LOADING_FINAL, VisitType.TAE_ASSESSMENT,
                           VisitType.TNT_ASSESSMENT, VisitType.MONITORING_ONLY]:
            breakdown.consultation_cost = self.cost_config.get_component_cost(
                "consultant_followup"
            )
        elif visit_type == VisitType.MONITORING_VIRTUAL:
            breakdown.consultation_cost = self.cost_config.get_component_cost(
                "virtual_review"
            )
        elif visit_type in [VisitType.LOADING_INJECTION, VisitType.TNT_INJECTION_ONLY]:
            breakdown.consultation_cost = self.cost_config.get_component_cost(
                "nurse_review"
            )
        
        return breakdown
    
    def record_visit(self, patient_id: str, visit_date: datetime,
                    visit_type: VisitType, injection_given: bool,
                    vision: Optional[float] = None) -> VisitCostBreakdown:
        """
        Record a visit with cost and workload tracking.
        
        Args:
            patient_id: Patient identifier
            visit_date: Date of visit
            visit_type: Type of visit
            injection_given: Whether injection was given
            vision: Visual acuity at visit
            
        Returns:
            VisitCostBreakdown for the recorded visit
        """
        # Calculate costs
        cost_breakdown = self.calculate_visit_cost(visit_type, injection_given)
        cost_breakdown.visit_date = visit_date
        
        # Update patient record
        if patient_id not in self.patient_records:
            self.patient_records[patient_id] = EnhancedPatientCostRecord(
                patient_id=patient_id
            )
        
        record = self.patient_records[patient_id]
        record.visits.append(cost_breakdown)
        
        # Update totals
        record.total_drug_cost += cost_breakdown.drug_cost
        record.total_procedure_cost += cost_breakdown.procedure_cost
        
        if cost_breakdown.has_injection:
            record.total_injections += 1
        if cost_breakdown.has_decision_maker:
            record.total_decision_visits += 1
        
        # Update vision tracking
        if vision is not None:
            if record.baseline_vision is None:
                record.baseline_vision = vision
            record.final_vision = vision
        
        # Update workload timeline
        month_key = visit_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if month_key not in self.workload_timeline:
            self.workload_timeline[month_key] = WorkloadMetrics(month=month_key)
        
        metrics = self.workload_timeline[month_key]
        metrics.total_visits += 1
        
        if cost_breakdown.has_injection:
            metrics.injections += 1
        if cost_breakdown.has_decision_maker:
            metrics.decision_visits += 1
        if cost_breakdown.oct_cost > 0:
            metrics.oct_scans += 1
        if visit_type == VisitType.MONITORING_VIRTUAL:
            metrics.virtual_reviews += 1
        
        return cost_breakdown
    
    def get_workload_summary(self) -> pd.DataFrame:
        """
        Get task-based workload metrics as a DataFrame for visualization.
        
        Returns:
            DataFrame with monthly task metrics
        """
        if not self.workload_timeline:
            return pd.DataFrame()
        
        data = []
        for month, metrics in sorted(self.workload_timeline.items()):
            data.append({
                'month': month,
                'total_visits': metrics.total_visits,
                'injections': metrics.injections,
                'decision_visits': metrics.decision_visits,
                'oct_scans': metrics.oct_scans,
                'virtual_reviews': metrics.virtual_reviews
            })
        
        return pd.DataFrame(data)
    
    def calculate_cost_effectiveness(self) -> Dict[str, Any]:
        """
        Calculate comprehensive cost-effectiveness metrics.
        
        Returns:
            Dictionary with cost-effectiveness metrics
        """
        if not self.patient_records:
            return {
                'total_cost': 0,
                'total_patients': 0,
                'cost_per_patient': 0,
                'patients_maintaining_vision': 0,
                'cost_per_vision_maintained': 0,
                'mean_vision_change': 0,
                'cost_per_letter_gained': 0,
                'cost_per_injection': 0,
                'cost_per_avoided_injection': 0
            }
        
        # Aggregate metrics
        total_cost = 0
        total_patients = len(self.patient_records)
        total_injections = 0
        patients_maintaining_vision = 0
        total_vision_change = 0
        patients_with_vision_data = 0
        
        for record in self.patient_records.values():
            total_cost += record.total_cost
            total_injections += record.total_injections
            
            if record.vision_change is not None:
                patients_with_vision_data += 1
                total_vision_change += record.vision_change
                
                # Count as maintaining if loss <= 5 letters
                if record.vision_change >= -5:
                    patients_maintaining_vision += 1
        
        # Calculate derived metrics
        cost_per_patient = total_cost / max(1, total_patients)
        cost_per_injection = total_cost / max(1, total_injections)
        cost_per_vision_maintained = total_cost / max(1, patients_maintaining_vision)
        
        mean_vision_change = (total_vision_change / patients_with_vision_data 
                             if patients_with_vision_data > 0 else 0)
        
        cost_per_letter = (total_cost / total_vision_change 
                          if total_vision_change > 0 else None)
        
        # Cost per avoided injection (drug + procedure)
        injection_cost = (self.cost_config.get_drug_cost(self.active_drug) + 
                         self.cost_config.get_component_cost("injection_administration"))
        
        return {
            'total_cost': total_cost,
            'total_patients': total_patients,
            'cost_per_patient': cost_per_patient,
            'patients_maintaining_vision': patients_maintaining_vision,
            'cost_per_vision_maintained': cost_per_vision_maintained,
            'mean_vision_change': mean_vision_change,
            'cost_per_letter_gained': cost_per_letter,
            'cost_per_injection': cost_per_injection,
            'cost_per_avoided_injection': injection_cost,
            'total_injections': total_injections,
            'mean_injections_per_patient': total_injections / max(1, total_patients)
        }
    
    def get_cost_breakdown(self) -> Dict[str, float]:
        """
        Get total costs broken down by category.
        
        Returns:
            Dictionary with cost categories and totals
        """
        breakdown = {
            'drug_costs': 0.0,
            'injection_costs': 0.0,
            'oct_costs': 0.0,
            'consultation_costs': 0.0,
            'other_costs': 0.0,
            'total_costs': 0.0
        }
        
        for record in self.patient_records.values():
            for visit in record.visits:
                breakdown['drug_costs'] += visit.drug_cost
                breakdown['injection_costs'] += visit.injection_cost
                breakdown['oct_costs'] += visit.oct_cost
                breakdown['consultation_costs'] += visit.consultation_cost
                breakdown['other_costs'] += visit.other_costs
                breakdown['total_costs'] += visit.total_cost
        
        return breakdown
    
    def export_patient_data(self, filepath: str) -> None:
        """Export patient-level cost data to CSV."""
        data = []
        for patient_id, record in self.patient_records.items():
            data.append({
                'patient_id': patient_id,
                'total_cost': record.total_cost,
                'drug_cost': record.total_drug_cost,
                'procedure_cost': record.total_procedure_cost,
                'total_injections': record.total_injections,
                'total_decision_visits': record.total_decision_visits,
                'baseline_vision': record.baseline_vision,
                'final_vision': record.final_vision,
                'vision_change': record.vision_change,
                'cost_per_injection': record.cost_per_injection,
                'cost_per_letter': record.cost_per_letter_gained
            })
        
        df = pd.DataFrame(data)
        df.to_csv(filepath, index=False)