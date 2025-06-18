# Heterogeneous ABS Engine Test Plan

Version: 1.0  
Date: 2025-01-18  
Status: Draft

## Test Strategy

This test plan covers unit tests, integration tests, and validation tests for the heterogeneous ABS engine. Tests are designed to ensure correctness, backward compatibility, and reproduction of real-world outcomes.

## Test Categories

### 1. Unit Tests

#### 1.0 Engine Selection Tests

**Test Class**: `TestABSFactory`

```python
def test_factory_selects_standard_engine():
    """Test factory returns standard engine for standard config."""
    # Given: Configuration without heterogeneity section
    # When: Create simulation via factory
    # Then: Returns AgentBasedSimulation instance
    
def test_factory_selects_heterogeneous_engine():
    """Test factory returns heterogeneous engine when appropriate."""
    # Given: Configuration with valid heterogeneity section
    # When: Create simulation via factory
    # Then: Returns HeterogeneousABS instance
    
def test_factory_with_disabled_heterogeneity():
    """Test factory returns standard engine when heterogeneity disabled."""
    # Given: Configuration with heterogeneity.enabled = false
    # When: Create simulation via factory
    # Then: Returns AgentBasedSimulation instance
    
def test_factory_console_output():
    """Test factory prints appropriate console messages."""
    # Given: Various configurations
    # When: Create simulations
    # Then: Verify console output matches engine selection
    
def test_factory_invalid_heterogeneity_fallback():
    """Test factory falls back to standard engine on invalid config."""
    # Given: Invalid trajectory proportions
    # When: Create simulation
    # Then: Returns standard engine with warning
```

#### 1.1 Configuration Parsing Tests

**Test Class**: `TestHeterogeneityConfigParser`

```python
def test_parse_valid_heterogeneity_section():
    """Test parsing a valid heterogeneity configuration section."""
    # Given: Protocol YAML with heterogeneity section
    # When: Parse configuration
    # Then: All parameters correctly extracted
    
def test_missing_heterogeneity_section():
    """Test behavior when heterogeneity section is missing."""
    # Given: Protocol YAML without heterogeneity section
    # When: Parse configuration
    # Then: Returns None, engine falls back to homogeneous
    
def test_disabled_heterogeneity():
    """Test when heterogeneity.enabled = false."""
    # Given: Heterogeneity section with enabled: false
    # When: Parse configuration
    # Then: Heterogeneity not activated
    
def test_invalid_trajectory_proportions():
    """Test validation when trajectory proportions don't sum to 1."""
    # Given: Proportions = [0.2, 0.3, 0.4]
    # When: Validate configuration
    # Then: Raises ValidationError
    
def test_invalid_distribution_parameters():
    """Test validation of distribution parameters."""
    # Given: Normal distribution with negative std
    # When: Validate configuration
    # Then: Raises ConfigurationError
    
def test_correlation_out_of_range():
    """Test correlation value validation."""
    # Given: correlation_with_baseline_va = 1.5
    # When: Validate configuration
    # Then: Raises ValidationError
```

#### 1.2 Patient Characteristic Assignment Tests

**Test Class**: `TestPatientCharacteristics`

```python
def test_trajectory_class_assignment():
    """Test random assignment respects proportions."""
    # Given: Proportions [0.25, 0.40, 0.35]
    # When: Assign 10,000 patients
    # Then: Actual proportions within 2% of target
    
def test_baseline_va_correlation():
    """Test correlation with baseline VA."""
    # Given: High baseline VA patients (>70)
    # When: Generate characteristics
    # Then: treatment_responder_type higher, disease_aggressiveness lower
    
def test_max_achievable_va_calculation():
    """Test ceiling calculation."""
    # Given: Various baseline VA values
    # When: Calculate max achievable VA
    # Then: Respects ceiling of 85, appropriate offsets
    
def test_distribution_sampling():
    """Test sampling from configured distributions."""
    # Given: Each distribution type (normal, lognormal, beta, uniform)
    # When: Sample 1000 values
    # Then: Mean and std match expected
    
def test_reproducible_with_seed():
    """Test deterministic behavior with seed."""
    # Given: Same seed
    # When: Generate patient characteristics twice
    # Then: Identical results
```

#### 1.3 Vision Update Tests

**Test Class**: `TestHeterogeneousVisionUpdate`

```python
def test_treatment_benefit_calculation():
    """Test heterogeneous treatment effect."""
    # Given: Patient with treatment_responder_type = 1.5
    # When: Apply treatment
    # Then: Benefit = base * 1.5 * ceiling_factor
    
def test_disease_progression_calculation():
    """Test heterogeneous progression."""
    # Given: Patient with disease_aggressiveness = 2.0
    # When: Calculate progression over 4 weeks
    # Then: Progression = base * 2.0 * 4
    
def test_ceiling_effect():
    """Test vision ceiling limits benefit."""
    # Given: Current VA = 80, max_achievable = 85
    # When: Calculate treatment benefit
    # Then: Benefit reduced by ceiling factor
    
def test_treatment_resistance():
    """Test declining efficacy over time."""
    # Given: Patient with resistance_rate = 0.1
    # When: Apply 10 treatments
    # Then: 10th treatment ~37% as effective as 1st
    
def test_catastrophic_event_trigger():
    """Test rare event occurrence."""
    # Given: Event probability = 0.001/month
    # When: Simulate 10,000 patient-months
    # Then: ~10 events occur (±3)
    
def test_vision_bounds():
    """Test vision stays within valid range."""
    # Given: Various update scenarios
    # When: Apply updates
    # Then: Vision always between 0 and 85
```

### 2. Integration Tests

#### 2.1 Full Simulation Tests

**Test Class**: `TestHeterogeneousSimulation`

```python
def test_heterogeneous_simulation_runs():
    """Test complete simulation execution."""
    # Given: Valid configuration with heterogeneity
    # When: Run 100 patients for 2 years
    # Then: Completes without errors, all patients have histories
    
def test_backward_compatibility():
    """Test engine produces compatible output format."""
    # Given: Heterogeneous simulation results
    # When: Pass to existing visualization pipeline
    # Then: All visualizations work correctly
    
def test_performance_overhead():
    """Test performance impact of heterogeneity."""
    # Given: 1000 patients, 5 years
    # When: Run both homogeneous and heterogeneous
    # Then: Heterogeneous < 20% slower
    
def test_memory_usage():
    """Test memory overhead."""
    # Given: 10,000 patient simulation
    # When: Compare memory usage
    # Then: < 1MB additional memory for heterogeneity
```

#### 2.2 Output Validation Tests

**Test Class**: `TestSimulationOutputs`

```python
def test_patient_history_structure():
    """Test visit records contain expected fields."""
    # Check all required fields present
    # Verify heterogeneity doesn't break structure
    
def test_event_log_consistency():
    """Test event log matches patient histories."""
    # Verify all visits in histories appear in event log
    # Check timing consistency
    
def test_validation_metrics_calculation():
    """Test validation metrics are computed correctly."""
    # Verify mean, std, correlations calculated
    # Check percentile calculations
```

### 3. Validation Tests (Seven-UP Reproduction)

#### 3.1 Population Statistics Tests

**Test Class**: `TestSevenUPValidation`

```python
def test_mean_vision_change():
    """Test 7-year mean change matches Seven-UP."""
    # Given: 1000+ patients, 7-year simulation
    # When: Calculate mean change
    # Then: -8.6 ± 2 letters (95% CI)
    
def test_standard_deviation():
    """Test outcome variability matches Seven-UP."""
    # Given: 7-year outcomes
    # When: Calculate SD
    # Then: 30 ± 3 letters
    
def test_outcome_distribution():
    """Test full distribution shape."""
    # Given: 7-year outcomes
    # When: Calculate percentiles
    # Then: Matches Seven-UP box plot
    
def test_extreme_outcomes():
    """Test proportion of extreme outcomes."""
    # Given: 7-year outcomes
    # When: Count >70 and <35 letters
    # Then: ~25% maintain >70, ~35% decline <35
```

#### 3.2 Correlation Tests

**Test Class**: `TestOutcomeCorrelations`

```python
def test_year2_year7_correlation():
    """Test early outcomes predict late outcomes."""
    # Given: 2-year and 7-year vision values
    # When: Calculate correlation
    # Then: r = 0.97 ± 0.02
    
def test_baseline_outcome_correlation():
    """Test baseline VA predicts outcomes."""
    # Given: Baseline and 7-year values
    # When: Analyze by baseline quartiles
    # Then: Higher baseline → better outcomes
    
def test_age_correlation():
    """Test age effect on outcomes."""
    # Given: Patients with age data
    # When: Correlate age with outcome
    # Then: Negative correlation observed
```

### 4. Edge Case Tests

**Test Class**: `TestEdgeCases`

```python
def test_all_good_responders():
    """Test when all patients are good responders."""
    # Override proportions to [1.0, 0, 0]
    # Verify outcomes better than average
    
def test_all_poor_responders():
    """Test when all patients are poor responders."""
    # Override proportions to [0, 0, 1.0]
    # Verify outcomes worse than average
    
def test_extreme_parameters():
    """Test with extreme heterogeneity parameters."""
    # Very high/low multipliers
    # Verify stability and bounds
    
def test_no_treatment():
    """Test natural history (no treatments)."""
    # Run without any treatments
    # Verify progression matches expectations
```

### 5. Configuration Variant Tests

**Test Class**: `TestConfigurationVariants`

```python
def test_minimal_heterogeneity_config():
    """Test with minimal configuration."""
    # Only trajectory classes, no other parameters
    
def test_maximal_heterogeneity_config():
    """Test with all features enabled."""
    # All parameters, events, correlations
    
def test_custom_validation_targets():
    """Test with different validation targets."""
    # Non-Seven-UP targets
    # Verify engine adapts
```

## Test Data

### 1. Test Configuration Files

Location: `tests/fixtures/heterogeneity/`

- `valid_heterogeneity.yaml` - Complete valid configuration
- `minimal_heterogeneity.yaml` - Minimum required parameters
- `invalid_proportions.yaml` - For validation testing
- `no_heterogeneity.yaml` - Missing section
- `disabled_heterogeneity.yaml` - enabled: false

### 2. Expected Outputs

- `seven_up_targets.json` - Validation targets
- `expected_distributions.json` - Distribution parameters

### 3. Baseline Comparisons

- Results from homogeneous engine for comparison
- Seven-UP study data for validation

## Test Execution

### Running Tests

```bash
# All heterogeneity tests
pytest tests/unit/test_heterogeneous_abs.py -v

# Validation tests only (slow)
pytest tests/validation/test_seven_up_validation.py -v

# Quick smoke tests
pytest tests/unit/test_heterogeneous_abs.py -k "config" -v

# With coverage
pytest tests/unit/test_heterogeneous_abs.py --cov=simulation.heterogeneous_abs
```

### Test Markers

```python
@pytest.mark.heterogeneity  # All heterogeneity tests
@pytest.mark.slow          # Long-running validation tests
@pytest.mark.validation    # Seven-UP validation tests
@pytest.mark.unit         # Fast unit tests
```

## Success Criteria

1. **Unit Tests**: 100% pass, >90% coverage
2. **Integration Tests**: All pass, no performance regression >20%
3. **Validation Tests**: 
   - Mean within 2 letters of target
   - SD within 3 letters of target
   - Correlation within 0.02 of target
   - Proportions within 5% of target

## Test Schedule

1. **Phase 1**: Unit tests (during development)
2. **Phase 2**: Integration tests (after engine complete)
3. **Phase 3**: Validation tests (before release)
4. **Phase 4**: Performance tests (optimization phase)