# Dual Timeframe Implementation Plan for AMD Protocol Explorer

This document outlines the implementation plan for adding dual timeframe tracking (calendar time + patient time) to the AMD Protocol Explorer, with a focus on enhancing the Agent-Based Simulation (ABS) model before considering Discrete Event Simulation (DES) enhancements.

## Phase 1: Dual Timeframe Foundation in ABS (4-6 weeks)

### Core Modifications
1. **Patient Generation System**
   - Implement stochastic arrival process (Poisson distribution)
   - Add parameters for mean arrival rate and variance
   - Create calendar-based recruitment spanning full simulation duration
   - Add system for seasonal variation in referral patterns (optional)

2. **Data Structure Updates**
   - Extend patient state to track both calendar time and patient time
   - Modify visit records to include both timestamps
   - Update treatment decision logic to use patient time
   - Ensure discontinuation events record both timeframes

3. **Simulation Engine Adjustments**
   - Modify scheduler to handle calendar-time events
   - Implement dual-timeframe event queue
   - Ensure proper time advancement in both reference frames
   - Create time conversion utilities

### Deliverables
- Working ABS with staggered patient generation
- Fully functioning dual timeframe tracking
- Basic analysis of both timeframes
- Unit tests for time conversions and event handling

## Phase 2: Resource Management & Costing (3-4 weeks)

### Financial Modeling
1. **Cost Structure Implementation**
   - Add cost parameters for key procedures:
     - Initial consultation: $X
     - Vision assessment: $Y
     - Injection procedure: $Z
     - Monitoring visit: $W
   - Implement time-based cost accumulation
   - Add cost tracking by patient and by clinic

2. **Resource Utilization Tracking**
   - Track staff time (ophthalmologist, nurse, technician)
   - Implement equipment utilization (OCT, examination rooms)
   - Record consumables usage
   - Create capacity tracking metrics

### Deliverables
- Resource utilization dashboard
- Cost analysis by patient type
- Clinic-level financial metrics
- Resource utilization heat maps across calendar time

## Phase 3: Visualization & Analysis Enhancements (3-4 weeks)

### Dual-Timeframe Analysis
1. **Calendar Time Visualizations**
   - Clinic load graphs (patients per day/week)
   - Resource utilization over calendar time
   - Staff utilization heat maps
   - Financial projections by calendar time

2. **Patient Time Visualizations**
   - Enhanced VA over patient time graphs (with sample size indicator)
   - Treatment patterns by patient cohort
   - Discontinuation rates by patient time
   - Comparison across patient cohorts (enrolled in different periods)

3. **Toggle Mechanism**
   - Create UI controls to switch between timeframes
   - Implement synchronized dual-view where appropriate
   - Add export capabilities for both analysis types

### Deliverables
- Comprehensive visualization suite with timeframe toggle
- Cohort analysis capabilities
- Statistical comparisons between calendar periods
- Enhanced visualization export features

## Phase 4: Service Constraints & Capacity Modeling (4-5 weeks)

### Constraint Modeling
1. **Capacity Limitations**
   - Maximum patients per day
   - Staff availability schedules
   - Equipment availability
   - Operating hours and days

2. **Scheduling Logic**
   - Appointment scheduling algorithm
   - Waitlist management
   - Priority queuing for urgent cases
   - Rescheduling mechanisms

3. **Impact Analysis**
   - Treatment delays due to capacity
   - Visual outcomes with realistic constraints
   - Financial impact of capacity limitations
   - Optimization opportunities

### Deliverables
- Constrained clinic simulation
- Waitlist and delay analysis
- Capacity optimization recommendations
- Visual outcome comparisons (ideal vs. constrained)

## Phase 5: DES Comparative Implementation (4-6 weeks)

### DES Model Development
1. **Parallel DES Implementation**
   - Create equivalent DES model with dual timeframes
   - Implement same resource constraints
   - Ensure comparable output metrics
   - Optimize DES for large-scale simulations

2. **Comparative Analysis**
   - Performance comparison (processing time, memory usage)
   - Output validation between ABS and DES
   - Modeling flexibility assessment
   - Usability and maintainability evaluation

### Deliverables
- Functional DES implementation with all key features
- Comparative analysis report
- Recommendations on which approach fits which use case
- Unified interface for both simulation types

## Technical Considerations

### ABS Strengths for This Project
- Better for modeling individual treatment decisions
- More intuitive for modeling patient-specific factors
- Easier to implement heterogeneous patient characteristics
- Naturally handles patient history effects on decisions

### DES Potential Benefits
- More efficient for resource constraint modeling
- Better performance with very large patient populations
- More straightforward implementation of queuing systems
- May handle calendar scheduling more efficiently

### Implementation Approach
1. Implement phases 1-4 fully in ABS
2. Build DES as comparison only for specific aspects where it might excel:
   - Resource queue management
   - Scheduling optimization
   - Large-scale simulations

## Initial Development Tasks for Phase 1

1. **Update ABS Patient Generation**:
   - Add stochastic patient arrival distribution
   - Implement calendar time tracking
   - Create recruitment rate parameters in configuration

2. **Modify Patient State Class**:
   - Add calendar time fields
   - Track treatment start date
   - Create time conversion methods

3. **Update Visualization**:
   - Create prototype calendar time views
   - Add sample size indicators
   - Implement basic timeframe toggle

4. **Testing Strategy**:
   - Create validation tests for dual timeframe logic
   - Verify patient generation distribution
   - Test time conversion accuracy

## Initial Cost Factors to Implement (Phase 2)

These are suggested initial cost values for development and testing:

| Procedure/Resource | Cost Units | Notes |
|-------------------|-----------|-------|
| Initial consultation | 1 | Base cost unit |
| OCT scan | 1 | Equipment usage |
| Treatment decision | 2 | Clinical expertise |
| Injection procedure | 10 | Treatment cost |
| Staff time (per hour) | 5 | Operational cost |
| Facility overhead (per visit) | 3 | Fixed operational cost |
| Follow-up visit | 1 | Basic monitoring |
| Consumables (per procedure) | 2 | Materials used |

## Next Steps

1. Begin with the ABS patient generation system modifications
2. Add the dual timestamp tracking to patient records
3. Create basic visualizations showing both timeframes
4. Implement simple resource tracking before adding constraints

This implementation plan allows for incremental development and testing, ensuring each component works correctly before adding additional complexity.