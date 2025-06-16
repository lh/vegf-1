# Time-Based Disease Transition Implementation Plan

## Executive Summary

We need to implement time-based disease transitions to replace the current per-visit model. This document provides a detailed plan for creating new simulation engines (ABS and DES) that properly model disease progression over time using **fortnightly (14-day) updates**.

## Current State Analysis

### Problem
The current implementation applies transition probabilities **per visit**, causing:
- Patients with frequent visits (4-week) to have 4x higher progression than those with 16-week intervals
- Biologically incorrect modeling (disease progresses continuously, not just at visits)
- Incompatibility with clinical data (which reports monthly/annual rates)

### Time Granularity Decision
After analyzing protocol intervals (all multiples of 14 days), we will use **fortnightly updates** because:
- Perfect alignment with ALL protocol intervals (28, 42, 56, 70, 84, 98, 112 days)
- No interpolation needed - exact 14-day periods
- Efficient: only 26 updates/patient/year vs 365 daily

### Current Architecture
```
ABSEngine:
├── run() - Main simulation loop (daily timestep)
├── _calculate_vision_change() - Per-visit vision changes
├── _should_discontinue() - Per-visit discontinuation checks
└── Uses DiseaseModel.progress() at each visit

DiseaseModel:
├── transition() - Applies per-visit probabilities
└── progress() - Wrapper that determines treatment status
```

### Key Finding
The transition probabilities are applied in `ABSEngine.run()` line 226:
```python
new_state = self.disease_model.progress(
    patient.current_state,
    days_since_injection=patient.days_since_last_injection_at(current_date)
)
```
This only happens when `current_date` matches a scheduled visit.

## Implementation Strategy

### Decision: Create New Engines
Rather than modifying existing engines, we'll create:
- `abs_engine_time_based.py`
- `des_engine_time_based.py`

**Rationale**:
1. Preserves working reference implementation
2. Allows A/B testing between models
3. Safer for production use
4. Easier rollback if issues arise

### Important: Production Engine Architecture
The APE V2 application (production system) uses wrapper engines that read from protocol specifications:
- **`ABSEngineWithSpecs`** (not plain ABSEngine) - reads vision parameters from protocol files
- **`DESEngineWithSpecs`** (not plain DESEngine) - reads vision parameters from protocol files

These wrappers override methods like `_sample_baseline_vision()` to use protocol-specified values instead of hardcoded defaults.

**Implication**: We need to create corresponding wrapper classes:
- `ABSEngineTimeBasedWithSpecs` - extends our time-based engine with protocol spec support
- `DESEngineTimeBasedWithSpecs` - same for DES

### Approach: Fortnightly State Updates
- Update disease states every 14 days regardless of visit schedule
- Visits only determine treatment administration
- Perfect alignment with protocol intervals (all multiples of 14 days)
- More accurate than monthly for treatment effect modeling

## Detailed Implementation Plan

### Phase 1: Test Suite Creation (Current)

Create comprehensive tests that capture current behavior:

```python
# test_abs_time_based.py

class TestABSTimeBased:
    def test_patient_initialization():
        """Verify patients start with correct baseline vision and state"""
        
    def test_fortnightly_disease_progression():
        """Verify disease states update every 14 days, not per-visit"""
        
    def test_visit_frequency_independence():
        """Verify progression rates don't depend on visit frequency"""
        
    def test_treatment_effect_duration():
        """Verify treatment effects decay over time"""
        
    def test_vision_changes_fortnightly():
        """Verify vision changes accumulate every 14 days"""
        
    def test_discontinuation_rates():
        """Verify discontinuation probabilities are time-based"""
        
    def test_backward_compatibility():
        """Verify similar outcomes with adjusted parameters"""
```

### Phase 2: Create Time-Based Disease Model

```python
class DiseaseModelTimeBased:
    UPDATE_INTERVAL_DAYS = 14  # Fortnightly updates
    
    def __init__(self, fortnightly_transitions, treatment_effects):
        """Initialize with FORTNIGHTLY (14-day) transition probabilities"""
        
    def update_state(self, patient, current_date):
        """Update disease state based on time since last update"""
        # Calculate fortnights (14-day periods) since last state update
        # Apply transition probability for exact 14-day period
        # Consider treatment effect decay
        
    def get_treatment_efficacy(self, days_since_injection):
        """Calculate current treatment efficacy (0-1)"""
        # Implement decay curve (e.g., exponential)
        # Half-life aligned with typical injection intervals
```

### Phase 3: Create Time-Based ABS Engine

```python
class ABSEngineTimeBased(ABSEngine):
    def run(self, duration_years, start_date=None):
        """Modified run loop with fortnightly updates"""
        
        # Daily loop for patient arrivals and visits
        while current_date <= end_date:
            # Process arrivals (unchanged)
            # Process scheduled visits (treatment only)
            
            # NEW: Fortnightly disease updates for all patients
            days_since_start = (current_date - start_date).days
            if days_since_start % 14 == 0 and days_since_start > 0:
                for patient in self.patients.values():
                    if not patient.is_discontinued:
                        self._update_patient_disease_state(patient, current_date)

# For production use with APE V2:
class ABSEngineTimeBasedWithSpecs(ABSEngineTimeBased):
    """Time-based engine that reads from protocol specifications."""
    
    def __init__(self, disease_model, protocol, protocol_spec, n_patients, seed=None):
        self.protocol_spec = protocol_spec
        super().__init__(disease_model, protocol, n_patients, seed)
        
    def _sample_baseline_vision(self):
        """Use protocol-specified vision parameters."""
        # Override to read from protocol_spec
        
    def _calculate_vision_change(self, old_state, new_state, treated):
        """Use protocol-specified vision change model."""
        # Override to read from protocol_spec
```

### Phase 4: Parameter Conversion

Create tool to convert per-visit probabilities to fortnightly rates:

```python
def get_typical_interval_days(disease_state):
    """Get typical visit interval for each disease state"""
    intervals = {
        'NAIVE': 28,         # Initial monthly visits
        'STABLE': 84,        # Extended to 12 weeks
        'ACTIVE': 42,        # 6-week intervals
        'HIGHLY_ACTIVE': 28  # Monthly monitoring
    }
    return intervals[disease_state]

def convert_per_visit_to_fortnightly(per_visit_prob, disease_state):
    """
    Convert per-visit probability to fortnightly (14-day) rate.
    
    Example: STABLE patient seen every 84 days = 6 fortnights
    So 1 visit per 6 fortnights = 0.167 visits/fortnight
    """
    typical_interval = get_typical_interval_days(disease_state)
    visits_per_fortnight = 14.0 / typical_interval
    
    # Solve: per_visit_prob = 1 - (1 - fortnightly_rate)^(1/visits_per_fortnight)
    fortnightly_rate = 1 - (1 - per_visit_prob)**visits_per_fortnight
    return fortnightly_rate
```

### Phase 5: Protocol Migration

Update protocol format:
```yaml
# OLD FORMAT
disease_transitions:
  STABLE:
    STABLE: 0.85  # per visit
    ACTIVE: 0.15  # per visit

# NEW FORMAT  
disease_transitions_fortnightly:
  STABLE:
    STABLE: 0.975  # per fortnight (14 days)
    ACTIVE: 0.025  # per fortnight (14 days)
transition_model: "fortnightly"  # Explicit model type
update_interval_days: 14  # Make interval explicit
```

### Phase 6: Integration with SimulationRunner

Update `simulation_v2/core/simulation_runner.py` to support time-based engines:
```python
# In SimulationRunner.run():
if engine_type.lower() == 'abs':
    if self.spec.transition_model == 'fortnightly':
        engine = ABSEngineTimeBasedWithSpecs(...)
    else:
        engine = ABSEngineWithSpecs(...)  # Current per-visit model
```

## Testing Strategy

### Unit Tests
1. Disease state transitions occur monthly
2. Treatment efficacy decay functions correctly
3. Vision changes accumulate properly
4. Discontinuation rates are time-based

### Integration Tests
1. Full simulation runs complete successfully
2. Results are deterministic with same seed
3. Patient histories contain monthly state updates

### Validation Tests
1. Compare outcomes with clinical data
2. Verify progression rates match literature
3. Ensure treatment effects align with trials

### Regression Tests
1. Similar overall outcomes with converted parameters
2. No performance degradation
3. Memory usage remains reasonable

## Key Technical Decisions

### 1. State Update Frequency
**Decision**: Fortnightly updates (every 14 days)
**Rationale**: Perfect alignment with ALL protocol intervals (multiples of 14), no interpolation needed

### 2. Treatment Effect Model
**Decision**: Exponential decay with half-life parameter
**Rationale**: Matches pharmacokinetic models, configurable per drug

### 3. Update Synchronization
**Decision**: All patients update on same 14-day cycle from simulation start
**Rationale**: Simpler implementation, deterministic behavior

### 4. Visit Role
**Decision**: Visits only determine treatment, not progression
**Rationale**: Reflects biological reality - disease progresses continuously

## Success Criteria

1. **Correctness**: Disease progression independent of visit frequency
2. **Validation**: Results match clinical progression rates
3. **Performance**: No significant slowdown vs current implementation
4. **Compatibility**: Can run both models for comparison
5. **Clarity**: Code clearly separates time-based updates from visits

## Next Steps

1. **Today**: Complete test suite for current behavior
2. **Tomorrow**: Implement DiseaseModelTimeBased
3. **Day 3**: Create ABSEngineTimeBased
4. **Day 4**: Parameter conversion and validation
5. **Day 5**: DES engine implementation

## Questions to Resolve

1. Should we implement treatment efficacy decay curves or step functions?
2. How to handle patients who miss scheduled visits?
3. Should fortnightly updates be synchronized globally or per-patient from enrollment?
4. How to migrate existing simulation results for comparison?
5. Should we allow custom update intervals (7, 14, 28 days) in protocols?

---
**Status**: Ready for Implementation