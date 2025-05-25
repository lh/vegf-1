# Streamgraph Visualization Fix: Cumulative Retreatment Tracking

## Problem Statement

The original streamgraph visualization showed retreated patients only at the point of their retreatment visit, causing the retreated patient line to fluctuate rather than grow cumulatively as expected. This made it difficult to track the total number of patients who had been retreated.

## Solution

We implemented a cumulative retreatment tracking system with the following key components:

1. **Added `has_been_retreated` Flag**:
   - Once a patient is retreated, they remain in the retreated state for all subsequent visits
   - This prevents patients from "disappearing" from the retreated group after their retreatment visit
   - The flag is checked in the state determination logic alongside the `is_retreatment_visit` flag

2. **Updated State Determination Logic**:
   - The state determination function now checks both `is_retreatment_visit` and `has_been_retreated` flags
   - This ensures retreated patients remain in that state throughout the visualization

3. **Enhanced Diagnostic Information**:
   - Added reporting of total visits with cumulative retreatment flag
   - Calculated percentage of visits with retreatment flag

## Key Changes

1. **Modified `run_streamgraph_simulation_parquet.py`**:
   ```python
   # Track cumulative retreatment status
   has_been_retreated = False
   
   # Once a patient is retreated, they remain in the retreated state
   if is_retreatment_visit:
       has_been_retreated = True
       
   # Create a record with both flags
   visit_record = {
       "patient_id": patient_id,
       "is_retreatment_visit": is_retreatment_visit,  # Flag for the actual retreatment visit
       "has_been_retreated": has_been_retreated,      # Cumulative flag for all visits after retreatment
       **visit  # Include all visit data
   }
   ```

2. **Updated State Determination in `create_patient_state_streamgraph.py`**:
   ```python
   def determine_state(row):
       # Check both retreatment flags for cumulative tracking
       if row.get("is_retreatment_visit", False) or row.get("has_been_retreated", False):
           return "retreated"
       
       # Other state determination logic follows...
   ```

## Testing and Verification

We created a verification script (`verify_cumulative_retreatment.py`) to ensure:

1. The `has_been_retreated` flag is correctly set for all visits after a patient's first retreatment
2. Patient state counts accurately reflect cumulative retreatment status
3. Retreated patient counts grow over time rather than fluctuating

Results from verification:
- Retreatment visits: 21
- Cumulative retreated visits: 139
- Retreated patients at month 36: 14 (28% of total patients)
- No decreases in retreated count over time

## Visual Impact

The updated streamgraph now shows:
- A steadily growing retreated patient segment (pale green)
- More accurate representation of patient state transitions
- Proper preservation of state information

## Future Considerations

1. **Enhanced Analytics**: Explore analyzing retreatment patterns by discontinuation type
2. **Visualization Enhancements**: Consider adding hover information about retreatment patterns
3. **Timing Analysis**: Add retreatment timing analysis to examine when retreatments typically occur