# DES (Discrete Event Simulation) Implementation Plan

## Current State Analysis

The Discrete Event Simulation (DES) component has been partially implemented, with some significant improvements already made in `treat_and_extend_des.py` and `treat_and_extend_des_fixed.py`. Based on our analysis, we've identified the following observations:

1. The core `DiscreteEventSimulation` class (in `simulation/des.py`) provides the basic event-driven infrastructure but lacks the complete implementation of the treat-and-extend protocol.

2. The specialized `TreatAndExtendDES` class (in `treat_and_extend_des.py` and its fixed version) provides a more complete implementation of the treat-and-extend protocol with:
   - Proper loading phase (3 injections at 4-week intervals)
   - Maintenance phase with dynamic intervals (8→10→12→14→16 weeks)
   - Injections at every visit
   - Enhanced discontinuation functionality
   - Clinician influence on treatment decisions

3. `treat_and_extend_des_fixed.py` addresses discontinuation tracking issues and ensures accurate statistics.

4. Integration with the enhanced discontinuation manager is working, but there appear to be two parallel implementations:
   - The original `EnhancedDiscontinuationManager`
   - A refactored version `RefactoredDiscontinuationManager` with compatibility wrappers

5. Test files (like `test_fixed_des.py` and `verify_des_fix.py`) demonstrate that the fixed implementation works correctly with discontinuation.

6. Existing frameworks for visualization and analysis (`run_simulation.py`) already support comparing ABS and DES results.

## Objectives

Our primary objectives for completing the DES implementation are:

1. **Ensure Correct Core Functionality**: Make sure the DES correctly implements the treat-and-extend protocol with realistic patient state progression.

2. **Streamline Implementation**: Resolve redundancies between the base `DiscreteEventSimulation` class and the `TreatAndExtendDES` implementation to create a more cohesive architecture.

3. **Improve Integration**: Ensure proper integration with the enhanced discontinuation manager and clinician module.

4. **Add Staggered Enrollment**: Implement staggered patient enrollment for DES similar to what exists for ABS.

5. **Output Format Compatibility**: Ensure the output format is compatible with the ABS output for seamless integration with the Streamlit dashboard.

6. **Testing and Validation**: Create comprehensive tests to validate the DES implementation against expected clinical outcomes.

## Implementation Plan

### Phase 1: Core Functionality Validation and Consolidation

1. **Validate Current Fixed Implementation**
   - Create a comprehensive test script that verifies all aspects of the treat-and-extend protocol
   - Ensure proper patient state progression through loading and maintenance phases
   - Validate vision outcomes and treatment intervals against literature values

2. **Refactor Event Handling**
   - Streamline the event handling between `DiscreteEventSimulation` and `TreatAndExtendDES`
   - Create clear separation between generic DES functionality and protocol-specific handling
   - Standardize the event data structure for better maintainability

3. **Standardize Patient State Representation**
   - Define a consistent patient state structure that captures all relevant information
   - Ensure compatibility with analysis and visualization components
   - Document the state structure for future reference

### Phase 2: Enhanced Features Implementation

1. **Integrate Refactored Discontinuation Manager**
   - Review both discontinuation manager implementations and select the more robust one
   - Ensure proper tracking of discontinuation statistics
   - Validate discontinuation probabilities against expected values

2. **Implement Staggered Patient Enrollment**
   - Create a staggered-DES implementation based on `StaggeredABS`
   - Ensure all visualization and analysis functions work with the staggered-DES results
   - Validate resource utilization patterns against expected clinical workflows

3. **Enhance Clinician Influence**
   - Verify clinician influence on treatment decisions is correctly implemented
   - Ensure clinician profiles affect discontinuation and retreatment decisions
   - Validate variability in treatment patterns based on clinician profiles

### Phase 3: Analysis and Visualization Integration

1. **Ensure Output Format Compatibility**
   - Standardize the output format between ABS and DES implementations
   - Create helper functions to convert between different formats if needed
   - Ensure all existing analysis scripts work with both simulation types

2. **Enhance Visualization**
   - Create DES-specific visualizations that highlight its distinctive features
   - Ensure all existing visualization functions work with DES results
   - Add comparison visualizations between ABS and DES results

3. **Create Dashboard Integration**
   - Ensure the Streamlit dashboard can effectively display DES results
   - Add selectors for simulation type in the dashboard
   - Create side-by-side comparisons between ABS and DES results

### Phase 4: Testing, Documentation, and Refinement

1. **Comprehensive Testing**
   - Create unit tests for all DES components
   - Create integration tests for the complete DES workflow
   - Validate against clinical benchmarks from literature

2. **Documentation**
   - Update docstrings for all DES-related functions and classes
   - Create a comprehensive guide to the DES implementation
   - Document differences between ABS and DES approaches

3. **Performance Optimization**
   - Profile and optimize the DES implementation for large simulations
   - Implement more efficient data structures for event processing
   - Reduce memory usage for long-running simulations

## Success Criteria

The DES implementation will be considered successful when:

1. It correctly implements the treat-and-extend protocol with loading and maintenance phases.
2. It produces realistic vision outcomes that match literature values.
3. It correctly handles discontinuation and retreatment scenarios.
4. It can be run with both standard and staggered patient enrollment.
5. Its outputs are compatible with existing analysis and visualization tools.
6. It can be integrated with the Streamlit dashboard with minimal changes.
7. It passes all unit and integration tests.
8. It is documented to a level that future developers can understand and extend it.

## Implementation Approach

1. We will use the existing `treat_and_extend_des_fixed.py` as our starting point since it represents the most advanced implementation.

2. We will create a more robust integration between this implementation and the core `DiscreteEventSimulation` class.

3. We will implement staggered enrollment by adapting the approach used in `StaggeredABS`.

4. We will ensure all output is compatible with existing analysis and visualization tools.

5. We will create comprehensive tests to validate each component and the complete workflow.

This approach allows us to build on existing work while creating a more cohesive and maintainable implementation.

## Timeline and Milestones

1. **Phase 1 (Core Functionality): 2 weeks**
   - Week 1: Validation tests and event handling refactoring
   - Week 2: Patient state standardization and initial integration tests

2. **Phase 2 (Enhanced Features): 2 weeks**
   - Week 3: Discontinuation manager integration and staggered enrollment
   - Week 4: Clinician influence enhancement and validation

3. **Phase 3 (Integration): 1 week**
   - Days 1-3: Output format standardization and visualization
   - Days 4-5: Dashboard integration

4. **Phase 4 (Testing and Documentation): 1 week**
   - Days 1-3: Comprehensive testing
   - Days 4-5: Documentation and final refinement

**Total Estimated Time: 6 weeks**

## Next Steps

The immediate next steps are:

1. Create a validation test script for the current `treat_and_extend_des_fixed.py` implementation
2. Refactor the event handling to create a clearer separation between framework and implementation
3. Begin implementing staggered enrollment for DES
4. Ensure compatibility with existing analysis and visualization tools

These steps will establish a solid foundation for completing the DES implementation and integrating it with the existing codebase.