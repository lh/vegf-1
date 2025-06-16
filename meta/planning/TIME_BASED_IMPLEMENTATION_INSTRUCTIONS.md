# Time-Based Disease Model Implementation Instructions

## Overview
Implement a time-based disease progression model that updates patient states fortnightly (every 14 days) rather than per-visit. This model should integrate seamlessly with the existing APE V2 system.

## Key Principles
1. **Add, Don't Replace** - Existing functionality must remain unchanged
2. **Explicit Parameters** - No hardcoded values; everything in config files
3. **Output Compatibility** - Must work with existing Analysis pages
4. **Performance Aware** - Use batch processing and vectorization where possible

## Implementation Order

### Phase 1: Core Components ✅ (Partially Complete)
- [x] DiseaseModelTimeBased (basic structure created)
- [ ] Complete DiseaseModelTimeBased with parameter loading
- [ ] ABSEngineTimeBased
- [ ] ABSEngineTimeBasedWithSpecs

### Phase 2: Parameter System
- [ ] Create parameter YAML files structure
- [ ] Vision parameters (decline, improvement, ceilings, etc.)
- [ ] Discontinuation parameters (all 6 reasons)
- [ ] Treatment effect parameters

### Phase 3: Integration
- [ ] Update SimulationRunner to detect time-based protocols
- [ ] Create protocol specification for time-based model
- [ ] Test output compatibility with Analysis pages

### Phase 4: Testing
- [ ] Unit tests for fortnightly updates
- [ ] Integration tests with existing visualization
- [ ] Performance benchmarks

## Code Structure

### File Locations
```
simulation_v2/
├── core/
│   ├── disease_model_time_based.py  # ✅ Created
│   └── patient_time_based.py        # TODO: Extended patient class
├── engines/
│   └── abs_engine_time_based.py     # TODO: Main engine
└── protocols/
    └── time_based/
        ├── protocol_spec.yaml        # TODO: Protocol definition
        └── parameters/
            ├── vision.yaml           # TODO: Vision parameters
            ├── discontinuation.yaml  # TODO: Discontinuation params
            └── treatment.yaml        # TODO: Treatment effects
```

### Key Interfaces to Maintain

1. **SimulationResults** - Must produce same structure:
   - patient_histories: Dict[str, Patient]
   - total_injections: int
   - final_vision_mean: float
   - discontinuation_rate: float

2. **Patient Visit History** - Each visit must have:
   - date: datetime
   - vision: int (measured, not actual)
   - disease_state: DiseaseState
   - treatment_given: bool

3. **Protocol Specification** - Extend with:
   - model_type: 'time_based'
   - fortnightly_transitions: dict
   - vision_parameters: dict
   - discontinuation_parameters: dict

## Implementation Guidelines

### 1. Disease State Updates
```python
# Every 14 days, for ALL patients (not just those with visits)
if (current_date - start_date).days % 14 == 0:
    batch_update_disease_states(patients, current_date)
```

### 2. Vision Evolution
- Update actual_vision fortnightly
- Track true value internally
- Only record measured_vision at visits (with ±5 letter noise)

### 3. Parameter Loading
```python
# All parameters from YAML files
vision_params = load_yaml('protocols/time_based/parameters/vision.yaml')
# Never hardcode values like:
# BAD: hemorrhage_risk = 0.001
# GOOD: hemorrhage_risk = params['hemorrhage']['base_risk']
```

### 4. Performance Patterns
```python
# Batch processing
patients_to_update = [p for p in patients if needs_update(p)]
vision_changes = np.random.normal(means, stds, len(patients_to_update))

# Avoid per-patient loops where possible
# BAD: for patient in patients: update(patient)
# GOOD: batch_update(patients)
```

### 5. Testing Approach
- Test fortnightly updates happen correctly
- Verify visit frequency doesn't affect progression
- Check output format matches existing engines
- Benchmark performance (target: <2x slower than current)

## Current Status
- Planning documents complete
- Basic DiseaseModelTimeBased structure created
- Ready to implement ABSEngineTimeBased

## Next Steps
1. Complete DiseaseModelTimeBased with proper parameter loading
2. Implement ABSEngineTimeBased with fortnightly update loop
3. Create parameter YAML files
4. Test integration with existing system

## Questions/Decisions During Implementation
1. Log any hardcoded values found that need parameterization
2. Note any performance bottlenecks discovered
3. Document any output format compatibility issues
4. Track any clinical validation questions that arise