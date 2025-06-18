# Resource and Cost Tracking Implementation Plan

## Overview
This document outlines the plan for adding resource tracking and cost analysis to the APE simulation system. The implementation will focus on the time-based simulation (ABS) as it will become the default engine.

## Key Requirements
1. Track resources needed at each timepoint during simulation
2. Calculate costs based on resource usage
3. Create two new pages: "Resources" and "Costs"
4. Integrate resource/cost comparisons into the existing Compare page
5. Maintain clean merge compatibility with ongoing ABS engine upgrades

## Available Cost Data

### Drug Costs (NHS actual cost including 20% VAT)
- **Aflibercept 2mg (Eylea)**: £548 per injection (£457 + VAT)
- **Aflibercept 8mg (Eylea HD)**: £407 per injection (£339 + VAT)
- **Ranibizumab (Lucentis)**: £623 per injection (£519 + VAT)
- **Ranibizumab biosimilar**: £353 per injection (£294 + VAT)
- **Bevacizumab compounded**: £60 per injection (£50 + VAT)
- **Faricimab (Vabysmo)**: £1,301 per injection (£1,084 + VAT)
- **Aflibercept biosimilar (projected)**: £274 per injection (£228 + VAT)

### Visit/Procedure Costs (from extracted data)
- Appointment costs range: £173,394 - £694,348 (aggregated)
- Need to extract unit costs for:
  - Injection visit
  - Monitoring visit
  - OCT scan
  - Consultation
  - Nurse time
  - Clinic overhead

## Data Model Design

### Resource Tracking
```python
@dataclass
class ResourceUsage:
    """Track resource usage at a specific timepoint"""
    time_point: float  # Days from simulation start
    patient_id: str
    resource_type: str  # 'drug', 'staff', 'equipment', 'facility'
    resource_name: str  # 'aflibercept_2mg', 'nurse', 'OCT_scanner', etc.
    quantity: float
    unit: str  # 'vials', 'hours', 'scans', etc.
    
@dataclass
class TimePointResources:
    """Aggregate resources needed at a specific time"""
    time_point: float
    resources: Dict[str, float]  # resource_name -> quantity
    patient_count: int
    active_patients: List[str]
```

### Cost Tracking
```python
@dataclass
class CostItem:
    """Individual cost item"""
    time_point: float
    patient_id: str
    cost_category: str  # 'drug', 'procedure', 'staff', 'overhead'
    item_name: str
    quantity: float
    unit_cost: float
    total_cost: float
    
@dataclass
class PatientCosts:
    """Track all costs for a patient"""
    patient_id: str
    total_cost: float
    cost_by_category: Dict[str, float]
    cost_timeline: List[CostItem]
    
@dataclass
class SimulationCosts:
    """Aggregate cost data for entire simulation"""
    total_cost: float
    cost_by_category: Dict[str, float]
    cost_by_timepoint: Dict[float, float]
    patient_costs: Dict[str, PatientCosts]
    average_cost_per_patient: float
```

## Implementation Architecture

### 1. Cost Configuration System
- Extend existing `cost_config.py` to support:
  - NHS-specific pricing with discount rates
  - Regional variations
  - Time-based price changes (e.g., biosimilar entry)
  - Bundle pricing (e.g., combined visit + injection)

### 2. Resource Tracker Module
```python
class ResourceTracker:
    """Track resource usage during simulation"""
    
    def record_injection(self, time_point: float, patient_id: str, drug_name: str):
        """Record drug usage for injection"""
        
    def record_visit(self, time_point: float, patient_id: str, visit_type: str):
        """Record resources for a clinic visit"""
        
    def record_procedure(self, time_point: float, patient_id: str, procedure: str):
        """Record procedure resource usage"""
        
    def get_resources_at_time(self, time_point: float) -> TimePointResources:
        """Get all resources needed at a specific time"""
        
    def get_resource_timeline(self) -> pd.DataFrame:
        """Get resource usage over time for visualization"""
```

### 3. Cost Calculator Module
```python
class CostCalculator:
    """Calculate costs based on resource usage"""
    
    def __init__(self, cost_config: CostConfig):
        self.cost_config = cost_config
        
    def calculate_visit_cost(self, visit_type: str, procedures: List[str]) -> float:
        """Calculate total cost for a visit"""
        
    def calculate_drug_cost(self, drug_name: str, dose: float = 1.0) -> float:
        """Calculate drug cost including wastage"""
        
    def calculate_period_costs(self, resources: List[ResourceUsage]) -> float:
        """Calculate total costs for a time period"""
```

### 4. Integration Points

#### ABS Engine Integration
- Hook into existing visit scheduling
- Track resources when visits are scheduled (not just when they occur)
- Handle cancellations and rescheduling

#### Results Storage
- Extend SimulationResults to include:
  - `resource_timeline: pd.DataFrame`
  - `cost_breakdown: Dict[str, Any]`
  - `resource_summary: Dict[str, Any]`

## Page Designs

### Resources Page
1. **Resource Timeline Visualization**
   - Stacked area chart showing resource usage over time
   - Categories: Drugs, Staff, Equipment, Facilities
   - Interactive tooltips with detailed breakdowns

2. **Resource Utilization Metrics**
   - Peak resource usage times
   - Average utilization rates
   - Resource bottlenecks identification

3. **Resource Planning Table**
   - Weekly/Monthly resource requirements
   - Exportable for operational planning

### Costs Page
1. **Cost Overview Dashboard**
   - Total simulation cost
   - Cost per patient (average, median, range)
   - Cost breakdown pie chart

2. **Cost Timeline Visualization**
   - Cumulative cost curve
   - Monthly/Quarterly cost bars
   - Cost by category over time

3. **Cost Driver Analysis**
   - Top cost drivers ranking
   - Cost variance analysis
   - What-if scenario comparison

4. **Patient Cost Distribution**
   - Histogram of patient costs
   - Cost quintiles analysis
   - High-cost patient identification

### Compare Page Integration
1. **Cost Comparison Metrics**
   - Total cost difference
   - Cost per patient comparison
   - Cost-effectiveness ratios

2. **Resource Comparison**
   - Resource utilization differences
   - Peak capacity requirements
   - Efficiency metrics

3. **Economic Analysis**
   - Incremental cost-effectiveness ratio (ICER)
   - Budget impact analysis
   - Resource reallocation opportunities

## Implementation Phases

### Phase 1: Foundation (No Code Yet)
1. Finalize cost data structure
2. Design resource tracking schema
3. Plan integration points with ABS engine
4. Create detailed UI mockups

### Phase 2: Core Implementation (After ABS Merge)
1. Implement ResourceTracker class
2. Implement CostCalculator class
3. Integrate with ABS engine visit scheduling
4. Extend SimulationResults storage

### Phase 3: Visualization
1. Build Resources page
2. Build Costs page
3. Add comparison metrics to Compare page
4. Implement export functionality

### Phase 4: Advanced Features
1. What-if scenario analysis
2. Budget constraint optimization
3. Resource allocation recommendations
4. Multi-site cost comparisons

## Testing Strategy
1. Unit tests for cost calculations
2. Integration tests with ABS engine
3. Validation against NHS reference costs
4. Performance testing with large simulations

## Future Enhancements
1. Real-time cost tracking during simulation
2. Machine learning for cost prediction
3. Integration with NHS costing databases
4. Multi-currency support for international comparisons

## Notes for Clean Merge
- All new code will be in separate modules
- No modifications to existing ABS engine code
- Use dependency injection for integration
- Configuration-driven approach for flexibility