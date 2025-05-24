# Discontinuation Rate Fix Documentation

## Problem Overview

The AMD simulation model was experiencing an issue where the reported discontinuation rates were exceeding 100% (e.g., 129.2% for 1000 patients). This is mathematically impossible for unique patients, as you cannot have more patients discontinuing than the total number of patients in the simulation.

## Root Causes

After thorough investigation, we identified several root causes:

1. **Double Counting**: The `evaluate_discontinuation()` method was being called twice for each patient at decision points, resulting in statistics being updated multiple times for the same patient.

2. **Multiple Discontinuations per Patient**: The model was counting each discontinuation event separately rather than tracking unique patients, so patients who:
   - Discontinued treatment
   - Had disease recurrence
   - Were retreated
   - Discontinued again
   Were counted as multiple discontinuations, inflating the total.

3. **Missing Enabled Flag**: The "enabled" flag in the discontinuation configuration was defaulting to `False` when not explicitly set, causing discontinuations to never occur in some simulation runs.

4. **Poor Separation of Concerns**: The discontinuation manager was both making decisions and updating statistics, violating separation of concerns principles.

## Fix Implementation

We implemented a comprehensive solution that solves all these issues while maintaining backward compatibility:

### 1. Refactored Discontinuation Manager

The `RefactoredDiscontinuationManager` in `simulation/refactored_discontinuation_manager.py`:

- Uses pure decision functions without side effects
- Explicitly tracks unique patient IDs using sets
- Separates decision logic from state tracking
- Provides a compatibility layer for backward compatibility

### 2. Fixed ABS Implementation

The `TreatAndExtendABS` class in `treat_and_extend_abs_fixed.py`:

- Calls `evaluate_discontinuation()` only once per decision point
- Explicitly registers discontinuations after changing patient state
- Tracks unique patient discontinuations separately from total events
- Ensures consistent statistics between simulation and manager

### 3. Fixed DES Implementation

The `TreatAndExtendDES` class in `treat_and_extend_des_fixed.py` implements the same fixes for the Discrete Event Simulation model.

### 4. Streamlit Integration

We've provided several ways to integrate the fix with the Streamlit app:

1. `streamlit_fixed_launcher.py`: A replacement launcher that uses monkey-patching to fix the discontinuation statistics
2. `streamlit_app/monkey_patch.py`: Patches the Streamlit app to use the fixed implementations
3. `simulation/discontinued_compat.py`: A runtime compatibility module for automatic patching

## Usage Instructions

To use the fixed implementation, you have several options:

### Option 1: Use Fixed Implementation Directly

```python
# Instead of:
from treat_and_extend_abs import TreatAndExtendABS
from treat_and_extend_des import TreatAndExtendDES

# Use:
from treat_and_extend_abs_fixed import TreatAndExtendABS 
from treat_and_extend_des_fixed import TreatAndExtendDES
```

### Option 2: Use Compatibility Module

```python
# Add this import at the top of your script
import simulation.discontinued_compat

# Then use the original imports - they'll be automatically patched
from treat_and_extend_abs import TreatAndExtendABS
from treat_and_extend_des import TreatAndExtendDES
```

### Option 3: Use Fixed Streamlit Launcher

To run the Streamlit app with the fix:

```bash
streamlit run streamlit_fixed_launcher.py
```

## Verification

You can verify that the fix is working by running:

```bash
python verify_fix.py
```

This script will:
1. Run a simulation with the fixed implementation
2. Check that discontinuation rates are ≤100%
3. Verify that unique patient tracking is working correctly
4. Report statistics on multiple discontinuations and retreatments

## Implementation Details

### 1. Unique Patient Tracking

We use sets to track unique patient IDs:

```python
# In RefactoredDiscontinuationManager
self.discontinued_patients = set()
self.retreated_patients = set()

# In simulation implementations
self.discontinued_patients = set()
self.retreated_patients = set()
```

This ensures that a patient is only counted once for each statistic, regardless of how many times they discontinue or retreat.

### 2. Single Evaluation

We've eliminated double calls to `evaluate_discontinuation()`:

```python
# Original (problematic) approach had two calls:
protocol_decision, ... = self.discontinuation_manager.evaluate_discontinuation(...)
should_discontinue, ... = self.discontinuation_manager.evaluate_discontinuation(...)

# Fixed approach has a single call:
discontinuation_decision = self.refactored_manager.evaluate_discontinuation(...)
```

### 3. Explicit Registration

State changes and statistics updates are explicitly separated:

```python
# Update patient state
patient.treatment_status["active"] = False
patient.treatment_status["discontinuation_date"] = event.time
patient.treatment_status["discontinuation_reason"] = discontinuation_decision.reason
patient.treatment_status["cessation_type"] = discontinuation_decision.cessation_type

# Only increment stats if this is a new discontinuation for this patient
if patient_id not in self.discontinued_patients:
    self.stats["protocol_discontinuations"] += 1
    self.stats["unique_discontinuations"] += 1
    self.discontinued_patients.add(patient_id)

# Register the discontinuation with the manager
self.refactored_manager.register_discontinuation(
    patient_id, 
    discontinuation_decision.cessation_type
)
```

## Statistics Explanation

With the fix, you'll see two key discontinuation metrics:

1. **Total Discontinuation Events**: The total number of discontinuation events, which may exceed the number of patients if some patients discontinue multiple times. This is similar to the old "total_discontinuations" metric.

2. **Unique Discontinued Patients**: The number of unique patients who discontinued at least once. This will never exceed the total number of patients. This is the new "unique_discontinuations" metric.

The correct discontinuation rate should be calculated as:
```
Discontinuation Rate = (Unique Discontinued Patients / Total Patients) × 100%
```

This rate will always be ≤100%.

## Future Directions

Once these fixes are confirmed to be working correctly, we recommend:

1. Migrating all code to use the fixed implementations directly
2. Removing the compatibility layer when no longer needed
3. Updating documentation to explain the proper interpretation of discontinuation statistics
4. Extending the test suite to include verification of discontinuation rates