# Patient Pathway Visualization Experiments

This directory contains tools for visualizing patient pathways from actual simulation results,
including Sankey diagrams and gap-based analysis of treatment patterns.

## Purpose

- Visualize patient journeys from real simulation data
- Analyze treatment gaps and de facto discontinuations
- Create Sankey diagrams showing state transitions
- Compare explicit vs gap-inferred discontinuation patterns

## Structure

```
experiments/
├── README.md                           # This file
├── patient_pathway_viz_plan.md         # Detailed plan for visualization development
├── visualize_simulation_pathways.py    # Main visualization app for simulation results
├── detect_treatment_gaps.py            # Analyze treatment gaps in simulation data
└── visualizations/                     # Saved visualization outputs (gitignored)
```

## Quick Start

1. Run a simulation using the main Streamlit app to generate data

2. Choose your visualization approach:

   **For treatment patterns only (comparable to real-world data):**
   ```bash
   streamlit run treatment_patterns_visualization.py --server.port 8514
   ```
   - Uses ONLY visit dates and intervals
   - NO disease state information
   - Can be directly compared with real-world treatment data
   
   **For complete simulation analysis (includes disease states):**
   ```bash
   streamlit run visualize_simulation_pathways_fast.py --server.port 8513
   ```
   - Uses full simulation data including disease states
   - Shows disease progression (Active, Stable, Highly Active)
   - NOT comparable to real-world data

3. Analyze treatment gaps:
   ```bash
   # Analyze all simulations
   python detect_treatment_gaps.py
   
   # Analyze specific simulation
   python detect_treatment_gaps.py --simulation sim_20250126_123456_abc123
   ```

## Working with Real Data

This visualization system works exclusively with actual simulation results:
- No synthetic or test data generation
- Loads results from `simulation_results/` directory
- Preserves scientific integrity of the analysis

## Gap-Based Analysis

The `detect_treatment_gaps.py` script identifies:
- De facto discontinuations (gaps > max protocol interval)
- Treatment interruptions and resumptions
- Protocol adherence violations
- Patterns that would appear in real-world data

Gap detection parameters:
- Max protocol interval: 112 days (16 weeks) for Eylea
- Scheduling buffer: 14 days
- Minimum discontinuation gap: 180 days (6 months)

## Visualization Features

The main visualization app provides:
- **Patient Flow Overview**: Sankey diagram of all state transitions
- **Discontinuation Analysis**: Focused view on discontinuation pathways
- **Transition Statistics**: Quantitative analysis of patterns

## Integration

Visualizations can be integrated into:
- Main Streamlit app analysis pages
- Patient pathway reports
- Protocol comparison studies

## Example Usage

```python
# In main app, import visualization functions
from experiments.visualize_simulation_pathways import (
    extract_patient_transitions,
    create_patient_flow_sankey
)

# Load simulation results
results = results_manager.load_results(simulation_path)

# Extract transitions
transitions_df = extract_patient_transitions(results)

# Create Sankey diagram
fig = create_patient_flow_sankey(transitions_df)
st.plotly_chart(fig, use_container_width=True)
```

## Tips

1. Run gap analysis to discover hidden patterns in treatment adherence
2. Use the sidebar to switch between different simulations
3. Export visualizations as HTML for sharing
4. Colors are consistent across all visualizations (defined in STATE_COLORS)