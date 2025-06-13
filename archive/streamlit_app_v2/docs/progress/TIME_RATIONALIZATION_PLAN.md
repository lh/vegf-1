# Time Representation Rationalization Plan

## Current State
We have identified 7+ different time representations in the codebase:
1. `datetime` objects - in simulation core
2. `datetime64[ns]` - in pandas/parquet  
3. `time_days` (int/float) - days from start
4. `time_months` (float) - for visualization
5. `time_years` (float) - legacy
6. `time` (float) - ambiguous, sometimes days, sometimes months
7. `date` - datetime fields
8. `timestamp` - sometimes float, sometimes datetime

## Goal
Standardize to only TWO representations:
1. **`datetime`** - For absolute time points (visit dates, event times, etc.)
2. **`time_days` (integer)** - For relative time calculations (intervals, durations, etc.)

Display-time conversion to months/years/weeks should happen ONLY at render time.

## Implementation Plan

### Phase 1: Storage Layer
1. **ParquetWriter** ✅ Already updated
   - Stores `date` (datetime) and `time_days` (int)
   - No more `time_years`

2. **ParquetReader**
   - Remove all `time_years` references
   - Ensure all time queries use `time_days`

3. **InMemoryResults**
   - Update to match Parquet structure
   - Store visits with `date` and `time_days`

### Phase 2: Simulation Core
1. **Event System**
   - Keep `event.time` as datetime ✅ Already correct
   - No changes needed

2. **Patient Visit Records**
   - Ensure all visits have `date` field (datetime)
   - Calculate `time_days` during normalization

3. **DataNormalizer**
   - Verify it produces consistent `date` fields
   - Add `time_days` calculation if missing

### Phase 3: Analysis Layer
1. **Remove `time_months` calculations**
   - Move to visualization layer only
   - Replace with `time_days` in all calculations

2. **Remove `time_years` completely**
   - Update all analysis to use `time_days`
   - Fix any remaining references

3. **Interval calculations**
   - All intervals in integer days
   - No more float time values

### Phase 4: Visualization Layer
1. **Create time conversion utilities**
   ```python
   def days_to_months_display(days: int) -> float:
       """Convert days to months for display only."""
       return days / 30.44  # More accurate than 30
   
   def days_to_years_display(days: int) -> float:
       """Convert days to years for display only."""
       return days / 365.25
   ```

2. **Update all visualizations**
   - Convert `time_days` to display units at render time
   - Never store converted values

3. **Axis labels**
   - Automatically choose appropriate units based on duration
   - < 90 days: show days
   - < 730 days: show months
   - >= 730 days: show years

### Phase 5: Testing & Validation
1. **Update all tests**
   - Remove `time_years` assertions
   - Verify `time_days` is always integer
   - Check datetime consistency

2. **Add validation**
   - Ensure no new time representations creep in
   - Add linting rules if possible

3. **Performance testing**
   - Verify integer operations are faster than float
   - Check memory usage improvements

## Migration Strategy
1. Start with storage layer (least disruptive)
2. Work outward to visualization (most visible)
3. Run tests after each phase
4. Keep changes atomic and reviewable

## Benefits
1. **Clarity**: No ambiguity about time units
2. **Performance**: Integer operations are faster
3. **Accuracy**: No floating point errors in time calculations
4. **Maintainability**: Only 2 representations to understand
5. **Future-proof**: Easy to add minute-level precision later

## Timeline
- Phase 1-2: 1 day (storage and core)
- Phase 3: 1 day (analysis layer)
- Phase 4: 1 day (visualization)
- Phase 5: 1 day (testing and validation)

Total: ~4 days of focused work