# Plan for Developing and Testing Discontinuation Streamgraph Visualization

## PRIME DIRECTIVE
**NEVER CREATE SYNTHETIC DATA. NEVER USE A FALLBACK POSITION. FAIL FAST.**

## Phase 1: Data Generation & Analysis
1. **Run Real Simulation**
   - Create a script to run ABS simulation with adequate patients (100+) and duration (3-5 years)
   - Configure discontinuation parameters to ensure we get variety of discontinuation types
   - Save complete simulation results to JSON file for analysis

2. **Data Inspection & Structure Analysis**
   - Create a script to load and inspect the simulation results
   - Extract and validate patient state data from simulation results
   - Analyze the exact data structure containing visit information
   - Confirm timestamps and patient state transitions are present
   - Document the precise format of discontinuation data

3. **Data Transformation**
   - Develop a transformation function to extract time-series patient state data
   - Aggregate patients by state at each time point
   - Verify conservation principle: total patient count remains constant across all time points
   - Export transformed data to intermediary format for visualization

## Phase 2: Core Visualization Development ✅
1. **Basic Streamgraph Implementation** ✅
   - Develop a standalone script to create streamgraph from transformed data
   - Use Plotly for implementation with proper stacking (`stackgroup='one'`)
   - Ensure proper patient state categories and transitions
   - Apply color system and visualization standards from project guidelines
   - Save visualization to output/visualizations directory

2. **Visualization Verification** ✅
   - Create validation tests to ensure visualization accurately represents data
   - Check all patient states are represented correctly
   - Verify x-axis time points match simulation duration
   - Ensure stack order preserves key state transitions
   - Validate conservation: width at each time point equals total patient count

3. **Enhance Visualization** ✅
   - Add clear labels and legends for state categories
   - Implement yearly tick marks (0, 12, 24, 36, 48, 60 months)
   - Apply Tufte principles for clarity and data focus
   - Add annotations showing key statistics (total discontinued, retreatment rate)
   - Generate multiple visualizations with different patient populations

## Phase 3: Review & Refinement
1. **Manual Review**
   - Present visualizations for your review
   - Discuss any needed adjustments or refinements
   - Explicitly confirm visualization meets requirements
   - Iterate on design based on feedback

2. **Edge Case Testing**
   - Test with different discontinuation parameter configurations
   - Test with extreme cases (very high/low discontinuation rates)
   - Verify visualization degrades gracefully with limited data
   - Test with large patient populations (1000+)

## Phase 4: Streamlit Integration
1. **Module Development**
   - Create modular implementation suitable for Streamlit
   - Ensure all functions are properly documented
   - Implement caching for performance optimization

2. **Integration Testing**
   - Test integration with Streamlit application
   - Verify data flows correctly from simulation to visualization
   - Validate interactive elements work as expected
   - Test performance with various dataset sizes

3. **Final Documentation**
   - Document the implementation
   - Create usage guide with examples
   - Update project documentation

## Key Principles
1. **Data Integrity**
   - Use ONLY real simulation data, never synthetic or placeholder data
   - Fail fast with clear error messages if data is missing
   - Verify data conservation principles at each step
   - Document data lineage and transformations

2. **Visualization Accuracy**
   - Ensure visualizations accurately represent the underlying data
   - Do not smooth, normalize, or "enhance" data for aesthetics
   - Show the real data with all its messiness

3. **Testing & Validation**
   - Validate all data transformations against original simulation data
   - Test with multiple parameter configurations
   - Verify edge cases and boundary conditions
   - Confirm compatibility with both ABS and DES models