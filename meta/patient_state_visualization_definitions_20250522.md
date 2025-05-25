# Patient State Visualization Definitions

**Created:** 2025-05-22 19:46:00  
**Context:** Streamgraph visualization development - defining current vs cumulative state views and clinical labels

## Executive Summary

We have developed two complementary approaches to visualizing patient states over time:

1. **Current State View**: Shows where patients are RIGHT NOW at each time point
2. **Cumulative State View**: Shows what patients have EVER experienced

## Current State View (Operational Planning)

**Purpose**: Resource planning and operational management  
**Key Insight**: "Recommencing treatment" is necessarily evanescent - patients cycle through this state briefly

### State Definitions

| State Label | Clinical Meaning | Duration | Mapping from Simulation |
|-------------|------------------|----------|------------------------|
| **Active** | Currently receiving regular injections | Ongoing | phase: loading/maintenance, not retreatment |
| **Recommencing treatment** | Currently undergoing retreatment after discontinuation | Transient (1-3 months) | is_retreatment_visit=True or loading after monitoring |
| **Untreated - remission** | Stable patients who reached max interval and stopped | Long-term | discontinuation_type: stable_max_interval |
| **Not booked** | Administrative issues preventing treatment | Variable | discontinuation_type: random_administrative |
| **Not renewed** | Treatment course complete, clinician chose not to continue | Long-term | discontinuation_type: course_complete_but_not_renewed |
| **Discontinued without reason** | Clinician decision to stop for unclear reasons | Variable | phase: monitoring without clear discontinuation_type |

## Cumulative State View (Outcome Analysis)

**Purpose**: Historical analysis and treatment pattern understanding  
**Key Insight**: Once categorized, patients remain in that category to show treatment history

### State Definitions

| State Label | Clinical Meaning | Mapping from Simulation |
|-------------|------------------|------------------------|
| **Active** | Never discontinued | No discontinuation flags ever set |
| **Retreated** | Has experienced at least one treatment restart | has_been_retreated=True |
| **Discontinued planned** | Has been discontinued due to stable remission | has_been_discontinued=True, type: stable_max_interval |
| **Discontinued administrative** | Has experienced administrative barriers | has_been_discontinued=True, type: random_administrative |
| **Discontinued duration** | Has completed treatment course without renewal | has_been_discontinued=True, type: course_complete_but_not_renewed |
| **Discontinued** | Has been discontinued without clear reason | has_been_discontinued=True, unclear type |

## Clinical Insights

### Why "Recommencing Treatment" Oscillates
- Represents patients currently in the retreatment process
- Transient state: patients move through quickly
- Oscillation shows turnover in retreatment pipeline
- Much more clinically realistic than permanent "retreated" label

### Conservation Principle
- All patients must be in exactly one state at any time point
- Total patient count preserved across all time points
- Transitions allowed between any states based on clinical circumstances

## Missing Implementation: Vision-Based Stopping

**Critical Gap**: No discontinuation criterion for poor visual outcomes

### Required Implementation
- **Threshold**: Stop treatment if vision drops below 30 letters
- **New Category**: "Stopped - poor outcome"
- **Current Status**: `premature_discontinuation_rate: 0.0` indicates this is missing
- **Priority**: High - essential for clinical realism

### Impact
- Currently missing significant discontinuation reason
- Affects simulation realism and treatment effectiveness modeling
- Important for understanding patient flow patterns

## Technical Implementation

### Data Flow
1. **Simulation**: Sets phase, discontinuation flags, retreatment flags
2. **Current State Logic**: Determines state from current phase and context
3. **Cumulative State Logic**: Uses has_been_X flags to maintain history
4. **Visualization**: Maps states to clinical labels with appropriate colors

### Key Files
- `create_current_state_streamgraph.py`: Current state visualization
- `create_patient_state_streamgraph.py`: Cumulative state visualization  
- `run_streamgraph_simulation_parquet.py`: State flag generation
- `visualization/color_system.py`: Consistent color mapping

## Usage Guidelines

### When to Use Current State View
- Operational planning and resource allocation
- Understanding current treatment load
- Scheduling and capacity planning
- Real-time treatment flow analysis

### When to Use Cumulative State View
- Treatment outcome analysis
- Historical pattern recognition
- Research and effectiveness studies
- Patient journey mapping

## Future Enhancements

1. **Vision-based discontinuation criterion** (Priority: High)
2. **Enhanced tooltips with full glossary**
3. **Interactive state transition analysis**
4. **Comparative visualization dashboard**

---

**Last Updated**: 2025-05-22 19:46:00  
**Related Files**: See streamgraph visualization scripts and meta/visualization_templates.md  
**Status**: Current state view implemented and tested, vision criterion pending