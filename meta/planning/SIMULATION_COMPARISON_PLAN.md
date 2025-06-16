# Simulation Comparison Feature - Detailed Plan

## Overview
A dedicated comparison page that allows users to select two saved simulations and compare their outcomes side-by-side, with key metrics and visualizations to support clinical decision-making.

## Page Location & Navigation
- **File**: `pages/4_Simulation_Comparison.py` (follows existing numbering)
- **Navigation**: Add to workflow indicator after Simulations
- **Access**: Only shows saved simulations (no live runs)

## Validation Rules
1. **Duration Match**: Both simulations must have the same duration (±30 days tolerance)
2. **Patient Count**: Warning if different, but allow comparison with clear indicator
3. **Time Alignment**: Both must use same time units (months)

## UI Design

### Section 1: Simulation Selection
```
┌─────────────────────────────────────────────────────────────────┐
│ 🔬 Compare Simulation Results                                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Select two simulations to compare:                              │
│                                                                  │
│  Simulation A                    Simulation B                    │
│  [📁 Select simulation ▼]        [📁 Select simulation ▼]       │
│                                                                  │
│  ⚠️ Simulations should have the same duration for valid comparison│
└─────────────────────────────────────────────────────────────────┘
```

### Section 2: Simulation Overview
```
┌─────────────────────────────────┬─────────────────────────────────┐
│ Simulation A Details            │ Simulation B Details            │
├─────────────────────────────────┼─────────────────────────────────┤
│ Protocol: Eylea T&E             │ Protocol: Eylea Fixed Bimonthly │
│ Patients: 1,000                 │ Patients: 1,000                 │
│ Duration: 5 years               │ Duration: 5 years               │
│ Model: Standard                 │ Model: Time-based               │
│ Baseline: Normal (μ=70, σ=10)   │ Baseline: Beta (μ=58.4)        │
│ Run Date: 2024-01-15            │ Run Date: 2024-01-16           │
└─────────────────────────────────┴─────────────────────────────────┘
```

### Section 3: Key Metrics Comparison
```
┌──────────────────────────────────────────────────────────────────┐
│ 📊 Key Outcome Metrics                                           │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│ Visual Acuity (ETDRS Letters)        A          B      Difference│
│ ─────────────────────────────────────────────────────────────── │
│ Baseline Mean                      70.0       58.4        -11.6  │
│ Year 1 Mean                        68.5       57.2        -11.3  │
│ Year 2 Mean                        66.2       55.8        -10.4  │
│ Year 5 Mean (End)                  61.3       52.1         -9.2  │
│ Mean Change from Baseline          -8.7       -6.3         +2.4  │
│                                                                   │
│ Treatment Burden                     A          B      Difference │
│ ─────────────────────────────────────────────────────────────── │
│ Mean Injections/Patient            32.5       38.0         +5.5  │
│ Mean Visits/Patient                42.3       38.0         -4.3  │
│ Injection:Visit Ratio              0.77       1.00        +0.23  │
│                                                                   │
│ Discontinuations                     A          B      Difference │
│ ─────────────────────────────────────────────────────────────── │
│ Total Discontinued                 23.5%      31.2%        +7.7%  │
│ - Poor Vision (<20)                 8.2%      15.3%        +7.1%  │
│ - Treatment Burden                  5.1%       4.8%        -0.3%  │
│ - Other                           10.2%      11.1%        +0.9%  │
└──────────────────────────────────────────────────────────────────┘
```

### Section 4: Visualizations

#### Toggle Control
```
View Mode: [Side-by-Side ◉] [Overlay ○]
```

#### Visual Acuity Over Time
- **Side-by-Side**: Two charts with same y-axis scale (0-85)
- **Overlay**: Single chart, A in blue, B in orange, with legend
- Show mean with confidence bands
- Consistent time axis (months)

#### Injection Frequency Distribution
- Histogram showing distribution of total injections per patient
- Side-by-side only (overlay would be confusing)
- Same x-axis scale for both

#### Visit Patterns (if applicable)
- Month-by-month visit load
- Useful for clinical capacity planning
- Show as line chart or heatmap

#### Discontinuation Timeline
- Cumulative discontinuation curves
- Can work well as overlay
- Different line styles for discontinuation reasons

## Technical Implementation

### Data Loading
```python
# Reuse existing simulation loading logic
from ape.utils.simulation_package import load_simulation_results

# Add comparison-specific validation
def validate_comparison_compatibility(sim_a, sim_b):
    """Check if two simulations can be meaningfully compared."""
    issues = []
    
    # Duration check (must match)
    duration_a = sim_a['metadata']['duration_months']
    duration_b = sim_b['metadata']['duration_months']
    if abs(duration_a - duration_b) > 1:  # 1 month tolerance
        issues.append(f"Duration mismatch: {duration_a} vs {duration_b} months")
    
    # Patient count (warning only)
    patients_a = sim_a['metadata']['n_patients']
    patients_b = sim_b['metadata']['n_patients']
    if patients_a != patients_b:
        st.warning(f"Different patient counts: {patients_a} vs {patients_b}")
    
    return issues
```

### Metric Calculations
```python
def calculate_comparison_metrics(sim_a, sim_b):
    """Calculate key comparison metrics."""
    metrics = {
        'visual_acuity': {
            'baseline': (mean_a, mean_b, diff),
            'year_1': (mean_a, mean_b, diff),
            'year_2': (mean_a, mean_b, diff),
            'final': (mean_a, mean_b, diff),
            'mean_change': (change_a, change_b, diff)
        },
        'treatment_burden': {
            'mean_injections': (inj_a, inj_b, diff),
            'mean_visits': (vis_a, vis_b, diff),
            'injection_ratio': (ratio_a, ratio_b, diff)
        },
        'discontinuations': {
            'total': (pct_a, pct_b, diff),
            'by_reason': {...}
        }
    }
    return metrics
```

### Visualization Components
```python
def create_comparison_chart(data_a, data_b, chart_type, view_mode='side_by_side'):
    """Factory for creating comparison visualizations."""
    if view_mode == 'side_by_side':
        col1, col2 = st.columns(2)
        with col1:
            plot_visual_acuity(data_a, title="Simulation A")
        with col2:
            plot_visual_acuity(data_b, title="Simulation B")
    else:  # overlay
        plot_visual_acuity_overlay(data_a, data_b)
```

## State Management
```python
# Use session state to remember selections
if 'comparison_sim_a' not in st.session_state:
    st.session_state.comparison_sim_a = None
if 'comparison_sim_b' not in st.session_state:
    st.session_state.comparison_sim_b = None
if 'comparison_view_mode' not in st.session_state:
    st.session_state.comparison_view_mode = 'side_by_side'
```

## Future Enhancements (Phase 2)
1. **Export Functionality**
   - PDF report with all comparisons
   - CSV of metric differences
   
2. **Statistical Testing**
   - T-tests for significant differences
   - Confidence intervals on differences
   
3. **Cost Comparison** (when implemented)
   - Total cost difference
   - Cost per vision-year gained
   - Budget impact analysis

4. **Preset Comparisons**
   - Quick buttons for common comparisons
   - "Compare all T&E vs Fixed" batch mode

## File Structure
```
pages/4_Simulation_Comparison.py
├── Import existing components
├── Simulation selection UI
├── Validation logic
├── Metrics calculation
├── Visualization section
│   ├── Toggle control
│   ├── Visual acuity comparison
│   ├── Injection distribution
│   └── Discontinuation patterns
└── Export options (future)
```

## Success Criteria
1. Users can easily select any two saved simulations
2. Clear validation messages for incompatible comparisons
3. Key metrics visible "above the fold"
4. Visualizations load quickly and are responsive
5. Toggle between views is smooth
6. Differences are highlighted clearly (color, +/- indicators)

## Open Questions for Tomorrow
1. Should we add a "swap simulations" button for quick A/B reversal?
2. For overlay plots, should we add a difference plot below (A-B)?
3. Worth adding a "favorite comparisons" feature for frequent analyses?
4. Should the comparison metrics be exportable as a summary table?

## Implementation Notes

### Key Decisions Made
1. **Same duration is required** - Makes comparison meaningful
2. **Side-by-side with optional overlay** - Best of both worlds
3. **Focus on key metrics**: Visual acuity at endpoint, visits, injections, costs
4. **2-way comparison only** - 3-way too complex for initial version
5. **No backward compatibility needed** - Fresh start

### Visual Design Principles
1. **Consistent scales** - All acuity charts use 0-85 y-axis
2. **Clear difference indicators** - Use +/- and color coding
3. **Simulation identity** - Always clear which is A vs B
4. **Data density** - Show key metrics prominently, details on demand

This plan focuses on delivering immediate value while keeping the implementation straightforward. The side-by-side approach with optional overlay gives flexibility without overwhelming complexity.