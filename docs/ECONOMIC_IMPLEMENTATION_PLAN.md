# Economic and Workload Analysis Implementation Plan

## Executive Summary

We need to implement a comprehensive economic and workload analysis system that tracks ACTUAL resource usage during simulations, NOT estimates. The system must support role-based resource tracking, daily workload patterns without smoothing, and cost calculations based on real patient pathways.

## Current State Analysis

### What We Have
1. **Time-Based Simulation Runner** (`TimeBasedSimulationRunner`)
   - Runs simulations with time-based disease progression
   - Tracks patient visits and outcomes
   - No economic tracking currently

2. **Protocol Specifications (TIME-BASED)**
   - T&E (Treat and Extend): `protocols/v2_time_based/aflibercept_tae_8week_min_time_based.yaml`
   - T&T (Treat and Treat): `protocols/v2_time_based/aflibercept_treat_and_treat_time_based.yaml`
   - Both use fortnightly (14-day) disease progression model
   - Both have economic parameters sections but not fully utilized

3. **Failed Implementation** (to be ignored)
   - Enhanced cost tracker that only estimates costs
   - Not integrated with actual simulation visits
   - Does not track resources or workload

### What We Need
1. **Resource Tracking During Simulation**
   - Track each visit with its resource requirements
   - Accumulate daily workload by role
   - Calculate costs based on actual visits

2. **Workload Analysis Page**
   - Show daily resource requirements by role
   - No smoothing - show actual peaks and troughs
   - Role-based capacity planning

3. **Economic Comparison**
   - Compare costs between protocols
   - Show impact of drug price changes
   - Resource utilization comparison

## Implementation Architecture

### Phase 1: Core Resource Tracking Infrastructure

#### 1.1 Resource Configuration System
```yaml
# protocols/resources/nhs_standard_resources.yaml
resources:
  roles:
    injector:
      capacity_per_session: 14
      description: "Administers injections"
    # ... other roles
  
  visit_requirements:
    injection_only:
      roles_needed:
        injector: 1
        injector_assistant: 1
      duration_minutes: 15
    # ... other visit types
```

#### 1.2 Resource Tracker Class
```python
# simulation_v2/economics/resource_tracker.py
class ResourceTracker:
    """Track resource usage during simulation."""
    
    def track_visit(self, date: datetime, visit_type: str, patient_id: str):
        """Record resource usage for a visit."""
    
    def get_daily_usage(self, date: datetime) -> Dict[str, int]:
        """Get resource usage for a specific date."""
    
    def calculate_sessions_needed(self, date: datetime, role: str) -> float:
        """Calculate sessions needed for a role on a date."""
```

#### 1.3 Visit Classification

**IMPORTANT:** Both protocols use TIME-BASED disease progression:
- Disease state updates every 14 days (fortnightly)
- Vision changes occur continuously, not just at visits
- Visits happen on scheduled intervals but disease progresses independently

- **T&E Protocol:**
  - Year 1: IDENTICAL to T&T (fixed intervals)
    - Visits 1-3: `injection_only` (monthly loading)
    - After visit 3: `decision_only` (post-loading assessment)
    - Visits 4-7: `injection_only` (bimonthly)
  - Year 2+: Treat and Extend begins
    - Visit 7 onwards: `decision_with_injection` (every visit has both)
    - Intervals adapt based on disease activity (56-112 days)
  
- **T&T Protocol:**
  - Visits 1-3: `injection_only` (monthly loading)
  - After visit 3: `decision_only` (post-loading assessment)
  - Visits 4+: `injection_only` (bimonthly forever)
  - Annual reviews: `decision_only` (at 12, 24, 36 months etc.)
  - Fixed 56-day intervals after loading

### Phase 2: Integration with Simulation Engine

#### 2.1 Enhanced Visit Tracking
```python
# Modify simulation engines to track visits
visit_record = {
    'date': visit_date,
    'patient_id': patient.id,
    'visit_type': self._classify_visit_type(visit_number, protocol_type),
    'injection_given': injection_given,
    'oct_performed': oct_performed,
    'costs': {
        'drug': drug_cost if injection_given else 0,
        'procedure': procedure_cost,
        'consultation': consultation_cost if decision_visit else 0
    }
}
```

#### 2.2 Time-Based Engine with Resources
```python
# simulation_v2/engines/abs_engine_time_based_with_resources.py
class ABSEngineTimeBasedWithResources(ABSEngineTimeBasedWithParams):
    """Time-based engine with resource tracking."""
    
    def __init__(self, resource_config, ...):
        super().__init__(...)
        self.resource_tracker = ResourceTracker(resource_config)
```

### Phase 3: Workload Analysis Page

#### 3.1 Page Structure
- Title: "Workload and Economic Analysis"
- Sections:
  1. Enhanced Workload Timeline
  2. Cost Summary
  3. Resource Utilization Dashboard
  4. Staffing Requirements

#### 3.2 Workload Timeline Chart
- Multi-series chart (one line per role)
- X-axis: Days
- Y-axis: Sessions needed
- Weekend highlighting
- NO SMOOTHING

#### 3.3 Cost Summary
- Total simulation cost
- Average cost per patient
- Cost breakdown by component
- Drug price sensitivity slider

### Phase 4: Enhanced Comparison Page

#### 4.1 Workload Comparison
- Side-by-side daily workload charts
- Peak staffing comparison
- Resource utilization differences

#### 4.2 Economic Comparison
- Total cost per patient
- Drug cost impact analysis
- Year 1 vs Year 2+ breakdown

## Testing Strategy

### Unit Tests

#### Test 1: Resource Configuration Loading
```python
def test_resource_config_loading():
    """Test loading resource configuration from YAML."""
    config = load_resource_config('nhs_standard_resources.yaml')
    assert 'roles' in config
    assert 'injector' in config['roles']
    assert config['roles']['injector']['capacity_per_session'] == 14
```

#### Test 2: Visit Classification
```python
def test_visit_classification_t_and_e():
    """Test T&E visit classification."""
    # Visit 1-3: decision_with_injection
    assert classify_visit('T&E', visit_number=1) == 'decision_with_injection'
    assert classify_visit('T&E', visit_number=3) == 'decision_with_injection'
    # All subsequent: decision_with_injection
    assert classify_visit('T&E', visit_number=7) == 'decision_with_injection'
    
def test_visit_classification_t_and_t():
    """Test T&T visit classification."""
    # Visit 1-3: injection_only
    assert classify_visit('T&T', visit_number=1) == 'injection_only'
    assert classify_visit('T&T', visit_number=3) == 'injection_only'
    # Annual reviews: decision_only
    assert classify_visit('T&T', visit_number=4, is_annual=True) == 'decision_only'
```

#### Test 3: Resource Tracking
```python
def test_resource_tracking():
    """Test resource usage tracking."""
    tracker = ResourceTracker(config)
    
    # Track injection visit
    tracker.track_visit(date(2024, 1, 15), 'injection_only', 'P001')
    
    # Check daily usage
    usage = tracker.get_daily_usage(date(2024, 1, 15))
    assert usage['injector'] == 1
    assert usage['injector_assistant'] == 1
    
    # Check sessions calculation
    sessions = tracker.calculate_sessions_needed(date(2024, 1, 15), 'injector')
    assert sessions == 1/14  # 1 procedure / 14 capacity
```

#### Test 4: Cost Calculation
```python
def test_cost_calculation_no_fallbacks():
    """Test cost calculation with no estimates or fallbacks."""
    # Should fail if no actual data
    with pytest.raises(ValueError, match="No visit data available"):
        calculate_cost_without_visits()
    
    # Should calculate from actual visits only
    visits = [
        {'costs': {'drug': 355, 'procedure': 134}},
        {'costs': {'drug': 355, 'procedure': 134, 'consultation': 75}}
    ]
    total = calculate_total_cost(visits)
    assert total == 355 + 134 + 355 + 134 + 75
```

### Integration Tests

#### Test 5: Full Simulation with Resources
```python
def test_simulation_with_resource_tracking():
    """Test complete simulation with resource tracking."""
    spec = load_protocol_spec('protocols/v2_time_based/aflibercept_treat_and_treat_time_based.yaml')
    runner = TimeBasedSimulationRunnerWithResources(spec, resource_config)
    
    results = runner.run('abs', n_patients=100, duration_years=2, seed=42)
    
    # Check resource data is collected
    assert hasattr(results, 'resource_usage')
    assert hasattr(results, 'daily_workload')
    assert hasattr(results, 'total_costs')
    
    # Verify no smoothing
    workload = results.daily_workload['injector']
    # Should see variations (not all same value)
    assert len(set(workload.values())) > 1
```

#### Test 6: Protocol Comparison
```python
def test_protocol_workload_comparison():
    """Test comparing workload between protocols."""
    # Run T&E
    te_results = run_simulation('treat_and_extend', n_patients=100)
    
    # Run T&T  
    tt_results = run_simulation('treat_and_treat', n_patients=100)
    
    # T&E should have more decision maker usage
    assert sum(te_results.resource_usage['decision_maker'].values()) > \
           sum(tt_results.resource_usage['decision_maker'].values())
    
    # T&T might have slightly more injections
    assert sum(tt_results.resource_usage['injector'].values()) >= \
           sum(te_results.resource_usage['injector'].values())
```

### UI Testing (Manual)

Since automated UI testing is difficult, we'll need manual verification:

1. **Workload Chart Verification**
   - Shows daily variations (no smoothing)
   - Weekends properly highlighted
   - All roles displayed with correct colors
   - Y-axis shows sessions needed

2. **Cost Summary Verification**
   - Drug price slider updates costs dynamically
   - Total cost matches sum of individual visits
   - Average per patient calculated correctly

3. **Resource Dashboard Verification**
   - Peak demand identified correctly
   - Utilization percentages accurate
   - Bottlenecks highlighted

4. **Export Verification**
   - PDF contains all data
   - Charts render correctly
   - Tables formatted properly

## Implementation Order

### Week 1: Core Infrastructure
1. Create resource configuration YAML structure
2. Implement ResourceTracker class
3. Write unit tests for resource tracking
4. Create visit classification logic

### Week 2: Simulation Integration  
1. Extend TimeBasedSimulationRunner with resources
2. Modify ABSEngine to track visits
3. Integration tests for full simulation
4. Verify data collection

### Week 3: Workload Analysis Page
1. Create new Streamlit page
2. Implement workload timeline chart
3. Add cost summary section
4. Resource utilization dashboard

### Week 4: Comparison and Polish
1. Enhance comparison page
2. Add export functionality
3. Final testing and bug fixes
4. Documentation

## Key Design Decisions

1. **No Estimates or Fallbacks**
   - If data is missing, fail with clear error
   - Only show actual tracked data

2. **Role-Based Architecture**
   - All resources defined by role, not job title
   - Configurable capacities and requirements

3. **Visit-Level Tracking**
   - Every visit tracked with full details
   - Resource usage calculated per visit

4. **Daily Granularity**
   - Show actual daily patterns
   - No weekly or monthly averaging

5. **Protocol-Specific Logic**
   - T&E: All visits are decision+injection after loading
   - T&T: Mostly injection-only with annual decisions

## Success Metrics

1. **Accurate Resource Tracking**
   - Every visit has resource data
   - Daily totals match individual visits

2. **Realistic Workload Patterns**
   - Daily variations visible
   - Peak days identified correctly

3. **Correct Cost Calculations**
   - Total costs match sum of visits
   - Per-patient average accounts for varying enrollment

4. **UI Compliance**
   - All charts follow Tufte principles
   - Only semantic colors used
   - Carbon design system buttons

5. **No Regressions**
   - Existing simulation functionality unchanged
   - Performance within 10% of baseline

## Risk Mitigation

1. **Performance Impact**
   - Resource tracking adds overhead
   - Mitigate: Efficient data structures, batch operations

2. **Memory Usage**
   - Storing per-visit data for large simulations
   - Mitigate: Streaming to disk if needed

3. **Configuration Complexity**
   - Many parameters to manage
   - Mitigate: Sensible defaults, validation, clear docs

4. **UI Responsiveness**
   - Large datasets for charts
   - Mitigate: Data aggregation, progressive loading

## Next Steps

1. Review and approve this plan
2. Create feature branch from main
3. Start with Phase 1 implementation
4. Weekly progress reviews