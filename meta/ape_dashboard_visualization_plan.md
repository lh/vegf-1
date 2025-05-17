# APE: AMD Protocol Explorer Dashboard Visualization Plan

## Overview

This document outlines the implementation plan for visualizations in the APE (AMD Protocol Explorer) Streamlit dashboard. The visualizations will help users understand and analyze simulation results, with a focus on treatment patterns, visual acuity outcomes, and patient journeys.

## Priority 1: Interactive Patient Explorer

### Purpose

The Interactive Patient Explorer will allow users to select individual patients from simulation results and examine their complete treatment journey, including visual acuity changes, treatment decisions, and disease activity.

### Key Features

#### 1. Patient Selection

- Dropdown or searchable list of patient IDs
- Summary statistics for each patient (injections, visits, VA change)
- Option to randomly sample patients with specific characteristics (e.g., discontinued, improved VA)

#### 2. Timeline Visualization

- Interactive timeline of patient's treatment journey
- Color-coded markers for different event types:
  - Injections (red triangles)
  - OCT scans (blue circles)
  - Monitoring visits (green squares)
  - Discontinuation events (black diamond)
- Visual acuity trajectory overlaid on timeline
- Phase transitions clearly marked (loading → maintenance → discontinued)
- Tooltips showing detailed information for each visit

#### 3. Visit Details Panel

- Detailed table of all visits for selected patient
- Columns: Date, Visit Type, Actions, VA, Disease State, Phase, Interval
- Ability to sort and filter visits
- Click to highlight corresponding point in timeline

#### 4. Clinical Outcomes Summary

- Key metrics panel:
  - Baseline VA and final VA
  - Total injections received
  - Average treatment interval
  - Time spent in each phase
  - Discontinuation status and type (if applicable)
  - Recurrence details (if applicable)
- Before/after VA comparison with clinical significance indicators

### Technical Implementation

#### Data Processing Requirements

- Extract patient history from simulation results
- Calculate derived metrics (VA change, average intervals, etc.)
- Format dates and times consistently
- Handle missing data gracefully

#### Visualization Components

- Timeline: Plotly interactive timeline with multiple series
- Metrics: Streamlit metrics and columns
- Details: Streamlit AgGrid or DataTable for visit history
- Status indicators: Custom HTML/CSS for phase and status displays

#### Interactivity

- Synchronize selection across all components
- Highlight selected visits in timeline when clicked in table
- Zoom and pan timeline to focus on specific time periods
- Toggle visibility of different event types

## Future Visualization Categories

### Visual Acuity Trajectories

- Mean VA over time with confidence intervals
- Individual patient VA trajectories (sample of patients)
- VA distribution at key timepoints
- VA changes by injection count

### Treatment Patterns

- Injection frequency heatmap
- Treatment duration waterfall plot
- Injection intervals by sequence number
- Phase transition analysis

### Disease Activity Analysis

- Fluid detection rates over time
- Recurrence patterns visualization
- Time to first recurrence distribution
- Treatment response categorization

### Protocol Compliance

- Loading phase completion rates
- Interval adherence visualization
- Clinician variation analysis
- Protocol deviation patterns

### Simulation Metrics Dashboard

- KPI summary cards
- Treatment burden metrics
- Cost-effectiveness analysis
- Sensitivity analysis visualization

### Comparative Analysis

- ABS vs DES comparison
- Protocol comparison
- Parameter sensitivity visualization
- Population subgroup comparison

## Implementation Phases

### Phase 1: Core Infrastructure & Patient Explorer

- Set up data processing pipeline
- Implement Interactive Patient Explorer
- Add basic KPI summary metrics
- Create visualizations for individual patient data

### Phase 2: Population-Level Visualizations

- Implement Visual Acuity Trajectories
- Add Treatment Patterns visualizations
- Create Disease Activity Analysis charts
- Develop Protocol Compliance visualizations

### Phase 3: Advanced Analysis & Comparison

- Implement comparative analysis tools
- Add parameter sensitivity visualization
- Create cost-effectiveness analysis
- Develop custom report generation

### Phase 4: Integration & Optimization

- Connect all visualizations with consistent filtering
- Optimize performance for large datasets
- Add data export capabilities
- Implement advanced customization options

## Data Requirements

### Patient-Level Data

```python
{
    "patient_id": "PATIENT001",
    "history": [
        {
            "date": datetime(2023, 1, 1),
            "type": "regular_visit",
            "actions": ["vision_test", "oct_scan", "injection"],
            "baseline_vision": 65.0,
            "vision": 65.0,
            "disease_state": "active",
            "phase": "loading",
            "interval": 4
        },
        # More visits...
    ],
    "treatment_status": {
        "active": False,
        "recurrence_detected": True,
        "discontinuation_date": datetime(2023, 6, 1),
        "cessation_type": "planned"
    },
    "disease_characteristics": {
        "has_PED": True
    }
}
```

### Simulation-Level Data

```python
{
    "config": {
        "num_patients": 1000,
        "duration_days": 365,
        "simulation_type": "ABS"
    },
    "stats": {
        "total_visits": 12500,
        "total_injections": 8500,
        "total_oct_scans": 12500,
        "vision_improvements": 750,
        "vision_declines": 250,
        "protocol_completions": 850,
        "protocol_discontinuations": 350,
        "monitoring_visits": 400,
        "retreatments": 120
    },
    "discontinuation_stats": {
        "discontinuations": {
            "planned": 200,
            "administrative": 100,
            "time_based": 50,
            "premature": 0
        },
        "retreatments_by_type": {
            "planned": 80,
            "administrative": 30,
            "time_based": 10,
            "premature": 0
        }
    }
}
```

## Next Steps

1. Implement the Interactive Patient Explorer as the first priority
   - Create data processing functions to extract and format patient data
   - Develop the timeline visualization component
   - Build the detailed visit history table
   - Implement the clinical outcomes summary panel

2. Test with sample simulation data from both ABS and DES simulations

3. Add basic simulation metrics summary to provide context

4. Gather feedback and iterate on the visualizations