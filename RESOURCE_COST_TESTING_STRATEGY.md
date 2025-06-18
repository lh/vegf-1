# Resource and Cost Tracking Testing Strategy

## Overview
This document defines the testing approach for the resource tracking and cost analysis features. All tests must use real simulation data and validate against known NHS reference costs.

## Unit Test Requirements

### 1. Cost Calculation Tests
```python
class TestCostCalculator:
    """Test individual cost calculation functions"""
    
    def test_drug_cost_with_vat(self):
        """Verify drug costs include 20% VAT"""
        # Given: Aflibercept generic net price £228
        # When: Calculate NHS cost
        # Then: Should return £273.60 (includes 20% VAT)
        
    def test_visit_component_aggregation(self):
        """Verify visit costs sum correctly"""
        # Given: Injection visit components
        # - Nurse time: 30 min @ £54/hr = £27
        # - Injection room: £50
        # - Consumables: £15
        # - Visual acuity test: £15
        # Then: Total should be £107
        
    def test_time_based_pricing(self):
        """Verify biosimilar entry changes prices"""
        # Given: Date before 2025-06-16
        # Then: Aflibercept biosimilar not available
        # Given: Date after 2025-06-16  
        # Then: Aflibercept biosimilar £274 (inc VAT)
```

### 2. Resource Tracking Tests
```python
class TestResourceTracker:
    """Test resource usage tracking"""
    
    def test_concurrent_resource_counting(self):
        """Verify peak concurrent usage calculation"""
        # Given: Multiple overlapping appointments
        # When: Calculate peak usage
        # Then: Should identify maximum concurrent resources
        
    def test_resource_aggregation_by_type(self):
        """Verify resources aggregate correctly by category"""
        # Given: Mixed resource usage events
        # When: Aggregate by type
        # Then: Totals should match sum of individual events
        
    def test_cancelled_appointment_handling(self):
        """Verify cancelled appointments don't consume resources"""
        # Given: Scheduled then cancelled appointment
        # When: Calculate resource usage
        # Then: Resources should be released
```

### 3. Data Structure Tests
```python
class TestDataStructures:
    """Test cost and resource data models"""
    
    def test_cost_item_immutability(self):
        """Verify cost items cannot be modified after creation"""
        
    def test_resource_usage_validation(self):
        """Verify resource usage constraints"""
        # - Quantity must be positive
        # - Time points must be within simulation bounds
        # - Patient IDs must exist
```

## Integration Test Scenarios

### 1. End-to-End Patient Journey
```python
def test_patient_complete_journey():
    """Test complete patient treatment with cost tracking"""
    # Given: Patient starting treatment
    # When: Complete 2-year treatment journey
    # Then: Verify:
    # - Total costs match expected range
    # - Resource usage aligns with visit schedule
    # - No missing cost components
```

### 2. Multi-Patient Simulation
```python
def test_large_simulation_costs():
    """Test cost accumulation for 1000+ patients"""
    # Given: 1000 patient simulation
    # When: Run complete simulation with tracking
    # Then: Verify:
    # - Total costs scale linearly
    # - Resource peaks identified correctly
    # - Memory usage remains bounded
```

### 3. Treatment Switching
```python
def test_treatment_switch_costs():
    """Test cost implications of treatment changes"""
    # Given: Patient on Eylea 2mg
    # When: Switch to aflibercept generic
    # Then: Verify:
    # - Switch administration cost applied
    # - Drug costs change appropriately
    # - Resource usage updated
```

## Validation Approach

### 1. NHS Reference Cost Validation
- Compare calculated costs against published NHS reference costs
- Tolerance: ±5% for aggregated costs
- Document any deviations with justification

### 2. Cross-Simulation Validation
- Run identical patient cohorts through both ABS and DES engines
- Verify resource usage patterns are consistent
- Cost totals should match within 1%

### 3. Manual Spot Checks
- Select 10 random patients per simulation
- Manually calculate expected costs
- Compare with system-generated values
- All values must match exactly

## Performance Benchmarks

### 1. Tracking Overhead
```python
def benchmark_tracking_overhead():
    """Measure performance impact of resource tracking"""
    # Baseline: Run simulation without tracking
    # With tracking: Run same simulation with full tracking
    # Target: <5% performance degradation
    # Maximum: <100ms per patient
```

### 2. Memory Usage
```python
def benchmark_memory_usage():
    """Measure memory consumption"""
    # Small simulation: 100 patients
    # Medium simulation: 1,000 patients  
    # Large simulation: 10,000 patients
    # Target: Linear memory growth
    # Maximum: 100KB per patient
```

### 3. Query Performance
```python
def benchmark_query_performance():
    """Measure data retrieval speed"""
    # Test queries:
    # - Total cost calculation: <100ms
    # - Resource timeline generation: <500ms
    # - Patient cost distribution: <200ms
    # - Peak usage identification: <300ms
```

### 4. Export Performance
```python
def benchmark_export_performance():
    """Measure export generation speed"""
    # CSV export (10k patients): <5 seconds
    # PDF report generation: <10 seconds
    # Excel with charts: <15 seconds
```

## Test Data Requirements

### 1. Reference Datasets
- Known patient journeys with pre-calculated costs
- Edge cases: early discontinuation, max injections
- Validation against real NHS trust data (anonymized)

### 2. Synthetic Test Scenarios
**IMPORTANT**: These are ONLY for unit testing, never for demos
- Minimum case: 1 injection, immediate discontinuation
- Maximum case: Monthly injections for 5 years
- Typical case: Based on real treatment patterns

### 3. Performance Test Data
- Small: 100 patients, 2 years
- Medium: 1,000 patients, 5 years
- Large: 10,000 patients, 5 years
- Stress: 50,000 patients, 10 years

## Continuous Validation

### 1. Automated Checks
- Run validation suite on every commit
- Check for cost calculation regressions
- Verify resource conservation laws

### 2. Monthly Validation
- Compare with updated NHS reference costs
- Validate against new clinical data
- Review and update test thresholds

### 3. Release Validation
- Full end-to-end testing
- Performance regression testing
- User acceptance testing with clinicians

## Test Implementation Priority

1. **Critical (Week 1)**
   - Drug cost calculations with VAT
   - Basic resource tracking
   - Data structure validation

2. **Important (Week 2)**
   - Visit cost aggregation
   - Integration with ABS engine
   - Performance benchmarks

3. **Enhanced (Week 3)**
   - Complex patient journeys
   - Edge case handling
   - Export functionality

## Success Criteria

All tests must pass with:
- 100% accuracy for individual calculations
- ±1% tolerance for aggregated values
- No memory leaks over extended runs
- Performance targets met or exceeded
- Zero data loss or corruption