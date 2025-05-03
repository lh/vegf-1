# Literature Data Requirements for Simulation Parameters

This document outlines the specific data needed from literature to inform realistic parameters for our DES and ABS simulation models of AMD treatment.

## Disease State Parameters

### 1. Disease State Distribution
- **Prevalence at diagnosis**: Proportion of newly diagnosed AMD patients in each state (NAIVE, STABLE, ACTIVE, HIGHLY_ACTIVE)
- **Natural history**: Distribution of disease states in untreated populations over time
- **Key sources**: Population-based epidemiological studies, natural history cohorts

### 2. State Transition Probabilities
- **Baseline transitions**: Monthly/weekly probability of transitioning between states without treatment
  - NAIVE → STABLE, ACTIVE, HIGHLY_ACTIVE
  - STABLE → ACTIVE, HIGHLY_ACTIVE
  - ACTIVE → STABLE, HIGHLY_ACTIVE
  - HIGHLY_ACTIVE → STABLE, ACTIVE
- **Treatment-modified transitions**: How anti-VEGF injections modify these probabilities
- **Time-dependent factors**: How transition probabilities change with disease duration
- **Key sources**: CATT, IVAN, VIEW trials; long-term follow-up studies (SEVEN-UP, HORIZON)

## Vision Change Parameters

### 3. Treatment Response Data
- **Baseline vision changes**: Mean and standard deviation of letter changes for each disease state:
  - With injection: Currently modeled as normal distributions
    * NAIVE: [5, 1] (mean, std dev)
    * STABLE: [1, 0.5]
    * ACTIVE: [3, 1]
    * HIGHLY_ACTIVE: [2, 1]
  - Without injection:
    * NAIVE: [0, 0.5]
    * STABLE: [-0.5, 0.5]
    * ACTIVE: [-2, 1]
    * HIGHLY_ACTIVE: [-3, 1]
- **Response variability**: Patient-to-patient variation in treatment response
- **Key sources**: Pivotal anti-VEGF trials, real-world registries (FRB!, LUMINOUS)

### 4. Time-Dependent Factors
- **Treatment waning**: Rate at which treatment effect diminishes over time
  - Currently modeled as: time_factor = 1 + (weeks_since_injection / max_weeks)
  - Need data on: Optimal value for max_weeks (currently 52)
- **Cumulative effects**: How repeated injections affect long-term outcomes
- **Key sources**: Treat-and-extend studies, long-term extension trials

### 5. Ceiling Effects
- **Maximum vision**: Realistic ceiling for vision improvement (currently 100 letters)
- **Diminishing returns**: How improvement potential changes with baseline vision
  - Currently modeled as: ceiling_factor = 1 - (current_vision / max_vision)
- **Key sources**: Post-hoc analyses of clinical trials, stratified by baseline VA

### 6. Measurement Variability
- **Test-retest reliability**: Standard deviation of ETDRS letter score measurements
  - Currently modeled as: measurement_noise = [0, 0.5]
- **Key sources**: Clinical measurement studies, control groups in trials

## Clinical Practice Parameters

### 7. Resource Constraints
- **Clinic capacity**: Realistic patient throughput per day (currently 20)
- **Scheduling patterns**: Distribution of clinic days (currently 5 days/week)
- **Wait times**: Typical wait times for new and follow-up appointments
- **Key sources**: Health services research, clinic workflow studies, national audits

### 8. Patient Flow
- **Arrival patterns**: Rate of new patient referrals (currently 1/week)
- **Discontinuation rates**: Probability of treatment discontinuation by visit number
- **Adherence patterns**: Missed appointment rates and patterns
- **Key sources**: Electronic health record studies, registry data

### 9. Treatment Protocols
- **Protocol adherence**: How closely clinicians follow official protocols
- **Protocol variations**: Common modifications to standard protocols
- **Decision thresholds**: Vision/OCT thresholds used for treatment decisions
- **Key sources**: Clinical practice surveys, adherence studies, chart reviews

## Population Characteristics

### 10. Demographic Data
- **Age distribution**: Age range and distribution of AMD patients
- **Gender distribution**: Proportion of male/female patients
- **Comorbidity profiles**: Prevalence of relevant comorbidities
- **Key sources**: National eye disease registries, population-based studies

### 11. Baseline Values
- **Initial vision**: Distribution of baseline visual acuity (mean, SD)
  - Currently using normal distribution with configurable parameters
- **Disease duration**: Time from symptom onset to treatment initiation
- **OCT characteristics**: Distribution of baseline anatomical features
- **Key sources**: Baseline characteristics from clinical trials, registry data

## Specific Literature Sources

### Clinical Trials
1. **VIEW 1 & 2**: Aflibercept efficacy and safety
2. **HARBOR**: Ranibizumab dosing study
3. **CATT/IVAN**: Comparative effectiveness trials
4. **SEVEN-UP/HORIZON**: Long-term outcomes
5. **Protocol T**: Comparative effectiveness in DME (methodology relevant)

### Real-World Evidence
1. **Fight Retinal Blindness! Registry**: Large dataset from Australia/New Zealand
2. **LUMINOUS**: Global observational study of ranibizumab
3. **IRIS Registry**: US-based ophthalmology registry
4. **UK AMD Database**: National dataset from UK
5. **AURA Study**: European real-world outcomes study

### Health Services Research
1. **Clinic capacity studies**: Workflow and throughput analyses
2. **Healthcare utilization patterns**: Visit frequency and resource use
3. **Adherence and discontinuation studies**: Patterns of care interruption

## Implementation Strategy

### Priority Data Elements
1. **Highest priority**:
   - Disease state transition probabilities
   - Vision change distributions by disease state
   - Treatment waning parameters
   
2. **Secondary priority**:
   - Patient arrival and discontinuation rates
   - Measurement variability
   - Ceiling effects
   
3. **Tertiary priority**:
   - Demographic distributions
   - Comorbidity effects
   - Protocol variations

### Data Extraction Approach
1. **Systematic literature review**:
   - Focus on meta-analyses where available
   - Extract numerical parameters with confidence intervals
   - Document assumptions and limitations
   
2. **Parameter estimation**:
   - Use Bayesian methods to combine multiple sources
   - Develop plausible ranges for sensitivity analysis
   - Document derivation methods for each parameter

3. **Validation strategy**:
   - Compare simulation outputs to published outcomes
   - Calibrate parameters to match real-world patterns
   - Document validation process and results

## Documentation Requirements

For each parameter set derived from literature:
1. **Source documentation**:
   - Full citation of primary sources
   - Sample size and study characteristics
   - Quality assessment of evidence
   
2. **Parameter documentation**:
   - Central estimate and uncertainty range
   - Transformation methods (if applicable)
   - Implementation details in simulation
   
3. **Validation documentation**:
   - Comparison of simulation outputs to reference data
   - Sensitivity analysis results
   - Known limitations and assumptions

## Appendix: Parameter Mapping to Simulation

| Parameter Category | YAML Configuration Path | Current Default | Literature Source Needed |
|-------------------|-------------------------|-----------------|--------------------------|
| Disease States | clinical_model.disease_states | ["NAIVE", "STABLE", "ACTIVE", "HIGHLY_ACTIVE"] | Disease classification studies |
| Initial Distribution | clinical_model.initial_phase_transitions | HIGHLY_ACTIVE: 0.01 | Epidemiological studies |
| State Transitions | clinical_model.transition_probabilities | Various (see config) | Natural history studies, clinical trials |
| Vision Change (with injection) | clinical_model.vision_change.base_change.*.injection | Various by state | Clinical trials, real-world data |
| Vision Change (no injection) | clinical_model.vision_change.base_change.*.no_injection | Various by state | Natural history, placebo arms |
| Time Factor | clinical_model.vision_change.time_factor.max_weeks | 52 | Pharmacokinetic studies |
| Ceiling Factor | clinical_model.vision_change.ceiling_factor.max_vision | 100 | Clinical measurement studies |
| Measurement Noise | clinical_model.vision_change.measurement_noise | [0, 0.5] | Test-retest reliability studies |
| Clinic Capacity | simulation.scheduling.daily_capacity | 20 | Health services research |
| Clinic Schedule | simulation.scheduling.days_per_week | 5 | Practice pattern surveys |
| Patient Generation | simulation.patient_generation.rate_per_week | 1 | Epidemiological studies, clinic data |
