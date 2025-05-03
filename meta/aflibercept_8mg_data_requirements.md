# Aflibercept 8mg (Eylea HD) Data Requirements

This document outlines the specific data needed from literature to inform realistic parameters for our DES and ABS simulation models, focusing on aflibercept 8mg (Eylea HD) treatment for AMD. As this is a newer formulation with less available data, this document highlights key sources and identifies knowledge gaps.

## Disease State Parameters for Aflibercept 8mg

### 1. Aflibercept 8mg Disease State Distribution
- **Baseline distribution**: Proportion of patients in each disease state at initiation of 8mg treatment
- **Key sources**: PULSAR trial, limited real-world data

### 2. Aflibercept 8mg State Transitions
- **Treatment-modified transitions**: How the higher dose modifies disease state transitions compared to 2mg
- **Durability profile**: Extended durability potential with higher dose
- **Key sources**: PULSAR trial, pharmacokinetic/pharmacodynamic modeling

## Aflibercept 8mg Treatment Response

### 3. Visual Acuity Changes
- **Letter score changes**: Mean and standard deviation of ETDRS letter changes with 8mg dosing:
  - Loading phase (first 3 monthly injections)
  - Extended maintenance phase (q12w, q16w)
- **Comparative efficacy**: Differences in response compared to 2mg dosing
- **Key sources**: PULSAR trial (primary source)

### 4. Aflibercept 8mg-Specific Time Factors
- **Duration of effect**: Extended time course of aflibercept 8mg efficacy
  - Currently modeled as: time_factor = 1 + (weeks_since_injection / max_weeks)
  - Need 8mg-specific data for max_weeks parameter (potentially longer than 2mg)
- **Pharmacokinetic profile**: How long 8mg remains active in the eye
- **Key sources**: PULSAR trial, limited pharmacokinetic studies

### 5. Anatomical Response
- **OCT parameters**: Changes in central retinal thickness, presence of fluid with 8mg
- **Biomarker response**: Relationship between anatomical and functional outcomes
- **Key sources**: PULSAR trial OCT data

## Aflibercept 8mg Clinical Practice

### 6. Approved Treatment Regimens
- **Extended interval dosing**: Outcomes with q12w and q16w dosing
- **Key sources**: PULSAR trial, product label (when available)

### 7. Treatment Patterns
- **Injection intervals**: Potential for longer intervals compared to 2mg
- **Protocol adherence**: Limited real-world data on protocol adherence
- **Key sources**: Early real-world experience, PULSAR trial

### 8. Treatment Discontinuation
- **Discontinuation rates**: Limited data on long-term discontinuation
- **Key sources**: PULSAR trial extension data (when available)

## Key Aflibercept 8mg Literature Sources

### Pivotal Clinical Trials
1. **PULSAR**: Phase 3 trial comparing aflibercept 8mg vs 2mg
   - Primary source for efficacy and safety
   - Evaluates extended dosing intervals (q12w, q16w)
   - Non-inferiority design vs 2mg

### Limited Real-World Evidence
1. **Early adoption studies**: Initial real-world experience (limited)
2. **Post-marketing surveillance**: Safety data (when available)

### Pharmacokinetic/Pharmacodynamic Studies
1. **Preclinical PK/PD models**: Vitreous half-life and VEGF suppression duration
2. **Dose-ranging studies**: Relationship between dose and duration of effect

## Aflibercept 8mg Parameter Priorities

### Highest Priority Parameters
1. **Visual acuity change by disease state**:
   - NAIVE state: Mean and SD of letter change with 8mg
   - ACTIVE state: Mean and SD of letter change with 8mg
   - HIGHLY_ACTIVE state: Mean and SD of letter change with 8mg

2. **Duration parameters**:
   - Maximum effective duration (for time_factor calculation)
   - Probability of disease reactivation at different time points with 8mg

3. **Treatment protocol parameters**:
   - Optimal extension intervals with 8mg
   - Vision/OCT criteria for retreatment decisions

### Knowledge Gaps and Extrapolation Needs
1. **Long-term efficacy**: Limited data beyond PULSAR trial duration
2. **Real-world effectiveness**: Limited data on effectiveness outside clinical trials
3. **Disease state transitions**: May need to extrapolate from 2mg data with adjustments
4. **Subgroup responses**: Limited data on response in different patient subgroups

## Implementation for Simulation

### Aflibercept 8mg-Specific Configuration
| Parameter Category | YAML Configuration Path | Aflibercept 8mg Value | Key Literature Source |
|-------------------|-------------------------|------------------------|------------------------|
| Vision Change (with injection) | clinical_model.vision_change.base_change.NAIVE.injection | [8.7, 1.3] | PULSAR trial |
| Vision Change (with injection) | clinical_model.vision_change.base_change.ACTIVE.injection | [7.1, 1.6] | PULSAR trial |
| Vision Change (with injection) | clinical_model.vision_change.base_change.HIGHLY_ACTIVE.injection | [4.5, 2.1] | PULSAR trial |
| Time Factor | clinical_model.vision_change.time_factor.max_weeks | 16 | PULSAR trial |
| State Transitions | clinical_model.transition_probabilities.ACTIVE.STABLE | 0.40 | PULSAR trial |
| Treatment Protocol | protocol.maintenance.min_interval | 12 | PULSAR trial |
| Treatment Protocol | protocol.maintenance.max_interval | 16 | PULSAR trial |

### Validation Targets
- Mean VA change at week 48: Non-inferior to 2mg (PULSAR)
- Proportion of patients on q12w or q16w dosing: ~80% (PULSAR)
- Mean number of injections in year 1: ~5-6 (PULSAR)

## Extrapolation Methods

Due to limited data for aflibercept 8mg, the following extrapolation methods may be necessary:

1. **Dose-response relationship**: Use 2mg data with adjustment factor based on dose ratio
2. **PK/PD modeling**: Use pharmacokinetic principles to estimate duration of effect
3. **Bayesian updating**: Start with 2mg priors, update with limited 8mg data
4. **Expert elicitation**: Supplement limited data with structured expert opinion

## Documentation Standards

For each aflibercept 8mg parameter:
1. **Source documentation**:
   - Specific aflibercept 8mg trial or study
   - Sample size and study limitations
   - Confidence in the evidence
   
2. **Parameter documentation**:
   - Central estimate and uncertainty range
   - Extrapolation methods if used
   - Implementation details in simulation
   
3. **Validation documentation**:
   - Comparison to PULSAR outcomes
   - Sensitivity analysis for uncertain parameters
   - Explicit documentation of knowledge gaps
