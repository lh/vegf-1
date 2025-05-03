# Faricimab (Vabysmo) Data Requirements

This document outlines the specific data needed from literature to inform realistic parameters for our DES and ABS simulation models, focusing on faricimab (Vabysmo) treatment for AMD. As a newer bispecific antibody targeting both VEGF-A and Ang-2, faricimab has a more limited evidence base, so this document highlights key sources and identifies knowledge gaps.

## Disease State Parameters for Faricimab

### 1. Faricimab Disease State Distribution
- **Baseline distribution**: Proportion of patients in each disease state at initiation of faricimab treatment
- **Key sources**: TENAYA and LUCERNE trials, limited real-world data

### 2. Faricimab-Specific State Transitions
- **Treatment-modified transitions**: How the dual mechanism of action modifies disease state transitions
- **Durability profile**: Extended durability potential with dual inhibition
- **Key sources**: TENAYA and LUCERNE trials, AVONELLE-X extension study

## Faricimab Treatment Response

### 3. Visual Acuity Changes
- **Letter score changes**: Mean and standard deviation of ETDRS letter changes with faricimab:
  - Loading phase (first 4 monthly injections)
  - Extended maintenance phase (q8w, q12w, q16w)
- **Comparative efficacy**: Differences in response compared to aflibercept
- **Key sources**: TENAYA and LUCERNE trials (primary sources)

### 4. Faricimab-Specific Time Factors
- **Duration of effect**: Extended time course of faricimab efficacy due to dual mechanism
  - Currently modeled as: time_factor = 1 + (weeks_since_injection / max_weeks)
  - Need faricimab-specific data for max_weeks parameter
- **Pharmacokinetic profile**: How long faricimab remains active in the eye
- **Key sources**: TENAYA and LUCERNE trials, pharmacokinetic studies

### 5. Anatomical Response
- **OCT parameters**: Changes in central retinal thickness, presence of fluid
- **Biomarker response**: Relationship between anatomical and functional outcomes
- **Ang-2 specific effects**: Potential vascular stabilization effects not seen with anti-VEGF alone
- **Key sources**: TENAYA and LUCERNE OCT data, mechanistic studies

## Faricimab Clinical Practice

### 6. Approved Treatment Regimens
- **Extended interval dosing**: Outcomes with personalized treatment interval (PTI) approach
- **Distribution of intervals**: Proportion of patients achieving q8w, q12w, q16w dosing
- **Key sources**: TENAYA and LUCERNE trials, product label

### 7. Treatment Patterns
- **Injection intervals**: Potential for longer intervals compared to anti-VEGF monotherapy
- **Protocol adherence**: Limited real-world data on protocol adherence
- **Key sources**: Early real-world experience, TENAYA and LUCERNE trials

### 8. Treatment Discontinuation
- **Discontinuation rates**: Limited data on long-term discontinuation
- **Key sources**: AVONELLE-X extension study (when available)

## Key Faricimab Literature Sources

### Pivotal Clinical Trials
1. **TENAYA and LUCERNE**: Phase 3 trials comparing faricimab vs aflibercept
   - Primary source for efficacy and safety
   - Evaluates personalized treatment interval (PTI) approach
   - Non-inferiority design vs aflibercept

2. **AVONELLE-X**: Long-term extension study
   - Data on durability beyond initial trial period
   - Safety with extended use

### Limited Real-World Evidence
1. **Early adoption studies**: Initial real-world experience (very limited)
2. **Post-marketing surveillance**: Safety data (when available)

### Mechanistic Studies
1. **Dual inhibition studies**: Effects of combined VEGF-A and Ang-2 inhibition
2. **Preclinical models**: Vascular stabilization effects

## Faricimab Parameter Priorities

### Highest Priority Parameters
1. **Visual acuity change by disease state**:
   - NAIVE state: Mean and SD of letter change with faricimab
   - ACTIVE state: Mean and SD of letter change with faricimab
   - HIGHLY_ACTIVE state: Mean and SD of letter change with faricimab

2. **Duration parameters**:
   - Maximum effective duration (for time_factor calculation)
   - Probability of disease reactivation at different time points with faricimab

3. **Treatment protocol parameters**:
   - Distribution of patients achieving different treatment intervals
   - Vision/OCT criteria for retreatment decisions

### Knowledge Gaps and Extrapolation Needs
1. **Long-term efficacy**: Limited data beyond TENAYA and LUCERNE duration
2. **Real-world effectiveness**: Very limited data on effectiveness outside clinical trials
3. **Disease state transitions**: May need to extrapolate from anti-VEGF data with adjustments
4. **Dual mechanism effects**: Limited understanding of how Ang-2 inhibition affects disease states

## Implementation for Simulation

### Faricimab-Specific Configuration
| Parameter Category | YAML Configuration Path | Faricimab Value | Key Literature Source |
|-------------------|-------------------------|-----------------|------------------------|
| Vision Change (with injection) | clinical_model.vision_change.base_change.NAIVE.injection | [8.3, 1.4] | TENAYA/LUCERNE trials |
| Vision Change (with injection) | clinical_model.vision_change.base_change.ACTIVE.injection | [7.0, 1.5] | TENAYA/LUCERNE trials |
| Vision Change (with injection) | clinical_model.vision_change.base_change.HIGHLY_ACTIVE.injection | [4.3, 2.0] | TENAYA/LUCERNE trials |
| Time Factor | clinical_model.vision_change.time_factor.max_weeks | 16 | TENAYA/LUCERNE trials |
| State Transitions | clinical_model.transition_probabilities.ACTIVE.STABLE | 0.38 | TENAYA/LUCERNE trials |
| Treatment Protocol | protocol.maintenance.min_interval | 8 | Product label |
| Treatment Protocol | protocol.maintenance.max_interval | 16 | Product label |

### Validation Targets
- Mean VA change at week 48: Non-inferior to aflibercept (TENAYA/LUCERNE)
- Proportion of patients on q12w or q16w dosing: ~80% (TENAYA/LUCERNE)
- Mean number of injections in year 1: ~6-7 (TENAYA/LUCERNE)

## Unique Considerations for Faricimab

### 1. Dual Mechanism of Action
- **Ang-2 inhibition effects**: Potential for vascular stabilization not captured in current model
- **Biomarker changes**: Different pattern of biomarker changes compared to anti-VEGF alone
- **Implementation approach**: May require new disease state or modifier to capture dual effects

### 2. Personalized Treatment Interval (PTI) Approach
- **Assessment-based extension**: Protocol differs from treat-and-extend
- **Implementation approach**: May require modification to treatment decision logic

### 3. Potential for Disease Modification
- **Vascular stabilization**: Theoretical potential for more durable effect
- **Implementation approach**: May require adjustment to disease state transition probabilities

## Extrapolation Methods

Due to limited data for faricimab, the following extrapolation methods may be necessary:

1. **Comparative efficacy**: Use aflibercept data with adjustment factors based on trial results
2. **Mechanistic modeling**: Incorporate dual mechanism effects based on preclinical data
3. **Bayesian updating**: Start with anti-VEGF priors, update with limited faricimab data
4. **Expert elicitation**: Supplement limited data with structured expert opinion

## Documentation Standards

For each faricimab parameter:
1. **Source documentation**:
   - Specific faricimab trial or study
   - Sample size and study limitations
   - Confidence in the evidence
   
2. **Parameter documentation**:
   - Central estimate and uncertainty range
   - Extrapolation methods if used
   - Implementation details in simulation
   
3. **Validation documentation**:
   - Comparison to TENAYA/LUCERNE outcomes
   - Sensitivity analysis for uncertain parameters
   - Explicit documentation of knowledge gaps
