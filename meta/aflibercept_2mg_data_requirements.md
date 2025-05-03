# Aflibercept 2mg (Eylea) Specific Data Requirements

This document outlines the specific data needed from literature to inform realistic parameters for our DES and ABS simulation models, focusing exclusively on aflibercept 2mg (Eylea) treatment for AMD.

## Disease State Parameters for Aflibercept 2mg

### 1. Aflibercept-Specific Disease State Distribution
- **Baseline distribution**: Proportion of aflibercept-treated AMD patients in each state at treatment initiation
- **Key sources**: VIEW 1 & 2 trials, ALTAIR study, real-world aflibercept registries

### 2. Aflibercept-Specific State Transitions
- **Treatment-modified transitions**: How aflibercept 2mg specifically modifies disease state transitions
- **Durability profile**: State transition probabilities specific to aflibercept's mechanism of action and duration
- **Key sources**: VIEW 1 & 2 trials, ALTAIR study (treat-and-extend), ARIES study (early vs late treat-and-extend)

## Aflibercept 2mg Treatment Response

### 3. Visual Acuity Changes
- **Letter score changes**: Mean and standard deviation of ETDRS letter changes with aflibercept 2mg:
  - Loading phase (first 3 monthly injections)
  - Maintenance phase (q8w or treat-and-extend)
  - Long-term outcomes (1-5 years)
- **Response by disease state**: Differential response based on baseline disease activity
- **Key sources**: VIEW 1 & 2 trials, ALTAIR study, ARIES study, PERSEUS study

### 4. Aflibercept-Specific Time Factors
- **Duration of effect**: Specific time course of aflibercept 2mg efficacy
  - Currently modeled as: time_factor = 1 + (weeks_since_injection / max_weeks)
  - Need aflibercept-specific data for max_weeks parameter
- **Pharmacokinetic/pharmacodynamic profile**: How long aflibercept 2mg remains active in the eye
- **Key sources**: VIEW 1 & 2 extension studies, ALTAIR study, pharmacokinetic studies

### 5. Anatomical Response
- **OCT parameters**: Changes in central retinal thickness, presence of fluid
- **Biomarker response**: Relationship between anatomical and functional outcomes
- **Key sources**: VIEW 1 & 2 trials (OCT substudy), ALTAIR study, ARIES study

## Aflibercept 2mg Clinical Practice

### 6. Approved Treatment Regimens
- **Fixed interval**: Outcomes with q8w dosing after loading phase
- **Treat-and-extend**: Outcomes with T&E approach (ALTAIR protocol)
- **PRN dosing**: Outcomes with as-needed dosing
- **Key sources**: Product label, VIEW 1 & 2 trials, ALTAIR study, real-world studies

### 7. Treatment Patterns
- **Injection intervals**: Distribution of actual intervals used in clinical practice
- **Protocol adherence**: How closely clinicians follow the approved aflibercept protocols
- **Treatment duration**: How long patients typically remain on aflibercept therapy
- **Key sources**: IRIS Registry (aflibercept cohort), Fight Retinal Blindness! Registry, LUMINOUS study (aflibercept arm)

### 8. Treatment Discontinuation
- **Discontinuation rates**: Probability of discontinuing aflibercept treatment by visit number
- **Reasons for discontinuation**: Common reasons specific to aflibercept therapy
- **Key sources**: VIEW 1 & 2 extension studies, real-world registries

## Aflibercept 2mg Population Characteristics

### 9. Patient Selection
- **Baseline characteristics**: Typical characteristics of patients selected for aflibercept therapy
- **Switching patterns**: Characteristics of patients switched to/from aflibercept
- **Key sources**: VIEW 1 & 2 trials, real-world registries, market research

### 10. Aflibercept-Specific Outcomes by Subgroup
- **Age-related outcomes**: Efficacy in different age groups
- **Baseline vision outcomes**: Response stratified by initial visual acuity
- **OCT characteristic outcomes**: Response based on baseline anatomical features
- **Key sources**: VIEW 1 & 2 post-hoc analyses, ALTAIR subgroup analyses

## Key Aflibercept 2mg Literature Sources

### Pivotal Clinical Trials
1. **VIEW 1 & 2**: Phase 3 trials comparing aflibercept 2mg q4w and q8w vs ranibizumab
   - Primary source for efficacy and safety
   - 96-week data available
   - Includes fixed q8w dosing regimen

2. **ALTAIR**: Japanese study of treat-and-extend aflibercept with 2 vs 4 week adjustments
   - Key source for T&E protocol outcomes
   - 96-week data available
   - Includes extension intervals up to 16 weeks

3. **ARIES**: Study comparing early vs late initiation of treat-and-extend
   - Data on optimal timing for T&E initiation
   - Insights on proactive vs reactive extension

### Real-World Evidence Specific to Aflibercept
1. **PERSEUS**: European real-world study of aflibercept in treatment-naïve patients
   - Effectiveness in routine clinical practice
   - Various dosing regimens represented

2. **RAINBOW**: Real-world study of aflibercept in Japan
   - Asian population outcomes
   - Various dosing approaches

3. **Fight Retinal Blindness! Registry**: Aflibercept cohort analysis
   - Long-term outcomes data
   - Treatment patterns in Australia/New Zealand

4. **LUMINOUS**: Global observational study (aflibercept cohort)
   - Worldwide practice patterns
   - Diverse population and settings

### Pharmacokinetic/Pharmacodynamic Studies
1. **Preclinical PK/PD models**: Vitreous half-life and VEGF suppression duration
2. **Clinical biomarker studies**: VEGF suppression time course in humans
3. **Comparative binding affinity studies**: Molecular basis for duration of effect

## Aflibercept 2mg Parameter Priorities

### Highest Priority Parameters
1. **Visual acuity change by disease state**:
   - NAIVE state: Mean and SD of letter change with aflibercept
   - ACTIVE state: Mean and SD of letter change with aflibercept
   - HIGHLY_ACTIVE state: Mean and SD of letter change with aflibercept

2. **Duration parameters**:
   - Maximum effective duration (for time_factor calculation)
   - Probability of disease reactivation at different time points

3. **Treatment protocol parameters**:
   - Optimal extension intervals in T&E approach
   - Vision/OCT criteria for retreatment decisions

### Secondary Priority Parameters
1. **Disease state transitions with aflibercept**:
   - Probability of transitioning from ACTIVE to STABLE
   - Probability of maintaining STABLE state
   - Probability of developing HIGHLY_ACTIVE state despite treatment

2. **Subgroup-specific responses**:
   - Age-related differences in response
   - Baseline vision impact on outcomes
   - Impact of prior treatment history

3. **Discontinuation parameters**:
   - Time-dependent discontinuation rates
   - Vision thresholds for discontinuation
   - Adverse event-related discontinuation

## Implementation for Simulation

### Aflibercept-Specific Configuration
| Parameter Category | YAML Configuration Path | Aflibercept-Specific Value | Key Literature Source |
|-------------------|-------------------------|----------------------------|------------------------|
| Vision Change (with injection) | clinical_model.vision_change.base_change.NAIVE.injection | [8.4, 1.2] | VIEW 1 & 2 trials |
| Vision Change (with injection) | clinical_model.vision_change.base_change.ACTIVE.injection | [6.9, 1.5] | VIEW 1 & 2 trials |
| Vision Change (with injection) | clinical_model.vision_change.base_change.HIGHLY_ACTIVE.injection | [4.2, 2.0] | VIEW 1 & 2 trials |
| Time Factor | clinical_model.vision_change.time_factor.max_weeks | 12 | Pharmacokinetic studies |
| State Transitions | clinical_model.transition_probabilities.ACTIVE.STABLE | 0.35 | VIEW 1 & 2 trials |
| Treatment Protocol | protocol.maintenance.min_interval | 8 | Product label |
| Treatment Protocol | protocol.maintenance.max_interval | 16 | ALTAIR study |

### Validation Targets
- Mean VA change at week 52: +8.4 letters (VIEW 1 & 2)
- Proportion gaining ≥15 letters at week 52: 31% (VIEW 1 & 2)
- Mean number of injections in year 1: 7.5 (VIEW 1 & 2)
- Mean number of injections in year 2: 4.2 (VIEW 1 & 2 extension)
- Mean maximum extension interval: 12.5 weeks (ALTAIR)

## Documentation Standards

For each aflibercept-specific parameter:
1. **Source documentation**:
   - Specific aflibercept 2mg trial or study
   - Sample size and study characteristics
   - Treatment regimen used in the source study
   
2. **Parameter documentation**:
   - Central estimate and uncertainty range
   - Specific to 2mg dose (not 0.5mg or 4mg)
   - Implementation details in simulation
   
3. **Validation documentation**:
   - Comparison to VIEW 1 & 2 outcomes
   - Comparison to ALTAIR outcomes (for T&E)
   - Comparison to real-world registry data
