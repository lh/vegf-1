# Economic Analysis Testing Strategy

## Core Principle: NO REGRESSIONS

We must ensure that adding economic tracking does NOT break existing functionality. This document outlines tests to verify both existing behavior and new features.

## Part 1: Regression Tests (Ensure Nothing Breaks)

### 1.1 Time-Based Simulation Core Tests

```python
def test_time_based_simulation_unchanged():
    """Ensure time-based simulations produce same results with/without economic tracking."""
    # Run baseline simulation without economic tracking
    baseline_spec = load_protocol_spec('protocols/v2_time_based/aflibercept_treat_and_treat_time_based.yaml')
    baseline_runner = TimeBasedSimulationRunner(baseline_spec)
    baseline_results = baseline_runner.run('abs', n_patients=100, duration_years=2, seed=42)
    
    # Run same simulation with economic tracking
    enhanced_runner = TimeBasedSimulationRunnerWithResources(baseline_spec, resource_config=None)
    enhanced_results = enhanced_runner.run('abs', n_patients=100, duration_years=2, seed=42)
    
    # Core metrics must be identical
    assert baseline_results.total_injections == enhanced_results.total_injections
    assert baseline_results.final_vision_mean == enhanced_results.final_vision_mean
    assert baseline_results.discontinuation_rate == enhanced_results.discontinuation_rate
    assert len(baseline_results.patient_histories) == len(enhanced_results.patient_histories)
```

### 1.2 Disease Progression Tests

```python
def test_fortnightly_disease_progression_unchanged():
    """Verify disease state updates every 14 days as expected."""
    spec = load_protocol_spec('protocols/v2_time_based/aflibercept_tae_8week_min_time_based.yaml')
    runner = TimeBasedSimulationRunnerWithResources(spec, resource_config)
    
    # Track a single patient's disease states
    results = runner.run('abs', n_patients=1, duration_years=1, seed=123)
    patient = results.patient_histories['P001']
    
    # Verify disease state changes align with 14-day intervals
    state_changes = []
    for i in range(len(patient['disease_states']) - 1):
        if patient['disease_states'][i] != patient['disease_states'][i+1]:
            state_changes.append(patient['times'][i+1])
    
    # All state changes should be multiples of 14 days
    for time in state_changes:
        assert time % 14 == 0, f"Disease state changed at non-14-day interval: {time}"
```

### 1.3 Visit Schedule Tests

```python
def test_t_and_t_visit_schedule():
    """Verify T&T maintains correct fixed visit schedule."""
    spec = load_protocol_spec('protocols/v2_time_based/aflibercept_treat_and_treat_time_based.yaml')
    runner = TimeBasedSimulationRunnerWithResources(spec, resource_config)
    results = runner.run('abs', n_patients=10, duration_years=2, seed=456)
    
    for patient_id, history in results.patient_histories.items():
        visits = history['visits']
        
        # Loading phase: monthly (28 days)
        assert visits[1]['time'] - visits[0]['time'] == 28
        assert visits[2]['time'] - visits[1]['time'] == 28
        
        # Maintenance phase: bimonthly (56 days)
        for i in range(3, min(7, len(visits)-1)):
            expected_interval = 56
            actual_interval = visits[i+1]['time'] - visits[i]['time']
            assert abs(actual_interval - expected_interval) <= 7  # Allow 1 week window

def test_t_and_e_year_one_matches_t_and_t():
    """Verify T&E Year 1 is identical to T&T."""
    tte_spec = load_protocol_spec('protocols/v2_time_based/aflibercept_tae_8week_min_time_based.yaml')
    tnt_spec = load_protocol_spec('protocols/v2_time_based/aflibercept_treat_and_treat_time_based.yaml')
    
    tte_runner = TimeBasedSimulationRunnerWithResources(tte_spec, resource_config)
    tnt_runner = TimeBasedSimulationRunnerWithResources(tnt_spec, resource_config)
    
    tte_results = tte_runner.run('abs', n_patients=50, duration_years=1, seed=789)
    tnt_results = tnt_runner.run('abs', n_patients=50, duration_years=1, seed=789)
    
    # Year 1 injection counts should be very similar
    assert abs(tte_results.total_injections - tnt_results.total_injections) < 50  # <1 per patient
```

## Part 2: Visit Classification Tests

### 2.1 T&T Visit Type Tests

```python
def test_tnt_visit_classification():
    """Test correct visit type classification for T&T protocol."""
    classifier = VisitClassifier('T&T')
    
    # Loading phase
    assert classifier.get_visit_type(1, day=0) == 'injection_only'
    assert classifier.get_visit_type(2, day=28) == 'injection_only'
    assert classifier.get_visit_type(3, day=56) == 'injection_only'
    
    # Post-loading assessment
    assert classifier.get_visit_type(4, day=84, is_assessment=True) == 'decision_only'
    
    # Regular maintenance
    assert classifier.get_visit_type(5, day=112) == 'injection_only'
    assert classifier.get_visit_type(6, day=168) == 'injection_only'
    
    # Annual review (around day 365)
    assert classifier.get_visit_type(10, day=365, is_annual=True) == 'decision_only'
```

### 2.2 T&E Visit Type Tests

```python
def test_tae_visit_classification():
    """Test correct visit type classification for T&E protocol."""
    classifier = VisitClassifier('T&E')
    
    # Year 1: Same as T&T
    assert classifier.get_visit_type(1, day=0) == 'injection_only'
    assert classifier.get_visit_type(2, day=28) == 'injection_only'
    assert classifier.get_visit_type(3, day=56) == 'injection_only'
    assert classifier.get_visit_type(4, day=84, is_assessment=True) == 'decision_only'
    assert classifier.get_visit_type(5, day=112) == 'injection_only'
    
    # Year 2+: All visits have both
    assert classifier.get_visit_type(8, day=400) == 'decision_with_injection'
    assert classifier.get_visit_type(12, day=600) == 'decision_with_injection'
```

## Part 3: Resource Tracking Tests

### 3.1 Resource Usage Accumulation

```python
def test_resource_tracking_accuracy():
    """Verify resources are tracked correctly per visit."""
    tracker = ResourceTracker(load_resource_config('nhs_standard_resources.yaml'))
    
    # Track some visits
    monday = date(2024, 1, 15)  # Monday
    tracker.track_visit(monday, 'injection_only', 'P001')
    tracker.track_visit(monday, 'injection_only', 'P002')
    tracker.track_visit(monday, 'decision_with_injection', 'P003')
    
    # Check daily usage
    usage = tracker.get_daily_usage(monday)
    assert usage['injector'] == 3  # All 3 visits need injector
    assert usage['injector_assistant'] == 3
    assert usage['vision_tester'] == 1  # Only decision visit
    assert usage['oct_operator'] == 1
    assert usage['decision_maker'] == 1
    
    # Check sessions calculation
    injector_sessions = tracker.calculate_sessions_needed(monday, 'injector')
    assert injector_sessions == 3/14  # 3 procedures / 14 capacity per session
```

### 3.2 No Data = Error Tests

```python
def test_no_fallback_on_missing_data():
    """Ensure system fails fast with missing data."""
    tracker = ResourceTracker(load_resource_config('nhs_standard_resources.yaml'))
    
    # Should fail if asking for data that doesn't exist
    with pytest.raises(ValueError, match="No visit data available"):
        tracker.get_daily_usage(date(2024, 1, 16))
    
    # Should fail if visit type unknown
    with pytest.raises(KeyError, match="Unknown visit type"):
        tracker.track_visit(date(2024, 1, 15), 'unknown_type', 'P001')
```

## Part 4: Workload Pattern Tests

### 4.1 Daily Variation Tests

```python
def test_workload_shows_daily_variations():
    """Verify workload data shows actual daily patterns, no smoothing."""
    spec = load_protocol_spec('protocols/v2_time_based/aflibercept_treat_and_treat_time_based.yaml')
    runner = TimeBasedSimulationRunnerWithResources(spec, resource_config)
    results = runner.run('abs', n_patients=200, duration_years=1, seed=111)
    
    # Get daily workload for injectors
    daily_workload = results.daily_workload['injector']
    
    # Should see variations (not all same value)
    workload_values = list(daily_workload.values())
    assert len(set(workload_values)) > 50  # Many different values
    
    # Should have zero on weekends
    for date, workload in daily_workload.items():
        if date.weekday() >= 5:  # Saturday or Sunday
            assert workload == 0
```

### 4.2 Peak Detection Tests

```python
def test_peak_workload_identification():
    """Verify system correctly identifies peak demand days."""
    spec = load_protocol_spec('protocols/v2_time_based/aflibercept_treat_and_treat_time_based.yaml')
    runner = TimeBasedSimulationRunnerWithResources(spec, resource_config)
    results = runner.run('abs', n_patients=500, duration_years=0.5, seed=222)
    
    # Find peak days
    peak_analysis = results.get_peak_workload_analysis()
    
    # Peak should be in early months (loading phase)
    assert peak_analysis['injector']['peak_date'].month <= 3
    assert peak_analysis['injector']['peak_demand'] > 20  # Many patients in loading
```

## Part 5: Cost Calculation Tests

### 5.1 Cost Accuracy Tests

```python
def test_cost_calculation_from_actual_visits():
    """Verify costs are calculated from actual visits only."""
    spec = load_protocol_spec('protocols/v2_time_based/aflibercept_treat_and_treat_time_based.yaml')
    runner = TimeBasedSimulationRunnerWithResources(spec, resource_config)
    results = runner.run('abs', n_patients=10, duration_years=1, seed=333)
    
    # Manually calculate expected costs
    expected_total = 0
    for patient_id, history in results.patient_histories.items():
        for visit in history['visits']:
            if visit['injection_given']:
                expected_total += 355  # drug cost
                expected_total += 134  # injection procedure
            if visit['is_decision_visit']:
                expected_total += 75   # consultation
            if visit['oct_performed']:
                expected_total += 110  # OCT scan
    
    assert results.total_costs == expected_total
```

### 5.2 Average Cost Per Patient Tests

```python
def test_average_cost_per_patient_varying_enrollment():
    """Test correct average calculation with patients joining at different times."""
    # Create custom scenario with staggered enrollment
    results = run_staggered_enrollment_simulation()
    
    # Calculate patient-months correctly
    total_patient_months = 0
    for patient in results.patient_histories.values():
        months_in_study = (patient['last_visit_time'] - patient['enrollment_time']) / 30
        total_patient_months += months_in_study
    
    expected_average = results.total_costs / (total_patient_months / 12)
    assert abs(results.average_cost_per_patient - expected_average) < 1.0
```

## Part 6: Integration Tests

### 6.1 Full Simulation Smoke Test

```python
def test_full_simulation_with_all_features():
    """Run complete simulation with all economic features enabled."""
    spec = load_protocol_spec('protocols/v2_time_based/aflibercept_tae_8week_min_time_based.yaml')
    resource_config = load_resource_config('nhs_standard_resources.yaml')
    
    runner = TimeBasedSimulationRunnerWithResources(spec, resource_config)
    results = runner.run('abs', n_patients=1000, duration_years=5, seed=444)
    
    # Verify all components present
    assert hasattr(results, 'patient_histories')
    assert hasattr(results, 'daily_workload')
    assert hasattr(results, 'resource_usage')
    assert hasattr(results, 'total_costs')
    assert hasattr(results, 'cost_breakdown')
    
    # Sanity checks
    assert results.total_injections > 0
    assert results.total_costs > 0
    assert len(results.daily_workload) > 0
    assert all(role in results.resource_usage for role in resource_config['roles'])
```

### 6.2 Protocol Comparison Test

```python
def test_protocol_comparison_workload_difference():
    """Verify T&E vs T&T shows expected workload differences."""
    tte_spec = load_protocol_spec('protocols/v2_time_based/aflibercept_tae_8week_min_time_based.yaml')
    tnt_spec = load_protocol_spec('protocols/v2_time_based/aflibercept_treat_and_treat_time_based.yaml')
    
    resource_config = load_resource_config('nhs_standard_resources.yaml')
    
    tte_runner = TimeBasedSimulationRunnerWithResources(tte_spec, resource_config)
    tnt_runner = TimeBasedSimulationRunnerWithResources(tnt_spec, resource_config)
    
    tte_results = tte_runner.run('abs', n_patients=200, duration_years=3, seed=555)
    tnt_results = tnt_runner.run('abs', n_patients=200, duration_years=3, seed=555)
    
    # T&E should have more decision maker usage after year 1
    tte_decision_total = sum(tte_results.resource_usage['decision_maker'].values())
    tnt_decision_total = sum(tnt_results.resource_usage['decision_maker'].values())
    
    assert tte_decision_total > tnt_decision_total * 1.5  # Significantly more
```

## Test Execution Plan

1. **Run all regression tests first** - Ensure nothing breaks
2. **Run unit tests** - Verify individual components
3. **Run integration tests** - Verify system behavior
4. **Performance tests** - Ensure no significant slowdown

```bash
# Run regression tests
pytest tests/test_regression.py -v

# Run unit tests
pytest tests/test_visit_classification.py -v
pytest tests/test_resource_tracking.py -v
pytest tests/test_cost_calculation.py -v

# Run integration tests
pytest tests/test_integration.py -v

# Run all with coverage
pytest --cov=simulation_v2 --cov-report=html
```

## Critical Success Criteria

1. **Zero regressions** - All existing tests must pass
2. **Accurate tracking** - Every visit tracked with correct resources
3. **No smoothing** - Daily workload patterns preserved
4. **Fast failure** - Missing data causes immediate errors
5. **Performance** - Less than 10% slowdown vs baseline