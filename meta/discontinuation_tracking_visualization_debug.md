# Discontinuation Tracking & Visualization Debugging Guide

This document summarizes the discontinuation tracking system and provides guidance for debugging visualization issues in the streamgraph implementation.

## Discontinuation Data Structure

### Core Discontinuation Types

The simulation supports four distinct discontinuation types:

1. **Planned (`stable_max_interval`)** 
   - Protocol-based discontinuation when patient is stable at maximum treatment interval
   - Requires 3+ consecutive stable visits
   - Typically occurs at 16+ week intervals

2. **Administrative (`random_administrative`)**
   - Non-clinical reasons like insurance changes, relocation, etc.
   - No monitoring after discontinuation (lost to follow-up)
   - Has a fixed annual probability (~5%)

3. **Course Complete (`course_complete_but_not_renewed`)**
   - End of standard treatment course without renewal
   - Typically occurs after 52 weeks of treatment
   - Less frequent monitoring schedule

4. **Premature (`premature`)**
   - Discontinuation before protocol criteria are met
   - Associated with significant VA loss (mean -9.4 letters)
   - Higher in non-adherent clinician profiles
   - Higher recurrence rates

### Visit Data Structure

In patient histories, discontinuation events are recorded in this structure:

```json
{
  "time": 180,  // Time in days or datetime object
  "is_discontinuation_visit": true,
  "discontinuation_reason": "stable_max_interval",
  "actions": ["vision_test", "oct_scan", "discontinue_treatment"],
  "vision": {
    "current_va": 75.0,
    // Other vision metrics...
  }
}
```

Retreatment visits are similarly marked:

```json
{
  "time": 360,
  "is_retreatment_visit": true,
  "actions": ["vision_test", "oct_scan", "treat"],
  "vision": {
    "current_va": 72.5,
    // Other vision metrics...
  }
}
```

## Patient State Tracking

The system tracks each patient in one of 9 possible states:

### Active States (5)
1. `active` - Never discontinued
2. `active_retreated_from_stable_max_interval` - Retreated after planned discontinuation
3. `active_retreated_from_random_administrative` - Retreated after administrative discontinuation
4. `active_retreated_from_course_complete` - Retreated after course completion
5. `active_retreated_from_premature` - Retreated after premature discontinuation

### Discontinued States (4)
6. `discontinued_stable_max_interval` - Planned discontinuation
7. `discontinued_random_administrative` - Administrative discontinuation
8. `discontinued_course_complete_but_not_renewed` - Course complete discontinuation
9. `discontinued_premature` - Premature discontinuation

## Visualization Data Flow

The streamgraph visualization follows these steps:

1. **Extract patient states from visit history**
   - In `extract_patient_states()` function
   - Processes each visit to determine patient state at that time point
   - Tracks transitions between states (active → discontinued → retreated)

2. **Aggregate states by month**
   - In `aggregate_states_by_month()` function
   - Creates time series data with counts in each state
   - For each month, finds most recent state for each patient
   - Ensures all states are represented (even with zero counts)

3. **Create streamgraph visualization**
   - Creates stacked area chart with each state represented
   - Ensures total population is conserved across time points
   - Shows transition between states over time

## Common Visualization Issues & Debugging

### Issue 1: Missing or Incorrect State Transitions
- **Symptom**: Patients not showing up in expected states after discontinuation/retreatment
- **Debugging**:
  - Verify that `is_discontinuation_visit` and `discontinuation_reason` are correctly set
  - Check state transition logic in `extract_patient_states()` function
  - Inspect raw visit history for specific patients to confirm discontinuation events

### Issue 2: Population Conservation Problems
- **Symptom**: Total patient count varying over time
- **Debugging**:
  - Verify the aggregation logic in `aggregate_states_by_month()`
  - Check that all states are properly counted at each time point
  - Look for patients being double-counted or missed entirely
  - Add explicit count verification at the top of the streamgraph function

### Issue 3: Time Alignment Issues
- **Symptom**: State transitions appearing at wrong times
- **Debugging**:
  - Check time conversion logic (days → months)
  - Verify visit `time` field format consistency (int, datetime, timedelta)
  - Ensure monthly aggregation is working correctly
  - Add debug logging of raw time values before conversion

### Issue 4: Missing Discontinuation Types
- **Symptom**: Certain discontinuation types not represented in the visualization
- **Debugging**:
  - Confirm that `discontinuation_reason` values match expected state names
  - Check mapping between simulation discontinuation types and visualization states
  - Verify all PATIENT_STATES are included in the visualization

### Issue 5: Retreatment Tracking Problems
- **Symptom**: Retreated patients not being tracked correctly
- **Debugging**:
  - Verify `is_retreatment_visit` is properly set
  - Check retreat state mapping based on prior discontinuation type
  - Ensure retreatment_by_type statistics are tracking correctly

## Debugging Data Inspection

To debug specific issues, add the following diagnostic code to your visualization:

```python
def inspect_state_transitions(patient_histories):
    """Inspect state transitions for debugging."""
    transitions = []
    
    # Take a sample of patients for inspection
    sample_patients = list(patient_histories.keys())[:5]
    
    for patient_id in sample_patients:
        visits = patient_histories[patient_id]
        
        # Extract key events
        discontinuations = [visit for visit in visits if visit.get("is_discontinuation_visit", False)]
        retreatments = [visit for visit in visits if visit.get("is_retreatment_visit", False)]
        
        # Report findings
        patient_info = {
            "patient_id": patient_id,
            "total_visits": len(visits),
            "discontinuations": [
                {
                    "time": visit.get("time", "unknown"),
                    "reason": visit.get("discontinuation_reason", "unknown")
                }
                for visit in discontinuations
            ],
            "retreatments": [
                {
                    "time": visit.get("time", "unknown")
                }
                for visit in retreatments
            ]
        }
        
        transitions.append(patient_info)
    
    # Print or return for inspection
    print("State transitions for sample patients:")
    import json
    print(json.dumps(transitions, indent=2))
    
    return transitions
```

Call this function before creating the streamgraph to see detailed state transition information.

## Population Conservation Verification

This is the most important principle in the visualization. Add this verification to ensure correct patient counting:

```python
def verify_population_conservation(monthly_data):
    """Verify total population is conserved across all months."""
    months = monthly_data["time_months"].unique()
    
    previous_total = None
    for month in sorted(months):
        month_data = monthly_data[monthly_data["time_months"] == month]
        total = month_data["count"].sum()
        
        if previous_total is not None and total != previous_total:
            print(f"WARNING: Population not conserved at month {month}. "
                  f"Previous: {previous_total}, Current: {total}")
        
        previous_total = total
    
    print(f"Final population count: {previous_total}")
    return previous_total
```

Add this verification after the monthly aggregation step to catch conservation issues.

## Visualization Debugging Steps

1. First, inspect the raw patient data structure:
   ```python
   # Inspect first patient
   first_patient_id = next(iter(patient_histories))
   first_patient = patient_histories[first_patient_id]
   print(f"Sample patient visits: {first_patient[:3]}")
   ```

2. Verify discontinuation events are being tracked:
   ```python
   # Check discontinuation events
   disc_visits = [v for p in patient_histories.values() 
                 for v in p if v.get("is_discontinuation_visit")]
   print(f"Total discontinuation events: {len(disc_visits)}")
   print(f"Discontinuation types: {set(v.get('discontinuation_reason') for v in disc_visits)}")
   ```

3. Check retreatment tracking:
   ```python
   # Check retreatment events
   retreat_visits = [v for p in patient_histories.values() 
                    for v in p if v.get("is_retreatment_visit")]
   print(f"Total retreatment events: {len(retreat_visits)}")
   ```

4. Verify state extraction logic:
   ```python
   # Run state extraction on sample data and inspect
   states_df = extract_patient_states(patient_histories)
   print(f"State transitions:\n{states_df.head(20)}")
   ```

5. Verify monthly aggregation:
   ```python
   # Run monthly aggregation and check conservation
   monthly_df = aggregate_states_by_month(states_df, duration_months=60)
   total_patients = len(patient_histories)
   
   # Check first month
   first_month = monthly_df[monthly_df["time_months"] == 0]
   first_month_total = first_month["count"].sum()
   print(f"Month 0 total: {first_month_total} (expected: {total_patients})")
   
   # Check last month
   last_month = monthly_df[monthly_df["time_months"] == 60]
   last_month_total = last_month["count"].sum()
   print(f"Month 60 total: {last_month_total} (expected: {total_patients})")
   ```

The key to debugging visualization issues is to verify each step of the data transformation process, ensuring that patient counts are correctly tracked and conserved at each time point.