# Testing Guide for streamlit_app_v2

## Overview

This project uses a comprehensive testing strategy including:
- **Unit Tests**: Fast, isolated tests for individual components
- **Integration Tests**: Tests for component interactions
- **UI Tests**: Playwright-based tests for full UI functionality

## Quick Start

### Run All Tests
```bash
# From streamlit_app_v2 directory
python scripts/run_tests.py --all
```

### Run Only Unit Tests (fast)
```bash
python scripts/run_tests.py
```

### Run Only UI Tests
```bash
python scripts/run_tests.py --ui
```

### Watch Mode (auto-rerun on file changes)
```bash
# Install pytest-watch first
pip install pytest-watch

# Then run in watch mode
python scripts/run_tests.py --watch
```

## Automatic Testing

### Git Pre-commit Hook
Tests run automatically before each commit. To set this up:

```bash
python scripts/setup_git_hooks.py
```

Once installed:
- Tests run automatically on `git commit`
- Skip UI tests: `SKIP_UI_TESTS=1 git commit -m "message"`
- Skip all tests: `git commit --no-verify -m "message"`

**NOTE**: UI tests are currently failing due to ongoing UI refactoring. 
**ALWAYS USE `SKIP_UI_TESTS=1` when committing until UI tests are fixed.**

### CI/CD
Tests run automatically on:
- Push to main, dev/*, or feature/* branches
- Pull requests to main
- See `.github/workflows/test.yml` for details

## Test Organization

```
tests/
├── README.md                    # This file
├── conftest.py                  # Shared fixtures
├── ui/
│   ├── conftest.py             # UI test fixtures (auto server management)
│   ├── test_streamlit_ui.py    # Playwright UI tests
│   └── test_analysis_page_api.py
├── unit/
│   ├── test_*.py               # Unit tests
│   └── ...
├── integration/
│   ├── test_*.py               # Integration tests
│   └── ...
├── memory/
│   ├── test_*.py               # Memory architecture tests
│   └── ...
├── performance/
│   ├── test_*.py               # Performance tests
│   └── ...
└── regression/
    ├── test_*.py               # Regression tests
    └── ...
```

## UI Testing Details

### Automatic Server Management
The UI tests automatically:
1. Check if Streamlit server is running
2. Start it if needed
3. Wait for it to be ready
4. Run tests
5. Stop server after tests

No manual server management needed!

### Writing UI Tests
```python
def test_example(page, streamlit_server):
    """Example UI test."""
    # page fixture provides a Playwright page
    # streamlit_server ensures server is running
    
    page.goto(streamlit_server)
    expect(page.locator("h1")).to_contain_text("AMD Protocol Explorer")
```

### Debugging UI Tests
```bash
# Run with visible browser
pytest tests/ui/test_streamlit_ui.py --headed

# Run with slow motion
pytest tests/ui/test_streamlit_ui.py --headed --slowmo 1000

# Take screenshots on failure
pytest tests/ui/test_streamlit_ui.py --screenshot only-on-failure
```

## Coverage Reports

### Generate Coverage Report
```bash
python scripts/run_tests.py --all --coverage
```

### View Coverage Report
```bash
# Opens in browser
open htmlcov/index.html
```

## Tips and Tricks

### 1. Fast Development Cycle
```bash
# Run only the test you're working on
pytest tests/unit/test_specific.py::TestClass::test_method -v

# Run tests matching a pattern
pytest -k "test_time" -v
```

### 2. Debugging Failed Tests
```bash
# Show print statements
pytest -s

# Drop into debugger on failure
pytest --pdb

# Show local variables on failure
pytest -l
```

### 3. Parallel Testing
```bash
# Install pytest-xdist
pip install pytest-xdist

# Run tests in parallel
pytest -n auto
```

### 4. Test Markers
```python
# Mark slow tests
@pytest.mark.slow
def test_large_simulation():
    pass

# Skip slow tests
pytest -m "not slow"
```

## Common Issues

### UI Tests Failing
1. **Server not starting**: Check if port 8501 is already in use
2. **Elements not found**: UI might have changed, update selectors
3. **Timeouts**: Increase timeout in conftest.py

### Performance
- UI tests are slower, run them separately during development
- Use `--exitfirst` (-x) to stop on first failure
- Use watch mode for rapid feedback

## Best Practices

1. **Write tests first** (TDD) when fixing bugs
2. **Keep tests fast** - mock expensive operations
3. **Test one thing** per test function
4. **Use descriptive names** - test_should_calculate_days_correctly()
5. **Clean up** - tests should not leave artifacts
6. **Independent tests** - order shouldn't matter