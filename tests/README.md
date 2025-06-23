# Tests Directory

All project tests organized by type.

## Structure

- `unit/` - Unit tests for individual functions and classes
  - Fast, isolated tests
  - Mock external dependencies
  - Test single units of functionality

- `integration/` - Integration tests
  - Test component interactions
  - Test with real dependencies
  - Verify system integration

- `regression/` - Regression tests
  - Prevent known bugs from reoccurring
  - Performance regression tests
  - Visual regression tests

- **Key Integration Tests**:
  - `test_workload_integration.py` - Full end-to-end workload analysis test
    - Simulates exactly what the UI does
    - Tests resource tracking, cost calculation, and workload analysis
    - Validates data persistence and loading

## Running Tests

```bash
# Run all tests
pytest

# Run specific test category
pytest tests/unit/
pytest tests/integration/
pytest tests/regression/

# Run with coverage
pytest --cov=ape --cov=simulation --cov=visualization

# Run specific test file
pytest tests/unit/test_clinical_model.py

# Run in verbose mode
pytest -v

# Run workload integration test (full simulation)
python tests/test_workload_integration.py

# Run workload integration test with pytest (smaller dataset)
pytest tests/test_workload_integration.py::test_workload_with_smaller_dataset -v
```

## Test Organization

- Name test files: `test_*.py` or `*_test.py`
- Group related tests in classes
- Use descriptive test names that explain what is being tested
- Include docstrings for complex tests

## Writing New Tests

1. **Determine test type**:
   - Unit test: Testing a single function/class in isolation
   - Integration test: Testing component interactions
   - Regression test: Preventing a specific bug

2. **Place in appropriate directory**:
   - `unit/` for isolated component tests
   - `integration/` for multi-component tests
   - `regression/` for bug prevention tests

3. **Follow naming conventions**:
   - File: `test_<module_name>.py`
   - Class: `Test<ComponentName>`
   - Method: `test_<specific_behavior>`

## Test Data

- Use fixtures for reusable test data
- Keep test data minimal and focused
- Never use production data in tests
- Mock external services and APIs

## Coverage Goals

- Aim for >80% coverage on critical paths
- 100% coverage on financial calculations
- Focus on testing behavior, not implementation