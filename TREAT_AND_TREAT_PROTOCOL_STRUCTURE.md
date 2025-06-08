# Treat-and-Treat Protocol Structure

## Overview

This document describes the STRUCTURE of the Treat-and-Treat protocol for Eylea 2mg. Clinical outcomes will be determined by simulation.

## Protocol Definition

### Treatment Schedule
- **Loading Phase**: 
  - 3 doses
  - Dose 1: Day 0
  - Dose 2: Days 28-35 (4-5 week window)
  - Dose 3: Days 28-35 after Dose 2 (4-5 week window)
  
- **Maintenance Phase**: 
  - Fixed intervals: 56-63 days (8-9 week window)
  - No dose modifications allowed
  - Continues indefinitely unless discontinued

### Monitoring Schedule
- **Clinical Assessment**: 
  - Timing: Between Dose 3 and Dose 4
  - Components: OCT, IOP, VA, clinical exam
  - Purpose: Safety check (does not change treatment schedule)

- **Annual Review**: 
  - Timing: Within 2 weeks of treatment anniversary
  - Components: OCT, IOP, VA, clinical exam, treatment review
  - Purpose: Continuation decision

## Structural Characteristics

### Fixed vs Flexible
- **Fixed intervals**: No adjustments based on disease activity
- **Predictable schedule**: All future visits can be booked at start
- **No decision points**: Except at annual review

### Visit Burden
- **Year 1**: 6-7 injections + 2 monitoring visits = 8-9 total visits
- **Year 2+**: 6 injections + 1 monitoring visit = 7 total visits

### Staffing Requirements
- **Injection visits**: Can potentially be nurse-led
- **Monitoring visits**: Require clinical assessment
- **Annual review**: Requires consultant input

## Economic Structure (Known Costs)

### NHS Costs per Visit Type
- **Injection only**: £354 (excluding drug)
- **Clinical assessment**: £306
- **Annual review**: £506
- **Drug cost**: £475 per injection

### Annual Cost Calculation
- **Year 1**: (6.5 × £829) + £306 + £506 = £6,201
- **Year 2+**: (6 × £829) + £506 = £5,480

### Administrative Benefits
- **Batch scheduling**: Fixed intervals allow grouping
- **Reduced rescheduling**: Predictable appointments
- **Lower admin time**: Estimated 20-30% reduction

## Implementation Requirements

### System Setup
1. Dedicated fixed-interval clinic slots
2. Batch booking system for 12 months ahead
3. Clear protocol for missed appointments
4. Annual review process

### Patient Selection Criteria
To be determined based on:
- Clinical factors
- Compliance history
- Geographic considerations
- Patient preference

### Safety Monitoring
- Robust annual review process
- Clear escalation if vision deteriorates
- Option to switch protocols if needed

## Protocol Files

### V2 Specification
- **Location**: `protocols/eylea_2mg_treat_and_treat_v2.yaml`
- **Status**: Structure complete, clinical parameters need calibration
- **Note**: Placeholder values for disease transitions and vision outcomes

### Cost Configuration
- **Location**: `protocols/parameter_sets/eylea_2mg_treat_and_treat/nhs_costs.yaml`
- **Status**: Complete based on NHS reference costs

## Next Steps

1. **Parameter Calibration**: 
   - Identify relevant fixed-dosing trial data
   - Calibrate disease transitions to match trial outcomes
   - Set vision change parameters based on evidence

2. **Simulation Studies**:
   - Run simulations to determine clinical outcomes
   - Compare with flexible protocols
   - Identify optimal patient selection criteria

3. **Validation**:
   - Compare simulation results with real-world data
   - Adjust parameters as needed
   - Document evidence sources

## Key Points

- This protocol defines a STRUCTURE for fixed-interval dosing
- Clinical effectiveness is NOT assumed
- Parameters require calibration to trial data
- Outcomes will be determined by simulation
- Economic benefits derive from reduced monitoring and predictable scheduling