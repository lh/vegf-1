# Warning Suppression Audit Report

**Date**: June 1, 2025  
**Purpose**: Catalog all warning suppressions for future reference and improvement

## Summary

This audit identifies all instances of warning suppression, filtering, or potentially hidden warnings in the codebase.

## Findings

### 1. Pytest Configuration (`pytest.ini`)
- **Lines 23-25**: Filters out `DeprecationWarning` and `PendingDeprecationWarning`
- **Impact**: These warnings are hidden during test runs
- **Recommendation**: Consider removing these filters to catch deprecation issues early

### 2. Pandas Warning Suppression
- **File**: `experiments/treatment_patterns_visualization.py`
- **Line 26**: `pd.set_option('future.no_silent_downcasting', True)`
- **Purpose**: Avoids FutureWarning about downcasting behavior
- **Impact**: Suppresses specific pandas future warnings

### 3. Comments About Warning Avoidance
- **File**: `components/treatment_patterns/pattern_analyzer.py`
- **Line 177**: Comment mentions "avoid downcasting warnings"
- **Code**: Uses `.astype('boolean').fillna(False)` to prevent warnings
- **File**: `experiments/treatment_patterns_visualization.py`
- **Line 222**: Similar comment about avoiding downcasting warnings

### 4. Bare Exception Handlers
These could potentially swallow warnings or errors:
- `pages/1_Protocol_Manager.py:56` - Silently ignores file deletion errors
- `tests/regression/test_edge_cases.py:202` - Test exception handling
- `tests/regression/test_protocol_manager.py:284` - Test exception handling
- `tests/save_baseline.py:143` - Baseline saving errors
- `tests/ui/conftest.py:22,115` - Test setup errors
- `utils/icon_button_solutions.py:150` - Icon button errors

### 5. Matplotlib Configuration
- **File**: `utils/visualization_modes.py`
- **Lines 152-162**: Sets `plt.rcParams` but doesn't suppress warnings
- **Impact**: None - just style configuration

### 6. Streamlit Warning Messages
- **File**: `experiments/visualize_simulation_pathways_fast.py`
- **Line 191**: `st.warning("Using iterative extraction (slower)...")`
- **Note**: This is displaying a warning to users, not suppressing system warnings

## Recommendations

1. **Remove pytest warning filters**: Update `pytest.ini` to show all warnings during tests
2. **Document pandas option**: Add comment explaining why `future.no_silent_downcasting` is set
3. **Replace bare except clauses**: Use specific exception types to avoid hiding unexpected errors
4. **Add warning capture in tests**: Use pytest's `pytest.warns()` to explicitly test for expected warnings
5. **Consider a warnings policy**: Document when it's acceptable to suppress warnings

## No Issues Found For:
- No use of `warnings.filterwarnings()` or `warnings.simplefilter()`
- No `np.seterr()` for numpy warning control
- No logging configuration that suppresses warnings
- No environment variable settings for `PYTHONWARNINGS`
- No matplotlib or plotly warning suppression

## Action Items

1. Review and update `pytest.ini` to remove warning filters
2. Add explicit exception types to bare `except:` clauses
3. Document the pandas downcasting option with rationale
4. Consider adding a warnings monitoring system to catch new suppressions