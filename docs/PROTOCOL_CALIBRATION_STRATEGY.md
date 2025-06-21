# Protocol Calibration Strategy for nAMD Treatment Simulation

## Executive Summary

This document outlines our approach to creating a flexible simulation system that can accurately model different treatment protocols for neovascular age-related macular degeneration (nAMD) while matching known clinical trial and real-world outcomes.

## Objectives

1. **Multi-Protocol Support**: Create a simulation framework that can accurately model:
   - Fixed interval dosing (e.g., VIEW 2q8)
   - Treat-and-extend (T&E) protocols
   - PRN (as-needed) protocols
   - "Treat-and-treat" (fixed intervals extended indefinitely - essentially VIEW protocol beyond trials)

2. **Clinical Validation**: Ensure simulation outputs match:
   - Clinical trial outcomes (VIEW, CATT, IVAN, etc.)
   - Real-world evidence from registries
   - Long-term follow-up studies (5-10 years)

3. **Flexibility**: Maintain ability to:
   - Switch between protocols without recalibration
   - Model patient heterogeneity accurately
   - Project long-term outcomes beyond trial periods

## Current Progress

### 1. Fixed Interval Protocol Calibration

**Implemented**: VIEW 2q8 protocol (3 monthly loading + q8 weeks)

**Key Achievement**: Successfully calibrated to match VIEW trial outcomes:
- Target: 8.4 letters vision gain, 7.5 injections Year 1
- Achieved: 9.5 letters vision gain, 8.0 injections Year 1
- Within 1.1 letters of target (13% error margin)

**Technical Innovation**: 
- Created `FixedIntervalProtocol` class for non-adaptive dosing
- Implemented patient-time analysis to handle recruitment periods correctly
- Developed three calibration levels (original, improved, balanced)

**"Treat-and-Treat" Extension**: The VIEW 2q8 protocol extended indefinitely represents a pragmatic approach:
- Continue q8 week injections without extensive monitoring
- Only 2-3 monitoring visits per year vs 8-12 for T&E
- Trade-off: May undertreat some patients but offers predictable outcomes and lower burden

### 2. Treat-and-Extend Protocol Status

**Current Implementation**: Standard T&E with configurable parameters:
- Min/max intervals: 28-112 days
- Extension/shortening increments: 14 days
- Treatment decisions based on disease state

**Challenge**: Current T&E protocol underperforms significantly:
- Achieving: -5.3 letters Year 1
- Target: +6-8 letters (based on real-world T&E outcomes)
- Gap: 11-13 letters

**Root Causes Identified**:
1. Disease state transitions too pessimistic
2. Vision change model parameters need adjustment
3. Treatment effect multipliers may be insufficient

### 3. Patient-Time vs Calendar-Time Analysis

**Critical Insight**: Simulations with recruitment periods require patient-time analysis
- Calendar-time analysis undercounts treatments for late enrollees
- Patient-time provides accurate per-patient year outcomes
- Essential for matching clinical trial results

## Calibration Strategy

### Phase 1: Individual Protocol Calibration ✓ (Partially Complete)

1. **Fixed Interval (VIEW 2q8)** ✓
   - Status: Complete
   - Accuracy: Within 13% of target
   - Extension: Can model "treat-and-treat" by continuing indefinitely

2. **Treat-and-Extend** (In Progress)
   - Current: Significant underperformance
   - Next: Adjust disease model parameters
   - Target: Match real-world T&E outcomes (~6 letters Year 1)

3. **PRN Protocol** (Planned)
   - Expected: Lower outcomes than T&E
   - Target: ~3-4 letters Year 1 based on meta-analyses

### Phase 2: Unified Disease Model (Next Major Task)

**Goal**: Create a single disease model that works across all protocols

**Approach**:
1. Use fixed interval results as baseline truth
2. Adjust protocol-specific parameters only (not disease model)
3. Validate each protocol maintains its relative performance

**Key Parameters to Unify**:
- Disease state transition probabilities
- Base vision change parameters
- Treatment effect multipliers

### Phase 3: Long-Term Validation

**Targets** (based on literature review):
- Year 2: Slight decline from peak (~7-8 letters)
- Year 5: Return to near baseline (~0-2 letters)
- Year 10: Below baseline (~-8 letters)

**Considerations**:
- Macular atrophy development (~50% by 10 years)
- Treatment persistence (50% discontinuation by 2 years)
- Injection frequency decline over time

## Technical Architecture

### Core Components

1. **Disease Model** (`DiseaseModel` class)
   - State transitions: NAIVE → STABLE/ACTIVE/HIGHLY_ACTIVE
   - Treatment effects on transitions
   - Vision change calculations

2. **Protocol Classes**
   - `FixedIntervalProtocol`: Non-adaptive schedules (including "treat-and-treat")
   - `StandardProtocol`: T&E and PRN logic
   - Future: `HybridProtocol` for complex regimens

3. **Clinical Improvements Module**
   - Loading phase effects
   - Response heterogeneity (good/average/poor responders)
   - Time-based discontinuation
   - Baseline vision distribution

4. **Analysis Tools**
   - Patient-time outcome analyzer
   - Calibration framework with scoring
   - Parameter exploration tools

### Calibration Parameters

**Primary Levers**:
1. Disease state transition probabilities
2. Vision change means/standard deviations
3. Treatment effect multipliers
4. Response type distributions
5. Discontinuation rates

**Protocol-Specific**:
1. Visit intervals (min/max)
2. Extension/shortening rules
3. Treatment decision logic
4. Monitoring requirements

## Validation Metrics

### Primary Outcomes
- Mean vision change at Years 1 and 2
- Injection frequency by year
- Proportion gaining ≥15 letters
- Vision maintenance rates (losing <15 letters)

### Secondary Outcomes
- Discontinuation rates
- Time to first recurrence
- Treatment burden (visits + injections)
- Long-term vision trajectory

### Acceptability Criteria
- Within 15% of target for primary outcomes
- Correct relative performance between protocols
- Realistic long-term trajectories
- Appropriate patient heterogeneity

## Protocol-Specific Considerations

### Fixed Interval / "Treat-and-Treat"
- **Advantages**: Predictable, low monitoring burden, good adherence
- **Disadvantages**: One-size-fits-all, potential over/undertreatment
- **Long-term**: Extended VIEW protocol shows sustained benefits with acceptable burden
- **Key insight**: Simplicity may outweigh individualization benefits in real-world settings

### Treat-and-Extend
- **Advantages**: Individualized, potentially fewer injections for stable patients
- **Disadvantages**: High monitoring burden, complex decision-making
- **Long-term**: Better outcomes than PRN but requires sustained engagement
- **Challenge**: Balancing extension criteria to avoid undertreatment

### PRN (As-Needed)
- **Advantages**: Minimum necessary injections
- **Disadvantages**: Reactive approach, consistently worse outcomes
- **Long-term**: Progressive vision loss due to undertreatment
- **Note**: Generally discouraged in modern practice

## Next Steps

### Immediate (Week 1-2)
1. Fix T&E protocol calibration
2. Document parameter sensitivity analysis
3. Create unified disease model proposal

### Short-term (Month 1)
1. Implement PRN protocol
2. Validate all protocols with unified model
3. Add long-term validation tests
4. Model "treat-and-treat" outcomes to Year 5

### Medium-term (Month 2-3)
1. Implement protocol switching capabilities
2. Validate against real-world registry data
3. Compare fixed vs individualized approaches long-term

### Long-term (Month 3+)
1. Sensitivity analysis across parameter space
2. Publication-ready validation report
3. Web interface for protocol comparison
4. Cost-effectiveness analysis of different approaches

## Key Challenges and Solutions

### Challenge 1: Protocol-Specific vs Universal Parameters
**Solution**: Two-tier parameter system
- Tier 1: Universal disease/vision parameters
- Tier 2: Protocol-specific behavioral parameters

### Challenge 2: Matching Both Trials and Real-World
**Solution**: Separate validation tracks
- "Trial mode": Ideal adherence, no discontinuation
- "Real-world mode": Variable adherence, realistic attrition

### Challenge 3: Long-Term Extrapolation
**Solution**: Anchor to known long-term studies
- Use 5 and 10-year outcome data
- Model atrophy and fibrosis development
- Account for mortality and loss to follow-up

### Challenge 4: Fixed vs Adaptive Protocol Balance
**Solution**: Recognize different use cases
- Fixed/"treat-and-treat": System efficiency, predictability
- T&E: Individual optimization, resource-intensive
- Model both accurately without bias

## Success Criteria

The calibration will be considered successful when:

1. **Individual Protocol Accuracy**: Each protocol achieves within 15% of known outcomes
2. **Relative Performance**: Correct ordering (Monthly > T&E > Fixed > PRN)
3. **Long-Term Validity**: Realistic vision trajectories over 10 years
4. **Switching Capability**: Patients can change protocols with appropriate outcomes
5. **Computational Efficiency**: Full 10-year simulation runs in <1 minute

## References

1. VIEW 1/2 Trials (Heier et al., 2012)
2. Fight Retinal Blindness Registry 
3. Spooner et al. 10-year Meta-analysis (2023)
4. Chandra et al. 5-year UK Database Study
5. CATT/IVAN Trial Results

---

*Document Version*: 1.0  
*Last Updated*: January 2025  
*Next Review*: After T&E calibration complete