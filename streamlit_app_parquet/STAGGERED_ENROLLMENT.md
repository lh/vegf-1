# Staggered Patient Enrollment in AMD Protocol Explorer

This document describes the staggered patient enrollment feature implemented in the AMD Protocol Explorer (APE), which enables more realistic modeling of clinical trials and patient recruitment.

## Overview

In real-world clinical trials and treatment programs, patients are enrolled gradually over time rather than all at once. The staggered enrollment feature models this behavior by using a Poisson process to generate patient arrivals at a specified rate.

This approach provides several key benefits:
- More realistic modeling of patient recruitment patterns
- Better visualization of resource utilization over time
- Ability to analyze both calendar time and patient time
- Enhanced understanding of the "dilution effect" in trials with continuous enrollment

## Implementation

The staggered enrollment feature is implemented through the following components:

1. **StaggeredABS Class**: An extension of the AgentBasedSimulation class that implements Poisson-based patient arrivals
2. **Dual Timeframe Analysis**: Calendar time (real-world date) vs. patient time (weeks since enrollment) 
3. **Enhanced Visualization Functions**: Special plot types that incorporate sample size information
4. **Streamlit Integration**: Dedicated UI for configuring and running staggered simulations

## Key Features

### Poisson Process for Arrivals

Patient arrivals follow a Poisson process, where:
- The arrival rate parameter represents the average number of new patients per week
- Inter-arrival times follow an exponential distribution
- The actual number of patients may differ from the target due to random variation

### Dual Timeframe Analysis

The implementation tracks two distinct time dimensions:
- **Calendar Time**: The actual simulation date (e.g., "January 15, 2023")
- **Patient Time**: Time since a specific patient enrolled (e.g., "Week 12")

This dual perspective is crucial for understanding:
- How overall clinical outcomes evolve over the course of a study
- How individual patients respond to treatment over their personal treatment journey

### Sample Size Visualization

The visualization framework incorporates sample size information into the analysis:
- Bar charts indicate the number of patients at each time point
- Confidence intervals widen with smaller sample sizes
- Weighted smoothing techniques account for variable sample sizes

## Usage

To use the staggered enrollment feature:

1. Navigate to the "Staggered Simulation" tab in the Streamlit app
2. Configure the parameters:
   - **Duration**: Length of the simulation in years
   - **Target Population Size**: Approximate number of patients to enroll
   - **Arrival Rate**: Average number of new patients per week

3. Explore the results:
   - **Enrollment Distribution**: Histogram of patient enrollment over time
   - **Dual Timeframe Visualization**: Side-by-side comparison of calendar time vs. patient time
   - **Patient Time Analysis**: Visual acuity trajectories aligned by enrollment date

## Technical Details

### Class Structure

- `StaggeredABS`: Main simulation class implementing staggered enrollment
- `PatientGenerator`: Helper class for generating Poisson arrivals
- `ABSPatientGenerator`: ABS-specific implementation of patient generation

### Visualization Functions

- `plot_patient_acuity_by_patient_time`: Individual patient visualization by weeks since enrollment
- `plot_mean_acuity_with_sample_size`: Mean acuity with confidence intervals and sample size indicators
- `plot_dual_timeframe_acuity`: Side-by-side calendar time vs. patient time visualization

### Data Processing

The implementation enhances patient history records with additional time information:
- `calendar_time`: The actual simulation date
- `days_since_enrollment`: Number of days since patient enrollment
- `weeks_since_enrollment`: Number of weeks since patient enrollment

## Future Extensions

Potential enhancements to the staggered enrollment feature:
- Variable arrival rates to model seasonal recruitment patterns
- Cohort-based analysis for comparing patients enrolled in different time periods
- Multi-center trial simulation with center-specific enrollment rates
- Time-dependent dropout rates to model early vs. late discontinuations

## References

For more information on staggered enrollment in clinical trials, see:
- Lachin, J.M., Foulkes, M.A. (1986). "Evaluation of Sample Size and Power for Analyses of Survival with Allowance for Nonuniform Patient Entry, Losses to Follow-Up, Noncompliance, and Stratification"
- Buyse, M., Ryan, L.M. (1987). "Issues of efficiency in combining efficacy and safety data"