# Enhanced Discontinuation Model: Complete Refactoring

This document provides a comprehensive overview of the refactoring approach used to fix discontinuation-related issues in both Agent-Based Simulation (ABS) and Discrete Event Simulation (DES) models.

## Problem Statement

The original discontinuation implementation had several critical issues:

1. **Double Counting**: The `evaluate_discontinuation()` method was being called twice for each discontinuation decision, leading to inflated statistics and rates exceeding 100%.

2. **Missing Enabled Flag**: The "enabled" flag defaulted to `False`, causing discontinuations to never occur in some simulations.

3. **Lack of Separation of Concerns**: The discontinuation manager both made decisions and updated statistics, violating software design principles.

4. **Inconsistent Tracking**: There was no distinction between unique patient discontinuations and total discontinuation events.

5. **Discrepancies Between Models**: ABS and DES implementations handled discontinuation differently, making cross-model comparisons difficult.

## Core Design Principles

Our refactoring was guided by these key principles:

### 1. Separation of Concerns

- **Decision vs. Action**: Separate the decision logic ("should this patient discontinue?") from the state changes ("update the patient's status and increment counters")
- **Pure Functions**: Decision methods don't modify state or have side effects
- **Explicit Registration**: State changes happen in the simulation code, which then explicitly registers events with the manager

### 2. Unique Patient Tracking

- **Set-Based Tracking**: Use sets to track unique patient IDs that have been discontinued or retreated
- **Explicit Counts**: Maintain explicit stats for both unique patients and total events
- **Rate Calculations**: Calculate rates based on unique patients, not events

### 3. Consistent Implementation

- **Common Interface**: Both ABS and DES use the same refactored discontinuation manager
- **Identical Tracking**: Both models track unique patients in the same way
- **Single Evaluation**: Both models call evaluation methods only once per decision point

### 4. Backward Compatibility

- **Compatibility Layer**: A wrapper class preserves the original interface for backward compatibility
- **Drop-in Replacement**: New implementations can be used as drop-in replacements for the originals

## Implementation Components

### 1. RefactoredDiscontinuationManager

The core of the new implementation is the `RefactoredDiscontinuationManager` class in `simulation/refactored_discontinuation_manager.py`, which:

- Provides pure decision functions that return structured results (`DiscontinuationDecision`, `RetreatmentDecision`)
- Tracks unique patient IDs for discontinuations and retreatments
- Exposes explicit registration methods for recording when a patient's state actually changes
- Maintains clear, accurate statistics that can be retrieved with `get_statistics()`

### 2. Fixed ABS Implementation

The `TreatAndExtendABS` class in `treat_and_extend_abs_fixed.py`:

- Uses the refactored manager for discontinuation decisions
- Calls evaluation methods only once per decision point
- Explicitly registers discontinuations after changing patient state
- Maintains its own tracking of unique patients for verification
- Provides improved statistics and consistency checks

### 3. Fixed DES Implementation

The `TreatAndExtendDES` class in `treat_and_extend_des_fixed.py`:

- Mirrors the ABS implementation's approach to discontinuation
- Uses the same refactored manager interface
- Follows the same pattern of single evaluation and explicit registration
- Maintains consistent tracking and statistics

### 4. Testing Framework

Comprehensive testing ensures correctness:

- Individual test scripts for ABS (`test_fixed_abs.py`) and DES (`test_fixed_des.py`)
- Integrated test script (`test_discontinuation_fixed.py`) for comparing both models
- Verification of plausible discontinuation rates (≤100%)
- Consistency checks between simulation and manager statistics
- Visual comparisons of results between models

## Code Examples

### Refactored Decision Function

```python
def evaluate_discontinuation(self, 
                           patient_state: Dict[str, Any], 
                           current_time: datetime,
                           patient_id: Optional[str] = None,
                           clinician_id: Optional[str] = None,
                           treatment_start_time: Optional[datetime] = None,
                           clinician: Optional[Clinician] = None) -> DiscontinuationDecision:
    """
    Evaluate whether a patient should discontinue treatment.
    
    Pure decision function that doesn't update any stats directly.
    """
    if not self.enabled:
        return DiscontinuationDecision(False, "", 0.0, "")
    
    # If patient already discontinued and we have an ID, don't discontinue again
    if patient_id and patient_id in self.discontinued_patients:
        return DiscontinuationDecision(False, "", 0.0, "")
    
    # Decision logic here...
    
    # Return structured result without changing state
    return DiscontinuationDecision(should_discontinue, reason, probability, cessation_type)
```

### Explicit Registration (ABS)

```python
# If discontinuation is recommended
if discontinuation_decision.should_discontinue:
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

## Expected Benefits

This refactoring delivers several important benefits:

1. **Accurate Statistics**: Discontinuation rates now correctly reflect the percentage of patients who have discontinued, not exceeding 100%.

2. **Consistent Behavior**: Both ABS and DES implementations now handle discontinuation consistently, making cross-model comparisons valid.

3. **Cleaner Code**: The separation of concerns creates cleaner, more maintainable code with clearer responsibilities.

4. **Better Testability**: Pure functions are easier to test and reason about, improving reliability.

5. **Improved Debugging**: More explicit tracking makes it easier to debug and understand discontinuation behavior.

## Migration Path

Applications can migrate to the new implementations by:

1. Importing `treat_and_extend_abs_fixed` or `treat_and_extend_des_fixed` instead of the originals
2. Using the new `TreatAndExtendABS` or `TreatAndExtendDES` classes
3. Consuming the improved statistics (esp. `unique_discontinuations`)

The compatibility layer ensures that existing code that depends on the original interface will continue to work.

## Verification and Validation

The refactoring has been extensively tested:

1. Unit tests to verify that individual components work correctly.
2. Integration tests to ensure both implementations produce plausible results.
3. Comparative tests to verify consistency between ABS and DES models.
4. Statistical analysis to ensure correct calculation of discontinuation rates.

All tests confirm that the refactored implementation resolves the original issues and provides accurate, consistent behavior.

## Summary

This comprehensive refactoring addresses all identified issues with the discontinuation implementation, providing:

- Accurate discontinuation statistics (rates ≤100%)
- Consistent behavior across ABS and DES models
- Clean separation of concerns for improved maintainability
- Clear tracking of unique patients vs. events
- Backward compatibility for existing code
- Extensive testing to verify correctness

The result is a more reliable, consistent, and maintainable implementation of the enhanced discontinuation model that correctly models patient discontinuation in AMD treatment simulations.