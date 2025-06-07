# Parquet-Only Storage Refactor

## Overview
Simplify the simulation storage architecture by using Parquet format for ALL simulations, regardless of size.

## Current State
- Small simulations (< 10,000 patient-years) → InMemoryResults (not saved to disk)
- Large simulations (≥ 10,000 patient-years) → ParquetResults (saved to disk)
- This dual path causes bugs, complexity, and confusion

## Target State
- ALL simulations → ParquetResults (saved to disk)
- Remove size-based logic
- Single, consistent storage path

## Implementation Plan

### Phase 1: Force Parquet for All New Simulations
1. **Modify ResultsFactory.create_results()**
   - Remove size threshold logic
   - Always create ParquetResults
   - Remove `force_parquet` parameter (no longer needed)

2. **Update Simulation Runner**
   - Remove `force_parquet` parameter from calls
   - Remove the save logic we just added (Parquet auto-saves)

### Phase 2: Handle Existing InMemoryResults
1. **Migration Path**
   - Keep InMemoryResults class for now (backward compatibility)
   - Keep load functionality to read old .pkl files
   - Add migration on load: convert to Parquet automatically

2. **Update ResultsFactory.load_results()**
   - If loading InMemoryResults, convert to Parquet
   - Save in new format
   - Return ParquetResults

### Phase 3: Clean Up
1. **Remove Obsolete Code**
   - Remove memory threshold constants
   - Remove storage type branching logic
   - Simplify tests

2. **Update Documentation**
   - Update docstrings
   - Update architecture docs
   - Update user-facing messages

## Benefits
1. **Simplicity**: One storage format, one code path
2. **Reliability**: All simulations saved to disk
3. **Consistency**: Export/import works for all simulations
4. **Maintainability**: Less code to maintain and test

## Migration Impact
- Existing InMemoryResults will be auto-converted on first load
- No user action required
- Backward compatible

## Code Changes

### 1. ResultsFactory (core/results/factory.py)
```python
# Remove these:
MEMORY_THRESHOLD_PATIENT_YEARS = 10_000  # Delete
MEMORY_WARNING_PATIENT_YEARS = 5_000     # Delete

def create_results(...):
    # Remove size calculation
    # Remove use_parquet logic
    # Always create ParquetResults
```

### 2. Simulations Page (pages/2_Simulations.py)
```python
# Remove the save logic we just added (lines 338-353)
# Parquet auto-saves, so this becomes unnecessary
```

### 3. Tests
- Update tests to expect ParquetResults always
- Remove tests for size thresholds
- Simplify mock expectations

## Timeline
- Phase 1: 30 minutes (force Parquet)
- Phase 2: 30 minutes (migration path)
- Phase 3: 30 minutes (cleanup)
- Testing: 30 minutes

Total: ~2 hours for complete refactor

## Return Path
After this refactor:
1. All simulations will be on disk
2. Export will work for all simulations
3. Recent Simulations list will show all simulations
4. We can continue with import testing

## Success Criteria
- [ ] All new simulations saved as Parquet
- [ ] Existing InMemoryResults can still be loaded
- [ ] Export works for all simulations
- [ ] All tests pass
- [ ] No performance regression