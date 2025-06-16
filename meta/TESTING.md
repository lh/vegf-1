# Testing Guide

This document explains how to run and understand the test suite for the macular simulation project.

## Running Tests

### Run All Tests
```bash
python -m pytest tests/
```

### Run Specific Test Categories
- Agent-based simulation tests:
  ```bash
  python -m pytest tests/unit/test_abs*.py
  ```
- Discrete event simulation tests:
  ```bash
  python -m pytest tests/unit/test_des*.py
  ```
- Protocol validation tests:
  ```bash
  python -m pytest tests/unit/test_protocol*.py
  ```

### Run Individual Test Files
```bash
python -m pytest path/to/test_file.py
```

### Run With Verbose Output
```bash
python -m pytest -v tests/
```

## Test Organization

Tests are organized into these categories:

1. **Unit Tests** (`tests/unit/`):
   - Test individual components in isolation
   - Fast-running tests with minimal dependencies

2. **Integration Tests** (coming soon):
   - Test interactions between components
   - May require test databases or external services

## Understanding Test Output

- `.` - Test passed
- `F` - Test failed
- `s` - Test skipped
- `x` - Test expected to fail but passed
- `E` - Error occurred during test setup/execution

## Common Issues

1. **Missing Dependencies**:
   ```bash
   pip install -r requirements-dev.txt
   ```

2. **Test Database Not Available**:
   - Some tests require a test SQLite database
   - Run `python setup_test_db.py` first

3. **Configuration Issues**:
   - Ensure `test_config.yaml` exists in project root
   - Copy from `test_config.example.yaml` if missing

## Writing New Tests

1. Follow existing test patterns
2. Place tests in appropriate category directory
3. Name test files with `test_` prefix
4. Use descriptive test function names:
   ```python
   def test_loading_phase_duration_calculation():
       # Test code here
   ```

## Test Coverage

To generate a coverage report:
```bash
python -m pytest --cov=simulation tests/
```

This will show which parts of the code are exercised by tests.
