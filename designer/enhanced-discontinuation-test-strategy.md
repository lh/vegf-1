# Enhanced Discontinuation Model Test Strategy

**Author:** Cline  
**Date:** May 3, 2025  
**Version:** 1.0

## Overview

This document outlines the comprehensive test strategy for the enhanced discontinuation model as described in the design and implementation plan documents. The test strategy focuses on integration tests for both ABS and DES implementations, which are the next priority in the implementation plan.

## Test Approach

We'll create a comprehensive test suite that:

1. Sets up small-scale simulations with controlled parameters
2. Tests each discontinuation type in isolation
3. Verifies patient pathways through the entire treatment-discontinuation-monitoring-retreatment cycle
4. Validates statistics collection against expected values

## Test Suite Structure

We'll create two parallel test files:

1. `tests/integration/test_enhanced_discontinuation_abs.py`
2. `tests/integration/test_enhanced_discontinuation_des.py`

Each file will contain similar test cases but tailored to the specific implementation (ABS or DES). This parallel structure will help ensure consistent behavior across both simulation types.

## Test Configuration Approach

For controlled testing, we'll create:

1. **Test-specific YAML configurations** with deterministic parameters
2. **Mock patient states** with predefined characteristics
3. **Fixed random seeds** to ensure reproducible results

## Detailed Test Cases

### 1. Basic Discontinuation Tests

**Purpose:** Verify basic discontinuation functionality for each cessation type.

```python
def test_stable_max_interval_discontinuation(self):
    """Test that patients who meet stable max interval criteria are discontinued."""
    # Set up configuration with 100% discontinuation probability for stable max interval
    # Run simulation with short duration
    # Verify patients are discontinued with the correct cessation type
    # Check discontinuation statistics

def test_random_administrative_discontinuation(self):
    """Test that administrative discontinuations occur at the expected rate."""
    # Similar setup with high administrative discontinuation probability
    
def test_treatment_duration_discontinuation(self):
    """Test that duration-based discontinuations occur after the threshold period."""
    # Setup with high time-based discontinuation probability
    
def test_premature_discontinuation(self):
    """Test that premature discontinuations can occur before max interval is reached."""
    # Setup with high premature discontinuation probability
```

### 2. Monitoring Schedule Tests

**Purpose:** Verify the correct monitoring schedule is applied based on cessation type.

```python
def test_planned_monitoring_schedule(self):
    """Test that planned cessation results in the correct monitoring schedule."""
    # Force stable_max_interval discontinuation
    # Verify monitoring visits are scheduled at the correct intervals
    # Check visit counts match expected schedule for planned cessation

def test_unplanned_monitoring_schedule(self):
    """Test that premature/time-based cessation results in more frequent monitoring."""
    # Force premature discontinuation
    # Verify more frequent monitoring schedule is applied
    # Check visit counts match expected schedule for unplanned cessation

def test_no_monitoring_for_administrative_cessation(self):
    """Test that administrative cessation results in no monitoring visits."""
    # Force administrative discontinuation
    # Verify no monitoring visits are scheduled
    # Check patient pathway ends after discontinuation
```

### 3. Clinician Variation Tests

**Purpose:** Verify clinician characteristics affect discontinuation and retreatment decisions.

```python
def test_adherent_clinician_follows_protocol(self):
    """Test that adherent clinicians generally follow the protocol."""
    # Setup with adherent clinicians only
    # Force borderline discontinuation scenario
    # Verify most patients follow the protocol-recommended path
    # Check statistics on protocol adherence

def test_non_adherent_clinician_overrides_protocol(self):
    """Test that non-adherent clinicians may override protocol decisions."""
    # Setup with non-adherent clinicians only
    # Create scenarios where protocol would recommend discontinuation
    # Verify significant percentage of decisions deviate from protocol
    # Check for premature discontinuations or continued treatment

def test_clinician_influence_on_retreatment(self):
    """Test that clinician risk tolerance affects retreatment decisions."""
    # Set up discontinued patients with disease recurrence
    # Test with different clinician profiles
    # Verify conservative clinicians retreat more frequently
    # Check retreatment statistics by clinician profile
```

### 4. End-to-End Patient Pathway Tests

**Purpose:** Verify complete patient pathways through discontinuation, monitoring, and retreatment.

```python
def test_stable_discontinuation_monitoring_no_recurrence_pathway(self):
    """Test patient pathway: stable discontinuation → monitoring → no recurrence."""
    # Force stable discontinuation
    # Configure no disease recurrence
    # Verify patient completes monitoring without retreatment
    # Check final patient state and statistics

def test_stable_discontinuation_monitoring_recurrence_retreatment_pathway(self):
    """Test patient pathway: stable discontinuation → monitoring → recurrence → retreatment."""
    # Force stable discontinuation
    # Configure disease recurrence at specific monitoring visit
    # Verify patient is retreated and returns to active treatment
    # Check treatment phase reset to loading
    # Verify treatment statistics reflect retreatment

def test_premature_discontinuation_higher_recurrence_pathway(self):
    """Test patient pathway: premature discontinuation → faster recurrence → retreatment."""
    # Force premature discontinuation
    # Configure higher recurrence probability
    # Verify faster recurrence compared to stable discontinuation
    # Check recurrence timing aligns with configured probabilities

def test_administrative_cessation_no_monitoring_pathway(self):
    """Test patient pathway: administrative cessation → no monitoring."""
    # Force administrative discontinuation
    # Verify no monitoring visits occur
    # Check patient remains discontinued
```

### 5. Statistics Collection Tests

**Purpose:** Verify statistics are correctly collected and can be used for analysis.

```python
def test_discontinuation_statistics_by_type(self):
    """Test that discontinuation statistics are correctly collected by type."""
    # Run simulation with all discontinuation types
    # Get discontinuation manager statistics
    # Verify counts for each discontinuation type
    # Check total discontinuations matches sum of individual types

def test_retreatment_statistics_by_type(self):
    """Test that retreatment statistics are correctly collected by type."""
    # Configure different recurrence and retreatment rates by cessation type
    # Run simulation with all discontinuation types and forced recurrences
    # Check retreatment rates by cessation type match configuration
    
def test_clinician_decision_statistics(self):
    """Test that clinician decision statistics are correctly collected."""
    # Configure different clinician profiles
    # Force scenarios requiring clinician decisions
    # Check statistics on protocol adherence vs overrides
    # Verify decisions by clinician profile match expected patterns
```

### 6. Clinical Validation Tests

**Purpose:** Verify the model produces results consistent with published clinical data.

```python
def test_recurrence_rates_match_artiaga_study(self):
    """Test that recurrence rates over time match the Artiaga study values."""
    # Configure simulation with parameters matching Artiaga study
    # Run 3-5 year simulation with stable discontinuations
    # Check 1-year, 3-year, and 5-year cumulative recurrence rates
    # Verify rates fall within confidence intervals of published data

def test_clinician_adherence_matches_literature(self):
    """Test that clinician adherence patterns match published patterns."""
    # Configure clinicians with published adherence rates
    # Run simulation with standard protocol
    # Measure deviations from protocol
    # Compare to literature values for protocol adherence
```

## Implementation Details

### 1. Test Configuration Files

We'll create test-specific YAML configuration files in `tests/integration/configs/` with the following naming convention:

```
test_[simulation_type]_[test_case].yaml
```

For example:
- `test_abs_stable_discontinuation.yaml`
- `test_des_clinician_variation.yaml`

These configurations will have deterministic parameters to ensure reproducible test results:

```yaml
# Example test configuration for stable discontinuation
discontinuation:
  enabled: true
  criteria:
    stable_max_interval:
      consecutive_visits: 3
      probability: 1.0  # Force discontinuation
      interval_weeks: 16
    random_administrative:
      annual_probability: 0.0  # Disable
    treatment_duration:
      threshold_weeks: 520  # Very high to disable
      probability: 0.0  # Disable
    premature:
      min_interval_weeks: 8
      probability_factor: 0.0  # Disable
```

### 2. Test Base Classes

We'll create base test classes for common functionality:

```python
class EnhancedDiscontinuationTestBase(unittest.TestCase):
    """Base class for enhanced discontinuation tests."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Set fixed random seed
        np.random.seed(42)
        
        # Load default test configuration
        self.config = self._load_config("default_test_config.yaml")
    
    def _load_config(self, config_name):
        """Load a test configuration."""
        config_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "configs",
            config_name
        )
        return SimulationConfig.from_yaml(config_path)
    
    def _run_simulation(self, config, duration_days=365, num_patients=10):
        """Run a simulation with the given configuration."""
        # Override simulation parameters
        config.duration_days = duration_days
        config.num_patients = num_patients
        
        # Create and run simulation
        # Implementation-specific (ABS or DES)
        
    def _count_discontinuations_by_type(self, patient_histories):
        """Count discontinuations by type in patient histories."""
        # Implementation-specific (ABS or DES)
```

### 3. ABS-Specific Implementation

```python
class EnhancedDiscontinuationABSTest(EnhancedDiscontinuationTestBase):
    """Test cases for enhanced discontinuation in ABS implementation."""
    
    def _run_simulation(self, config, duration_days=365, num_patients=10):
        """Run an ABS simulation with the given configuration."""
        # Override simulation parameters
        config.duration_days = duration_days
        config.num_patients = num_patients
        
        # Create and run simulation
        sim = TreatAndExtendABS(config)
        return sim.run()
    
    def _count_discontinuations_by_type(self, patient_histories):
        """Count discontinuations by type in patient histories."""
        counts = {
            "stable_max_interval": 0,
            "random_administrative": 0,
            "treatment_duration": 0,
            "premature": 0,
            "total": 0
        }
        
        for patient_id, visits in patient_histories.items():
            for visit in visits:
                if "treatment_status" in visit and visit["treatment_status"].get("cessation_type"):
                    cessation_type = visit["treatment_status"]["cessation_type"]
                    counts[cessation_type] = counts.get(cessation_type, 0) + 1
                    counts["total"] += 1
                    break  # Count each patient only once
        
        return counts
```

### 4. DES-Specific Implementation

Similar to the ABS implementation, but adapted for the DES structure.

## Test Execution Strategy

For each test:

1. Create a controlled YAML configuration specifically for that test
2. Set deterministic parameters (e.g., probabilities of 0 or 1 for targeted testing)
3. Use specific random seeds
4. Run small-scale simulations (10-20 patients, 1-2 years)
5. Check specific outcomes and statistics against expected values

This approach will allow us to validate each component of the enhanced discontinuation model independently, then test them together in the end-to-end pathway tests.

## Test Implementation Plan

### Phase 1: Basic Framework (Week 1)

1. Create test directory structure and base classes
2. Implement basic configuration loading and simulation running
3. Create test configurations for each discontinuation type
4. Implement basic discontinuation tests

### Phase 2: Monitoring and Clinician Tests (Week 2)

1. Implement monitoring schedule tests
2. Implement clinician variation tests
3. Create test configurations for different clinician profiles

### Phase 3: End-to-End and Statistics Tests (Week 3)

1. Implement end-to-end patient pathway tests
2. Implement statistics collection tests
3. Create test configurations for different patient pathways

### Phase 4: Clinical Validation Tests (Week 4)

1. Implement clinical validation tests
2. Create test configurations matching clinical study parameters
3. Run comprehensive test suite and fix any issues

## Expected Outcomes

1. Comprehensive test coverage for both ABS and DES implementations
2. Validation of all discontinuation types and their specific behaviors
3. Verification of clinician variation effects on treatment decisions
4. Confirmation of correct statistics collection for analysis
5. Validation against clinical data to ensure realistic simulation results

## References

1. Aslanis et al. (2021): Prospective study of treatment discontinuation after treat-and-extend
2. Artiaga et al. (2023): Retrospective study of treatment discontinuation with long-term follow-up
3. Arendt et al.: Study of discontinuation after three 16-week intervals
4. ALTAIR Study (2020): Japanese treat-and-extend study with 2-week vs. 4-week adjustments
5. Comprehensive AMD Parameters document (meta/comprehensive-amd-parameters.md)
