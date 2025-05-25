# Enum Consistency Fix

## Root Cause Analysis

The issue was an inconsistency in how disease states are stored in patient visit records:

1. **Fixed Total Simulations (TreatAndExtendABS/DES)**:
   - Manually set disease_state to string values ('active' or 'stable')
   - Based on fluid detection status
   - Example from treat_and_extend_abs.py line 168:
     ```python
     'disease_state': 'active' if fluid_detected else 'stable',
     ```

2. **Constant Rate Simulations (StaggeredABS)**:
   - Use the base AgentBasedSimulation class
   - Gets disease_state from PatientState.process_visit()
   - Which gets it from ClinicalModel.simulate_vision_change()
   - Returns a DiseaseState enum (NAIVE, STABLE, ACTIVE, HIGHLY_ACTIVE)

## Why This Matters

When the patient explorer tries to display disease states, it was assuming they were strings. When it encountered enum values from constant rate simulations, it would display them as "DiseaseState.ACTIVE" instead of just "ACTIVE".

## Solution Implemented

Added enum handling in patient_explorer.py (lines 717-724):

```python
# Handle disease_state - it might be a string or an enum
disease_state = visit.get('disease_state', 'Unknown')
if hasattr(disease_state, 'name'):
    # It's an enum, get the name
    disease_state = disease_state.name
elif not isinstance(disease_state, str):
    # Convert to string if it's not already
    disease_state = str(disease_state)
```

This ensures that regardless of whether the simulation stores disease states as strings or enums, they will be displayed consistently as strings in the UI.

## Alternative Solutions Considered

1. **Normalize at simulation level**: Modify all simulations to use the same format
   - Pros: Consistency at the source
   - Cons: Would require changing multiple simulation files, risk breaking existing functionality

2. **Normalize in data_normalizer.py**: Add enum handling to the data normalization layer
   - Pros: Central place for all data normalization
   - Cons: Would need to traverse all nested structures looking for enums

3. **Fix at display level** (chosen solution):
   - Pros: Minimal changes, handles the issue where it manifests
   - Cons: Only fixes the display issue, not the underlying inconsistency

## Testing

The fix was tested with a script that verified both string and enum disease states are handled correctly:
- String values pass through unchanged
- Enum values are converted to their name (e.g., DiseaseState.ACTIVE → "ACTIVE")

## Future Considerations

Long-term, it would be better to standardize on one approach across all simulations. The enum approach is more type-safe and allows for validation, but the string approach is simpler and doesn't require special handling for serialization.