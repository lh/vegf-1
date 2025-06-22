# Cost Tracking Technical Design

## 1. Data Model

### 1.1 Visit Classification
```python
from enum import Enum
from dataclasses import dataclass
from typing import List, Dict, Optional

class VisitType(Enum):
    """Types of visits in the simulation"""
    INITIAL_ASSESSMENT = "initial_assessment"
    LOADING_INJECTION = "loading_injection"
    LOADING_ASSESSMENT = "loading_assessment"  # Last loading visit
    INJECTION_ONLY = "injection_only"          # T&T maintenance
    FULL_ASSESSMENT = "full_assessment"        # T&E visit
    MONITORING_ONLY = "monitoring_only"        # No injection needed
    DISCONTINUATION = "discontinuation"

@dataclass
class VisitCost:
    """Cost breakdown for a visit"""
    visit_type: VisitType
    drug_cost: float = 0.0
    injection_cost: float = 0.0
    oct_cost: float = 0.0
    va_test_cost: float = 0.0
    review_cost: float = 0.0
    other_costs: float = 0.0
    
    @property
    def total_cost(self) -> float:
        return sum([self.drug_cost, self.injection_cost, self.oct_cost,
                    self.va_test_cost, self.review_cost, self.other_costs])
    
    @property
    def has_injection(self) -> bool:
        return self.injection_cost > 0
    
    @property
    def has_decision_maker(self) -> bool:
        return self.visit_type in [
            VisitType.INITIAL_ASSESSMENT,
            VisitType.LOADING_ASSESSMENT,
            VisitType.FULL_ASSESSMENT,
            VisitType.MONITORING_ONLY
        ]
```

### 1.2 Enhanced Patient Cost Tracking
```python
@dataclass
class PatientCostRecord:
    """Complete cost record for a patient"""
    patient_id: str
    visits: List[Tuple[datetime, VisitCost]]
    total_drug_cost: float = 0.0
    total_visit_cost: float = 0.0
    total_injections: int = 0
    total_decision_visits: int = 0
    months_in_treatment: float = 0.0
    final_vision: Optional[float] = None
    vision_change: Optional[float] = None
```

## 2. Integration Points

### 2.1 Protocol Integration

#### Modify StandardProtocol
```python
class CostAwareProtocol(StandardProtocol):
    """Protocol that determines visit types based on treatment strategy"""
    
    def determine_visit_type(self, patient: Patient, visit_number: int) -> VisitType:
        """Determine the type of visit based on protocol and patient state"""
        
        # Initial visit
        if visit_number == 0:
            return VisitType.INITIAL_ASSESSMENT
        
        # Loading phase
        if visit_number < self.loading_doses:
            return VisitType.LOADING_INJECTION
        elif visit_number == self.loading_doses:
            return VisitType.LOADING_ASSESSMENT
        
        # Maintenance phase depends on protocol type
        if self.protocol_type == "treat_and_extend":
            return VisitType.FULL_ASSESSMENT
        elif self.protocol_type == "fixed":
            # T&T: Quarterly assessments, otherwise injection only
            if visit_number % 3 == 0:  # Every 3rd visit
                return VisitType.FULL_ASSESSMENT
            else:
                return VisitType.INJECTION_ONLY
        
        return VisitType.FULL_ASSESSMENT  # Default
```

#### Modify Visit Recording
```python
def record_visit_with_costs(self, patient: Patient, visit: Dict, 
                           cost_tracker: EnhancedCostTracker):
    """Record visit and associated costs"""
    
    visit_type = self.determine_visit_type(patient, len(patient.visit_history))
    
    # Record in cost tracker
    cost_tracker.record_visit(
        patient_id=patient.id,
        visit_date=visit['date'],
        visit_type=visit_type,
        injection_given=visit['treatment_given'],
        disease_state=visit['disease_state']
    )
```

### 2.2 Enhanced Cost Tracker

```python
class EnhancedCostTracker:
    """Tracks costs and workload metrics"""
    
    def __init__(self, cost_config: CostConfig):
        self.cost_config = cost_config
        self.patient_records: Dict[str, PatientCostRecord] = {}
        self.workload_timeline: Dict[datetime, Dict[str, int]] = {}
        
    def record_visit(self, patient_id: str, visit_date: datetime, 
                    visit_type: VisitType, injection_given: bool,
                    disease_state: str):
        """Record a visit with cost and workload tracking"""
        
        # Calculate costs
        visit_cost = self._calculate_visit_cost(visit_type, injection_given)
        
        # Update patient record
        if patient_id not in self.patient_records:
            self.patient_records[patient_id] = PatientCostRecord(patient_id=patient_id, visits=[])
        
        record = self.patient_records[patient_id]
        record.visits.append((visit_date, visit_cost))
        record.total_drug_cost += visit_cost.drug_cost
        record.total_visit_cost += (visit_cost.total_cost - visit_cost.drug_cost)
        
        if visit_cost.has_injection:
            record.total_injections += 1
        if visit_cost.has_decision_maker:
            record.total_decision_visits += 1
        
        # Update workload timeline
        month_key = visit_date.replace(day=1)
        if month_key not in self.workload_timeline:
            self.workload_timeline[month_key] = {
                'injections': 0,
                'decision_visits': 0,
                'total_visits': 0
            }
        
        self.workload_timeline[month_key]['total_visits'] += 1
        if visit_cost.has_injection:
            self.workload_timeline[month_key]['injections'] += 1
        if visit_cost.has_decision_maker:
            self.workload_timeline[month_key]['decision_visits'] += 1
    
    def _calculate_visit_cost(self, visit_type: VisitType, 
                             injection_given: bool) -> VisitCost:
        """Calculate cost components for a visit"""
        
        visit_cost = VisitCost(visit_type=visit_type)
        
        # Get visit configuration
        visit_config = self.cost_config.get_visit_config(visit_type)
        
        # Add component costs
        if 'injection' in visit_config['components'] and injection_given:
            visit_cost.injection_cost = self.cost_config.component_costs['injection']
            visit_cost.drug_cost = self.cost_config.drug_costs[self.cost_config.active_drug]
        
        if 'oct_scan' in visit_config['components']:
            visit_cost.oct_cost = self.cost_config.component_costs['oct_scan']
        
        if 'visual_acuity_test' in visit_config['components']:
            visit_cost.va_test_cost = self.cost_config.component_costs['visual_acuity_test']
        
        if 'clinical_review' in visit_config['components']:
            visit_cost.review_cost = self.cost_config.component_costs['face_to_face_review']
        
        return visit_cost
    
    def get_patient_summary(self, patient_id: str) -> Dict:
        """Get cost and outcome summary for a patient"""
        record = self.patient_records.get(patient_id)
        if not record:
            return {}
        
        return {
            'total_cost': record.total_drug_cost + record.total_visit_cost,
            'drug_cost': record.total_drug_cost,
            'visit_cost': record.total_visit_cost,
            'injections': record.total_injections,
            'decision_visits': record.total_decision_visits,
            'cost_per_injection': (record.total_drug_cost + record.total_visit_cost) / max(1, record.total_injections),
            'months_treated': record.months_in_treatment,
            'vision_change': record.vision_change
        }
    
    def calculate_cost_effectiveness(self) -> Dict:
        """Calculate cost-effectiveness metrics"""
        
        total_costs = 0
        total_patients = 0
        patients_maintaining_vision = 0
        total_vision_years_saved = 0
        
        for patient_id, record in self.patient_records.items():
            total_costs += record.total_drug_cost + record.total_visit_cost
            total_patients += 1
            
            if record.vision_change is not None and record.vision_change >= -5:
                patients_maintaining_vision += 1
            
            if record.vision_change is not None and record.vision_change > 0:
                # Simple calculation: positive vision change * years in treatment
                years = record.months_in_treatment / 12
                total_vision_years_saved += record.vision_change * years / 15  # Normalize by 15 letters
        
        return {
            'total_cost': total_costs,
            'cost_per_patient': total_costs / max(1, total_patients),
            'patients_maintaining_vision': patients_maintaining_vision,
            'cost_per_vision_maintained': total_costs / max(1, patients_maintaining_vision),
            'vision_years_saved': total_vision_years_saved,
            'cost_per_vision_year': total_costs / max(1, total_vision_years_saved)
        }
```

## 3. Visualization Components

### 3.1 Workload Timeline
```python
def create_workload_timeline(workload_data: Dict[datetime, Dict]) -> go.Figure:
    """Create stacked area chart of workload over time"""
    
    dates = sorted(workload_data.keys())
    injections = [workload_data[d]['injections'] for d in dates]
    decision_visits = [workload_data[d]['decision_visits'] for d in dates]
    
    fig = go.Figure()
    
    # Injection workload
    fig.add_trace(go.Scatter(
        x=dates,
        y=injections,
        name='Injections',
        fill='tonexty',
        line=dict(color='#1f77b4', width=2),
        hovertemplate='%{y} injections<extra></extra>'
    ))
    
    # Decision-maker workload
    fig.add_trace(go.Scatter(
        x=dates,
        y=decision_visits,
        name='Decision-maker visits',
        fill='tozeroy',
        line=dict(color='#ff7f0e', width=2),
        hovertemplate='%{y} assessments<extra></extra>'
    ))
    
    fig.update_layout(
        title='Clinical Workload Over Time',
        xaxis_title='Month',
        yaxis_title='Number of Procedures',
        hovermode='x unified'
    )
    
    return fig
```

### 3.2 Cost Breakdown
```python
def create_cost_breakdown(cost_tracker: EnhancedCostTracker) -> go.Figure:
    """Create pie chart of cost components"""
    
    total_drug = sum(r.total_drug_cost for r in cost_tracker.patient_records.values())
    total_injection = sum(sum(vc.injection_cost for _, vc in r.visits) 
                         for r in cost_tracker.patient_records.values())
    total_oct = sum(sum(vc.oct_cost for _, vc in r.visits) 
                   for r in cost_tracker.patient_records.values())
    total_review = sum(sum(vc.review_cost for _, vc in r.visits) 
                      for r in cost_tracker.patient_records.values())
    total_other = sum(sum(vc.va_test_cost + vc.other_costs for _, vc in r.visits) 
                     for r in cost_tracker.patient_records.values())
    
    fig = go.Figure(data=[go.Pie(
        labels=['Drug', 'Injection', 'OCT', 'Clinical Review', 'Other'],
        values=[total_drug, total_injection, total_oct, total_review, total_other],
        hole=.3
    )])
    
    fig.update_layout(title='Cost Breakdown by Component')
    
    return fig
```

### 3.3 Cost-Effectiveness Dashboard
```python
def create_cost_effectiveness_display(cost_tracker: EnhancedCostTracker) -> None:
    """Create Streamlit components for cost-effectiveness display"""
    
    ce_metrics = cost_tracker.calculate_cost_effectiveness()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Total Cost",
            f"£{ce_metrics['total_cost']:,.0f}",
            help="Total cost for all patients in simulation"
        )
        st.metric(
            "Cost per Patient",
            f"£{ce_metrics['cost_per_patient']:,.0f}"
        )
    
    with col2:
        st.metric(
            "Patients Maintaining Vision",
            f"{ce_metrics['patients_maintaining_vision']}",
            help="Patients with ≤5 letter loss"
        )
        st.metric(
            "Cost per Vision Maintained",
            f"£{ce_metrics['cost_per_vision_maintained']:,.0f}"
        )
    
    with col3:
        st.metric(
            "Vision Years Saved",
            f"{ce_metrics['vision_years_saved']:.1f}",
            help="Weighted by vision improvement and treatment duration"
        )
        st.metric(
            "Cost per Vision Year",
            f"£{ce_metrics['cost_per_vision_year']:,.0f}"
        )
```

## 4. Implementation Strategy

### 4.1 Phase 1: Core Infrastructure
1. Implement VisitType enum and VisitCost dataclass
2. Create EnhancedCostTracker class
3. Add cost configuration loading

### 4.2 Phase 2: Protocol Integration
1. Modify protocol classes to determine visit types
2. Integrate cost tracking into visit recording
3. Add workload timeline tracking

### 4.3 Phase 3: User Interface
1. Create cost parameter controls
2. Implement workload visualization
3. Add cost breakdown charts

### 4.4 Phase 4: Analysis and Reporting
1. Implement cost-effectiveness calculations
2. Create comparison tools
3. Add export functionality

## 5. Testing Strategy

### 5.1 Unit Tests
- Test visit type determination logic
- Verify cost calculations
- Validate workload counting

### 5.2 Integration Tests
- Test T&E vs T&T cost differences
- Verify timeline accuracy
- Check cost aggregation

### 5.3 Validation Tests
- Compare with NHS cost calculator
- Verify against known scenarios
- Check edge cases