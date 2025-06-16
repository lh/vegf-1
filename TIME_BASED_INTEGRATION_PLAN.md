# Time-Based Model Integration Plan

## Integration Strategy: Add, Don't Replace

### 1. Protocol Selection
Add new protocol type in the UI:
```
Protocol Type:
○ Standard (Per-Visit Model)
● Time-Based (Fortnightly Updates)
```

### 2. Output Compatibility
Ensure time-based engine produces the same output structure:
- Same patient history format
- Same visit records (but with actual_vision tracked internally)
- Same summary statistics
- **Analysis pages work unchanged**

### 3. New Parameter UI
Create new parameter editor for time-based model:
- Vision decline/improvement parameters
- Treatment effect decay
- Hemorrhage risk
- Discontinuation parameters
- All with tooltips explaining clinical meaning

### 4. File Structure
```
protocols/
├── v2/                    # Existing per-visit protocols
│   ├── eylea.yaml
│   └── lucentis.yaml
└── v2_time_based/         # New time-based protocols
    ├── eylea_time.yaml
    └── parameters/
        ├── vision.yaml
        ├── discontinuation.yaml
        └── treatment_effect.yaml
```

### 5. SimulationRunner Integration
```python
# In simulation_runner.py
def run(self, engine_type, n_patients, duration_years, seed):
    # Check protocol type
    if hasattr(self.spec, 'model_type') and self.spec.model_type == 'time_based':
        # Create time-based engine
        if engine_type.lower() == 'abs':
            engine = ABSEngineTimeBasedWithSpecs(...)
        else:
            raise NotImplementedError("DES time-based not yet implemented")
    else:
        # Use existing engines
        engine = self._create_standard_engine(engine_type)
```

### 6. Performance Optimizations

#### A. Batch Processing
```python
# Instead of checking each patient individually
for patient in patients:
    if should_update(patient, date):
        update_state(patient)

# Process all patients needing updates together
patients_to_update = [p for p in patients if should_update(p, date)]
batch_update_states(patients_to_update)
```

#### B. Vectorized Operations
```python
# Use NumPy for vision changes
vision_changes = np.random.normal(
    means[patient_states], 
    stds[patient_states], 
    size=len(patients_to_update)
)
```

#### C. Lazy Evaluation
```python
# Only calculate expensive metrics when needed
class LazyMetrics:
    def __init__(self, patient):
        self._injection_rate = None
    
    @property
    def injection_rate_last_year(self):
        if self._injection_rate is None:
            self._injection_rate = self._calculate_injection_rate()
        return self._injection_rate
```

### 7. Validation Approach
Track key metrics for comparison with NHS/clinical data:
```python
validation_metrics = {
    'mean_injections_year_1': None,
    'mean_injections_year_2': None,
    'vision_gain_3_months': None,  # % gaining ≥5 letters
    'vision_loss_2_years': None,   # % losing ≥15 letters
    'discontinuation_2_years': None,
    'stable_disease_proportion': None
}
```

## Implementation Priority

### Phase 1: Core Engine (Week 1)
1. ✅ DiseaseModelTimeBased
2. ABSEngineTimeBased
3. ABSEngineTimeBasedWithSpecs
4. Basic parameter files

### Phase 2: Integration (Week 2)
1. Update SimulationRunner
2. Create protocol detection logic
3. Ensure output compatibility
4. Test with Analysis pages

### Phase 3: UI (Week 3)
1. Protocol selection UI
2. Parameter editor for time-based
3. Help text and documentation
4. Parameter presets

### Phase 4: Optimization (Week 4)
1. Profile performance
2. Implement batch processing
3. Add progress indicators
4. Memory optimization

## Success Criteria
1. **Seamless Integration**: User can switch between models easily
2. **Visualization Works**: All existing Analysis pages display correctly
3. **Performance**: <2x slower than per-visit model
4. **Parameter Control**: Easy to modify all time-based parameters
5. **Clinical Validity**: Results align with NHS model trends