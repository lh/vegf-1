# Test Plan for APE Refactoring

This document outlines the testing strategy for the refactored APE (AMD Protocol Explorer) application.

## Testing Objectives

1. Verify that the refactored application maintains all functionality of the original
2. Ensure that all components interact correctly
3. Validate the visualization caching and export system
4. Confirm that error handling works as expected
5. Verify backward compatibility with existing data

## Testing Levels

### 1. Unit Testing

Test individual components in isolation to verify correctness.

#### 1.1. Components to Test

- **Visualization Components**
  - Test matplotlib visualization functions
  - Test R integration
  - Test visualization caching
  - Test export functionality

- **Data Models**
  - Test SimulationResults data model
  - Test Report data model
  - Test SimulationParameters data model

- **Utility Modules**
  - Test session state management
  - Test error handling
  - Test config management

### 2. Integration Testing

Test interactions between components.

#### 2.1. Component Interactions to Test

- **Visualization System**
  - Test that matplotlib visualizations are shown immediately
  - Test that R visualizations replace matplotlib when ready
  - Test that visualizations are properly cached
  - Test that visualizations can be exported for reports

- **Page Flows**
  - Test navigation between pages
  - Test that session state is maintained between pages
  - Test that visualizations persist between page navigations

- **Data Flow**
  - Test that simulation results are correctly passed to visualization components
  - Test that user inputs are correctly captured and validated
  - Test that reports use cached visualizations

### 3. System Testing

Test the entire application as a whole.

#### 3.1. Scenarios to Test

- **End-to-End Simulation**
  - Run a standard simulation and verify results
  - Run a staggered simulation and verify results
  - Generate reports from simulation results

- **Error Handling**
  - Test recovery from missing dependencies
  - Test recovery from invalid user inputs
  - Test graceful degradation when R is not available

- **Performance**
  - Test visualization caching performance
  - Test application responsiveness with large datasets
  - Test memory usage with multiple simulations

### 4. Acceptance Testing

Verify that the application meets user requirements.

#### 4.1. User Requirements to Verify

- **Functionality**
  - All pages are accessible and functional
  - All visualizations are displayed correctly
  - Reports can be generated in different formats

- **Usability**
  - UI is responsive and intuitive
  - Visualizations are high-quality and informative
  - Error messages are clear and helpful

- **Compatibility**
  - Application works with existing simulation results
  - Application works with various screen sizes
  - Application works with or without R installed

## Test Cases

### Unit Test Cases

1. **Visualization Cache**
   - Test caching a matplotlib figure
   - Test retrieving a cached visualization
   - Test cache expiration
   - Test cache cleanup

2. **Data Models**
   - Test creating SimulationResults from dictionary
   - Test creating Report from dictionary
   - Test parameter validation

3. **Config Management**
   - Test loading configuration from file
   - Test default configuration values
   - Test feature flags

### Integration Test Cases

1. **Progressive Enhancement**
   - Test that matplotlib visualization is shown immediately
   - Test that R visualization replaces matplotlib when ready
   - Test fallback to matplotlib when R fails

2. **Report Generation**
   - Test that report uses cached visualizations
   - Test that report can be generated in different formats
   - Test that report includes all required sections

3. **Navigation and State**
   - Test that session state is preserved during navigation
   - Test that cached visualizations are reused across pages
   - Test that simulation results are available in patient explorer

### System Test Cases

1. **End-to-End Simulation**
   - Test running a standard simulation with various parameters
   - Test running a staggered simulation with various parameters
   - Test exploring patient data after simulation

2. **Error Handling**
   - Test recovery from R errors
   - Test recovery from invalid parameters
   - Test recovery from missing data

3. **Performance**
   - Test application response time with large population
   - Test memory usage with multiple simulations
   - Test visualization caching efficiency

## Test Environment

- **Development Environment**: Local machine with R and all dependencies installed
- **Limited Environment**: Local machine without R installed
- **Production-like Environment**: Server environment with all dependencies

## Test Tools and Framework

- **Manual Testing**: UI testing and visual verification
- **pytest**: For automated unit and integration tests
- **streamlit test utilities**: For testing streamlit components

## Test Data

- **Sample Simulation Results**: Pre-generated simulation results for testing
- **Edge Cases**: Simulation results with missing or invalid data
- **Large Datasets**: Simulation results with large population sizes

## Test Schedule

1. **Unit Testing**: Implement as components are developed
2. **Integration Testing**: Implement after all components are developed
3. **System Testing**: Perform before merging to main branch
4. **Acceptance Testing**: Perform with stakeholders before release

## Risk Assessment

- **Dependency on R**: Visualization quality may degrade if R is not available
- **Session State Management**: Complex session state may be lost during navigation
- **Performance**: Large simulations may cause performance issues

## Test Deliverables

- **Test Plans**: This document
- **Test Cases**: Detailed test cases for each level
- **Test Reports**: Results of test execution
- **Bug Reports**: Documentation of any issues found

## Continuous Testing

- **Continuous Integration**: Run tests automatically on each commit
- **Regression Testing**: Ensure that new changes don't break existing functionality
- **Performance Monitoring**: Track application performance over time

## Implementation Plan

1. Create a test directory structure
   ```
   streamlit_app/
   ├── tests/
   │   ├── unit/           # Unit tests
   │   ├── integration/    # Integration tests
   │   ├── system/         # System tests
   │   └── conftest.py     # Test fixtures
   ```

2. Set up pytest configuration

3. Implement test fixtures for:
   - Simulation results
   - Visualization cache
   - Streamlit components

4. Start with unit tests for completed components

5. Add integration tests as more components are completed

6. Finish with system tests before finalizing the refactoring