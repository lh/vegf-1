# Protocol Implementation Refactoring Plan

## Objective
Convert mixed dictionary/object protocol implementation to a consistent object-oriented approach.

## Files to Modify

### Core Protocol Models
1. protocol_models.py
- Create comprehensive protocol class hierarchy
- Define clear interfaces for protocol phases
- Move protocol logic from simulation into protocol classes
- Classes needed:
  * TreatmentProtocol
  * ProtocolPhase (base class)
  * LoadingPhase
  * MaintenancePhase
  * VisitType
  * TreatmentDecision
  * ProtocolParameters

### Configuration & Parsing
2. protocol_parser.py
- Modify to create protocol objects instead of dictionaries
- Add validation during object creation
- Keep YAML parsing but transform to objects

3. validation/config_validator.py
- Update validation rules for new object structure
- Add type checking

### Simulation Core
4. simulation/config.py
- Update SimulationConfig to work with protocol objects
- Modify parameter access methods

5. simulation/base.py
- Update base simulation to handle protocol objects
- Modify event processing
- Add protocol-specific event types

### Simulation Implementations
6. simulation/abs.py
- Update Patient class to use protocol objects
- Modify protocol-related methods
- Update type hints

7. simulation/des.py
- Update patient state handling
- Modify protocol-related methods
- Update type hints

### Test Files
8. test_protocol_configs.py
- Update test cases for new object model

9. test_abs_simulation.py
- Update test initialization
- Modify protocol handling

10. test_des_simulation.py
- Update test initialization
- Modify protocol handling

## Implementation Order
1. Phase 1: Core Protocol Model ✓
   - ✓ Implement new protocol_models.py
   - ✓ Add protocol class hierarchy
   - ✓ Add phase implementations
   - ✓ Update protocol_parser.py
   - ✓ Define protocol-specific event types
   - ✓ Add protocol state validation
   - ✓ Add tests for new models

2. Phase 2: Configuration & Validation ✓
   - ✓ Update config_validator.py
   - ✓ Update simulation/config.py
   - ✓ Add configuration tests
   - ✓ Add protocol transition validation
   - ✓ Add parameter constraint checking

3. Phase 3: Simulation Updates ✓
   - ✓ Update simulation/base.py with protocol events
   - ✓ Update Event class to handle protocol objects
   - ✓ Update simulation/abs.py
   - ✓ Update simulation/des.py
   - ✓ Add simulation tests

4. Phase 4: Test Framework
   - Add integration tests for simulations
   - Update test_protocol_configs.py
   - Add comparative test framework
   - Verify full workflow
   - Add performance benchmarks

## Success Criteria
1. ✓ All protocol logic encapsulated in protocol classes
2. ✓ Clear type hints throughout codebase
3. ✓ Improved error handling and validation
4. → Protocol behavior matches specifications
5. → All tests passing
6. ✓ No mixed dictionary/object usage
7. → Documentation complete and up to date
8. → Performance benchmarks established

## Migration Strategy
1. Create new classes alongside existing code
2. Add tests for new implementation
3. Gradually migrate simulation code
4. Deprecate dictionary-based approach
5. Remove old code

## Validation Points
- After each phase, run full test suite
- Verify protocol behavior matches current implementation
- Check type safety and validation
- Ensure YAML configurations still work
- Verify simulation results match current output

## Rollback Plan
- Keep dictionary implementation until full verification
- Maintain compatibility layer during migration
- Document all changes for potential rollback

## Success Criteria
1. All protocol logic encapsulated in protocol classes
2. Clear type hints throughout codebase
3. Improved error handling and validation
4. No loss of current functionality
5. All tests passing
6. No mixed dictionary/object usage
7. Clear documentation of new structure

## Documentation Updates Needed
1. Update class documentation
2. Add protocol class usage examples
3. Update YAML configuration docs
4. Add migration guide for any external code
