# Phase Tracking Next Steps

## Current Status

We've identified that our streamgraph visualization isn't properly displaying all six patient states. After analyzing the problem, we discovered:

1. The simulation correctly tracks all discontinuation types (administrative, not_renewed, etc.) in the discontinuation manager.
2. However, the phase tracking analysis has trouble detecting these types from the visit records.
3. We've improved the detection logic in `streamgraph_fixed_phase_tracking_enhanced.py`, but there's still a structural issue in how discontinuation types are stored.

## Implementation Status

1. ✅ **Root Cause Analysis**: Identified that discontinuation types are properly tracked in the discontinuation manager, but not properly propagated to visit records.

2. ✅ **Enhanced Detection Logic**: Implemented improved pattern matching for discontinuation types with a wider range of patterns.

3. ✅ **Documentation**: Created `PHASE_TRACKING_SUMMARY.md` with explanation of the issue and recommended solutions.

4. ✅ **Testing**: Created test scripts to validate our improvements and identify remaining issues.

## Remaining Issues

Based on our testing, our enhanced detection logic shows the "active," "active_retreated," and "discontinued_planned" states, but still doesn't show the "discontinued_administrative" and "discontinued_not_renewed" states. This is because:

1. The discontinuation manager doesn't include the discontinuation type in visit records (only in its internal state).
2. There's no direct way for the visualization to access the discontinuation manager's internal state.
3. The patterns in visit records aren't sufficient to reliably determine all discontinuation types.

## Next Steps

To fully fix this issue, the simulation code needs to be modified to store discontinuation type information directly in visit records:

1. **Modify the Enhanced Discontinuation Manager**:
   In `enhanced_discontinuation_manager.py`, when creating a discontinuation visit, add explicit discontinuation type information:
   
   ```python
   def create_discontinuation_visit(self, patient_id, current_time, reason="stable_max_interval"):
       # Create visit data with explicit discontinuation type
       visit_data = {
           "time": current_time,
           "phase": "monitoring",
           "visit_type": "discontinuation",
           "is_discontinuation_visit": True,
           "discontinuation_reason": reason,
           "cessation_type": reason,  # Add this explicitly
           "discontinuation_type": reason  # Add for clarity
       }
       # Rest of the method...
   ```

2. **Store Discontinuation Types in Results**:
   When preparing simulation results, include the discontinuation type mapping:
   
   ```python
   def prepare_results(self):
       results = super().prepare_results()
       
       # Add explicit discontinuation type mapping
       if self.discontinuation_manager and hasattr(self.discontinuation_manager, 'discontinuation_types'):
           results['discontinuation_types'] = self.discontinuation_manager.discontinuation_types
       
       return results
   ```

3. **Enhanced Visualization Access**:
   Modify the streamgraph visualization to directly access the discontinuation types:
   
   ```python
   def count_patient_states_by_phase(results):
       # Existing code...
       
       # Get discontinuation types directly
       discontinuation_types = results.get('discontinuation_types', {})
       
       # Use them in analyze_phase_transitions
       analysis = analyze_phase_transitions(
           visits_to_month, 
           patient_id=patient_id, 
           discontinuation_types=discontinuation_types
       )
       
       # Rest of the method...
   ```

4. **Consistent Type Normalization**:
   Ensure that discontinuation types are consistently normalized across all components:
   
   ```python
   def normalize_discontinuation_type(type_str):
       """Normalize discontinuation type to a standard form."""
       if not type_str:
           return "not_renewed"  # Default
       
       type_lower = str(type_str).lower()
       
       if any(k in type_lower for k in ["stable_max", "planned", "stable"]):
           return "planned"
       elif any(k in type_lower for k in ["admin", "administrative"]):
           return "administrative"
       elif any(k in type_lower for k in ["premature", "early"]):
           return "premature"
       elif any(k in type_lower for k in ["not_renewed", "course_complete"]):
           return "not_renewed"
       
       return type_lower  # Use as-is if no match
   ```

5. **Add Tests for All Discontinuation Types**:
   Create tests that validate all types are properly tracked and visualized:
   
   ```python
   def test_all_discontinuation_types_visualized():
       """Test that all discontinuation types appear in the visualization."""
       # Configure test with all discontinuation types
       config = TestConfig()
       
       # Run simulation with various discontinuation types
       results = run_test_simulation(config)
       
       # Analyze results to ensure all types are present
       timeline_data = count_patient_states_by_phase(results)
       
       # Check if each state type has values > 0 at some point
       pivot_data = timeline_data.pivot(
           index='time',
           columns='state',
           values='count'
       ).fillna(0)
       
       # Test all expected states are present with non-zero counts
       all_states = [
           'active',
           'active_retreated',
           'discontinued_planned',
           'discontinued_administrative',
           'discontinued_not_renewed',
           'discontinued_premature'
       ]
       
       for state in all_states:
           assert state in pivot_data.columns
           assert pivot_data[state].max() > 0, f"State {state} has no non-zero values"
   ```

## Conclusion

The current streamgraph visualization doesn't capture all discontinuation types because the information is stored in the discontinuation manager's internal state rather than in visit records. Our enhanced detection logic improves this somewhat, but to fully fix the issue, we need to modify how discontinuation types are stored and propagated throughout the simulation.

The most effective solution is to add explicit discontinuation type information to visit records during the simulation, ensure this information is included in the simulation results, and make it available to the phase tracking analysis for the visualization.