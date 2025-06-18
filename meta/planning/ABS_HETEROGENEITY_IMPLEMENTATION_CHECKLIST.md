# ABS Heterogeneity Implementation Checklist

Based on: ABS_HETEROGENEITY_FINAL_SPECIFICATION.md  
Date: 2025-01-18

## Phase 1: Core Implementation

### 1.1 Factory Pattern
- [ ] Create `simulation/abs_factory.py`
  - [ ] Implement `create_simulation()` method
  - [ ] Implement `_supports_heterogeneity()` validation
  - [ ] Add console output messages
  - [ ] Handle configuration errors gracefully

### 1.2 Heterogeneity Manager
- [ ] Create `simulation/heterogeneity_manager.py`
  - [ ] Initialize with separate RNG streams (trajectory, parameter, event)
  - [ ] Implement trajectory class assignment
  - [ ] Implement parameter generation from distributions
  - [ ] Add correlation with baseline VA
  - [ ] Implement distribution pre-sampling for performance
  - [ ] Add sample caching with circular buffer

### 1.3 Heterogeneous ABS Engine
- [ ] Create `simulation/heterogeneous_abs.py`
  - [ ] Extend `AgentBasedSimulation`
  - [ ] Override `__init__` to create `HeterogeneityManager`
  - [ ] Override `add_patient()` to create heterogeneous patients
  - [ ] Ensure output format compatibility

### 1.4 Heterogeneous Patient
- [ ] Create `HeterogeneousPatient` class in same file
  - [ ] Extend base `Patient` class
  - [ ] Store heterogeneous characteristics
  - [ ] Implement `update_vision()` with:
    - [ ] Treatment effect multiplier
    - [ ] Disease progression multiplier
    - [ ] Treatment resistance calculation
    - [ ] Ceiling effect
    - [ ] Catastrophic event checking
  - [ ] Track treatment count for resistance
  - [ ] Track catastrophic event history

### 1.5 Data Persistence
- [ ] Update visit record structure to include:
  - [ ] `patient_characteristics` dictionary
  - [ ] `trajectory_class`
  - [ ] All multipliers and parameters
  - [ ] Treatment count

## Phase 2: Configuration & Validation

### 2.1 Configuration Schema
- [ ] Create JSON schema for heterogeneity section
- [ ] Add schema validation to factory
- [ ] Create comprehensive error messages

### 2.2 Validation Framework
- [ ] Create `protocols/validation/seven_up_targets.yaml`
- [ ] Implement validation metric calculations:
  - [ ] Mean change at 7 years
  - [ ] Standard deviation
  - [ ] Year 2-7 correlation
  - [ ] Proportion above 70 letters
  - [ ] Proportion below 35 letters

### 2.3 Example Configuration
- [ ] Create example protocol with heterogeneity section
- [ ] Test with factory to ensure proper selection
- [ ] Document all parameters with comments

## Phase 3: Testing

### 3.1 Unit Tests
- [ ] Create `tests/unit/test_abs_factory.py`
  - [ ] Test engine selection logic
  - [ ] Test configuration validation
  - [ ] Test error handling
  - [ ] Test console output

- [ ] Create `tests/unit/test_heterogeneous_abs.py`
  - [ ] Test patient creation
  - [ ] Test characteristic assignment
  - [ ] Test trajectory class proportions
  - [ ] Test vision update calculations
  - [ ] Test catastrophic events
  - [ ] Test reproducibility with seed

### 3.2 Integration Tests
- [ ] Create `tests/integration/test_heterogeneous_simulation.py`
  - [ ] Test full simulation run
  - [ ] Test output format compatibility
  - [ ] Test performance (< 20% overhead)
  - [ ] Test memory usage

### 3.3 Validation Tests
- [ ] Create `tests/validation/test_seven_up_validation.py`
  - [ ] Run 1000+ patient simulation
  - [ ] Calculate all validation metrics
  - [ ] Compare to targets with tolerances
  - [ ] Generate validation report

## Phase 4: Integration & Documentation

### 4.1 Simulation Runner Integration
- [ ] Update `ape/core/simulation_runner.py`
  - [ ] Import and use `ABSFactory`
  - [ ] Remove manual engine selection
  - [ ] Test with existing UI

### 4.2 Visualization Support
- [ ] Add heterogeneity metrics to output
- [ ] Create trajectory class visualization
- [ ] Update existing plots to show heterogeneity

### 4.3 Documentation
- [ ] Create user guide for heterogeneity feature
- [ ] Document parameter tuning guidelines
- [ ] Create migration guide for existing protocols
- [ ] Update main documentation

## Quality Checkpoints

### Before Phase 2
- [ ] Core classes compile without errors
- [ ] Basic unit tests pass
- [ ] Factory correctly selects engines

### Before Phase 3
- [ ] Configuration validation works
- [ ] Can run simple heterogeneous simulation
- [ ] Persistence includes all data

### Before Phase 4
- [ ] All tests pass
- [ ] Seven-UP validation within tolerances
- [ ] Performance requirements met

### Before Release
- [ ] Documentation complete
- [ ] Example configurations work
- [ ] UI integration tested
- [ ] Code review completed

## Performance Checklist

- [ ] Pre-sampling implemented and tested
- [ ] Memory overhead < 100 bytes per patient
- [ ] Performance overhead < 20%
- [ ] 10,000 patient simulation completes

## Debug Features

- [ ] Debug mode configuration works
- [ ] Patient assignment logging
- [ ] Distribution sample logging
- [ ] Validation metric logging

## Final Verification

- [ ] Run example: Standard protocol → Standard engine
- [ ] Run example: Heterogeneous protocol → Heterogeneous engine
- [ ] Verify console messages appear
- [ ] Verify results reproduce Seven-UP patterns
- [ ] Verify existing code still works unchanged