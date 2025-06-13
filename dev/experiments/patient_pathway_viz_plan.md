# Patient Pathway Visualization Development Plan

## Overview
Develop Sankey diagram visualizations for patient pathways using the new discontinuation system.

## Visualization Options

### 1. Plotly Sankey (Recommended)
- **Pros**: Interactive, beautiful, works great with Streamlit
- **Cons**: Adds dependency (but already installed)
- **Best for**: Main application

### 2. Matplotlib Sankey
- **Pros**: No new dependencies, part of core toolkit
- **Cons**: Less interactive, more complex to build
- **Best for**: Static reports

## Data Generation Strategy

Create standalone scripts that:
1. Generate realistic patient pathway data
2. Save as Parquet files for reuse
3. Allow iterative visualization development
4. Keep data generation separate from visualization

## Proposed Sankey Views

### 1. State Transitions Over Time
```
Time 0 → Month 12 → Month 24 → Final State
- Active → Active → Discontinued (Planned)
- Active → Active → Discontinued (Poor Response)
- Active → Monitoring → Retreated → Active
```

### 2. Discontinuation Flow Analysis
```
All Patients → [Various paths] → Final Discontinuation Reasons
- Shows volume through each discontinuation type
- Highlights where we lose most patients
```

### 3. Treatment Intensity Transitions
```
Intensive → Stable → Max Interval → Discontinued
- Shows progression through treatment phases
```

## Development Approach

1. **Data Generation Script** (`generate_pathway_test_data.py`)
   - Run simulation with new discontinuation system
   - Extract state transitions
   - Save as Parquet with timestamps

2. **Standalone Viz Development** (`develop_sankey_viz.py`)
   - Load test data
   - Experiment with different Sankey layouts
   - Perfect the visualization

3. **Integration** 
   - Add polished visualization to main Streamlit app
   - Use same code with real simulation data

## Benefits
- Parallel development (you work on UI, I work on viz)
- Faster iteration (no need to run full app)
- Reusable test data
- Clean separation of concerns