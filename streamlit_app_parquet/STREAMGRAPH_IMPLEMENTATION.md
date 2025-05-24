# Streamgraph Implementation Guide

## Overview

The streamgraph visualization provides a dynamic view of patient cohort flow through treatment states over time. Unlike traditional bar charts that show static snapshots, the streamgraph shows:

1. **Cohort size changes** - The overall height represents total patients
2. **State transitions** - Flow between active, discontinued, and retreated states  
3. **Time evolution** - Changes across the full simulation period
4. **Proportional relationships** - Relative sizes of patient groups

## Key Features

### Color Scheme
- **Active patients**: Blue tones (primary color)
- **Discontinued patients**: Warm colors (yellows, oranges, reds)
- **Retreated patients**: Cool colors (blues, purples)

### Special Highlighting
- Newly transitioned patients can be highlighted with brighter colors
- Transitions appear as temporary spikes in the stream

### Data Requirements
**IMPORTANT**: The streamgraph REQUIRES detailed patient history data from the simulation.
- It MUST have patient timeline data with visit histories
- It will FAIL FAST with a clear error message if data is missing
- NO synthetic or fallback data is generated - this is a scientific analysis tool

## Implementation Details

### Module: `streamgraph_discontinuation.py`

Key functions:
- `prepare_cohort_timeline_data()` - Extracts or generates timeline data
- `create_patient_streamgraph()` - Creates the visualization
- `calculate_streamgraph_baseline()` - Implements the "wiggle" algorithm for smooth flows

### Integration

The streamgraph is integrated into the main simulation runner:

```python
# In simulation_runner.py
def generate_discontinuation_plot(results):
    # First try streamgraph
    streamgraph_fig = generate_enhanced_discontinuation_streamgraph(results)
    bar_chart_fig = generate_enhanced_discontinuation_plot(results)
    return [streamgraph_fig, bar_chart_fig]
```

### Display in Streamlit

```python
# In pages/run_simulation.py
if "discontinuation_counts" in results:
    figs = generate_discontinuation_plot(results)
    
    # Show streamgraph first
    st.write("**Patient Cohort Flow**")
    st.pyplot(figs[0])
    st.caption("Streamgraph showing patient lifecycle")
    
    # Show bar chart for detail
    st.write("**Discontinuation Breakdown**")
    st.pyplot(figs[1])
    st.caption("Discontinuation reasons by retreatment status")
```

## Design Decisions

1. **Wiggle Algorithm**: Uses baseline adjustment to minimize visual "wiggling" and create smooth flows
2. **Synthetic Data**: When patient histories aren't available, creates realistic timeline from summary stats
3. **Color Semantics**: Maintains consistent meaning - warm for discontinued, cool for retreated
4. **Legend Grouping**: Groups related states for easier interpretation

## Future Enhancements

1. **Interactive Features**: Hover tooltips showing exact counts
2. **Animation**: Show progression over time
3. **Filtering**: Allow users to focus on specific states
4. **Export Options**: Save as high-resolution image or data table