# Plan to Merge Test Directories

## Current Structure

### tests/ (existing)
- data/
- fixtures/
- integration/
- unit/
- test_v2_economics_integration.py

### tests_v2/ (from streamlit_app_v2)
- baseline_results/
- fixtures/
- integration/
- memory/
- performance/
- playwright/
- regression/
- ui/
- Various test files

## Merge Strategy

1. **Keep both fixtures/** - May have different test data
2. **Merge integration/** - Combine test files
3. **Move unique directories from tests_v2/**:
   - baseline_results/
   - memory/
   - performance/
   - playwright/
   - regression/
   - ui/

4. **Move test files from tests_v2/**
5. **Update imports in all test files**

## Commands to Execute

```bash
# Move unique directories
git mv tests_v2/baseline_results tests/
git mv tests_v2/memory tests/
git mv tests_v2/performance tests/
git mv tests_v2/playwright tests/
git mv tests_v2/regression tests/
git mv tests_v2/ui tests/

# Move test files
git mv tests_v2/*.py tests/
git mv tests_v2/*.md tests/

# Merge fixtures (check for conflicts)
git mv tests_v2/fixtures/* tests/fixtures/

# Merge integration (check for conflicts)
git mv tests_v2/integration/* tests/integration/
```