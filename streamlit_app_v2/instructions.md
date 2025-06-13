# 📋 IMPLEMENTATION INSTRUCTIONS

**IMPORTANT**: This is the active implementation plan. Always refer to this document when working on the current feature.

## 🚀 Current Phase: Staggered Enrollment Implementation - Ready for Phase 4

### Overview
The V2 simulation engines currently implement unrealistic instant recruitment where all patients exist from day 0. This needs to be replaced with proper staggered enrollment as was implemented in V1. The rectangular streamgraph shape revealed this issue - all patients are created at simulation start with only initial visits staggered across the first month.

**Phase 1 Status**: ✅ COMPLETE (2025-01-13) - Core engine changes implemented
**Phase 2 Status**: ✅ COMPLETE (2025-01-13) - Data pipeline updated
**Phase 3 Status**: ✅ COMPLETE (2025-06-13) - Streamgraph shows wedge shape
**Current Task**: Phase 4 - UI Integration for recruitment modes
**Timeline**: 7-10 days total (3 phases complete, ~2-4 days remaining)
**Approach**: Replace instant recruitment entirely (no real-world use case)

### 📍 Key Documents
- **V1 Implementation Reference**: `/simulation/staggered_abs.py` - Working staggered enrollment
- **Issue Discovery**: Streamgraph showed constant patient totals instead of wedge shape
- **Root Cause**: `simulation_v2/engines/abs_engine.py` lines 119-124, `des_engine.py` lines 108-116

### Key Principle
**All patients must have an enrollment date** - this is when they enter the simulation, not just when they have their first visit. The simulation represents a continuous real-world scenario where patients arrive throughout the entire simulation period.

### Recruitment Modes to Implement

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

### Implementation Phases

#### Phase 1: Core Engine Changes (2-3 days) ✅ COMPLETE
- [x] Study V1 `StaggeredABS` implementation
- [x] Add enrollment_date to Patient class
- [x] Replace instant patient creation in ABS engine
- [x] Replace instant patient creation in DES engine
- [x] Implement Poisson arrival process
- [x] Test simulations still run (even if visualizations break)
- [x] Create comprehensive statistical tests for Poisson process
- [x] Update edge case tests for stochastic enrollment
- [x] Verify implementation with visualization script

#### Phase 2: Data Pipeline (1-2 days) ✅ COMPLETE
- [x] Update Parquet writer to include enrollment_date
- [x] Add enrollment_time_days field (days from simulation start)
- [x] Ensure visit times are relative to enrollment
- [x] Test data integrity with small simulations
- [x] Verify late enrollees are handled correctly
- [x] Implement strict type checking (datetime vs int days)
- [x] Fix timing bug where first visits occurred before enrollment

#### Phase 3: Fix Streamgraph (1 day) ✅ COMPLETE
- [x] Update time_series_generator.py to respect enrollment dates
- [x] Add check: `if enrollment_time <= time_point`
- [x] Verify streamgraph shows wedge shape (growing patient count)
- [x] Test with both calendar and patient time views

#### Phase 4: UI Integration (1-2 days)
- [ ] Add recruitment mode radio buttons to Simulations page
- [ ] Add conditional inputs (total vs rate)
- [ ] Calculate and display derived value
- [ ] Wire parameters to simulation engines
- [ ] Add help text explaining the modes

#### Phase 5: Analysis Enhancement (2-3 days)
- [ ] Add enrollment statistics section to Analysis Overview
- [ ] Create enrollment distribution histogram
- [ ] Show actual vs expected enrollment rate
- [ ] Add cohort analysis (monthly enrollment groups)
- [ ] Ensure all visualizations handle varying sample sizes

## 🧪 Testing Protocol

### Unit Tests:
1. Test Poisson arrival generation
2. Test enrollment date tracking
3. Verify conservation of patient counts
4. Test late enrollee handling

### Visual Validation:
1. Streamgraph shows continuous growth (no plateau)
2. Patient Explorer shows different enrollment dates
3. Analysis statistics match expected distributions
4. All existing visualizations continue working

### Red Flags:
- Constant patient totals (rectangular streamgraph)
- All patients starting at day 0
- Missing enrollment dates in data
- Performance degradation

## 📏 Implementation Rules

1. **Replace, Don't Add** - Remove instant recruitment entirely
2. **Real-World Behavior** - Continuous enrollment throughout simulation
3. **No Special Cases** - Late enrollees just have fewer visits
4. **Backward Compatibility** - Old simulations show warning banner
5. **Performance** - May actually improve by spreading patient creation

## 🔧 Key Code Locations

### Files to Modify:
- `simulation_v2/engines/abs_engine.py` - Core enrollment logic
- `simulation_v2/engines/des_engine.py` - Core enrollment logic
- `simulation_v2/core/patient.py` - Add enrollment_date field
- `core/storage/writer.py` - Include enrollment in Parquet
- `components/treatment_patterns/time_series_generator.py` - Fix patient counting
- `pages/2_Simulations.py` - Add recruitment mode UI
- `pages/3_Analysis.py` - Add enrollment statistics

### Code to Reuse from V1:
```python
# From V1 patient_generator.py
inter_arrival_times = np.random.exponential(1.0 / self.rate_per_day, size=estimated_patients)
arrival_times = np.cumsum(inter_arrival_times)
```

## ✅ Previous Phases Complete

### Phase 1: Export/Import Functionality
- ✅ Complete and working
- ✅ Security hardened
- ✅ UI integrated

### Phase 2: Treatment State Streamgraph
- ✅ Pre-calculation infrastructure implemented
- ✅ Plotly streamgraph visualization created
- ✅ Integrated into Analysis page
- ✅ Discovered recruitment issue (reason for current phase)

## 📊 Success Metrics

### Staggered Enrollment Implementation:
- [x] Streamgraph shows wedge shape (continuous growth)
- [x] Enrollment follows Poisson distribution (verified with K-S test)
- [ ] UI clearly shows mutual exclusivity of modes
- [ ] All visualizations handle varying cohort sizes
- [x] Performance maintained or improved
- [ ] Backward compatibility for old simulations

### Phase 1 Accomplishments (2025-01-13):
- ✅ Implemented Poisson arrival process with exponential inter-arrival times
- ✅ Added enrollment_date field to Patient class
- ✅ Modified both ABS and DES engines for lazy patient creation
- ✅ Created comprehensive statistical tests (K-S test, chi-square test)
- ✅ Updated edge case tests to handle stochastic variations
- ✅ Verified enrollment spans entire simulation period (not all at day 0)
- ✅ Created verification script showing proper distribution

### Phase 2 Accomplishments (2025-01-13):
- ✅ Updated ParquetWriter to save enrollment_date and enrollment_time_days
- ✅ Implemented strict type checking for datetime vs int days
- ✅ Fixed timing bug where first visits could occur before enrollment
- ✅ All visit times now correctly relative to patient enrollment
- ✅ Created comprehensive tests for enrollment data integrity
- ✅ Verified late enrollees have proportionally fewer visits
- ✅ Updated test fixtures to include enrollment dates

---

### Phase 3 Accomplishments (2025-06-13):
- ✅ Updated time_series_generator.py to filter patients by enrollment date
- ✅ Added enrollment time checks to only count enrolled patients at each time point
- ✅ Streamgraph now shows proper wedge shape (growing from 0 to full patient count)
- ✅ Percentage view correctly normalizes among enrolled patients only
- ✅ Tested with multiple time resolutions (week, month, quarter) - all show wedge
- ✅ Verified in actual UI with 10,000 patient simulation

---

**Remember**: This fixes the "original sin" discovered during streamgraph implementation. The rectangular shape revealed that all patients start at day 0, which is unrealistic for clinical simulations.