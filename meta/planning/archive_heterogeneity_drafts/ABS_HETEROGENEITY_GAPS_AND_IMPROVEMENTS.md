# ABS Heterogeneity: Gaps and Improvements

Date: 2025-01-18  
Purpose: Address gaps and improvements identified in planning review

## Critical Gaps to Address

### 1. Patient Data Persistence

**Issue**: No plan for saving/loading heterogeneous patient characteristics

**Solution**:
```python
# Add to patient visit records
visit_record = {
    'date': datetime,
    'vision': float,
    # ... existing fields ...
    'patient_characteristics': {  # NEW
        'trajectory_class': str,
        'treatment_responder_type': float,
        'disease_aggressiveness': float,
        'max_achievable_va': float,
        'resistance_rate': float,
        'treatments_received': int
    }
}
```

This ensures:
- Characteristics are saved with results
- Analysis can group by patient types
- Simulations can be resumed

### 2. Random Number Generation Strategy

**Issue**: No RNG strategy for reproducibility

**Solution**:
```python
class HeterogeneityManager:
    def __init__(self, config, seed: int):
        # Create separate RNG streams for each component
        self.trajectory_rng = np.random.RandomState(seed)
        self.parameter_rng = np.random.RandomState(seed + 1)
        self.event_rng = np.random.RandomState(seed + 2)
        
    def assign_trajectory_class(self):
        # Use dedicated RNG stream
        return self.trajectory_rng.choice(
            classes, p=proportions
        )
```

This ensures:
- Reproducible results with same seed
- Independence between random components
- Thread safety for future parallelization

### 3. Performance Optimization

**Issue**: Vague performance requirements

**Solution**:
```python
class HeterogeneityManager:
    def __init__(self, config, seed: int):
        # Pre-sample distributions for efficiency
        self.sample_cache_size = 10000
        self._precompute_samples()
        
    def _precompute_samples(self):
        """Pre-generate samples from all distributions."""
        self.samples = {}
        for param, config in self.patient_parameters.items():
            self.samples[param] = self._generate_samples(
                config, self.sample_cache_size
            )
            
    def get_sample(self, param: str) -> float:
        """Get next pre-computed sample."""
        # Circular buffer approach
        idx = self.sample_indices[param]
        value = self.samples[param][idx]
        self.sample_indices[param] = (idx + 1) % self.sample_cache_size
        return value
```

### 4. Validation Data Structure

**Issue**: No clear validation data management

**Solution**: Create validation data structure
```yaml
# protocols/validation/seven_up_targets.yaml
validation_targets:
  seven_up:
    description: "Seven-UP AMD study outcomes"
    duration_years: 7
    population_size: 1000  # minimum for validation
    
    statistical_targets:
      mean_change:
        value: -8.6
        units: "ETDRS letters"
        tolerance: 2.0
        
      standard_deviation:
        value: 30
        units: "ETDRS letters"
        tolerance: 3.0
        
      correlations:
        year2_year7:
          value: 0.97
          tolerance: 0.02
          
      distributions:
        above_70_letters:
          value: 0.25
          tolerance: 0.05
        below_35_letters:
          value: 0.35
          tolerance: 0.05
```

### 5. Configuration Validation

**Issue**: No schema validation mentioned

**Solution**: Add JSON schema
```python
HETEROGENEITY_SCHEMA = {
    "type": "object",
    "required": ["enabled", "version", "trajectory_classes"],
    "properties": {
        "enabled": {"type": "boolean"},
        "version": {"type": "string", "pattern": "^\\d+\\.\\d+$"},
        "trajectory_classes": {
            "type": "object",
            "additionalProperties": {
                "type": "object",
                "required": ["proportion", "parameters"],
                "properties": {
                    "proportion": {
                        "type": "number",
                        "minimum": 0,
                        "maximum": 1
                    }
                }
            }
        }
    }
}
```

### 6. Integration with Existing Visualizations

**Issue**: How to display heterogeneous outcomes

**Solution**: Add heterogeneity-aware visualizations
```python
def create_outcome_distribution_plot(results):
    """Show outcome distribution with trajectory classes."""
    # Group by trajectory class
    # Show violin plots or box plots
    # Overlay Seven-UP targets
    
def create_patient_trajectory_plot(results):
    """Show individual patient trajectories colored by class."""
    # Sample representative patients from each class
    # Show how different types progress
```

## Implementation Priorities

### Phase 1: Core Functionality
1. Patient characteristic persistence
2. RNG strategy implementation
3. Basic validation framework

### Phase 2: Performance & Validation
1. Distribution pre-sampling
2. Seven-UP validation tests
3. Performance benchmarking

### Phase 3: Integration & UI
1. Visualization updates
2. Configuration validator
3. User documentation

## Risk Mitigation

### 1. Performance Risk
- Start with simple heterogeneity
- Profile each addition
- Set performance gates in CI/CD

### 2. Validation Risk
- Implement validation tests early
- Use multiple datasets beyond Seven-UP
- Create automated validation reports

### 3. Maintenance Risk
- Minimize code duplication
- Use inheritance effectively
- Comprehensive test coverage

## Additional Recommendations

### 1. Create Debug Mode
```python
# In heterogeneity config
heterogeneity:
  enabled: true
  debug: true  # Enables detailed logging
  debug_output:
    - patient_assignments
    - distribution_samples
    - validation_metrics
```

### 2. Add Heterogeneity Impact Report
After simulation, generate report showing:
- Distribution of patient outcomes by class
- Comparison to homogeneous simulation
- Validation against targets
- Performance metrics

### 3. Parameter Sensitivity Tool
Tool to help users understand impact of heterogeneity parameters:
- Run mini-simulations with parameter variations
- Show outcome sensitivity
- Suggest parameter adjustments

## Conclusion

These additions address the main gaps while maintaining the clean design from the original planning documents. The key is to implement incrementally, validating at each step.