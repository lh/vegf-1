# TDD Plan for Economic Features

## Overview

This document outlines the Test-Driven Development (TDD) approach for implementing economic analysis features in the AMD simulation framework. We'll write tests first, watch them fail, then implement code to make them pass.

## Testing Baseline

Current test framework: **pytest**
- Existing test structure in `tests/unit/` and `tests/integration/`
- Tests use fixtures and mocking where appropriate
- Current tests focus on clinical simulation, not economics

## TDD Phases

Each phase corresponds to the implementation phases in [instructions.md](instructions.md).

### Phase 1: Cost Configuration (CostConfig)

#### Test 1.1: Load Basic Cost Configuration
```python
def test_load_cost_config_from_yaml():
    """Test loading a cost configuration from YAML file"""
    # Given a YAML file with cost data
    # When I load it using CostConfig.from_yaml()
    # Then I should get a valid CostConfig object with correct values
```

#### Test 1.2: Access Drug Costs
```python
def test_get_drug_cost():
    """Test retrieving drug costs from configuration"""
    # Given a loaded cost configuration
    # When I request cost for 'eylea_2mg'
    # Then I should get 800.0
    # When I request cost for unknown drug
    # Then I should get 0.0 (safe default)
```

#### Test 1.3: Calculate Visit Costs from Components
```python
def test_calculate_visit_cost_from_components():
    """Test calculating visit cost from component list"""
    # Given a cost config with component costs
    # When I request cost for 'injection_virtual' visit type
    # Then I should get sum of all components (injection + oct + pressure + virtual_review)
```

#### Test 1.4: Handle Cost Overrides
```python
def test_visit_cost_with_override():
    """Test that explicit cost overrides component sum"""
    # Given a visit type with total_override set
    # When I calculate the cost
    # Then I should get the override value, not component sum
```

### Phase 2: Cost Analysis (CostAnalyzer)

#### Test 2.1: Analyze Simple Injection Visit
```python
def test_analyze_injection_visit_with_metadata():
    """Test analyzing a visit with full metadata"""
    # Given an injection visit with metadata specifying components
    # When I analyze the visit
    # Then I should get a CostEvent with correct total and breakdown
```

#### Test 2.2: Infer Components from Context
```python
def test_infer_components_loading_phase():
    """Test component inference for loading phase"""
    # Given an injection visit with phase='loading' but no component list
    # When I analyze the visit
    # Then components should be inferred as ['injection', 'visual_acuity_test']
```

#### Test 2.3: Handle Missing Metadata Gracefully
```python
def test_analyze_visit_without_metadata():
    """Test graceful handling of visits without metadata"""
    # Given a visit with minimal information
    # When I analyze it
    # Then I should get reasonable defaults based on visit type
```

#### Test 2.4: Calculate Drug Costs Separately
```python
def test_separate_drug_and_visit_costs():
    """Test that drug costs are tracked separately from visit costs"""
    # Given an injection visit with drug='eylea_2mg'
    # When I analyze it
    # Then the CostEvent should separate drug_cost from visit_cost in metadata
```

### Phase 3: Cost Tracking (CostTracker)

#### Test 3.1: Process Single Patient History
```python
def test_process_patient_history():
    """Test processing a complete patient history"""
    # Given a patient history with multiple visits
    # When I process it with CostTracker
    # Then I should get cost events for each visit
```

#### Test 3.2: Calculate Patient Summary Statistics
```python
def test_get_patient_costs():
    """Test retrieving costs for specific patient"""
    # Given processed simulation results
    # When I request costs for patient_001
    # Then I should get DataFrame with time-ordered cost events
```

#### Test 3.3: Generate Population Summary
```python
def test_summary_statistics():
    """Test calculating summary statistics across all patients"""
    # Given processed simulation with multiple patients
    # When I request summary statistics
    # Then I should get total costs, averages, and breakdowns by category
```

#### Test 3.4: Export to Parquet
```python
def test_export_to_parquet():
    """Test exporting cost data to Parquet format"""
    # Given processed cost data
    # When I export to Parquet
    # Then I should get two files: cost_events.parquet and cost_summary.parquet
    # And they should contain the expected columns and data
```

### Phase 4: Integration Tests

#### Test 4.1: End-to-End Cost Calculation
```python
def test_full_simulation_cost_analysis():
    """Test complete flow from simulation to cost report"""
    # Given a small simulation result
    # When I run full cost analysis
    # Then total costs should match manual calculation
```

#### Test 4.2: Cost Configuration Switching
```python
def test_multiple_cost_scenarios():
    """Test running same clinical data with different cost configs"""
    # Given simulation results and two cost configs
    # When I analyze with each config
    # Then I should get different cost totals
```

## Test Data Strategy

### 1. Test Fixtures
Create reusable test fixtures in `tests/fixtures/economics/`:

#### `test_cost_config.yaml` - Simple cost configuration
```yaml
metadata:
  name: "Test Cost Configuration"
  currency: "GBP"
  version: "1.0"

drug_costs:
  test_drug: 100.0
  eylea_2mg: 800.0

visit_components:
  injection: 50.0
  oct_scan: 25.0
  visual_acuity_test: 10.0
  virtual_review: 15.0

visit_types:
  test_visit:
    components: [injection, oct_scan]
    total_override: null
  injection_virtual:
    components: [injection, oct_scan, virtual_review]
    total_override: null
  injection_loading:
    components: [injection, visual_acuity_test]
    total_override: null

special_events:
  initial_assessment: 100.0
```

#### `sample_patient_history.json` - Minimal patient data
```json
{
  "patient_id": "test_001",
  "visits": [
    {
      "type": "injection",
      "time": 0,
      "drug": "test_drug",
      "metadata": {
        "visit_subtype": "injection_loading",
        "phase": "loading"
      }
    },
    {
      "type": "monitoring",
      "time": 1,
      "metadata": {
        "components_performed": ["oct_scan", "virtual_review"]
      }
    }
  ]
}
```

#### `expected_cost_events.json` - Expected outputs for validation
```json
[
  {
    "patient_id": "test_001",
    "time": 0,
    "event_type": "visit",
    "category": "injection_loading",
    "amount": 160.0,
    "drug_cost": 100.0,
    "visit_cost": 60.0
  },
  {
    "patient_id": "test_001",
    "time": 1,
    "event_type": "visit",
    "category": "monitoring",
    "amount": 40.0,
    "drug_cost": 0.0,
    "visit_cost": 40.0
  }
]
```

### 2. Mock Data Builders
```python
@pytest.fixture
def simple_cost_config():
    """Minimal cost configuration for testing"""
    return {
        'drug_costs': {'test_drug': 100.0},
        'visit_components': {'injection': 50.0, 'oct': 25.0},
        'visit_types': {
            'test_visit': {
                'components': ['injection', 'oct']
            }
        }
    }

@pytest.fixture
def sample_visit():
    """Sample visit with metadata"""
    return {
        'type': 'injection',
        'time': 0,
        'drug': 'test_drug',
        'metadata': {
            'visit_subtype': 'test_visit',
            'phase': 'loading'
        }
    }
```

## Implementation Order

1. **Start with CostConfig tests** (simplest, no dependencies)
2. **Move to CostAnalyzer tests** (depends on CostConfig)
3. **Implement CostTracker tests** (depends on both above)
4. **Add integration tests** (validates full system)

## Red-Green-Refactor Cycle

For each test:
1. **Red**: Write test, run it, see it fail
2. **Green**: Write minimal code to make test pass
3. **Refactor**: Clean up code while keeping tests green

## Regression Prevention

Before implementing new features:
1. Run existing test suite to ensure no breaks
2. Add new tests for new functionality
3. Run all tests after implementation
4. Document any changes to existing behavior

## Success Metrics

- All new tests pass
- No existing tests broken
- Code coverage for economic module > 90%
- Integration with existing simulation verified
- Parquet export validated for Streamlit compatibility

## Test Execution Plan

### Running Tests During Development

1. **Run specific test class**:
   ```bash
   pytest tests/unit/test_cost_config.py -v
   ```

2. **Run with coverage**:
   ```bash
   pytest tests/unit/test_cost_*.py --cov=simulation.economics --cov-report=html
   ```

3. **Run in watch mode** (requires pytest-watch):
   ```bash
   ptw tests/unit/test_cost_config.py
   ```

4. **Run only failing tests**:
   ```bash
   pytest --lf
   ```

### Test Organization

```
tests/
├── conftest.py          # Shared fixtures
├── fixtures/
│   └── economics/       # Test data files
├── unit/
│   ├── test_cost_config.py      # CostConfig tests
│   ├── test_cost_analyzer.py    # CostAnalyzer tests
│   └── test_cost_tracker.py     # CostTracker tests
└── integration/
    └── test_economic_integration.py  # End-to-end tests
```

### Continuous Integration

Add to existing CI pipeline:
```yaml
- name: Run economic tests
  run: |
    pytest tests/unit/test_cost_*.py -v
    pytest tests/integration/test_economic_*.py -v
```