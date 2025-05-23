# Streamgraph Test Parameters Summary

## Time Points Being Tested
1. **Time = 0 months**: Initial state, all patients should be active
2. **Time = 1 month**: Early stage, checking for any early discontinuations
3. **Time = 6 months**: Mid-point, expecting some discontinuations and state changes
4. **Time = 24 months (2 years)**: End state, full picture of all transitions

## Patient State Categories Being Checked
1. **Active States**:
   - `active`: Currently in treatment, never discontinued
   - `active_retreated`: Previously discontinued but returned to treatment

2. **Discontinuation States**:
   - `discontinued_planned`: Patient choice/planned discontinuation
   - `discontinued_administrative`: Administrative reasons
   - `discontinued_not_renewed`: Treatment not renewed
   - `discontinued_premature`: Early/premature discontinuation
   - `discontinued_after_retreatment`: Discontinued after attempting retreatment

## Key Fields Being Examined
1. **Visit-level fields**:
   - `is_discontinuation_visit`: Boolean flag for discontinuation
   - `discontinuation_reason`: Why the patient discontinued
   - `discontinuation_type`: Category of discontinuation
   - `is_retreatment_visit`: Boolean flag for retreatment
   - `time`: Visit timing (days or timedelta)
   - `date`: Visit date (datetime)

2. **Alternative field names** (in case of variations):
   - `discontinued` instead of `is_discontinuation_visit`
   - `reason` instead of `discontinuation_reason`
   - `patient_state` to indicate current state
   - `actions` list that might contain "discontinue"

## Data Structure Assumptions
1. `patient_histories` is a dict where:
   - Keys are patient IDs (strings)
   - Values are lists of visit dictionaries
2. Each visit dict contains timing and state information
3. Visits are chronologically ordered within each patient's list

## Expected Patient Conservation
- Total patient count should remain constant across all time points
- Patients can only transition between states, not disappear
- Sum of all state counts at any time point should equal total population

## Critical Tests for Current Issue
Since all patients are showing as "Active (Never Discontinued)", we specifically test:
1. Whether discontinuation flags are being properly detected
2. Whether field names match what the code expects
3. Whether time conversion is working correctly
4. Whether state transitions are being tracked properly