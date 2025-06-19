# Parallel Clinical Improvements Implementation Plan

## Overview
Implement clinical improvements alongside existing simulation engine without breaking current functionality. All improvements will be behind feature flags for easy testing and rollback.

## Architecture Approach

### 1. Feature Flag System
Create a configuration object that enables/disables improvements:

```python
class ClinicalImprovements:
    """Feature flags for clinical improvements"""
    def __init__(self):
        self.use_loading_phase = False
        self.use_time_based_discontinuation = False
        self.use_response_based_vision = False
        self.use_baseline_distribution = False
        self.use_response_heterogeneity = False
        
    def enable_all(self):
        """Enable all improvements for testing"""
        self.use_loading_phase = True
        self.use_time_based_discontinuation = True
        self.use_response_based_vision = True
        self.use_baseline_distribution = True
        self.use_response_heterogeneity = True
```

### 2. Parallel Implementation Strategy

#### Option A: Decorator Pattern (Recommended)
Wrap existing patient/simulation logic with improvement decorators:

```python
# simulation/clinical_improvements.py
class ImprovedPatientWrapper:
    """Wraps existing patient with clinical improvements"""
    def __init__(self, patient, improvements_config):
        self.patient = patient
        self.config = improvements_config
        self.injection_count = 0
        self.response_type = self._assign_response_type()
        
    def get_next_interval(self):
        if self.config.use_loading_phase and self.injection_count < 3:
            return 28  # Monthly loading
        return self.patient.get_next_interval()
```

#### Option B: Strategy Pattern
Create alternative implementations that can be swapped in:

```python
# simulation/strategies.py
class StandardVisionStrategy:
    def calculate_vision_change(self, patient):
        # Existing logic
        
class ImprovedVisionStrategy:
    def calculate_vision_change(self, patient):
        # New response-based logic
```

## Implementation Plan

### Phase 1: Infrastructure (Day 1)
1. Create `simulation/clinical_improvements/` module
2. Implement feature flag configuration
3. Create base wrapper/strategy classes
4. Add improvements parameter to simulation functions

### Phase 2: Core Improvements (Days 2-3)

#### A. Loading Phase
- File: `simulation/clinical_improvements/loading_phase.py`
- Wrap injection scheduling logic
- Test: Verify ~7 injections in Year 1

#### B. Time-Based Discontinuation
- File: `simulation/clinical_improvements/discontinuation.py`
- Add annual probability checks
- Test: Verify discontinuation rates match targets

#### C. Response-Based Vision
- File: `simulation/clinical_improvements/vision_response.py`
- Implement phase-based vision changes
- Test: Verify gain→maintenance→decline pattern

### Phase 3: Heterogeneity (Days 4-5)

#### D. Baseline Distribution
- File: `simulation/clinical_improvements/baseline_distribution.py`
- Replace uniform with normal distribution
- Test: Verify bell curve distribution

#### E. Response Types
- File: `simulation/clinical_improvements/response_types.py`
- Assign good/average/poor responder status
- Test: Verify increased SD over time

### Phase 4: Integration & Testing (Days 6-7)

#### Integration Points
1. Modify `simulation.py` to accept improvements config:
```python
def run_simulation(params, improvements=None):
    if improvements is None:
        improvements = ClinicalImprovements()  # All disabled by default
    # ... existing logic with conditional improvements
```

2. Add UI toggle (optional):
```python
# In Streamlit app
use_clinical_improvements = st.checkbox("Use Clinical Improvements (Beta)")
```

#### Testing Strategy
1. Create `test_clinical_improvements.py`
2. Run parallel comparisons: old vs new
3. Validate against clinical targets
4. Performance benchmarking

## File Structure
```
simulation/
├── __init__.py
├── clinical_improvements/
│   ├── __init__.py
│   ├── config.py              # Feature flags
│   ├── loading_phase.py       # Loading phase logic
│   ├── discontinuation.py     # Discontinuation logic
│   ├── vision_response.py     # Vision trajectory
│   ├── baseline_distribution.py # Baseline sampling
│   ├── response_types.py      # Heterogeneity
│   └── patient_wrapper.py     # Main wrapper class
└── test_clinical_improvements.py
```

## Success Criteria

### Functional Requirements
- [ ] All existing functionality works unchanged when improvements disabled
- [ ] Each improvement can be toggled independently
- [ ] No performance degradation > 10%

### Clinical Targets (with all improvements enabled)
- [ ] Year 1 injections: 6.5-7.5 (mean ~7.0)
- [ ] Year 1 vision change: 7-10 letters
- [ ] Year 1 discontinuation: 10-15%
- [ ] Year 5 discontinuation: 45-50%
- [ ] Vision SD increases over time

## Rollback Plan
If improvements cause issues:
1. Disable all feature flags (immediate)
2. Remove improvement calls from simulation.py
3. Delete clinical_improvements module if needed

## Testing Commands
```bash
# Run without improvements (baseline)
python test_clinical_improvements.py --baseline

# Run with all improvements
python test_clinical_improvements.py --improved

# Compare results
python test_clinical_improvements.py --compare

# Test individual improvements
python test_clinical_improvements.py --test-loading-phase
python test_clinical_improvements.py --test-discontinuation
# etc.
```

## Next Steps
1. Create branch ✓
2. Create this plan ✓
3. Set up clinical_improvements module structure
4. Implement loading phase first (biggest impact)
5. Add tests for each improvement
6. Iterate based on results

## Notes
- Start with wrapper pattern for minimal disruption
- Keep existing simulation code untouched
- Document all clinical assumptions
- Make improvements data-driven (configurable parameters)