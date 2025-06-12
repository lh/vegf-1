# Staggered Enrollment Implementation Plan for APE V2

## Executive Summary

The V2 simulation engines currently implement unrealistic instant recruitment where all patients exist from day 0. This needs to be replaced with proper staggered enrollment as was implemented in V1. Since instant recruitment has no real-world use case, we will replace it entirely rather than maintaining both options.

## Key Principle

**All patients must have an enrollment date** - this is when they enter the simulation, not just when they have their first visit. The simulation represents a continuous real-world scenario where patients arrive throughout the entire simulation period.

## Recruitment Modes to Implement

Two mutually exclusive modes (user chooses one):

1. **Fixed Total Mode**
   - User specifies: Total number of patients
   - System calculates: Arrival rate spread evenly across entire simulation duration
   - Example: 1000 patients over 2 years = ~9.6 patients/week
   - Display: "Expected rate: X patients/week"

2. **Constant Rate Mode**  
   - User specifies: Patients per week (or month)
   - System calculates: Expected total based on simulation duration
   - Example: 10 patients/week for 2 years = ~1040 patients (varies due to Poisson)
   - Display: "Expected total: ~X patients"

## Major Components to Modify

### 1. Simulation Engines (Critical Path)

**Files to modify:**
- `simulation_v2/engines/abs_engine.py`
- `simulation_v2/engines/des_engine.py`

**Changes needed:**
- Add enrollment_date tracking to Patient objects
- Replace instant patient creation with gradual enrollment over entire simulation
- Use Poisson process for arrival times (copy from V1)
- Only create patients when their enrollment date is reached
- Handle patients who enroll late (they simply have fewer visits recorded)

### 2. Data Structures

**Files to modify:**
- `simulation_v2/core/patient.py`
- `core/storage/writer.py`

**Changes needed:**
- Add `enrollment_date` field to Patient class
- Add `enrollment_time_days` to Parquet output (days from simulation start)
- Ensure visit times are relative to enrollment, not simulation start
- No special handling for "incomplete" patients - just record what happened

### 3. UI Components

**Files to modify:**
- `pages/2_Simulations.py`
- `components/simulation_ui.py`

**New UI elements needed:**
```
Recruitment Mode: [•] Fixed Total  [ ] Constant Rate

[If Fixed Total selected:]
Total Patients: [____1000____]
Expected rate: 9.6 patients/week

[If Constant Rate selected:]
Patients/week: [____10____]
Expected total: ~1040 patients
```

### 4. Time Series Generation (Streamgraph Fix)

**Files to modify:**
- `components/treatment_patterns/time_series_generator.py`

**Critical fix:**
- `get_patient_states_at_time()` must only count patients who have enrolled by that time point
- Remove assumption that all patients exist at all times
- Add check: `if enrollment_time <= time_point`

### 5. Analysis Components

**Files to modify:**
- `pages/3_Analysis.py` - Add enrollment statistics section

**New enrollment statistics to show:**
- Enrollment distribution histogram
- Actual vs expected enrollment rate
- Number of patients by enrollment cohort (monthly)
- Average follow-up duration by enrollment time

**Files to review for robustness:**
- `utils/chart_builder.py`
- `components/visual_acuity_analysis.py`
- `pages/4_Patient_Explorer.py`

## Implementation Phases

### Phase 1: Core Engine Changes (2-3 days)
1. Study V1 `StaggeredABS` implementation
2. Add enrollment tracking to Patient class
3. Implement Poisson arrival process in both engines
4. Ensure enrollment continues throughout entire simulation
5. Test that simulations still run (even if visualizations break)

### Phase 2: Data Pipeline (1-2 days)
1. Update Parquet writer to include enrollment data
2. Verify all patient data includes enrollment information
3. Handle late enrollees (no special logic needed - just record actual data)
4. Test data integrity with small simulations

### Phase 3: Fix Streamgraph (1 day)
1. Update time series generator to respect enrollment dates
2. Verify streamgraph shows proper wedge shape
3. Test with both calendar and patient time views
4. Ensure patient counts ramp up throughout simulation

### Phase 4: UI Integration (1-2 days)
1. Add recruitment mode radio buttons
2. Add conditional inputs (total vs rate)
3. Calculate and display derived value (rate or total)
4. Wire up parameters to simulation engines
5. Add clear help text explaining the choice

### Phase 5: Analysis Enhancement (2-3 days)
1. Add enrollment statistics section to Analysis Overview
2. Create enrollment distribution visualization
3. Add cohort analysis capabilities
4. Ensure all visualizations handle varying sample sizes gracefully

## Testing Strategy

### Unit Tests
- Test Poisson arrival generation across full simulation duration
- Test enrollment date tracking
- Test time series with continuous enrollment
- Verify late enrollees are handled correctly

### Integration Tests
- Run simulations in both modes
- Verify enrollment continues throughout
- Check that total/rate calculations are correct
- Ensure late enrollees have appropriate data recorded

### Visual Validation
- Streamgraph should show continuous growth
- No plateau in patient counts until simulation end
- Individual patient timelines should start at different times throughout

## Risk Mitigation

### Data Compatibility
- New simulations will have enrollment data
- Old simulations should display with warning: "Legacy simulation - all patients enrolled at start"
- Consider migration script for critical old simulations

### Performance Considerations
- Continuous enrollment may smooth out memory usage
- Need to verify performance with typical scenarios
- May actually improve performance by spreading patient creation

### Visualization Robustness
- All visualizations must handle varying cohort sizes
- Add sample size indicators where relevant
- Use confidence intervals that reflect actual sample sizes

## Success Criteria

1. **Streamgraph shows continuous growth**: Patient counts increase throughout simulation
2. **Enrollment is realistic**: Follows Poisson process continuously
3. **UI is clear**: Mutual exclusivity of modes is obvious
4. **Late enrollees handled correctly**: Their partial data is recorded accurately
5. **Analysis shows enrollment patterns**: New statistics section works well

## Code Reuse from V1

Key files to study from V1:
- `/simulation/staggered_abs.py` - Core staggered implementation
- `/simulation/patient_generator.py` - Poisson arrival logic  
- `/simulation/abs_patient_generator.py` - ABS-specific generation

**Key insight from V1**: The arrival schedule is generated upfront but patients are only created when their time arrives.

## Design Decisions

1. **Continuous enrollment**: Patients arrive throughout the entire simulation period, reflecting real-world clinical settings
2. **No special handling for incomplete data**: Late enrollees simply have fewer visits recorded
3. **Mutual exclusivity**: User chooses EITHER total patients OR arrival rate, system calculates the other
4. **Enrollment statistics**: Add dedicated section to Analysis Overview for enrollment insights

## Timeline Estimate

Total: 7-10 days of focused development

This plan prioritizes creating a realistic simulation that mirrors real-world patient recruitment while ensuring all existing analysis tools continue to function correctly.

## Appendix: Technical Notes

### Poisson Process Implementation
The V1 implementation uses numpy's exponential distribution to generate inter-arrival times:
```python
# From V1 patient_generator.py
inter_arrival_times = np.random.exponential(1.0 / self.rate_per_day, size=estimated_patients)
arrival_times = np.cumsum(inter_arrival_times)
```

### Enrollment Date Storage
Each patient needs:
- `enrollment_date`: datetime when patient enters simulation
- `enrollment_time_days`: float days from simulation start (for Parquet)

### UI State Management
The recruitment mode selection should update dynamically:
- When user changes mode, clear the other input
- Recalculate derived value on every change
- Store both mode and parameters in session state

### Backward Compatibility
For old simulations without enrollment data:
- Detect missing enrollment fields
- Display warning banner
- Treat as if all enrolled at day 0 (current behavior)