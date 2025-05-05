# Enhanced Discontinuation DES Integration Tests

This document explains the implementation and structure of integration tests for the Enhanced Discontinuation Model with Discrete Event Simulation (DES).

## Overview

The integration tests for the Enhanced Discontinuation Model with DES ensure that the discontinuation logic works correctly in the context of the DES implementation. These tests verify different discontinuation types, monitoring schedules, clinician variation, and end-to-end patient pathways.

## Test Structure

The tests are implemented in the `EnhancedDiscontinuationDESTest` class in `tests/integration/test_enhanced_discontinuation_des.py`. This class includes methods to:

1. Set up test configurations
2. Create test patient states
3. Verify discontinuation decisions
4. Check monitoring schedules
5. Validate complete patient pathways

## Test Methods

### Direct Component Testing Approach

Unlike the ABS integration tests which use full simulation-based testing, the DES tests use a direct component testing approach. This means:

- Tests directly interact with the `EnhancedDiscontinuationManager` and other components
- Patient states are created directly rather than through simulation
- Verification is done on individual component outputs rather than simulation results

This approach provides several benefits:
- Faster execution
- More precise control of test scenarios
- Clearer failure messages
- Less dependence on simulation internals

### Key Test Cases

The test suite includes tests for:

1. **Stable Max Interval Discontinuation**: Tests that patients who meet stable max interval criteria are correctly discontinued

2. **Administrative Discontinuation**: Tests that random administrative discontinuations occur with the expected probability

3. **Treatment Duration Discontinuation**: Tests that patients are discontinued after the threshold treatment duration

4. **Premature Discontinuation**: Tests that premature discontinuations can occur before max interval is reached

5. **No Monitoring for Administrative Cessation**: Tests that administrative cessations don't result in monitoring visits

6. **Planned Monitoring Schedule**: Tests that planned cessations result in the correct monitoring schedule

7. **Clinician Influence on Retreatment**: Tests that clinician risk tolerance affects retreatment decisions

8. **Complete Patient Pathway**: Tests the full sequence: stable discontinuation → monitoring → recurrence → retreatment

## Implementation Details

### Mock Configuration

A `MockSimulationConfig` class is used to provide controlled test configurations. This allows tests to manipulate specific parameters like:

- Discontinuation probabilities
- Monitoring schedules
- Clinician characteristics

### Patient State Structure

The DES implementation uses dictionaries for patient state representation. The key structure includes:

```python
patient_state = {
    "disease_activity": {
        "fluid_detected": bool,
        "consecutive_stable_visits": int,
        "max_interval_reached": bool,
        "current_interval": int
    },
    "treatment_status": {
        "active": bool,
        "recurrence_detected": bool,
        "weeks_since_discontinuation": int,
        "cessation_type": str
    },
    "disease_characteristics": {
        "has_PED": bool  # Pigment Epithelial Detachment
    }
}
```

### Utility Methods

The test class includes utility methods to:

- Count discontinuations by type
- Count monitoring visits
- Count retreatments
- Run simulations with specific configurations

## Design Decisions

1. **Direct Testing vs. Simulation**: We chose direct testing over simulation testing for robustness and clarity.

2. **Controlled Test Data**: All test data is explicitly created rather than relying on random generation to ensure reproducibility.

3. **Component Isolation**: Tests focus on specific component behaviors rather than end-to-end simulation output.

4. **Sphinx Documentation**: Tests include detailed docstrings following Sphinx format to facilitate documentation generation.

## Running the Tests

The tests can be run using:

```bash
python -m unittest tests/integration/test_enhanced_discontinuation_des.py
```

Or with a specific test:

```bash
python -m unittest tests.integration.test_enhanced_discontinuation_des.EnhancedDiscontinuationDESTest.test_stable_max_interval_discontinuation
```