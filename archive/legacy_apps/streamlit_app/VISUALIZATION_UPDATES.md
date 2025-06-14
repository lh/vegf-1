# Visualization Updates for AMD Protocol Explorer

This document describes the enhanced visualization capabilities added to AMD Protocol Explorer to support staggered patient enrollment and dual timeframe analysis.

## Overview

To properly visualize data from simulations with staggered patient enrollment, we have added several new visualization functions that support dual timeframe analysis and sample size awareness.

## New Visualization Functions

The following new functions have been added to `/visualization/acuity_viz.py`:

### 1. `plot_patient_acuity_by_patient_time`

This function plots a single patient's visual acuity trajectory by weeks since enrollment rather than by calendar date.

**Key features:**
- X-axis represents weeks since patient enrollment
- Markers indicate injection visits and monitoring visits
- Vertical grid lines at standard clinical timepoints (4, 12, 24, 36, 48 weeks)

**Use case:** Analyzing individual patient treatment response over their personal treatment journey

### 2. `plot_mean_acuity_with_sample_size`

This function creates a dual-axis visualization showing mean visual acuity with confidence intervals and a bar chart showing sample size at each time point.

**Key features:**
- Primary axis shows mean visual acuity with 95% confidence intervals
- Secondary axis shows sample size as bar chart
- Supports both calendar time and patient time modes
- Confidence intervals widen appropriately with smaller sample sizes
- Properly handles missing data and varying sample sizes

**Use case:** Understanding how statistical confidence varies with sample size over time, especially important in staggered enrollment where early and late timepoints have fewer patients

### 3. `plot_dual_timeframe_acuity`

This function creates a two-panel visualization comparing calendar time and patient time analysis side-by-side.

**Key features:**
- Left panel shows mean visual acuity by calendar date
- Right panel shows mean visual acuity by weeks since enrollment
- Both panels include sample size indicators
- Common y-axis scale for direct comparison
- Demonstrates the "dilution effect" in calendar time due to continuous enrollment

**Use case:** Comparing the two time perspectives to distinguish time-based effects from enrollment effects

## Sample Size Awareness

A key enhancement in these visualizations is sample size awareness:

- **Variable confidence intervals:** Confidence intervals are calculated based on standard error (σ/√n), so they automatically widen with smaller sample sizes
- **Visual sample size indication:** Bar charts show the number of patients at each time point
- **Weighted smoothing:** When smoothing is applied, it respects sample sizes, giving more weight to timepoints with more patients

## Dual Timeframe Analysis

The dual timeframe approach enables important insights:

1. **Calendar time analysis:**
   - Shows real-world timeline (e.g., January 2023 to December 2023)
   - Useful for resource planning and utilization forecasting
   - Affected by the "dilution effect" where new patients continuously enter the study
   - Early timepoints typically show lower mean acuity due to predominance of newly enrolled patients

2. **Patient time analysis:**
   - Shows weeks since enrollment (e.g., Week 0 to Week 52)
   - Useful for understanding treatment response trajectory
   - Eliminates the dilution effect by aligning patients by their individual start dates
   - Later timepoints have fewer patients due to more recent enrollments

## Integration with Streamlit

These visualizations are integrated into the Streamlit app through:

1. A dedicated "Staggered Simulation" tab
2. Enhanced Patient Explorer that supports both standard and staggered simulation data
3. Interactive display of dual timeframe visualizations
4. Detailed explanation of visualization interpretation

## Technical Implementation

The implementation handles several challenges:

- **Time alignment:** Converting between calendar dates and weeks since enrollment
- **Varying sample sizes:** Properly weighting means and calculating confidence intervals
- **Missing data:** Handling patients who haven't reached later timepoints yet
- **Figure composition:** Creating multi-panel visualizations with shared axes and legends

## Future Enhancements

Planned future enhancements to visualization capabilities:

1. **Interactive time sliders:** Allow users to focus on specific time periods
2. **Cohort comparison:** Group patients by enrollment period for direct comparison
3. **3D visualization:** Add a third dimension to show distribution of outcomes over time
4. **Projection capabilities:** Extrapolate trends to future timepoints based on current data
5. **Patient subgroup analysis:** Compare outcomes between different patient subgroups

## Using the New Visualizations

To use these visualizations in your own analysis:

1. Import the functions from `visualization.acuity_viz`
2. Prepare patient data with appropriate date information
3. For patient time analysis, ensure enrollment dates are available for each patient
4. Call the appropriate visualization function with your data

Example:
```python
from visualization.acuity_viz import plot_dual_timeframe_acuity

plot_dual_timeframe_acuity(
    patient_data=patient_histories,
    enrollment_dates=enrollment_dates,
    start_date=simulation_start_date,
    end_date=simulation_end_date,
    show=True,
    save_path="dual_timeframe_analysis.png"
)
```
EOF < /dev/null