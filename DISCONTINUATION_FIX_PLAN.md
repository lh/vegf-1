# Discontinuation Fix Implementation Plan

## Current State Analysis

### The Problem
We have three different definitions of "discontinued" causing massive discrepancies:

1. **True Discontinuation**: 41% (816/1990 patients) - based on `discontinued` flag
2. **"No Further Visits"**: 97.3% - anyone without visit in 6+ months  
3. **Sankey Terminal States**: ~97% - anyone without visit in last 30 days

### Root Causes
1. `time_series_generator.py` line 182: Labels patients as "No Further Visits" after 6 months without a visit
2. `pattern_analyzer_enhanced.py` line 39: Only considers patients active if visit within last 30 days
3. Neither checks the actual `discontinued` flag from patient data

### What We Changed (And Need to Revert)
We modified data processing to count unique patients instead of transitions in:
- `pattern_analyzer_enhanced.py` - create_terminal_transitions
- `sankey_builder.py` - transition counting  
- `sankey_builder_enhanced.py` - transition counting
- `pages/4_Simulation_Comparison.py` - process_transitions function
- `pages/3_Analysis.py` - pattern details calculations

## Implementation Plan

### Phase 1: Documentation ✓
- Document the current state
- Create this implementation plan
- Identify all files that need changes

### Phase 2: Revert Changes
Files to revert on `fix/terminal-state-conservation` branch:
1. `ape/components/treatment_patterns/pattern_analyzer_enhanced.py`
2. `ape/components/treatment_patterns/sankey_builder.py`
3. `ape/components/treatment_patterns/sankey_builder_enhanced.py`  
4. `pages/4_Simulation_Comparison.py`
5. `pages/3_Analysis.py`

### Phase 3: Fix Terminal State Definitions
1. **Modify "No Further Visits" detection**:
   - Check `discontinued` flag instead of time-based cutoff
   - In `time_series_generator.py` get_patient_states_at_time()
   
2. **Fix "Still in Treatment" detection**:
   - Include ALL non-discontinued patients
   - Remove 30-day cutoff in `pattern_analyzer_enhanced.py`

### Phase 4: Update Sankey Visualization
1. Keep transition counts for flows (as originally implemented)
2. For terminal nodes only:
   - Count unique patients in final states
   - Ensure conservation (sum of terminal = initial)
3. Do this in visualization layer, not data processing

### Phase 5: Align Colors and Labels
1. Use consistent gray for discontinued across all visualizations
2. Use consistent green for active/still in treatment
3. Update color mappings in:
   - STATE_COLOR_MAPPING in pattern_analyzer.py
   - Color assignments in streamgraph
   - Color assignments in Sankey

### Phase 6: Add Memorable Names
1. Add memorable name display to:
   - Analysis page header
   - Comparison page for each simulation
   - Any other visualization pages

### Phase 7: Testing and Verification
1. Run diagnostic script to verify rates
2. Check all visualizations show consistent data
3. Verify patient conservation in Sankey
4. Test with multiple simulations

## Success Criteria
- All visualizations show ~41% discontinuation rate (not 97%)
- Sankey terminal nodes sum equals initial node
- Colors are consistent across visualizations
- Memorable names displayed
- No broken functionality (intervals, gaps, etc.)