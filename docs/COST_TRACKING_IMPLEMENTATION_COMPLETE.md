# Cost Tracking Implementation Complete

## Summary

Cost tracking functionality has been successfully implemented for the AMD simulation system, with a focus on the time-based T&E and T&T protocols as requested.

## What Was Implemented

### 1. Task-Based Workload Tracking
- Moved from personnel-specific tracking (nurses/consultants) to task-based tracking
- Key tasks tracked:
  - Injection tasks
  - Decision tasks
  - Imaging tasks
  - Administrative tasks
  - Virtual review tasks
- Flexible staffing model allows sites to assign tasks to available personnel

### 2. Enhanced Cost Tracker (`simulation_v2/economics/enhanced_cost_tracker.py`)
- Visit type classification:
  - Initial assessment
  - Loading phase injections
  - T&E assessments (full assessment every visit)
  - T&T injection-only visits (nurse-led)
  - T&T annual assessments
- NHS HRG-aligned cost calculations
- Patient-level cost tracking
- Workload metrics by month

### 3. Cost-Aware Simulation Engine (`simulation_v2/engines/abs_engine_with_enhanced_costs.py`)
- Extends standard ABS engine with cost tracking
- Integrates with clinical improvements
- Determines visit types based on protocol
- Records costs and workload for each visit
- Produces enhanced results with economic data

### 4. Streamlit UI Components

#### Cost Configuration Widget (`ape/components/cost_tracking/cost_configuration_widget.py`)
- Drug selection with NHS prices:
  - Eylea Biosimilar (£355) - default
  - Eylea Originator (£979)
  - Other anti-VEGF options
  - Custom pricing
- Cost adjustment sliders
- Protocol cost comparison preview
- Year 1 cost estimates

#### Workload Visualizer (`ape/components/cost_tracking/workload_visualizer.py`)
- Task timeline visualization
- Task distribution analysis
- Resource requirement charts
- FTE calculations
- Data export functionality

#### Cost Analysis Dashboard (`ape/components/cost_tracking/cost_analysis_dashboard.py`)
- Key metrics display
- Cost breakdown visualization
- Patient-level analysis
- Cost timeline tracking
- Data export options

### 5. Integration Points

#### Updated Simulation Page (`pages/2_Simulations_with_costs.py`)
- Added cost tracking toggle
- Integrated cost configuration UI
- Pass cost config to simulation runner

#### New Cost Analysis Page (`pages/5_Cost_Analysis.py`)
- Dedicated page for economic analysis
- Automatically loads cost data from simulations
- Handles both live cost tracker objects and saved data files

#### Enhanced Simulation Runner (`ape/core/simulation_runner_with_costs.py`)
- Wraps standard runner with cost capabilities
- Detects when to use cost-aware engines
- Saves cost data with results

## Key Features

### Protocol-Specific Cost Patterns

#### T&E (Treat & Extend)
- Every visit includes full assessment
- Higher cost per visit (£599 with biosimilar)
- All visits count as decision tasks
- More consultant/decision-maker time required

#### T&T (Treat & Treat)
- Most visits are injection-only
- Lower cost per visit (£529 for injection-only)
- Quarterly full assessments
- Less decision-maker time, more injection task time

### NHS Alignment
- Costs match NHS HRG codes exactly:
  - Injection administration: £134 (HRG BZ86B)
  - OCT scan: £110 (HRG BZ88A)
  - Consultant follow-up: £75 (WF01A)
  - Consultant first visit: £160 (WF01A)
- Validated against NHS wAMD cost calculator

### Data Outputs
- Workload summary (monthly task counts)
- Patient-level cost data
- Cost breakdown by component
- Cost effectiveness metrics
- Task-based resource requirements

## Testing

Two test scripts are provided:

1. `test_cost_tracking.py` - Comprehensive functionality test
2. `test_cost_tracking_protocols.py` - Focused test for T&E and T&T protocols

## Usage

### Running a Simulation with Cost Tracking

1. Go to the Simulations page
2. Select your protocol (T&E or T&T time-based)
3. Enable "Cost Tracking" checkbox
4. Configure drug type and costs if needed
5. Run simulation

### Analyzing Results

1. After simulation completes, go to Cost Analysis page
2. View key metrics and breakdowns
3. Check workload analysis tab for task distribution
4. Export data for further analysis

## Next Steps

The cost tracking implementation is complete and ready for use. Suggested next steps:

1. Run full-scale simulations with both T&E and T&T protocols
2. Compare economic outcomes between protocols
3. Validate workload predictions against real-world data
4. Use results for service planning and commissioning decisions

## Files Created/Modified

### New Files
- `/ape/components/cost_tracking/` - All UI components
- `/simulation_v2/economics/enhanced_cost_tracker.py` - Core tracking logic
- `/simulation_v2/engines/abs_engine_with_enhanced_costs.py` - Cost-aware engine
- `/pages/2_Simulations_with_costs.py` - Updated simulation page
- `/pages/5_Cost_Analysis.py` - New analysis page
- Various planning and test files

### Modified Files
- Updated imports and integration points
- Added cost tracking to simulation workflow

## Key Design Decisions

1. **Task-based not role-based**: Flexibility for different staffing models
2. **NHS HRG alignment**: Accurate UK cost modeling
3. **Protocol awareness**: Different cost patterns for T&E vs T&T
4. **Data presentation only**: No conclusions drawn by the system
5. **Biosimilar default**: Reflects current NHS practice

The implementation is complete and ready for production use with the time-based T&E and T&T protocols.