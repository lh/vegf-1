# Plan for Accessing Individual Patient Data for Visualization

## Problem Statement

The current visual acuity over time visualization lacks access to individual patient data points, which limits our ability to show the distribution of actual data when sample sizes become small. We need a strategy to access the raw patient data from the simulation to enhance our visualization without modifying the simulation code itself.

## Investigation Results

### 1. Current Data Flow Analysis

I've examined the ABS simulation code and found:

- The ABS simulation stores complete patient histories in Patient objects (`simulation/abs.py`)
  - Each Patient has a `history` list that contains visit records with date, type, actions, vision, and disease_state
  - The `process_event` method updates this history at each visit (lines 201-212)

- When the simulation completes, `TreatAndExtendABS` returns `patient_histories` (line 811 in `treat_and_extend_abs.py`)
  - This is a dictionary mapping patient IDs to their visit histories

- The simulation runner in Streamlit receives these histories (line 626 in `streamlit_app/simulation_runner.py`):
  ```python
  results["patient_histories"] = patient_histories
  ```

### 2. Simulation Output Structure

The patient histories are already being passed through the system:
- The simulation generates complete patient visit records including:
  - `date`: Visit date
  - `vision`: Visual acuity in ETDRS letters
  - `baseline_vision`: Initial vision
  - `phase`: Treatment phase
  - `type`: Visit type
  - `disease_state`: Current disease state
  - `interval`: Next visit interval

### 3. Current Issues

The problem is not data availability but rather data format:
- The data structure expected in the visualization code (line 1787+ in simulation_runner.py) is looking for `patient_data` but the actual field is `patient_histories`
- The visualization code expects specific field names that might not match (looking for "visual_acuity" but the field might be "vision")

## Solution Without Code Changes

Based on the investigation, the patient data is ALREADY being passed through! The issue is a simple name mismatch:

1. **The simulation provides**: `patient_histories`
2. **The visualization expects**: `patient_data`

The data is there - it's just using a different key name in the results dictionary.

## Recommended Approach (Minimal Code Change)

We have two options:

### Option 1: Map the Existing Data (Single Line Fix)
Add this line to the visualization code in the generate_va_over_time_plot function:
```python
patient_data = results.get("patient_data", results.get("patient_histories", {}))
```
This will check for patient_data first, then fall back to patient_histories if not found.

### Option 2: Add Alias in Results Processing (Single Line Fix)
Add this to the process_simulation_results function:
```python
results["patient_data"] = results["patient_histories"]
```
This creates an alias so both names work.

## Field Mapping Issues

Additionally, we need to ensure field names match:
- The simulation uses `vision` for visual acuity
- The visualization might expect `visual_acuity`

We can handle this with a simple transformation when processing the data.

## Implementation Strategy

Now that we know the data is already available, the implementation is much simpler:

1. **Phase 1: Fix the Name Mismatch**
   - Add alias to map patient_histories to patient_data
   - Ensure backward compatibility by checking both names

2. **Phase 2: Handle Field Mapping**
   - Map `vision` field to `visual_acuity` if needed
   - Map `date` field to `time_months` (converting from datetime to months)
   - Keep original field names available for compatibility

3. **Phase 3: Test and Verify**
   - Test with existing simulations to ensure data appears
   - Verify individual points show when sample size drops below threshold
   - Ensure no performance impact

## Next Steps

1. Create an alias in process_simulation_results to map patient_histories to patient_data
2. Ensure field names match what the visualization expects
3. Test that individual points appear when sample size < 50

## Success Criteria

- Individual patient data points appear automatically when sample size drops below 50
- No changes to simulation code required
- Minimal changes to visualization code (just mapping names)
- Both old and new field names continue to work for backward compatibility