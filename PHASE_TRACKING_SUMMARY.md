# Phase Tracking in Streamgraph Visualization

## Summary of Findings

We have investigated the issue with phase tracking in the streamgraph visualization where not all expected patient states are being displayed. Our key findings are:

1. **Six Expected States**: The streamgraph visualization is designed to display six patient states:
   - `active` - Patients who have never been discontinued
   - `active_retreated` - Patients who were discontinued but have returned to treatment
   - `discontinued_planned` - Patients who discontinued due to planned/stable reasons
   - `discontinued_administrative` - Patients who discontinued due to administrative reasons
   - `discontinued_not_renewed` - Patients who completed treatment and did not renew
   - `discontinued_premature` - Patients who discontinued prematurely

2. **Current Issue**: Only four states are being displayed in the visualization:
   - `active`
   - `active_retreated`
   - `discontinued_planned`
   - `discontinued_premature`

3. **Underlying Problem**: The phase transition analysis function is not correctly identifying the `discontinued_administrative` and `discontinued_not_renewed` states from the simulation data.

4. **Data Confirmation**: The simulation data confirms that these discontinuation types exist in the data:
   ```
   Discontinuation counts from manager:
     Planned: 702 (14.1%)
     Administrative: 43 (0.9%)
     Not Renewed: 817 (16.4%)
     Premature: 3420 (68.6%)
   ```

5. **Data Structure Issue**: While the discontinuation manager is tracking these states correctly, the phase transition analysis isn't identifying them in the visit records because:
   - Actual discontinuation types are stored in the simulation manager (`discontinuation_manager.discontinuation_types`)
   - Visit records don't contain explicit discontinuation type information for all types
   - The phase transition detection relies on pattern matching and transition analysis
   - The mappings between actual discontinuation reasons and standardized types are incomplete

6. **Low Frequency**: Administrative discontinuations are rare (0.9% in our sample), making them harder to detect and debug

## Root Causes

1. **Missing Information in Visit Records**: The problem primarily stems from visit records not containing the necessary information to determine the discontinuation type. While some visits have explicit discontinuation reasons, others don't.

2. **Phase Transition Logic**: The current phase transition analysis function relies on detecting transitions from treatment phases (loading, maintenance) to monitoring phase, but doesn't have reliable access to the original discontinuation type information.

3. **Reason String Mapping**: The current mapping of reason strings to discontinuation types doesn't handle all possible values from the simulation.

## Recommended Solutions

1. **Enhanced Visit Information**: Modify the simulation to include explicit discontinuation type information in visit records:
   ```python
   # In discontinuation_manager.py, when creating a discontinuation visit:
   visit_data = {
       "time": current_time,
       "phase": "monitoring",
       "visit_type": "discontinuation",
       "is_discontinuation_visit": True,
       "discontinuation_reason": reason,
       "cessation_type": cessation_type,  # Add this explicitly
       "discontinuation_type": cessation_type  # Add this for clarity
   }
   ```

2. **Direct Type Access**: Modify the phase transition analysis to directly access the discontinuation manager's type tracking:
   ```python
   # In streamgraph_fixed_phase_tracking.py:
   def analyze_phase_transitions(patient_visits, patient_id=None, discontinuation_types=None):
       # ...existing code...
       
       # If we have direct access to discontinuation types, use it
       if discontinuation_types and patient_id in discontinuation_types:
           latest_discontinuation_type = discontinuation_types[patient_id]
   ```

3. **Expanded Reason Mapping**: Update the reason string mapping to handle all possible values from the simulation:
   ```python
   # Add all possible values from the simulation logs
   if any(k in reason_lower for k in ["random_administrative", "admin", "administrative"]):
       latest_discontinuation_type = "administrative"
   elif any(k in reason_lower for k in ["course_complete_but_not_renewed", "not_renewed", "treatment_duration"]):
       latest_discontinuation_type = "not_renewed"
   ```

4. **Fallback Detection**: Implement a more sophisticated fallback mechanism for when explicit reason information isn't available:
   ```python
   # Check visit type, timing patterns, and other metadata
   visit_type = current_visit.get("visit_type", "").lower()
   if "administrative" in visit_type:
       latest_discontinuation_type = "administrative"
   elif visit.get("treatment_duration_weeks", 0) >= 52 and not visit.get("renewed", False):
       latest_discontinuation_type = "not_renewed"
   ```

## Implementation Plan

1. **Phase 1: Improved Detection**
   - Enhance the `analyze_phase_transitions` function with more sophisticated reason mapping and fallback detection
   - Update the `determine_patient_state` function to properly normalize discontinuation types

2. **Phase 2: Simulation Enhancement**
   - Modify the discontinuation manager to include explicit discontinuation type information in visit records
   - Ensure all discontinuation types are properly recorded in visit metadata

3. **Phase 3: Visualization Display**
   - Modify the streamgraph visualization to always display all six states, even when some have zero counts
   - Add debugging information to help identify when states have low or zero counts

4. **Phase 4: Testing & Validation**
   - Create test cases for each discontinuation type to verify they are properly detected
   - Run a large-scale simulation to validate all states are properly represented
   - Add automated tests to prevent regression

## Conclusion

The current visualization doesn't show all patient states because the phase transition analysis isn't capturing all discontinuation types from the simulation data. This issue can be resolved by enhancing the detection logic and ensuring all necessary information is available in the visit records.

By implementing the recommended solutions, we can achieve a complete representation of patient states in the streamgraph visualization, providing a more accurate picture of the simulation results.