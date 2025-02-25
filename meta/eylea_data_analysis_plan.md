# Eylea Treatment Data Analysis Plan

## Objective
Derive clinically realistic parameters for intravitreal injection simulations from real-world treatment data.

## Phase 1 - Data Preparation & Exploration
1. Data Quality Assessment:
   - Check completeness of key fields: injection dates, VA measurements, CRT values
   - Identify missing data patterns
   - Assess distribution of baseline characteristics (age, baseline VA, comorbidities)

2. Cohort Selection:
   - Filter to complete treatment courses
   - Exclude patients with <3 injections
   - Stratify by treatment eye (first vs second eye treated)

## Phase 2 - Temporal Injection Analysis
1. Injection Interval Calculation:
   - Compute time between consecutive injections per patient
   - Identify protocol patterns (monthly vs treat-and-extend)
   
2. Treatment Intensity Metrics:
   - Injections/year calculation
   - Duration of treatment persistence
   - Gap analysis (>6 month breaks)

3. Visualization:
   - Kernel density plot of injection intervals
   - Waterfall plot of treatment duration
   - Heatmap of injection frequency over time

## Phase 3 - Visual Acuity Analysis  
1. Trajectory Modeling:
   - Slopes of VA change from baseline
   - Peak VA achievement timing
   - Proportion maintaining ≥5 letter gain

2. Statistical Modeling:
   - Mixed-effects model with random patient intercepts
   - Time-to-peak VA analysis
   - VA variance decomposition (within/between patient)

3. Visualization:
   - Spaghetti plots of individual VA trajectories
   - LOESS curve of population-level trend
   - Boxplots of VA distribution at fixed timepoints

## Phase 4 - Anatomical Response Analysis
1. CRT Changes:
   - Absolute/relative CRT reduction from baseline
   - Correlation with VA changes
   - Time to stable CRT (<10% variation)

2. Fluid Status:
   - Presence of IRF/SRF over time
   - Fluid recurrence patterns

## Phase 5 - Survival Analysis
1. Discontinuation Predictors:
   - Cox PH model for treatment dropout
   - Competing risks analysis (death vs other discontinuation)
   
2. Retention Metrics:
   - Kaplan-Meier survival curves
   - Median treatment duration
   - 1/2/3-year retention rates

## Phase 6 - Parameter Derivation for Simulation
1. Treatment Response Parameters:
   - VA change distributions (mean, SD) for responders/non-responders
   - Probability of anatomical response
   - Time-to-response distributions

2. Disease Progression Parameters:
   - Rate of VA decline without treatment
   - Probability of disease reactivation
   - Time-to-reactivation distributions

3. Treatment Protocol Parameters:
   - Empirical distribution of injection intervals
   - Probability of protocol switching
   - Discontinuation hazard function

## Implementation Plan

### Initial Data Analysis Script
1. Create `analysis/eylea_data_analysis.py` for:
   - Data loading and cleaning
   - Patient cohort identification
   - Basic descriptive statistics

2. Key metrics to calculate:
   - Mean/median injection intervals
   - VA change from baseline at 3/6/12 months
   - Treatment duration distribution

### Visualization Module
1. Create `visualization/treatment_patterns_viz.py` for:
   - Injection interval distributions
   - VA trajectory plots
   - Treatment persistence curves

### Parameter Estimation Module
1. Create `analysis/parameter_estimation.py` for:
   - Statistical modeling of VA trajectories
   - Fitting distributions to empirical data
   - Generating parameter tables for simulation input

### Integration with Simulation
1. Create parameter configuration files:
   - Update `protocols/parameter_sets/eylea/` with derived parameters
   - Document parameter sources and confidence intervals
